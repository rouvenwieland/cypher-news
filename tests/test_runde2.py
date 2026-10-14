"""Verification round 2 (2026-10-14): all-day keep-awake, daylight saving time (25.10.2026), restart in the middle of a run.
Each test pins one defect found by reading "what happens between two steps"."""
import os, shutil, sqlite3, subprocess, threading, time
from datetime import datetime, timezone

import pytest

from tests.test_verify import _ready

END_DST_2026 = 1792890000    # 2026-10-25T01:00Z: Europe/Berlin goes from +120 (CEST) to +60 (CET)
START_DST_2027 = 1806195600  # 2027-03-28T01:00Z: back to +120


class _Clock:
    def __init__(self, iso):
        self.set(iso)

    def set(self, iso):
        self.t = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


def _freeze(monkeypatch, clock):
    from cypher import scheduler
    real = scheduler.datetime

    class FakeDT(real):
        @classmethod
        def now(cls, tz=None):
            return clock.t if tz else clock.t.replace(tzinfo=None)
    monkeypatch.setattr(scheduler, 'datetime', FakeDT)


def _uid():
    from cypher import db
    return db.all_users()[0]['id']


# R2-C1: tz_offset is a fixed number. On 25.10.2026 every user who has not opened the app since 03:00 got the drop one hour
# EARLY (06:00 instead of 07:00), in March one hour LATE. The always-awake service now builds it reliably at the wrong time.
def test_dst_end_drop_stays_at_chosen_local_hour(client, monkeypatch):
    from cypher import scheduler
    _ready(client, drop_hour=7, tz_offset=120, tz_changes=[[END_DST_2026, 60]])
    clock = _Clock('2026-10-25T05:30:00')  # 06:30 CET; the stale summer offset says 07:30
    _freeze(monkeypatch, clock)
    scheduler._fails.clear()
    assert scheduler.due_users() == [], 'drop would come at 06:00 CET instead of 07:00'
    clock.set('2026-10-25T06:05:00')     # 07:05 CET
    assert scheduler.due_users() == [_uid()]


def test_dst_start_drop_is_not_an_hour_late(client, monkeypatch):
    from cypher import scheduler
    _ready(client, drop_hour=7, tz_offset=60, tz_changes=[[START_DST_2027, 120]])
    _freeze(monkeypatch, _Clock('2027-03-28T05:30:00'))  # 07:30 CEST; the stale winter offset says 06:30
    scheduler._fails.clear()
    assert scheduler.due_users() == [_uid()], 'drop would come at 08:00 CEST instead of 07:00'


def test_tz_changes_are_validated(client):
    from tests.test_app import start
    start(client)
    for bad in ('x', [[1, 2, 3]], [['a', 60]], [[1, 60]] * 9, [None], {'t': 1}):
        assert client.put('/api/profile', json={'tz_changes': bad}).status_code == 400, bad
    assert client.put('/api/profile', json={'tz_changes': [[END_DST_2026 + 10, 60], [END_DST_2026, 999]]}).status_code == 200


# R2-C2: the day of a scheduled drop was taken AFTER the build. A build that runs across local midnight (drop hour 23, late
# start because of retries or a queue) was booked on the NEXT day, so the next day's own drop was silently skipped.
def test_build_across_midnight_is_booked_on_the_day_it_was_due(client, monkeypatch):
    from cypher import db, scheduler
    _ready(client, drop_hour=23, tz_offset=0)
    clock = _Clock('2026-11-02T23:58:00')
    _freeze(monkeypatch, clock)
    scheduler._fails.clear()
    real = scheduler.pipeline.build_drop

    def slow(*a, **k):
        clock.set('2026-11-03T00:03:00')
        return real(*a, **k)
    monkeypatch.setattr(scheduler.pipeline, 'build_drop', slow)
    assert scheduler.run_due() == 1
    assert db.all_users()[0]['last_drop_day'] == '2026-11-02'
    clock.set('2026-11-03T23:05:00')
    assert scheduler.due_users() == [_uid()], "the next day's drop is skipped"


# R2-C3: the local date can go BACK (travel west, or a zone whose clock change is at midnight). The check was "==", so a day
# that already had its drop counted as "not delivered" again and was built a second time.
def test_local_date_going_back_does_not_rebuild(client, monkeypatch):
    from cypher import db, scheduler
    _ready(client, drop_hour=0, tz_offset=-420)
    db.update_user(_uid(), last_drop_day='2026-11-03')     # built at 00:00 on 3.11. in a zone further east
    _freeze(monkeypatch, _Clock('2026-11-03T06:30:00'))     # 23:30 on 2.11. local (UTC-7)
    scheduler._fails.clear()
    assert scheduler.due_users() == []


# R2-C4: restart between "drop saved + push sent" and the next backup upload (every 5 min). Render restores the older backup,
# the drop is gone although the push already said "Dein Drop ist da"; the scheduler then builds and pushes a second one
# (model: verify/DropRestart.tla). Fix: upload right after the drop is saved, send the push only once that upload is done.
def test_push_is_sent_only_after_the_backup_contains_the_drop(client, monkeypatch, tmp_path):
    from cypher import backup, db, push, scheduler
    _ready(client, drop_hour=0, tz_offset=0)
    sub = {'endpoint': 'https://push.example.com/abc', 'keys': {'p256dh': 'x', 'auth': 'y'}}
    assert client.post('/api/push', json=sub).status_code == 200
    uploads, pushes, done = [], [], threading.Event()

    def fake_upload(path):
        with sqlite3.connect(path) as c:
            uploads.append(c.execute('SELECT COUNT(*) FROM drops').fetchone()[0])

    def fake_send(*a, **k):
        pushes.append(list(uploads))
        done.set()
        return True
    monkeypatch.setattr(push, 'send', fake_send)
    stop = threading.Event()
    monkeypatch.setitem(backup.STATE, 'enabled', False)
    backup.start_thread(interval=30, min_gap=0.05, upload=fake_upload, stop=stop)
    try:
        time.sleep(0.3)                        # first upload at boot (no drop yet)
        scheduler._fails.clear()
        assert scheduler.run_due() == 1
        assert done.wait(10), 'push never sent'
        assert pushes[0] and pushes[0][-1] >= 1, f'push sent before any backup contained the drop (uploads so far: {pushes[0]})'
    finally:
        stop.set()
        backup._wake.set()


def test_backup_nudge_uploads_soon_but_not_more_often_than_min_gap(client, tmp_path, monkeypatch):
    from cypher import backup
    from tests.test_app import start
    start(client)
    monkeypatch.setitem(backup.STATE, 'enabled', False)
    times, stop = [], threading.Event()
    backup.start_thread(interval=30, min_gap=0.3, upload=lambda p: times.append(time.time()), stop=stop)
    try:
        time.sleep(0.1)
        for _ in range(5):                     # a burst of saved drops
            client.put('/api/profile', json={'notes': f'x{time.time()}'})
            backup.nudge()
            time.sleep(0.05)
        time.sleep(1.0)
        assert 2 <= len(times) <= 4, times     # boot upload + coalesced burst, not one per nudge
        gaps = [b - a for a, b in zip(times, times[1:])]
        assert min(gaps) >= 0.29, gaps
    finally:
        stop.set()
        backup._wake.set()


# R2-C5 (client): the browser knows the real time zone rules; app.js computes the next offset changes and sends them.
@pytest.mark.skipif(shutil.which('node') is None, reason='node not installed')
def test_client_finds_the_berlin_transitions():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'app.js'), encoding='utf-8').read()
    start = src.index('function tzChanges(')
    end = src.index('\n}\n', start) + 2
    js = src[start:end] + "\nconsole.log(JSON.stringify(tzChanges(Date.UTC(2026, 9, 14))));"
    out = subprocess.run(['node', '-e', js], capture_output=True, text=True, env=dict(os.environ, TZ='Europe/Berlin'), timeout=30)
    assert out.returncode == 0, out.stderr
    import json
    got = json.loads(out.stdout)
    assert got[:2] == [[END_DST_2026, 60], [START_DST_2027, 120]], got
