import json
from tests.calls import CALLS

GOOD = 'sk-or-good-key-0000000000000000'


def run_drop(c, timeout=20):
    """POST /api/drop starts a background job; poll the status like the browser does. Returns (http_status_of_result, json)."""
    import time
    r = c.post('/api/drop', headers={'X-Client': '2'})
    if r.status_code != 202:
        return r.status_code, r.get_json()
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = c.get('/api/drop/status').get_json()
        if st['state'] == 'done':
            return 200, st['drop']
        if st['state'] == 'error':
            return (402 if st['error'] in ('no_key', 'no_credit') else 400 if st['error'] == 'no_profile' else 502), {'error': st['error']}
        time.sleep(0.1)
    raise AssertionError('drop did not finish')


def start(c):
    r = c.post('/api/start'); assert r.status_code == 200
    return r.get_json()['recovery']


def test_session_and_profile(client):
    assert client.get('/api/me').get_json()['session'] is False
    rec = start(client)
    assert client.post('/api/start').status_code == 409
    assert client.put('/api/profile', json={'notes': 'Konzerte Berlin', 'sources': [{'platform': 'reddit', 'value': 'r/berlin'}, {'platform': 'evil', 'value': 'x'}]}).status_code == 200
    me = client.get('/api/me').get_json()
    assert me['notes'] == 'Konzerte Berlin' and me['sources'] == [{'platform': 'reddit', 'value': 'r/berlin'}]
    other = client.application.test_client()
    assert other.get('/api/me').get_json()['session'] is False
    assert other.post('/api/restore', json={'code': rec}).status_code == 200
    assert other.get('/api/me').get_json()['notes'] == 'Konzerte Berlin'
    assert client.get('/api/me').get_json()['session'] is False  # old device is logged out


def test_requires_auth_and_csrf(client):
    assert client.get('/api/drops').status_code == 401
    start(client)
    assert client.put('/api/profile', json={'notes': 'x'}, headers={'Origin': 'https://evil.example'}).status_code == 403


def test_key_validation_and_encryption(client):
    start(client)
    assert client.post('/api/key', json={'key': 'nope'}).status_code == 400
    assert client.post('/api/key', json={'key': 'sk-or-bad-key-0000000000000000'}).status_code == 400
    assert client.post('/api/key', json={'key': GOOD}).status_code == 200
    import cypher.db as db
    with db.conn() as c:
        raw = c.execute('SELECT key_enc FROM users').fetchone()[0]
    assert raw and GOOD not in raw and db.decrypt(raw) == GOOD
    assert client.get('/api/me').get_json()['has_key'] is True
    assert GOOD not in client.get('/api/me').get_data(as_text=True)


def test_drop_without_key_is_402(client):
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte'})
    assert run_drop(client)[0] == 402


def test_full_drop_and_history(client):
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte Berlin', 'sources': [{'platform': 'reddit', 'value': 'r/berlin'}]})
    client.post('/api/key', json={'key': GOOD})
    code, d = run_drop(client); assert code == 200, d
    assert d['items'][0]['title'] == 'Erster Treffer' and d['meta']['model'] == 'test/primary:free'
    assert CALLS and all(a == f'Bearer {GOOD}' for a, _ in CALLS)
    assert client.get('/api/drops').get_json()['drops'][0]['count'] == len(d['items'])
    assert client.get(f"/api/drops/{d['id']}").get_json()['title'] == 'Testdrop'


def test_bad_user_key_gives_502_or_402_not_crash(client):
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte'})
    import cypher.db as db
    u = db.all_users()[0]
    db.update_user(u['id'], key_enc=db.encrypt('sk-or-bad-key-0000000000000000'))
    code, d = run_drop(client); assert code == 502 and d['error'] == 'key_invalid'


def test_saved_feedback_share_export_delete(client):
    start(client)
    client.post('/api/saved', json={'title': 'T', 'url': 'https://x.y', 'image': 'javascript:alert(1)'})
    s = client.get('/api/saved').get_json()['saved']; assert len(s) == 1 and s[0]['image'] == ''
    client.delete('/api/saved', json={'title': 'T'}); assert client.get('/api/saved').get_json()['saved'] == []
    assert client.post('/api/feedback', json={'account': 'r/berlin', 'category': 'Konzerte', 'vote': 1}).status_code == 200
    assert client.post('/api/shared', data={'text': 'Giveaway https://insta.example/p/1'}).status_code == 200
    assert client.post('/api/shared', data={}).status_code == 400
    assert client.get('/api/export').status_code == 200
    assert client.delete('/api/me').status_code == 200
    assert client.get('/api/me').get_json()['session'] is False


def test_shared_item_enters_next_drop(client):
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte'}); client.post('/api/key', json={'key': GOOD})
    client.post('/api/shared', data={'text': 'Verlosung bis Sonntag https://example.com/v'})
    code, d = run_drop(client); assert code == 200
    import cypher.db as db
    with db.conn() as c:
        assert c.execute('SELECT used FROM shared').fetchone()[0] == 1


def test_cron_and_scheduler(client):
    assert client.post('/api/cron').status_code == 403
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte', 'drop_hour': 0, 'tz_offset': 0}); client.post('/api/key', json={'key': GOOD})
    import cypher.scheduler as s
    assert s.run_due() == 1
    assert s.run_due() == 0  # already delivered today


def test_free_quota(client, monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-server-key-00000000000000')
    start(client); client.put('/api/profile', json={'notes': 'Konzerte'})
    assert client.get('/api/me').get_json()['free_left'] == 1
    assert run_drop(client)[0] == 200
    assert run_drop(client)[0] == 402


def test_ssrf_guard():
    from cypher import sources
    for u in ('http://127.0.0.1/x', 'http://localhost:5000', 'http://169.254.169.254/', 'file:///etc/passwd', 'ftp://a.b'):
        assert not sources.is_public_url(u)


def test_detect():
    from cypher import sources
    assert sources.detect('https://www.instagram.com/foo.bar/')[0] == 'instagram'
    assert sources.detect('https://www.tiktok.com/@abc')[:2] == ('tiktok', 'abc')
    assert sources.detect('r/berlin')[0] == 'reddit' and sources.detect('me@mastodon.social')[0] == 'mastodon'


def test_backup_roundtrip(client, tmp_path, monkeypatch):
    from cypher import backup, db
    start(client)
    uploaded = []
    h = backup.upload_if_changed(None, upload=lambda p: uploaded.append(open(p, 'rb').read()))
    assert uploaded and backup.upload_if_changed(h, upload=lambda p: uploaded.append(1)) == h and len(uploaded) == 1
    # restore into a fresh path
    monkeypatch.setenv('HF_TOKEN', 'x'); monkeypatch.setenv('BACKUP_REPO', 'a/b')
    new = tmp_path / 'restored.db'; monkeypatch.setattr(db, 'DB_PATH', str(new))
    src = tmp_path / 'snap.db'; src.write_bytes(uploaded[0])
    assert backup.restore(download=lambda: str(src)) and len(db.all_users()) == 1


def test_get_follows_redirects_only_to_public_hosts(fake_or, monkeypatch):
    """Regression: get() crashed on every call; and redirects must be re-checked against the SSRF guard."""
    from cypher import sources
    monkeypatch.setattr(sources, 'is_public_url', lambda u: u.startswith(fake_or))
    r, body = sources.get(fake_or + '/auth/key', headers={'Authorization': 'Bearer sk-or-good-key-0000000000000000'})
    assert r.status_code == 200
    import pytest
    with pytest.raises(ValueError):
        sources.get('http://169.254.169.254/')


def test_zero_config_secrets(client, monkeypatch):
    """No SECRET_KEY / VAPID env: the app generates stable ones, so a user never has to copy secrets."""
    monkeypatch.delenv('SECRET_KEY'); monkeypatch.delenv('VAPID_PRIVATE_KEY', raising=False)
    from cypher import db, push
    token = db.encrypt('hello')
    assert db.decrypt(token) == 'hello'
    k1 = push.public_key(); assert len(k1) > 60 and push.public_key() == k1
    assert client.get('/api/me').get_json()['vapid'] == k1


def test_source_test_endpoint(client):
    start(client)
    r = client.post('/api/sources/test', json={'platform': 'reddit', 'value': 'r/berlin'}).get_json()
    assert r['count'] == 1 and 'Mauerpark' in r['sample']
    assert client.post('/api/sources/test', json={'platform': 'evil', 'value': 'x'}).status_code == 400


def test_model_lists_from_env(monkeypatch):
    from cypher import ai
    monkeypatch.setenv('MODEL_VISION', 'a/x:free, b/y:free'); monkeypatch.setenv('MODEL_PRIMARY', 'c/z:free'); monkeypatch.delenv('MODEL_FALLBACK', raising=False)
    assert ai.vision_models() == ['a/x:free', 'b/y:free'] and ai.text_models() == ['c/z:free']


def test_restored_backup_is_writable(client, tmp_path, monkeypatch):
    """Regression (day-2 outage): the HF cache file is read-only (0444); a plain copy made the DB read-only -> 'attempt to write a readonly database'."""
    import os, stat
    from cypher import backup, db
    start(client)
    snap = backup.snapshot(); os.chmod(snap, 0o444)
    monkeypatch.setenv('HF_TOKEN', 'x'); monkeypatch.setenv('BACKUP_REPO', 'a/b')
    new = tmp_path / 'restored.db'; monkeypatch.setattr(db, 'DB_PATH', str(new))
    assert backup.restore(download=lambda: snap) == 'restored'
    assert os.stat(new).st_mode & stat.S_IWUSR, 'restored DB must be writable by its owner'
    db.create_user()  # a write works
    assert len(db.all_users()) == 2


def test_failed_restore_never_leaves_empty_db_and_blocks_start(client, tmp_path, monkeypatch):
    import pytest
    from cypher import backup, db
    monkeypatch.setenv('HF_TOKEN', 'x'); monkeypatch.setenv('BACKUP_REPO', 'a/b')
    new = tmp_path / 'never.db'; monkeypatch.setattr(db, 'DB_PATH', str(new))
    bad = tmp_path / 'garbage'; bad.write_bytes(b'not a database' * 100)
    assert backup.restore(download=lambda: str(bad)) == 'error' and not new.exists()
    monkeypatch.setattr(backup, 'restore', lambda download=None: 'error')
    monkeypatch.setattr(backup.time, 'sleep', lambda s: None)
    with pytest.raises(RuntimeError):
        backup.restore_or_die()


def test_scheduler_retries_transient_failures(client, monkeypatch):
    from cypher import db, scheduler
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte', 'drop_hour': 0, 'tz_offset': 0}); client.post('/api/key', json={'key': GOOD})
    scheduler._fails.clear()
    calls = {'n': 0}
    real = scheduler.pipeline.build_drop
    def flaky(*a, **k):
        calls['n'] += 1
        if calls['n'] == 1:
            from cypher import ai
            raise ai.AIError('all_models_failed: boom')
        return real(*a, **k)
    monkeypatch.setattr(scheduler.pipeline, 'build_drop', flaky)
    assert scheduler.run_due() == 0                      # first attempt fails (transient)
    assert db.all_users()[0]['last_drop_day'] == ''      # NOT marked as done for the day
    assert scheduler.run_due() == 0                      # retry is delayed
    monkeypatch.setattr(scheduler, 'RETRY_AFTER', 0)
    assert scheduler.run_due() == 1                      # second attempt succeeds
    assert db.all_users()[0]['last_drop_day'] != ''


def test_no_key_is_not_retried(client):
    from cypher import db, scheduler
    start(client); scheduler._fails.clear()
    client.put('/api/profile', json={'notes': 'Konzerte', 'drop_hour': 0, 'tz_offset': 0})
    assert scheduler.run_due() == 0 and db.all_users()[0]['last_drop_day'] != ''


def test_drop_job_survives_concurrent_clicks(client):
    start(client); client.put('/api/profile', json={'notes': 'Konzerte'}); client.post('/api/key', json={'key': GOOD})
    assert client.get('/api/drop/status').get_json()['state'] == 'idle'
    assert client.post('/api/drop', headers={'X-Client': '2'}).status_code == 202
    assert client.post('/api/drop', headers={'X-Client': '2'}).status_code == 202   # second click does not start a second job


def test_static_code_is_never_cached_stale(client):
    """Regression: the service worker served an old app.js forever, so the old client rendered {state:'running'} as an empty drop."""
    for path in ('/static/js/app.js', '/static/css/app.css', '/sw.js'):
        assert 'no-cache' in client.get(path).headers['Cache-Control']
    sw = client.get('/sw.js').get_data(as_text=True)
    assert 'cypher-news-v5' in sw and 'network first' in sw







def test_x_detect_and_platform_picker(client):
    from cypher import sources
    assert sources.detect('https://x.com/OpenAI')[:2] == ('x', 'OpenAI') and sources.detect('twitter:@sama')[:2] == ('x', 'sama')
    start(client)
    assert client.post('/api/sources/detect', json={'value': '@OpenAI', 'platform': 'x'}).get_json() == {'platform': 'x', 'value': 'OpenAI'}
    assert client.post('/api/sources/detect', json={'value': '@openai'}).get_json()['platform'] is None
    assert client.put('/api/profile', json={'sources': [{'platform': 'x', 'value': 'OpenAI'}]}).status_code == 200
    assert client.get('/api/me').get_json()['sources'] == [{'platform': 'x', 'value': 'OpenAI'}]




def test_old_database_gets_migrated(tmp_path, monkeypatch):
    import sqlite3
    from cypher import db
    old = tmp_path / 'old.db'
    c = sqlite3.connect(old); c.execute("CREATE TABLE users(id TEXT PRIMARY KEY, token_hash TEXT UNIQUE, recovery_hash TEXT UNIQUE, created REAL, notes TEXT DEFAULT '', sources TEXT DEFAULT '[]', drop_hour INTEGER DEFAULT 8, tz_offset INTEGER DEFAULT 60, quality TEXT DEFAULT 'fast', key_enc TEXT DEFAULT '', push_sub TEXT DEFAULT '', last_drop_day TEXT DEFAULT '', free_used_day TEXT DEFAULT '', free_used INTEGER DEFAULT 0, feedback TEXT DEFAULT '{}')")
    c.execute("INSERT INTO users(id,token_hash,recovery_hash,created) VALUES('u1','a','b',0)"); c.commit(); c.close()
    monkeypatch.setattr(db, 'DB_PATH', str(old)); monkeypatch.setenv('SECRET_KEY', 'x')
    assert db.all_users()[0]['x_token_enc'] == ''   # existing user kept, new column present


def test_shared_x_link_is_read(client, monkeypatch):
    from cypher import db, sources
    class R: status_code = 200
    payload = b'{"text":"Neues Modell! https://t.co/zzz","created_at":"2026-10-11T07:00:00.000Z","user":{"screen_name":"OpenAI"},"photos":[{"url":"https://pbs.twimg.com/media/p.jpg"}]}'
    monkeypatch.setattr(sources, 'get', lambda url, **kw: (R(), payload))
    monkeypatch.setattr(sources, 'thumb_b64', lambda u, **kw: 'QUJD')
    start(client)
    assert client.post('/api/shared', data={'text': 'schau https://x.com/OpenAI/status/12345'}).status_code == 200
    with db.conn() as c:
        row = c.execute('SELECT text,url,image_b64 FROM shared').fetchone()
    assert 'Neues Modell!' in row['text'] and 't.co' not in row['text'] and row['url'] == 'https://x.com/OpenAI/status/12345' and row['image_b64'] == 'QUJD'
    assert sources.x_tweet('https://example.com/nothing') is None


NITTER_RSS = b'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>OpenAI / @OpenAI</title>
<item><title>RT by @OpenAI: Fresh updates for dots</title><description><![CDATA[<p>Fresh updates for dots.<br/>Create yours on iOS https://t.co/abc</p><img src="https://nitter.example.org/pic/media%2FGabc123.jpg%3Fname%3Dorig" />]]></description>
<pubDate>Fri, 09 Oct 2026 19:12:31 GMT</pubDate><link>https://nitter.example.org/ChatGPT/status/2108636745915052037#m</link></item>
<item><title>R to @someone: danke</title><description><![CDATA[<p>danke</p>]]></description><pubDate>Fri, 09 Oct 2026 18:00:00 GMT</pubDate><link>https://nitter.example.org/OpenAI/status/2108000000000000001#m</link></item>
<item><title>GPT-6 ist da</title><description><![CDATA[<p>GPT-6 ist da</p><img src="https://pbs.twimg.com/media/Hdirect.jpg" />]]></description><pubDate>Thu, 08 Oct 2026 18:26:38 GMT</pubDate><link>https://nitter.example.org/OpenAI/status/2108262812489531498#m</link></item>
</channel></rss>'''


def test_x_via_nitter_mirrors(monkeypatch):
    from cypher import sources
    monkeypatch.setenv('NITTER_HOSTS', 'dead.example.org,bot.example.org,ok.example.org')
    class R:
        def __init__(self, code): self.status_code = code
    def fake_get(url, **kw):
        if 'dead.' in url: raise ValueError('down')
        if 'bot.' in url: return R(200), b'<!DOCTYPE html><title>Checking you are not a bot</title>'
        return R(200), NITTER_RSS
    monkeypatch.setattr(sources, 'get', fake_get)
    items = sources.x('@OpenAI')     # first mirror is down, second shows a bot check, third works
    assert [i['url'] for i in items] == ['https://x.com/ChatGPT/status/2108636745915052037', 'https://x.com/OpenAI/status/2108262812489531498']  # reply skipped
    assert items[0]['text'].startswith('RT Fresh updates') and 't.co' not in items[0]['text']
    assert items[1]['image_url'] == 'https://pbs.twimg.com/media/Hdirect.jpg'  # mirror links twimg directly
    assert items[0]['image_url'] == 'https://pbs.twimg.com/media/Gabc123.jpg' and items[0]['platform'] == 'x' and items[0]['account'] == '@OpenAI'
    assert sources.x('https://x.com/OpenAI/status/1')[0]['account'] == '@OpenAI' and sources.x('not a handle!!!') == []


def test_x_all_mirrors_down_returns_empty(monkeypatch):
    from cypher import sources
    monkeypatch.setenv('NITTER_HOSTS', 'a.example.org,b.example.org')
    monkeypatch.setattr(sources, 'get', lambda url, **kw: (_ for _ in ()).throw(ValueError('down')))
    assert sources.x('openai') == []


def test_nitter_host_list_comes_from_status_page_with_fallback(client, monkeypatch):
    from cypher import sources
    monkeypatch.delenv('NITTER_HOSTS', raising=False)
    class R: status_code = 200
    page = b'{"hosts":[{"domain":"a.example.org","points":50,"rss":true},{"domain":"b.example.org","points":90,"rss":true},{"domain":"c.example.org","points":99,"rss":false},{"domain":"evil host","points":1,"rss":true}]}'
    monkeypatch.setattr(sources, 'get', lambda url, **kw: (R(), page))
    hosts = sources.nitter_hosts()
    assert hosts[:2] == ['b.example.org', 'a.example.org'] and 'c.example.org' not in hosts and 'evil host' not in hosts and 'nitter.kareem.one' in hosts
    from cypher import db
    db.cache_set('nitter_hosts', None)  # cache poisoned/empty -> still usable
    monkeypatch.setattr(sources, 'get', lambda url, **kw: (_ for _ in ()).throw(ValueError('down')))
    db.cache_set('nitter_hosts', None)
    assert sources.nitter_hosts() == sources.STATIC_NITTER or 'nitter.kareem.one' in sources.nitter_hosts()


def test_legacy_client_still_gets_the_finished_drop(client):
    """Regression (phone showed '0 Treffer aus 0 von 0 Quellen'): an old cached client expects the drop itself in the POST response."""
    start(client); client.put('/api/profile', json={'notes': 'Konzerte Berlin'}); client.post('/api/key', json={'key': GOOD})
    r = client.post('/api/drop')                       # no X-Client header = old client
    assert r.status_code == 200 and r.get_json()['items'][0]['title'] == 'Erster Treffer' and r.get_json()['meta']['model']
    client.delete('/api/key')
    assert client.post('/api/drop').status_code == 402  # old clients get the old error codes too
    assert "'X-Client': '2'" in open('static/js/app.js').read()
