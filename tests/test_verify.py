"""Verification tests (2026-10): each test pins one suspected defect found by reading the code."""
import json, threading, time

import pytest

from tests.calls import CALLS
from tests.test_app import GOOD, run_drop, start


def _ready(client, notes='Konzerte', **prof):
    start(client)
    client.put('/api/profile', json=dict({'notes': notes}, **prof))
    client.post('/api/key', json={'key': GOOD})


def _item(n, text, url, acct='r/berlin', platform='reddit'):
    return {'platform': platform, 'account': acct, 'kind': 'post', 'text': text, 'url': url,
            'taken_at': '2026-10-06T10:00:00+00:00', 'image_url': ''}


# V1: dedupe must not merge different posts that only share a placeholder text ("Bild-Post")
@pytest.mark.xfail(strict=True, reason="V-open")
def test_dedupe_keeps_captionless_posts_of_different_accounts(client, monkeypatch):
    from cypher import pipeline, sources
    posts = [_item(i, 'Bild-Post', f'https://example.com/p/{i}', acct=f'@acc{i}', platform='instagram') for i in range(3)]
    monkeypatch.setattr(sources, 'news', lambda t: [])
    monkeypatch.setitem(sources.FETCHERS, 'instagram', lambda v: [posts[int(v)]])
    _ready(client, sources=[{'platform': 'instagram', 'value': str(i)} for i in range(3)])
    code, d = run_drop(client)
    assert code == 200
    assert d['meta']['candidates'] == 3, d['meta']


# V2: shared items beyond the 10 fetched must not be marked as used (lost); and a failed drop must not consume them
@pytest.mark.xfail(strict=True, reason="V-open")
def test_shared_items_survive_overflow_and_failed_drop(client, monkeypatch):
    from cypher import db, sources, ai
    monkeypatch.setattr(sources, 'news', lambda t: [])
    _ready(client)
    for i in range(12):
        client.post('/api/shared', data={'text': f'Geteilt Nummer {i} https://example.com/s{i}'})
    with db.conn() as c:
        assert c.execute('SELECT COUNT(*) FROM shared WHERE used=0').fetchone()[0] == 12
    from cypher import pipeline
    real = ai.chat_chain
    monkeypatch.setattr(ai, 'chat_chain', lambda *a, **k: (_ for _ in ()).throw(ai.AIError('rate_limited')))
    code, d = run_drop(client)
    assert code == 502
    with db.conn() as c:
        left = c.execute('SELECT COUNT(*) FROM shared WHERE used=0').fetchone()[0]
    assert left == 12, f'{12 - left} shared items lost although no drop was delivered'


@pytest.mark.xfail(strict=True, reason="V-open")
def test_shared_overflow_beyond_ten_stays_for_next_drop(client, monkeypatch):
    from cypher import db, sources
    monkeypatch.setattr(sources, 'news', lambda t: [])
    _ready(client)
    for i in range(12):
        client.post('/api/shared', data={'text': f'Geteilt Nummer {i} https://example.com/s{i}'})
    assert run_drop(client)[0] == 200
    with db.conn() as c:
        assert c.execute('SELECT COUNT(*) FROM shared WHERE used=0').fetchone()[0] == 2


# V3: a failed (empty) news fetch must not be cached for 3 hours for every user
@pytest.mark.xfail(strict=True, reason="V-open")
def test_failed_news_fetch_is_not_cached(client, monkeypatch):
    from cypher import db, pipeline, sources
    calls = []
    def flaky(t):
        calls.append(t)
        return [] if len(calls) == 1 else [_item(0, f'{t}: Meldung', 'https://example.com/n1', 'Blatt', 'news')]
    monkeypatch.setattr(sources, 'news', flaky)
    _ready(client)
    u = db.all_users()[0]
    items1, _ = pipeline.collect(u, ['Konzerte'], [])
    items2, _ = pipeline.collect(u, ['Konzerte'], [])
    assert len(calls) == 2 and len(items2) == 1


# V4: concurrent runs for one user must produce only one scheduled drop per day
@pytest.mark.xfail(strict=True, reason="V-open")
def test_concurrent_scheduled_runs_build_one_drop(client, monkeypatch):
    from cypher import db, scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    scheduler._fails.clear()
    real = scheduler.pipeline.build_drop
    def slow(*a, **k):
        time.sleep(0.4)
        return real(*a, **k)
    monkeypatch.setattr(scheduler.pipeline, 'build_drop', slow)
    ts = [threading.Thread(target=scheduler.run_due) for _ in range(3)]
    [t.start() for t in ts]; [t.join() for t in ts]
    with db.conn() as c:
        n = c.execute('SELECT COUNT(*) FROM drops').fetchone()[0]
    assert n == 1, f'{n} drops for one user and one day'


# V5: deleting the account during a running build must not leave a drop behind
@pytest.mark.xfail(strict=True, reason="V-open")
def test_delete_during_build_leaves_no_drop(client, monkeypatch):
    from cypher import db, scheduler
    _ready(client)
    real = scheduler.pipeline.build_drop
    def build_then_delete(u, *a, **k):
        d = real(u, *a, **k)
        db.delete_user(u['id'])
        return d
    monkeypatch.setattr(scheduler.pipeline, 'build_drop', build_then_delete)
    uid = db.all_users()[0]['id']
    scheduler.run_for_user(uid, manual=True)
    with db.conn() as c:
        assert c.execute('SELECT COUNT(*) FROM drops').fetchone()[0] == 0


# V6: a transient push error (HTTP 5xx) must not delete the subscription; only 404/410 may
@pytest.mark.xfail(strict=True, reason="V-open")
def test_transient_push_error_keeps_subscription(client, monkeypatch):
    from cypher import db, push, scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    sub = {'endpoint': 'https://push.example.com/abc', 'keys': {'p256dh': 'x', 'auth': 'y'}}
    assert client.post('/api/push', json=sub).status_code == 200
    import pywebpush

    class R:  # minimal response stand-in
        def __init__(self, code): self.status_code = code
    def boom(*a, **k):
        raise pywebpush.WebPushException('server error', response=R(503))
    monkeypatch.setattr(pywebpush, 'webpush', boom)
    monkeypatch.setattr(push, 'keys', lambda: {'private': 'x', 'public': 'y'})
    uid = db.all_users()[0]['id']
    scheduler.run_for_user(uid, manual=False)
    assert db.all_users()[0]['push_sub'], 'subscription deleted after a 503'


def test_gone_push_subscription_is_removed(client, monkeypatch):
    from cypher import db, push, scheduler
    _ready(client)
    sub = {'endpoint': 'https://push.example.com/abc', 'keys': {'p256dh': 'x', 'auth': 'y'}}
    client.post('/api/push', json=sub)
    import pywebpush

    class R:
        status_code = 410
    def gone(*a, **k):
        raise pywebpush.WebPushException('gone', response=R())
    monkeypatch.setattr(pywebpush, 'webpush', gone)
    monkeypatch.setattr(push, 'keys', lambda: {'private': 'x', 'public': 'y'})
    scheduler.run_for_user(db.all_users()[0]['id'], manual=False)
    assert db.all_users()[0]['push_sub'] == ''


# V7: backup snapshots must not pile up in the temp dir
@pytest.mark.xfail(strict=True, reason="V-open")
def test_snapshot_temp_is_cleaned_after_upload(client, tmp_path, monkeypatch):
    import os
    from cypher import backup
    start(client)
    seen = []
    backup.upload_if_changed(None, upload=lambda p: seen.append(p))
    assert seen and not os.path.exists(seen[0]), 'snapshot copy left behind in temp dir'


# V8: invalid profile values are a client error, not a crash
@pytest.mark.xfail(strict=True, reason="V-open")
def test_profile_garbage_gives_400_not_500(client):
    start(client)
    assert client.put('/api/profile', json={'drop_hour': 'abc'}).status_code == 400
    assert client.put('/api/profile', json={'tz_offset': None}).status_code == 400
    assert client.put('/api/profile', json={'sources': ['x', 5]}).status_code in (200, 400)
