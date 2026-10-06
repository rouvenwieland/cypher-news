"""Daily drops. Runs in a background thread (SCHEDULER=1) and/or via POST /api/cron (call it from a free cron service)."""
import json, os, threading, time
from datetime import datetime, timedelta, timezone

from . import ai, db, pipeline, push

_run_lock = threading.Lock()
FREE_PER_DAY = int(os.environ.get('FREE_DROPS_PER_DAY', '1'))


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
    """Returns (ok, error_code, drop). Never raises."""
    with db.conn() as c:
        u = c.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        return False, 'no_user', None
    if not (u['notes'] or '').strip() and not json.loads(u['sources'] or '[]'):
        return False, 'no_profile', None
    key, free = pick_key(u)
    if not key:
        return False, 'no_key', None
    try:
        with _run_lock:  # one drop at a time: protects free-tier rate limits
            drop = pipeline.build_drop(u, key, u['quality'])
    except ai.AIError as e:
        return False, str(e).split(':')[0], None
    except Exception:
        return False, 'internal', None
    day = local_now(u).strftime('%Y-%m-%d')
    fields = {'last_drop_day': day}
    if free:
        fields.update(free_used_day=day, free_used=(u['free_used'] if u['free_used_day'] == day else 0) + 1)
    drop['id'] = None
    with db.conn() as c:
        cur = c.execute('INSERT INTO drops(user_id,day,created,data) VALUES(?,?,?,?)', (uid, day, time.time(), json.dumps(drop)))
        drop['id'] = cur.lastrowid
        c.execute('DELETE FROM drops WHERE user_id=? AND id NOT IN (SELECT id FROM drops WHERE user_id=? ORDER BY created DESC LIMIT 30)', (uid, uid))
    db.update_user(uid, **fields)
    if u['push_sub'] and not manual:
        if not push.send(u['push_sub'], 'Dein Drop ist da', f"{len(drop['items'])} Treffer: {drop['title']}"[:120]):
            db.update_user(uid, push_sub='')
    return True, '', drop


def due_users(now_utc=None):
    out = []
    for u in db.all_users():
        ln = local_now(u)
        if u['last_drop_day'] != ln.strftime('%Y-%m-%d') and ln.hour >= (u['drop_hour'] if u['drop_hour'] is not None else 8):
            out.append(u['id'])
    return out


def run_due():
    n = 0
    for uid in due_users():
        ok, _, _ = run_for_user(uid)
        n += 1 if ok else 0
        if not ok:  # do not retry failed users every tick today
            with db.conn() as c:
                u = c.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
            if u:
                db.update_user(uid, last_drop_day=local_now(u).strftime('%Y-%m-%d'))
    return n


def start_thread(interval=600):
    def loop():
        while True:
            try:
                run_due()
            except Exception:
                pass
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()
