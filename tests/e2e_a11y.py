"""Browser checks for the accessibility fixes (dialog, errors, focus, labels, targets, reflow, axe). Not collected by pytest.

    venv\\Scripts\\python tests\\e2e_server.py 5055            (server with fake AI, in one terminal)
    python tests\\e2e_a11y.py http://127.0.0.1:5055           (any Python that has playwright; exit code 1 on a failed check)

Restart the server before each run: the app limits /api/start to 10 and /api/restore to 8 per hour and a run uses 5 and 2.
Optional environment: AXE_JS=<path to axe.min.js> adds the axe-core runs (serious/critical findings fail), CHROMIUM=<chrome executable>.
"""
import os, sys
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5055').rstrip('/')
AXE = open(os.environ['AXE_JS'], encoding='utf-8').read() if os.environ.get('AXE_JS') else ''
GOOD = 'sk-or-good-key-0000000000000000'
FAILS = []


def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '   -> ' + str(detail)))
    if not ok:
        FAILS.append(name)


def active(pg):
    return pg.evaluate("() => { const a = document.activeElement; return a ? {tag: a.tagName, id: a.id, label: a.getAttribute('aria-label') || '', text: (a.textContent || '').trim().slice(0, 40), cls: a.className} : null }")


def wait_until(pg, fn, timeout=5000):
    """Poll a JS function (page.wait_for_function needs eval, which the page's CSP forbids)."""
    for _ in range(timeout // 100):
        if pg.evaluate(fn):
            return True
        pg.wait_for_timeout(100)
    return False


def settle(pg):
    """After the dialog the app finishes booting (loads data, opens the profile page for a new account, moves the focus)."""
    wait_until(pg, "() => document.title.startsWith('Profil') && document.activeElement && document.activeElement.tagName === 'H1'")


def landing(b, **ctx):
    c = b.new_context(**ctx); pg = c.new_page()
    pg.goto(BASE); pg.wait_for_selector('#preloader.gone', state='attached', timeout=20000)
    return c, pg


def new_user(b, **ctx):
    c, pg = landing(b, **ctx)
    pg.click('#btnStart'); pg.wait_for_selector('#recoveryModal', state='visible'); code = pg.inner_text('#recoveryCode')
    pg.click('#closeCode'); pg.wait_for_selector('#mainApp', state='visible')
    settle(pg)
    return c, pg, code


def drop_item(i, long=False):
    t = f'Meldung {i}' + (' mit einem sehr langen Titel, der in einer schmalen Karte über viele Zeilen umbricht und trotzdem nicht abgeschnitten werden darf' if long else '')
    s = 'Zusammenfassung ' + str(i) + (' ' + 'Dieser Text ist absichtlich lang, damit er bei Zoom und Textabstand viele Zeilen braucht. ' * 8 if long else '.')
    return {'category': ['Konzerte', 'Tech', 'Drops'][i % 3], 'title': t, 'summary': s, 'when': 'Heute', 'source': 'Testblatt', 'account': 'Testblatt', 'platform': 'news', 'url': 'https://example.com/' + str(i)}


def show_drop(pg, n=3, long=False, view='feed'):
    pg.evaluate("([items, v]) => { showTab('drop', false, true); renderDrop({title: 'Testausgabe', intro: 'Hallo.', date: 'Heute', meta: {sources_ok: 1, sources_total: 1}, items}); setView(v); }", [[drop_item(i, long) for i in range(n)], view])
    pg.wait_for_timeout(2600)      # let the reveal animation finish (colour contrast is measured on the final state)


def theme(pg, t):
    pg.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", t); pg.wait_for_timeout(700)


def axe(pg, name):
    if not AXE:
        return
    pg.evaluate(AXE)
    # .sig-noise: aria-hidden decoration (random words that fade out); WCAG 1.4.3 exempts pure decoration
    res = pg.evaluate("axe.run({exclude: [['.sig-noise']]}, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']}})")
    bad = [(v['impact'], v['id'], len(v['nodes']), v['nodes'][0]['target']) for v in res['violations'] if v['impact'] in ('serious', 'critical')]
    soft = [(v['impact'], v['id'], len(v['nodes']), v['nodes'][0]['target']) for v in res['violations'] if v['impact'] not in ('serious', 'critical')]
    check('axe ' + name + ' (0 serious/critical)', not bad, bad)
    if soft:
        print('     note (minor/moderate):', soft)


def small_targets(pg):
    return pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('button, a[href], input:not([type=hidden]), select, textarea, summary, [tabindex="0"]').forEach((e) => {
        const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
        if (!r.width || !r.height || cs.visibility === 'hidden' || e.closest('[hidden], [inert]') || e.classList.contains('skip') || e.classList.contains('sr-only')) return;
        if (e.tagName === 'A' && e.closest('p, li') && getComputedStyle(e).display === 'inline') return;      // inline text link: exempt (WCAG 2.5.8)
        if (r.width < 43.5 || r.height < 43.5) out.push((e.id || e.className || e.tagName) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
      });
      return out;
    }""")


def overflow_x(pg):
    return pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")


def clipped_text(pg):
    return pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('.story-card, .story-body, .story-body h2, .story-body .summary, .feed-card, .art-title, .fsum').forEach((e) => {
        if (e.closest('[hidden], .hidden') || !e.offsetParent) return;
        if (e.scrollHeight > e.clientHeight + 1) out.push((e.className || e.tagName) + ' ' + e.scrollHeight + '>' + e.clientHeight);
      });
      return out;
    }""")


def tab_walk(pg, label, minimum):
    """Tab from <main> through the page: every visible control gets the focus in DOM order (no trap, nothing skipped) and shows a focus indicator."""
    pg.evaluate("window.scrollTo(0, 0)"); pg.evaluate("document.querySelector('#main').focus()")
    n = pg.evaluate("""() => { window.__exp = [...document.querySelectorAll('#mainApp button, #mainApp a[href], #mainApp input, #mainApp select, #mainApp textarea, #mainApp summary, #mainApp [tabindex="0"]')]
      .filter((e) => e.getBoundingClientRect().width && !e.closest('[hidden]') && getComputedStyle(e).visibility !== 'hidden' && !(e.tagName !== 'SUMMARY' && e.closest('details:not([open])'))); return window.__exp.length; }""")
    wrong, no_ring = [], []
    for i in range(n):
        pg.keyboard.press('Tab')
        r = pg.evaluate("""(i) => { const e = document.activeElement, cs = getComputedStyle(e), f = /^(INPUT|SELECT|TEXTAREA)$/.test(e.tagName);
          return {same: e === window.__exp[i], k: e.id || e.getAttribute('aria-label') || (e.textContent || '').trim().slice(0, 24),
            ring: (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || (f && cs.boxShadow !== 'none')}; }""", i)
        if not r['same']:
            wrong.append((i, r['k']))
        if not r['ring']:
            no_ring.append(r['k'])
    check('%s: Tab walks through every control in order (%d stops), no trap' % (label, n), n >= minimum and not wrong, wrong[:5])
    check('%s: every focus stop shows a focus indicator' % label, not no_ring, no_ring)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or None)

        # ---------- landing, start dialog ----------
        c, pg = landing(b, viewport={'width': 390, 'height': 844})
        errs = []; pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') and 'password' not in m.text.lower() else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        check('landing title', pg.title() == 'Cypher News - Daily Drop', pg.title())
        pg.wait_for_timeout(3000)
        axe(pg, 'landing dark'); theme(pg, 'light'); axe(pg, 'landing light'); theme(pg, 'dark')
        check('landing: touch targets >= 44 px', not small_targets(pg), small_targets(pg))
        pg.click('#btnStart'); pg.wait_for_selector('#recoveryModal', state='visible')
        code = pg.inner_text('#recoveryCode')
        check('dialog: start focus is the heading, not "Gespeichert"', active(pg)['id'] == 'recoveryTitle', active(pg))
        check('dialog: described by hint and code', pg.get_attribute('#recoveryModal', 'aria-describedby') == 'recoveryHint recoveryCode')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
        check('dialog: Escape does not close (code is shown once)', pg.is_visible('#recoveryModal'))
        check('dialog: Escape explains itself and moves to "Gespeichert"', 'nur einmal' in pg.inner_text('#recoveryNote') and active(pg)['id'] == 'closeCode', (pg.inner_text('#recoveryNote'), active(pg)))
        pg.keyboard.press('Tab'); check('dialog: Tab wraps from last to first', active(pg)['id'] == 'copyCode', active(pg))
        pg.keyboard.press('Shift+Tab'); check('dialog: Shift+Tab wraps back', active(pg)['id'] == 'closeCode', active(pg))
        pg.click('#copyCode'); pg.wait_for_timeout(200)
        check('dialog: copy result shown inside the dialog', pg.inner_text('#recoveryNote').strip().startswith(('Kopiert', 'Kopieren nicht')), pg.inner_text('#recoveryNote'))
        axe(pg, 'recovery dialog')
        pg.click('#closeCode'); pg.wait_for_selector('#mainApp', state='visible')
        wait_until(pg, "() => document.title.startsWith('Profil')")
        check('title after first start (profile page)', pg.title() == 'Profil - Cypher News', pg.title())
        wait_until(pg, "() => document.activeElement && document.activeElement.tagName === 'H1'")
        check('focus after the dialog: heading of the page that is shown', active(pg)['text'] == 'Profil', active(pg))

        # ---------- profile: errors next to the fields ----------
        pg.click('#sourceAdd'); pg.wait_for_timeout(100)
        check('source: empty input -> alert text at the field', pg.is_visible('#sourceError') and pg.get_attribute('#sourceInput', 'aria-invalid') == 'true' and 'sourceError' in pg.get_attribute('#sourceInput', 'aria-describedby'))
        check('source error element is role=alert', pg.get_attribute('#sourceError', 'role') == 'alert')
        pg.fill('#sourceInput', 'foobar'); check('source: typing clears the error', not pg.is_visible('#sourceError') and pg.get_attribute('#sourceInput', 'aria-invalid') is None)
        pg.click('#sourceAdd'); pg.wait_for_timeout(500)
        check('source: unknown platform -> persistent error', 'nicht erkannt' in pg.inner_text('#sourceError'), pg.inner_text('#sourceError'))
        check('source: invalid field keeps focus', active(pg)['id'] == 'sourceInput', active(pg))
        pg.wait_for_timeout(4500)
        check('source: error outlives the toast (still there after 4.5 s)', pg.is_visible('#sourceError'))
        axe(pg, 'profile with error')
        pg.fill('#keyInput', 'abc'); pg.click('#keySave'); pg.wait_for_timeout(400)
        check('key: format error at the field', pg.is_visible('#keyError') and pg.get_attribute('#keyInput', 'aria-invalid') == 'true' and 'sk-or-' in pg.inner_text('#keyError'), pg.inner_text('#keyError'))
        pg.fill('#keyInput', 'sk-or-bad-key-0000000000000000'); pg.click('#keySave'); pg.wait_for_timeout(500)
        check('key: rejected key error at the field', 'lehnt' in pg.inner_text('#keyError'), pg.inner_text('#keyError'))
        pg.fill('#keyInput', GOOD); pg.click('#keySave'); pg.locator('#keyStatus', has_text='gespeichert').wait_for()
        check('key: error gone after success', not pg.is_visible('#keyError') and pg.get_attribute('#keyInput', 'aria-describedby') is None)
        pg.click('.chip[data-topic="Konzerte Berlin"]'); pg.fill('#sourceInput', 'r/berlin'); pg.click('#sourceAdd'); pg.wait_for_selector('.source-chip')
        pg.click('#saveProfile'); pg.locator('#toast', has_text='Gespeichert').wait_for()

        # ---------- segment switch: visible selection ----------
        seg = pg.evaluate("""() => {
          const s = document.querySelector('#qualitySeg'), cs = getComputedStyle(s, '::before'), b = s.querySelector('[aria-pressed=true]'), bs = getComputedStyle(b), bb = getComputedStyle(b, '::before');
          return {shadow: cs.boxShadow, accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(), weight: bs.fontWeight, check: bb.width, other: getComputedStyle(s.querySelector('[aria-pressed=false]')).fontWeight};
        }""")
        check('segment: selected has a 2 px frame in --accent, bold text and a check mark', 'inset' in seg['shadow'] and '2px' in seg['shadow'] and int(seg['weight']) >= 700 and seg['check'] == '5px' and int(seg['other']) < 700, seg)
        pg.screenshot(path=os.environ.get('SHOTS', '.') + '/seg-profile.png', clip=pg.evaluate("(() => { const r = document.querySelector('#qualitySeg').getBoundingClientRect(); return {x: Math.max(0, r.x - 8), y: r.y - 8, width: Math.min(390, r.width + 16), height: r.height + 16}; })()")) if os.environ.get('SHOTS') else None

        # ---------- profile: tab order, targets, axe ----------
        check('profile: touch targets >= 44 px', not small_targets(pg), small_targets(pg))
        tab_walk(pg, 'profile', 15)
        axe(pg, 'profile dark'); theme(pg, 'light'); axe(pg, 'profile light'); theme(pg, 'dark')

        # ---------- drop button: stays focusable while busy ----------
        posts = []
        pg.on('request', lambda r: posts.append(r.url) if r.method == 'POST' and r.url.endswith('/api/drop') else None)
        pg.click('[data-tab=drop]')
        check('tab click: focus goes to the heading of the page', active(pg)['tag'] == 'H1', active(pg))
        pg.focus('#dropBtn'); pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
        st = pg.evaluate("() => ({dis: document.getElementById('dropBtn').disabled, aria: document.getElementById('dropBtn').getAttribute('aria-disabled'), act: document.activeElement.id})")
        check('drop button: aria-disabled while busy, not disabled, keeps the focus', not st['dis'] and st['aria'] == 'true' and st['act'] == 'dropBtn', st)
        pg.keyboard.press('Enter'); pg.keyboard.press('Space'); pg.wait_for_timeout(300)
        check('drop button: clicks while busy are ignored', len(posts) == 1, posts)
        pg.wait_for_selector('#dropBtn[aria-disabled="false"]', timeout=60000); pg.wait_for_selector('.feed-card')
        check('drop done: focus moves to the title', active(pg)['id'] == 'introTitle', active(pg))
        check('document title', pg.title() == 'Heute - Cypher News', pg.title())

        # ---------- save toggle labels ----------
        sv = pg.locator('.feed-card [data-act=save]').first
        l0, p0 = sv.get_attribute('aria-label'), sv.get_attribute('aria-pressed'); sv.click(); pg.wait_for_timeout(300)
        l1, p1 = sv.get_attribute('aria-label'), sv.get_attribute('aria-pressed')
        check('save toggle: fixed label "Merken: <Titel>", aria-pressed switches', l0 == l1 and l0.startswith('Merken: ') and p0 == 'false' and p1 == 'true', (l0, l1, p0, p1))

        # ---------- saved list: focus after removal ----------
        for i in (1, 2, 3):
            pg.evaluate("(t) => api('/api/saved', 'POST', {title: t, summary: 'x', category: 'Tech', when: 'Heute', source: 'Testblatt', url: 'https://example.com/' + t})", f'Merk {i}')
        pg.click('[data-tab=saved]'); pg.wait_for_selector('#savedContainer .feed-card'); pg.wait_for_timeout(500)
        check('tab click: focus on heading of "Gemerkt"', active(pg)['tag'] == 'H1' and active(pg)['text'] == 'Gemerkt', active(pg))
        un = pg.locator('#savedContainer [data-act=unsave]')
        check('saved: remove button has a clear label and no aria-pressed', un.first.get_attribute('aria-label').startswith('Aus Gemerkt entfernen: ') and un.first.get_attribute('aria-pressed') is None)
        n0 = un.count()
        un.nth(1).focus(); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
        a = active(pg)
        check('unsave (middle): focus goes to the next entry', pg.locator('#savedContainer [data-act=unsave]').count() == n0 - 1 and 'Merk 1' in a['label'] and a['tag'] == 'BUTTON', a)
        last = pg.locator('#savedContainer [data-act=unsave]').last; last.focus(); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
        a = active(pg)
        check('unsave (last): focus goes to the previous entry', a['tag'] == 'BUTTON' and 'Merk 1' in a['label'], a)
        axe(pg, 'saved'); theme(pg, 'light'); axe(pg, 'saved light'); theme(pg, 'dark')
        while pg.locator('#savedContainer [data-act=unsave]').count():
            pg.locator('#savedContainer [data-act=unsave]').first.click(); pg.wait_for_timeout(350)
        a = active(pg)
        check('unsave (all gone): focus on the empty-state note', 'empty' in a['cls'] and 'Noch nichts gemerkt' in pg.inner_text('#savedContainer'), a)

        # ---------- history -> drop ----------
        pg.click('[data-tab=history]'); pg.wait_for_selector('.hist'); pg.wait_for_timeout(500)
        check('tab click: focus on heading of "Verlauf"', active(pg)['text'] == 'Verlauf', active(pg))
        check('title: Verlauf', pg.title() == 'Verlauf - Cypher News', pg.title())
        axe(pg, 'history'); theme(pg, 'light'); axe(pg, 'history light'); theme(pg, 'dark')
        pg.click('.hist'); pg.wait_for_timeout(600)
        check('history -> drop: focus on the drop title', active(pg)['id'] == 'introTitle', active(pg))

        # ---------- drop screens: axe, targets ----------
        show_drop(pg, 4)
        check('drop (feed): touch targets >= 44 px', not small_targets(pg), small_targets(pg))
        tab_walk(pg, 'drop (feed)', 15)
        axe(pg, 'drop feed'); theme(pg, 'light'); axe(pg, 'drop feed light'); theme(pg, 'dark')
        show_drop(pg, 4, view='stories')
        check('drop (cards): touch targets >= 44 px', not small_targets(pg), small_targets(pg))
        tab_walk(pg, 'drop (cards)', 15)
        axe(pg, 'drop cards'); theme(pg, 'light'); axe(pg, 'drop cards light'); theme(pg, 'dark')
        # direct entry: the title of the page that is shown
        pg.reload(); pg.wait_for_selector('#mainApp', state='visible'); pg.wait_for_timeout(1200)
        check('direct entry: document title is the tab title', pg.title() == 'Heute - Cypher News', pg.title())
        errs = [e for e in errs if not e.startswith('Failed to load resource')]      # the 400/404 answers are the error cases tested on purpose above
        check('console clean', not errs, errs)
        c.close()

        # ---------- restore errors (landing) ----------
        c, pg = landing(b, viewport={'width': 390, 'height': 844})
        pg.click('#btnShowRestore'); pg.click('#btnRestore'); pg.wait_for_timeout(150)
        check('restore: empty -> error at the field', pg.is_visible('#restoreError') and pg.get_attribute('#restoreCode', 'aria-invalid') == 'true' and active(pg)['id'] == 'restoreCode')
        pg.fill('#restoreCode', '0000-0000-0000-0000'); pg.click('#btnRestore'); pg.wait_for_timeout(500)
        check('restore: unknown code -> persistent "Code nicht gefunden"', 'nicht gefunden' in pg.inner_text('#restoreError') and pg.get_attribute('#restoreError', 'role') == 'alert' and 'restoreError' in pg.get_attribute('#restoreCode', 'aria-describedby'), pg.inner_text('#restoreError'))
        pg.wait_for_timeout(4500)
        check('restore: error still there after the toast time', pg.is_visible('#restoreError'))
        axe(pg, 'landing with restore error')
        pg.fill('#restoreCode', code); check('restore: typing clears the error', not pg.is_visible('#restoreError') and pg.get_attribute('#restoreCode', 'aria-invalid') is None)
        pg.click('#btnRestore'); pg.wait_for_selector('#mainApp', state='visible')
        check('restore: works with the right code', True)
        c.close()

        # ---------- start fails: message at the button that was used ----------
        c, pg = landing(b, viewport={'width': 390, 'height': 844})
        pg.route('**/api/start', lambda r: r.fulfill(status=500, content_type='application/json', body='{}'))
        pg.click('#btnStart'); pg.wait_for_timeout(300)
        check('start fails: persistent alert at the button', pg.is_visible('#startError') and pg.get_attribute('#startError', 'role') == 'alert' and 'startError' in pg.get_attribute('#btnStart', 'aria-describedby'), pg.inner_text('#startError') if pg.is_visible('#startError') else 'hidden')
        pg.click('.l-final [data-start]'); pg.wait_for_timeout(300)
        check('start fails (bottom button): the message appears next to that button', pg.is_visible('#startErrorFinal') and 'startErrorFinal' in pg.get_attribute('.l-final [data-start]', 'aria-describedby'))
        pg.wait_for_timeout(4500)
        check('start fails: message outlives the toast time', pg.is_visible('#startErrorFinal'))
        c.close()

        # ---------- cards: no cut-off text, zoom 200 / 400 %, text spacing ----------
        c, pg, _ = new_user(b, viewport={'width': 390, 'height': 844}, bypass_csp=True)       # bypass_csp only to inject the text-spacing test style
        show_drop(pg, 3, long=True, view='stories')
        check('cards (390 px): no clipped text', not clipped_text(pg), clipped_text(pg))
        pg.add_style_tag(content='* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; } p { margin-bottom: 2em !important; }')
        pg.wait_for_timeout(200)
        check('cards (text spacing WCAG 1.4.12): no clipped text', not clipped_text(pg), clipped_text(pg))
        c.close()
        for zoom, (w, h) in ((2, (640, 512)), (4, (320, 256))):
            c, pg = landing(b, viewport={'width': w, 'height': h}, device_scale_factor=zoom)
            check(f'zoom {zoom * 100} %: landing has no horizontal scroll', overflow_x(pg) <= 1, overflow_x(pg))
            pg.click('#btnStart'); pg.wait_for_selector('#recoveryModal', state='visible')
            check(f'zoom {zoom * 100} %: dialog buttons reachable', pg.evaluate("() => { const r = document.querySelector('#closeCode').getBoundingClientRect(); return r.right <= innerWidth + 1 && r.left >= -1; }"))
            check(f'zoom {zoom * 100} %: dialog from title to buttons reachable by scrolling', pg.evaluate("() => { const m = document.getElementById('recoveryModal'); m.scrollTop = 0; const t = document.getElementById('recoveryTitle').getBoundingClientRect().top; m.scrollTop = m.scrollHeight; return t >= -1 && document.getElementById('closeCode').getBoundingClientRect().bottom <= innerHeight + 1; }"))
            pg.click('#closeCode'); pg.wait_for_selector('#mainApp', state='visible'); settle(pg)
            check(f'zoom {zoom * 100} %: profile has no horizontal scroll', overflow_x(pg) <= 1, overflow_x(pg))
            show_drop(pg, 3, long=True, view='feed')
            check(f'zoom {zoom * 100} %: feed has no horizontal scroll or clipped text', overflow_x(pg) <= 1 and not clipped_text(pg), (overflow_x(pg), clipped_text(pg)))
            show_drop(pg, 3, long=True, view='stories')
            check(f'zoom {zoom * 100} %: cards have no horizontal page scroll and no clipped text', overflow_x(pg) <= 1 and not clipped_text(pg), (overflow_x(pg), clipped_text(pg)))
            c.close()

        # ---------- reduced motion ----------
        c, pg = landing(b, viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
        check('reduced motion: no preloader, no cinema mode', pg.evaluate("() => !document.getElementById('preloader') || getComputedStyle(document.getElementById('preloader')).display === 'none'") and pg.evaluate("() => !document.body.classList.contains('cin')"))
        axe(pg, 'landing reduced motion')
        pg.click('#btnStart'); pg.wait_for_selector('#recoveryModal', state='visible')
        pg.click('#closeCode'); pg.wait_for_selector('#mainApp', state='visible'); settle(pg)
        show_drop(pg, 3, view='stories')
        pg.focus('#storyNext')
        for _ in range(4):
            pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
        st = pg.evaluate("() => ({id: document.activeElement.id, aria: document.getElementById('storyNext').getAttribute('aria-disabled'), dis: document.getElementById('storyNext').disabled})")
        check('cards: "Nächste Karte" keeps the focus on the last card (aria-disabled)', st == {'id': 'storyNext', 'aria': 'true', 'dis': False}, st)
        check('reduced motion: transitions are (nearly) off', pg.evaluate("() => parseFloat(getComputedStyle(document.querySelector('.seg > button')).transitionDuration) < 0.05"))
        c.close()
        b.close()

    print('\n%d check(s) failed' % len(FAILS) if FAILS else '\nall checks passed')
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
