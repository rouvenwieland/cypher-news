"""Daily drops pause for a profile that has not used the app for 14 days, and resume by themselves at the next visit
("Willkommen zurück – Drops laufen wieder"). "Active" = the user's own browser used the app: opened it (/api/me with a session),
opened a drop, built one, saved the profile (every call that needs the session cookie). The server's own work (scheduler,
keep-awake pings) never counts."""
import sqlite3, time

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from tests.test_verify import _ready

DAY = 86400
NOFIX = settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None, max_examples=60)


def _uid():
    from cypher import db
    return db.all_users()[0]['id']


def _last_seen(uid=None):
    from cypher import db
    return db.all_users()[0]['last_seen']


def _age(days):
    """Pretend the user was last seen `days` days ago."""
    from cypher import db
    t = time.time() - days * DAY
    db.update_user(_uid(), last_seen=t, created=min(t, db.all_users()[0]['created']))   # the account itself is at least that old


# ---------- storage ----------
def test_new_account_counts_as_just_seen(client):
    from tests.test_app import start
    start(client)
    assert abs(_last_seen() - time.time()) < 5


def test_old_database_without_the_column_is_migrated_and_nobody_is_paused(tmp_path, monkeypatch):
    """Rollout: the live DB has no last_seen. Everybody gets 14 days of grace from the deploy, nobody is paused on day one."""
    from cypher import db, scheduler
    old = tmp_path / 'old.db'
    c = sqlite3.connect(old)
    c.execute("CREATE TABLE users(id TEXT PRIMARY KEY, token_hash TEXT UNIQUE, recovery_hash TEXT UNIQUE, created REAL, notes TEXT DEFAULT '', sources TEXT DEFAULT '[]', drop_hour INTEGER DEFAULT 8, tz_offset INTEGER DEFAULT 60, quality TEXT DEFAULT 'fast', key_enc TEXT DEFAULT '', push_sub TEXT DEFAULT '', last_drop_day TEXT DEFAULT '', free_used_day TEXT DEFAULT '', free_used INTEGER DEFAULT 0, feedback TEXT DEFAULT '{}')")
    c.execute("INSERT INTO users(id,token_hash,recovery_hash,created) VALUES('u1','a','b',1000)")   # account from 1970
    c.commit(); c.close()
    monkeypatch.setattr(db, 'DB_PATH', str(old)); monkeypatch.setenv('SECRET_KEY', 'x')
    u = db.all_users()[0]
    assert abs(u['last_seen'] - time.time()) < 5
    assert not scheduler.is_paused(u)
    assert len(db.all_users()) == 1 and db.all_users()[0]['last_seen'] == u['last_seen']   # migrated once, not on every connection


def test_touch_writes_at_most_once_an_hour(client):
    from cypher import db
    from tests.test_app import start
    start(client)
    uid, t0 = _uid(), time.time()
    db.update_user(uid, last_seen=t0 - 7200)
    assert db.touch(uid, now=t0) is True
    assert db.touch(uid, now=t0 + 600) is False               # ten minutes later: no new write
    assert _last_seen() == t0
    assert db.touch(uid, now=t0 + 3601) is True
    assert db.touch('nobody', now=t0 + 9999) is False


# ---------- the rule ----------
def test_threshold_is_14_days():
    from cypher import scheduler
    assert scheduler.PAUSE_AFTER_DAYS == 14
    u = {'last_seen': 0, 'created': 1_000_000.0}
    assert not scheduler.is_paused(u, 1_000_000.0 + 14 * DAY)       # exactly 14 days: still active
    assert scheduler.is_paused(u, 1_000_000.0 + 14 * DAY + 1)


@given(st.floats(0, 3e9), st.floats(0, 3e9), st.floats(0, 100 * DAY))
def test_paused_exactly_when_the_newest_sign_of_life_is_older_than_14_days(created, seen, later):
    from cypher import scheduler
    u = {'created': created, 'last_seen': seen}
    now = max(created, seen) + later
    assert scheduler.is_paused(u, now) == (later > 14 * DAY)


@given(st.floats(0, 3e9), st.floats(0, 100 * DAY), st.floats(0, 100 * DAY))
def test_a_pause_never_ends_without_a_visit(seen, a, b):
    """Monotone: later in time and no visit in between, a paused profile stays paused."""
    from cypher import scheduler
    u = {'created': 0, 'last_seen': seen}
    if scheduler.is_paused(u, seen + a):
        assert scheduler.is_paused(u, seen + a + b)


@given(st.floats(0, 3e9))
def test_missing_or_null_last_seen_falls_back_to_created(created):
    from cypher import scheduler
    assert scheduler.last_active({'created': created, 'last_seen': None}) == created
    assert scheduler.last_active({'created': None, 'last_seen': 5.0}) == 5.0


# ---------- the scheduler ----------
def test_inactive_profile_gets_no_drop_and_nothing_is_booked(client):
    from cypher import db, scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    scheduler._fails.clear()
    assert scheduler.due_users() == [_uid()]              # active: due
    _age(15)
    assert scheduler.due_users() == []
    assert scheduler.run_due() == 0
    assert db.all_users()[0]['last_drop_day'] == '', 'a paused day must not be booked as done: the next visit resumes the drops'
    assert scheduler._fails == {}, 'a pause is not a failure (no retry counter)'
    with db.conn() as c:
        assert c.execute('SELECT COUNT(*) FROM drops').fetchone()[0] == 0


def test_scheduled_run_refuses_a_paused_profile_but_a_manual_one_works(client):
    from cypher import scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    _age(30)
    assert scheduler.run_for_user(_uid()) == (False, 'paused', None)
    ok, err, drop = scheduler.run_for_user(_uid(), manual=True)
    assert ok and drop['items']


def test_visit_resumes_the_drops_and_says_so_once(client):
    from cypher import scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    scheduler._fails.clear()
    assert client.get('/api/me').get_json()['resumed'] is False       # a normal visit
    _age(15)
    assert scheduler.due_users() == []
    me = client.get('/api/me').get_json()
    assert me['resumed'] is True                                       # app shows "Willkommen zurück – Drops laufen wieder"
    assert abs(_last_seen() - time.time()) < 5
    assert scheduler.due_users() == [_uid()]                           # ... and the drops run again
    assert client.get('/api/me').get_json()['resumed'] is False       # only once
    assert scheduler.run_due() == 1


@pytest.mark.parametrize('call', [lambda c: c.get('/api/drops'), lambda c: c.get('/api/saved'),
                                  lambda c: c.put('/api/profile', json={'drop_hour': 9}), lambda c: c.get('/api/export')])
def test_any_session_call_ends_the_pause(client, call):
    from cypher import scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    _age(20)
    assert scheduler.is_paused(__import__('cypher.db', fromlist=['db']).all_users()[0])
    assert call(client).status_code == 200
    assert abs(_last_seen() - time.time()) < 5


def test_opening_an_old_drop_counts(client):
    _ready(client, drop_hour=0, tz_offset=0)
    assert client.post('/api/drop').status_code == 200
    i = client.get('/api/drops').get_json()['drops'][0]['id']
    _age(40)
    assert client.get(f'/api/drops/{i}').status_code == 200
    assert abs(_last_seen() - time.time()) < 5


def test_nothing_to_resume_for_a_profile_without_content(client):
    """A new account that never set anything up has no drops to resume: no welcome-back message."""
    from tests.test_app import start
    start(client)
    _age(60)
    assert client.get('/api/me').get_json()['resumed'] is False


def test_server_side_work_does_not_count_as_a_visit(client):
    """Healthz pings (keep-awake) and the scheduler itself must not keep an abandoned profile alive."""
    from cypher import scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    _age(15)
    before = _last_seen()
    assert client.get('/healthz').status_code == 200
    scheduler.run_due()
    assert client.post('/api/cron', headers={'X-Cron-Secret': 'cron'}).status_code == 200
    anonymous = client.application.test_client()
    assert anonymous.get('/api/me').get_json()['session'] is False
    assert _last_seen() == before


def test_visit_after_the_pause_is_followed_by_exactly_one_drop_for_the_day(client):
    from cypher import db, scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    scheduler._fails.clear()
    _age(15)
    assert scheduler.run_due() == 0
    client.get('/api/me')
    assert scheduler.run_due() == 1 and scheduler.run_due() == 0
    with db.conn() as c:
        assert c.execute('SELECT COUNT(*) FROM drops').fetchone()[0] == 1


@NOFIX
@given(st.lists(st.tuples(st.integers(0, 40 * 24), st.sampled_from(['visit', 'check'])), min_size=1, max_size=12))
def test_timeline_of_visits_and_scheduler_checks(client, events):
    """Random timeline in hours. Model: paused at a check iff the last visit (or the start) is more than 14 days back.
    Visits within the same hour may not be written (throttle), so the model allows one hour of slack at the boundary."""
    from cypher import db, scheduler
    if not db.all_users():
        _ready(client, drop_hour=0, tz_offset=0)
    uid = _uid()
    t0 = 1_800_000_000.0
    db.update_user(uid, last_seen=t0, created=t0)
    last_visit = t0
    now = t0
    for hours, kind in sorted(events):
        now = t0 + hours * 3600
        if kind == 'visit':
            db.touch(uid, now=now)
            last_visit = max(last_visit, now)
            continue
        u = db.all_users()[0]
        idle = now - last_visit
        paused = scheduler.is_paused(u, now)
        if idle > 14 * DAY + 3600:
            assert paused, f'{idle / DAY:.2f} days idle must be paused'
        if idle <= 14 * DAY - 3600:
            assert not paused, f'{idle / DAY:.2f} days idle must not be paused'
