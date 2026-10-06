"""SQLite storage. One file, no server. Secrets (OpenRouter keys) are encrypted with SECRET_KEY."""
import base64, hashlib, json, os, secrets, sqlite3, threading, time
from contextlib import contextmanager
from cryptography.fernet import Fernet, InvalidToken

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'data', 'cypher.db'))
_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id TEXT PRIMARY KEY, token_hash TEXT UNIQUE, recovery_hash TEXT UNIQUE, created REAL,
  notes TEXT DEFAULT '', sources TEXT DEFAULT '[]', drop_hour INTEGER DEFAULT 8, tz_offset INTEGER DEFAULT 60,
  quality TEXT DEFAULT 'fast', key_enc TEXT DEFAULT '', push_sub TEXT DEFAULT '', last_drop_day TEXT DEFAULT '',
  free_used_day TEXT DEFAULT '', free_used INTEGER DEFAULT 0, feedback TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS drops(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, day TEXT, created REAL, data TEXT);
CREATE INDEX IF NOT EXISTS drops_user ON drops(user_id, created);
CREATE TABLE IF NOT EXISTS saved(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, created REAL, item TEXT);
CREATE TABLE IF NOT EXISTS shared(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, created REAL, text TEXT, url TEXT, image_b64 TEXT, used INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS cache(k TEXT PRIMARY KEY, ts REAL, v TEXT);
"""


def setting(name, make):
    """Persistent app setting (generated once, stored in the DB). Used as a fallback when no env secret is set."""
    with conn() as c:
        r = c.execute('SELECT v FROM cache WHERE k=?', ('setting:' + name,)).fetchone()
        if r:
            return json.loads(r['v'])
        v = make()
        c.execute('INSERT INTO cache(k,ts,v) VALUES(?,?,?)', ('setting:' + name, time.time(), json.dumps(v)))
        return v


def _fernet():
    sk = os.environ.get('SECRET_KEY') or setting('secret_key', lambda: secrets.token_urlsafe(48))
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(sk.encode()).digest()))


def encrypt(s): return _fernet().encrypt(s.encode()).decode() if s else ''


def decrypt(s):
    try:
        return _fernet().decrypt(s.encode()).decode() if s else ''
    except (InvalidToken, RuntimeError):
        return ''


def _h(s): return hashlib.sha256(s.encode()).hexdigest()


@contextmanager
def conn():
    with _lock:
        os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
        c = sqlite3.connect(DB_PATH, timeout=20)
        c.row_factory = sqlite3.Row
        c.executescript(SCHEMA)
        try:
            yield c
            c.commit()
        finally:
            c.close()


def create_user():
    """Anonymous account: no email, no password. Returns (user_id, token, recovery_code)."""
    uid, token = secrets.token_hex(8), secrets.token_urlsafe(32)
    recovery = '-'.join(secrets.token_hex(2) for _ in range(4))
    with conn() as c:
        c.execute('INSERT INTO users(id,token_hash,recovery_hash,created) VALUES(?,?,?,?)', (uid, _h(token), _h(recovery), time.time()))
    return uid, token, recovery


def user_by_token(token):
    if not token:
        return None
    with conn() as c:
        return c.execute('SELECT * FROM users WHERE token_hash=?', (_h(token),)).fetchone()


def restore(recovery):
    """New device: swap in a fresh token for the account that owns this recovery code."""
    token = secrets.token_urlsafe(32)
    with conn() as c:
        r = c.execute('SELECT id FROM users WHERE recovery_hash=?', (_h(recovery.strip().lower()),)).fetchone()
        if not r:
            return None
        c.execute('UPDATE users SET token_hash=? WHERE id=?', (_h(token), r['id']))
    return token


def update_user(uid, **f):
    if not f:
        return
    with conn() as c:
        c.execute('UPDATE users SET ' + ','.join(f'{k}=?' for k in f) + ' WHERE id=?', (*f.values(), uid))


def delete_user(uid):
    with conn() as c:
        for t in ('drops', 'saved', 'shared'):
            c.execute(f'DELETE FROM {t} WHERE user_id=?', (uid,))
        c.execute('DELETE FROM users WHERE id=?', (uid,))


def all_users():
    with conn() as c:
        return c.execute('SELECT * FROM users').fetchall()


def cache_get(k, ttl):
    with conn() as c:
        r = c.execute('SELECT ts,v FROM cache WHERE k=?', (k,)).fetchone()
    if r and time.time() - r['ts'] < ttl:
        return json.loads(r['v'])
    return None


def cache_set(k, v):
    with conn() as c:
        c.execute('INSERT OR REPLACE INTO cache(k,ts,v) VALUES(?,?,?)', (k, time.time(), json.dumps(v)))
