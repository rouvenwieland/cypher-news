import os, sys
from datetime import datetime
from playwright.sync_api import sync_playwright
OUT = sys.argv[2]
with sync_playwright() as p:
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'   # CI image; elsewhere Playwright's own Chromium (or CHROMIUM=<path>)
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or (exe if os.path.exists(exe) else None), args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Europe/Berlin', locale='de-DE'); pg = ctx.new_page()
    errs = []; pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(sys.argv[1]); pg.wait_for_selector('#btnStart'); pg.screenshot(path=OUT + '/1_welcome.png')
    pg.click('#btnStart'); pg.wait_for_selector('#recoveryModal', state='visible'); code = pg.inner_text('#recoveryCode'); print('code', code)
    pg.screenshot(path=OUT + '/2_code.png'); pg.click('#closeCode'); pg.wait_for_selector('#mainApp', state='visible')
    pg.click('.chip[data-topic="Konzerte Berlin"]'); pg.fill('#sourceInput', 'r/berlin'); pg.click('#sourceAdd'); pg.wait_for_selector('.source-chip')
    pg.click('#saveProfile'); pg.screenshot(path=OUT + '/3_profile.png', full_page=True)
    pg.fill('#keyInput', 'sk-or-good-key-0000000000000000'); pg.click('#keySave'); pg.locator('#keyStatus', has_text='gespeichert').wait_for()
    pg.click('[data-tab=drop]'); pg.click('#dropBtn'); pg.wait_for_selector('#resultsArea', state='visible', timeout=30000); pg.wait_for_selector('.feed-card')
    pg.wait_for_timeout(1500); pg.screenshot(path=OUT + '/4_drop.png', full_page=True)
    pg.click('#btnFeed'); pg.wait_for_timeout(800); pg.screenshot(path=OUT + '/5_feed.png', full_page=True)
    pg.click('.feed-card [data-act=save]'); pg.click('[data-tab=saved]'); pg.wait_for_selector('#savedContainer .feed-card'); pg.screenshot(path=OUT + '/6_saved.png')
    pg.click('[data-tab=history]'); pg.wait_for_selector('.hist')
    # --- drop times: only 06:00-23:00 Berlin time (the free server sleeps at night, see DEPLOY.md) ---
    def hours(page):
        return page.evaluate("() => [...document.querySelectorAll('#dropHour option')].filter((o) => !o.disabled).map((o) => +o.value)")
    assert hours(pg) == list(range(6, 24)), hours(pg)
    assert pg.input_value('#dropHour') == '8'
    assert '06:00 bis 23:00 Uhr Berlin-Zeit' in pg.text_content('#dropHint')
    pg.click('[data-tab=profile]'); pg.screenshot(path=OUT + '/7_profile_rhythm.png', full_page=True)
    # an older setting outside the window arrives at the start of the window, and the app says so
    pg.evaluate("() => api('/api/profile', 'PUT', {drop_hour: 3})"); pg.reload(); pg.wait_for_selector('#mainApp', state='visible')
    assert pg.input_value('#dropHour') == '6' and '06:00 Uhr' in pg.text_content('#dropInfo'), (pg.input_value('#dropHour'), pg.text_content('#dropInfo'))
    # other time zones see their own local hours (browser time zone data, date pinned so summer/winter time cannot change the result)
    for tz, expect in (('America/New_York', list(range(0, 18))), ('Asia/Tokyo', list(range(0, 7)) + list(range(13, 24)))):
        cx = b.new_context(timezone_id=tz, locale='de-DE'); cx.clock.set_fixed_time(datetime(2026, 7, 15, 12, 0))
        assert cx.request.post(sys.argv[1].rstrip('/') + '/api/start').ok
        px = cx.new_page(); px.goto(sys.argv[1]); px.wait_for_selector('#mainApp', state='visible')
        assert hours(px) == expect, (tz, hours(px))
        assert 'Berlin-Zeit' in px.text_content('#dropHint') and 'Möglich bei dir' in px.text_content('#dropHint'), px.text_content('#dropHint')
        cx.close()
    # a profile whose drops were paused (14 days away): the app welcomes the user back (the server flag is faked here, see tests/test_pause.py)
    def resumed(route):
        if route.request.method != 'GET':
            return route.continue_()
        r = route.fetch(); body = r.json(); body['resumed'] = True
        route.fulfill(response=r, json=body)
    pg.route('**/api/me', resumed); pg.reload()
    pg.locator('#toast', has_text='Willkommen zurück – Drops laufen wieder').wait_for(timeout=15000)
    pg.screenshot(path=OUT + '/8_welcome_back.png'); pg.unroute('**/api/me')
    # restore on a second device
    ctx2 = b.new_context(); p2 = ctx2.new_page(); p2.goto(sys.argv[1]); p2.click('#btnShowRestore'); p2.fill('#restoreCode', code); p2.click('#btnRestore')
    p2.wait_for_selector('#mainApp', state='visible'); p2.wait_for_selector('.feed-card', state='attached', timeout=15000)   # the last drop loads after the app is shown
    assert 'Mauerpark' in p2.text_content('body') or p2.locator('.feed-card').count() > 0
    print('console errors:', errs); b.close()
