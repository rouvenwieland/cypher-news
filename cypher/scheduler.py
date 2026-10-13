"""Daily drops. Runs in a background thread (SCHEDULER=1) and/or via POST /api/cron (call it from a free cron service)."""
import json, os, threading, time, traceback
from datetime import datetime, timedelta, timezone

from . import ai, db, pipeline, push

_run_slots = threading.BoundedSemaphore(2)  # at most 2 drops at once (free-tier rate limits), never one global blocking lock
_fails = {}  # uid -> (day, attempts, last_try): transient failures are retried, not dropped for the whole day
HARD_ERRORS = ('no_user', 'no_profile', 'no_key', 'key_invalid', 'no_credit', 'no_model_configured')
RETRY_AFTER, MAX_ATTEMPTS = 20 * 60, 4
FREE_PER_DAY = int(os.environ.get('FREE_DROPS_PER_DAY', '1'))


_inflight, _inflight_lock = set(), threading.Lock()  # users whose drop is being built right now (one build per user at a time)


def local_now(u):
    return datetime.now(timezone.utc) + timedelta(minutes=u['tz_offset'] or 0)


def pick_key(u):
    """User's own key first; else the server key within the free quota. Returns (key, is_free) or (None, False)."""
    k = db.decrypt(u['key_enc'])
    if k:
        return k, False
    server = os.environ.get('OPENROUTER_API_KEY')
    day = local_now(u).strftime('%Y-%m-%d')
    used = u['free_used'] if u['free_used_day'] == day else 0
    if server and used < FREE_PER_DAY:
        return server, True
    return None, False


def run_for_user(uid, manual=False):
    """Returns (ok, error_code, drop). Never raises. At most one build per user at a time ('busy'); a scheduled run never repeats
    a day that is already delivered ('already_done')."""
    with _inflight_lock:
        if uid in _inflight:
            return False, 'busy', None
        _inflight.add(uid)
    try:
        return _run_for_user(uid, manual)
    finally:
        with _inflight_lock:
            _inflight.discard(uid)


def _run_for_user(uid, manual):
    with db.conn() as c:
        u = c.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        return False, 'no_user', None
    if not manual and u['last_drop_day'] == local_now(u).strftime('%Y-%m-%d'):
        return False, 'already_done', None
    if not (u['notes'] or '').strip() and not json.loads(u['sources'] or '[]'):
        return False, 'no_profile', None
    key, free = pick_key(u)
    if not key:
        return False, 'no_key', None
    try:
        with _run_slots:
            drop = pipeline.build_drop(u, key, u['quality'])
    except ai.AIError as e:
        print(f'drop failed for {uid}: {e}', flush=True)
        return False, str(e).split(':')[0], None
    except Exception:
        print(f'drop crashed for {uid}:\n' + traceback.format_exc(), flush=True)
        return False, 'internal', None
    day = local_now(u).strftime('%Y-%m-%d')
    fields = {'last_drop_day': day}
    if free:
        fields.update(free_used_day=day, free_used=(u['free_used'] if u['free_used_day'] == day else 0) + 1)
    drop['id'] = None
    with db.conn() as c:
        if not c.execute('SELECT 1 FROM users WHERE id=?', (uid,)).fetchone():  # account deleted while the drop was being built
            return False, 'no_user', None
        cur = c.execute('INSERT INTO drops(user_id,day,created,data) VALUES(?,?,?,?)', (uid, day, time.time(), json.dumps(drop)))
        drop['id'] = cur.lastrowid
        c.execute('DELETE FROM drops WHERE user_id=? AND id NOT IN (SELECT id FROM drops WHERE user_id=? ORDER BY created DESC LIMIT 30)', (uid, uid))
    db.update_user(uid, **fields)
    if u['push_sub'] and not manual:
        if not push.send(u['push_sub'], 'Dein Drop ist da', f"{len(drop['items'])} Treffer: {drop['title']}"[:120]):
            db.update_user(uid, push_sub='')
    return True, '', drop


def due_users(now_utc=None):
    out, now = [], time.time()
    for u in db.all_users():
        ln = local_now(u)
        day = ln.strftime('%Y-%m-%d')
        if u['last_drop_day'] == day or ln.hour < (u['drop_hour'] if u['drop_hour'] is not None else 8):
            continue
        fday, attempts, last = _fails.get(u['id'], (day, 0, 0))
        if fday == day and (attempts >= MAX_ATTEMPTS or now - last < RETRY_AFTER):
            continue
        out.append(u['id'])
    return out


def run_due():
    n = 0
    for uid in due_users():
        ok, err, _ = run_for_user(uid)
        if ok:
            n += 1
            _fails.pop(uid, None)
            continue
        if err in ('busy', 'already_done'):  # another run owns / has finished this user: not a failure
            continue
        with db.conn() as c:
            u = c.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
        if not u:
            continue
        day = local_now(u).strftime('%Y-%m-%d')
        if err in HARD_ERRORS:  # nothing a retry can fix: give up for today
            db.update_user(uid, last_drop_day=day)
        else:  # AI hiccup, rate limit, network: try again later (max 4 times a day)
            fday, attempts, _ = _fails.get(uid, (day, 0, 0))
            _fails[uid] = (day, (attempts if fday == day else 0) + 1, time.time())
    return n


_kick_lock, _last_kick = threading.Lock(), [0.0]


def kick(min_interval=240):
    """Called by the keep-awake ping: makes sure due drops get built even if the scheduler thread died or the app just woke up."""
    with _kick_lock:
        if time.time() - _last_kick[0] < min_interval:
            return False
        _last_kick[0] = time.time()
    threading.Thread(target=lambda: _safe(run_due), daemon=True).start()
    return True


def _safe(fn):
    try:
        return fn()
    except Exception:
        print('scheduler error:\n' + traceback.format_exc(), flush=True)


def start_thread(interval=600):
    def loop():
        while True:
            _safe(run_due)
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()
