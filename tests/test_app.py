import json
from tests.calls import CALLS

GOOD = 'sk-or-good-key-0000000000000000'


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
    assert client.post('/api/drop').status_code == 402


def test_full_drop_and_history(client):
    start(client)
    client.put('/api/profile', json={'notes': 'Konzerte Berlin', 'sources': [{'platform': 'reddit', 'value': 'r/berlin'}]})
    client.post('/api/key', json={'key': GOOD})
    r = client.post('/api/drop'); assert r.status_code == 200, r.get_data(as_text=True)
    d = r.get_json()
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
    r = client.post('/api/drop'); assert r.status_code == 502 and r.get_json()['error'] == 'key_invalid'


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
    d = client.post('/api/drop').get_json()
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
    assert client.post('/api/drop').status_code == 200
    assert client.post('/api/drop').status_code == 402


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
