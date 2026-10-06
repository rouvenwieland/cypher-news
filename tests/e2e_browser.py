import sys
from playwright.sync_api import sync_playwright
OUT = sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844}); pg = ctx.new_page()
    errs = []; pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(sys.argv[1]); pg.wait_for_selector('#btnStart'); pg.screenshot(path=OUT + '/1_welcome.png')
    pg.click('#btnStart'); pg.wait_for_selector('#recoveryModal', state='visible'); code = pg.inner_text('#recoveryCode'); print('code', code)
    pg.screenshot(path=OUT + '/2_code.png'); pg.click('#closeCode'); pg.wait_for_selector('#mainApp', state='visible')
    pg.click('.chip[data-topic="Konzerte Berlin"]'); pg.fill('#sourceInput', 'r/berlin'); pg.click('#sourceAdd'); pg.wait_for_selector('.source-chip')
    pg.click('#saveProfile'); pg.screenshot(path=OUT + '/3_profile.png', full_page=True)
    pg.fill('#keyInput', 'sk-or-good-key-0000000000000000'); pg.click('#keySave'); pg.locator('#keyStatus', has_text='gespeichert').wait_for()
    pg.click('[data-tab=drop]'); pg.click('#dropBtn'); pg.wait_for_selector('#resultsArea', state='visible', timeout=30000); pg.wait_for_selector('.story-card')
    pg.wait_for_timeout(1500); pg.screenshot(path=OUT + '/4_drop.png', full_page=True)
    pg.click('#btnFeed'); pg.wait_for_timeout(800); pg.screenshot(path=OUT + '/5_feed.png', full_page=True)
    pg.click('.feed-card [data-act=save]'); pg.click('[data-tab=saved]'); pg.wait_for_selector('#savedContainer .feed-card'); pg.screenshot(path=OUT + '/6_saved.png')
    pg.click('[data-tab=history]'); pg.wait_for_selector('.hist')
    # restore on a second device
    ctx2 = b.new_context(); p2 = ctx2.new_page(); p2.goto(sys.argv[1]); p2.click('#btnShowRestore'); p2.fill('#restoreCode', code); p2.click('#btnRestore')
    p2.wait_for_selector('#mainApp', state='visible'); assert 'Mauerpark' in p2.inner_text('body') or p2.locator('.story-card').count() > 0
    print('console errors:', errs); b.close()
