"""Source-level guards for the accessibility fixes (round 2). The browser checks live in tests/e2e_a11y.py;
these run everywhere (no browser) and stop the fixes from being undone by an edit."""
import os, re

ROOT = os.path.join(os.path.dirname(__file__), '..')


def read(*p):
    return open(os.path.join(ROOT, *p), encoding='utf-8').read()


HTML, JS = read('templates', 'index.html'), read('static', 'js', 'app.js')
APP_CSS, STYLE_CSS = read('static', 'css', 'app.css'), read('static', 'css', 'style.css')


def rule(css, selector):
    """Body of the first rule whose selector list contains `selector` exactly."""
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', re.sub(r'/\*.*?\*/', '', css, flags=re.S)):
        if selector in [x.strip() for x in m.group(1).split(',')]:
            return m.group(2)
    raise AssertionError('no CSS rule for ' + selector)


def px(css, selector, prop):
    m = re.search(prop + r':\s*(\d+)px', rule(css, selector))
    assert m, (selector, prop)
    return int(m.group(1))


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def token(block_start, name):
    i = STYLE_CSS.index(block_start)
    return re.search('--' + name + r':\s*(#[0-9a-fA-F]{6})', STYLE_CSS[i:]).group(1)


# ---- 4 segment switch
def test_segment_selection_has_accent_frame_and_contrast():
    assert 'inset 0 0 0 2px var(--accent)' in rule(STYLE_CSS, '.seg::before')
    assert 'font-weight: 700' in rule(STYLE_CSS, '.seg > button[aria-pressed="true"]')
    assert 'opacity: 1' in rule(STYLE_CSS, '.seg > button[aria-pressed="true"]::before')       # check mark
    for block in (':root {', ':root[data-theme="light"] {'):                                 # the frame must be 3:1 against track and thumb (WCAG 1.4.11)
        accent = token(block, 'accent')
        assert ratio(accent, token(block, 'surface')) >= 3 and ratio(accent, token(block, 'surface-2')) >= 3, block


# ---- 6 errors next to the field
def test_every_error_message_has_a_persistent_alert_element():
    used = set(re.findall(r"setErr\([^,()]+(?:\([^()]*\))?,\s*'(\w+)'", JS)) | set(re.findall(r"clearOnInput\([^,]+,\s*'(\w+)'", JS)) | {'startError', 'startErrorFinal'}
    in_html = set(re.findall(r'<p class="field-error" id="(\w+)" role="alert" hidden></p>', HTML))
    assert used == in_html, (used ^ in_html)
    assert re.search(r'<input[^>]*id="restoreCode"', HTML) and 'CODE_RE' in JS


def test_errors_are_not_only_toasts():
    assert 'toast(\'Code nicht gefunden' not in JS and "Code nicht gefunden. Prüfe" in JS
    assert re.search(r'id="toast" role="status"', HTML) and re.search(r'id="toastErr" role="alert"', HTML)
    # a field error needs the three links: text with role=alert, aria-describedby and (inputs) aria-invalid
    set_err = JS[JS.index('function setErr'):JS.index('const clearOnInput')]
    assert 'aria-describedby' in set_err and 'aria-invalid' in set_err
    assert 'aria-invalid' in STYLE_CSS and '.field-error' in STYLE_CSS


# ---- 7 focus
def test_busy_buttons_use_aria_disabled_not_disabled():
    assert not re.search(r'\.disabled\s*=', JS) and 'disabled =' not in JS
    assert 'aria-disabled' in JS and 'isOff(' in JS
    assert '[disabled]' not in STYLE_CSS + APP_CSS and '[aria-disabled="true"]' in STYLE_CSS and '[aria-disabled="true"]' in APP_CSS


def test_tab_change_focuses_page_heading_and_unsave_keeps_focus():
    assert "$('main').focus" not in JS[JS.index('function showTab'):JS.index("$('tabNav')")]
    for h in ('<h1 tabindex="-1">Noch kein Drop.</h1>', '<h1 class="page-title" tabindex="-1">Profil</h1>', '<h1 class="page-title" tabindex="-1">Gemerkt</h1>', '<h1 class="page-title" tabindex="-1">Verlauf</h1>', '<h1 id="introTitle" tabindex="-1">'):
        assert h in HTML, h
    unsave = JS[JS.index("$('savedContainer').addEventListener"):JS.index('function dayParts')]
    assert 'card.remove()' in unsave and '.focus()' in unsave and 'loadSaved()' not in unsave


# ---- 8 dialog
def test_recovery_dialog_is_safe_for_a_code_shown_once():
    dlg = re.search(r'<div class="modal-overlay" id="recoveryModal"[^>]*>', HTML).group(0)
    assert 'aria-modal="true"' in dlg and 'aria-describedby="recoveryHint recoveryCode"' in dlg
    assert 'id="recoveryTitle" tabindex="-1"' in HTML and 'id="recoveryNote" role="status"' in HTML
    assert "$('recoveryTitle').focus()" in JS and "$('closeCode').focus();" not in JS[JS.index('function openRecovery'):JS.index('function setNote')]
    keys = JS[JS.index("$('recoveryModal').addEventListener('keydown'"):JS.index("$('closeCode').addEventListener")]
    assert "e.key === 'Escape'" in keys and 'hidden = true' not in keys           # Escape never closes: the code is shown only once
    assert "e.key !== 'Tab'" in keys                                              # focus trap
    assert 'Escape' in read('DESIGN.md')                                          # the decision is documented
    assert 'overflow-y: auto' in rule(STYLE_CSS, '.modal-overlay') and 'margin: auto' in rule(STYLE_CSS, '.modal-card')   # reachable at 400 % zoom


# ---- 9 label
def test_save_toggle_has_a_fixed_label():
    assert 'Gemerkt, zum Entfernen' not in JS
    assert 'data-act="save" data-i="${i}" aria-pressed="${saved}" aria-label="Merken: ${t}"' in JS
    assert 'aria-label="Aus Gemerkt entfernen: ${t}"' in JS and 'data-act="unsave" data-title="${t}" aria-label' in JS


# ---- 10 cards
def test_cards_grow_with_their_text():
    assert not re.search(r'(?<![-\w])height:', rule(APP_CSS, '.stories-container'))       # no fixed height (min-height / --card-h are fine)
    assert 'min-height: var(--card-h)' in rule(APP_CSS, '.story-card') and 'height: 100%' not in rule(APP_CSS, '.story-card')
    assert 'height: 100%' not in rule(APP_CSS, '.stories-inner')
    for sel in ('.story-body h2', '.story-body .summary', '.story-body'):
        r = rule(APP_CSS, sel)
        assert 'line-clamp' not in r and 'overflow: hidden' not in r, sel


# ---- 11 title, touch targets
def test_document_title_on_direct_entry():
    boot = JS[JS.index('async function bootApp'):JS.index('function tzChanges')]
    assert 'setTitle(' in boot and 'Heute' in JS


def test_touch_targets_are_44px_for_every_pointer():
    assert px(APP_CSS, '.chip', 'min-height') >= 44 and px(APP_CSS, '.cat-filters .chip', 'min-height') >= 44
    assert px(APP_CSS, '.source-chip', 'min-height') >= 44 and px(APP_CSS, '.source-chip .remove', 'width') >= 44
    assert px(STYLE_CSS, '.seg > button', 'min-height') >= 44            # includes .q-btn
    assert 'pointer: coarse' not in APP_CSS                              # not only for touch screens


# ---- the page serves the new elements
def test_index_serves_error_elements(client):
    html = client.get('/').get_data(as_text=True)
    for i in ('startError', 'restoreError', 'sourceError', 'keyError', 'saveError', 'toastErr'):
        assert f'id="{i}"' in html
