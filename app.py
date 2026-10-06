"""Cypher News - Daily Drop. Multi-user Flask app (SQLite). Run: gunicorn app:app  |  python app.py"""
import base64, io, json, os, re, threading, time
from collections import defaultdict
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, jsonify, make_response, redirect, render_template, request, send_from_directory

from cypher import ai, backup, db, push, scheduler, sources

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024
COOKIE = 'cn_token'
PRIMARY = os.environ.get('MODEL_PRIMARY', '')
SECURE = os.environ.get('COOKIE_SECURE', '1') == '1'

_hits = defaultdict(list)
_hits_lock = threading.Lock()


def rate_limit(name, limit, per):
    ip = (request.headers.get('X-Forwarded-For', request.remote_addr) or '?').split(',')[0].strip()
    k = (name, ip)
    now = time.time()
    with _hits_lock:
        _hits[k] = [t for t in _hits[k] if now - t < per]
        if len(_hits[k]) >= limit:
            return False
        _hits[k].append(now)
    return True


@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options'] = 'nosniff'
    r.headers['Referrer-Policy'] = 'same-origin'
    r.headers['X-Frame-Options'] = 'DENY'
    r.headers['Content-Security-Policy'] = ("default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; "
                                            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
    return r


def api(fn):
    """Auth via cookie + CSRF guard (same-origin + JSON for writes)."""
    @wraps(fn)
    def w(*a, **kw):
        if request.method not in ('GET', 'HEAD'):
            o = request.headers.get('Origin')
            if o and urlparse(o).netloc != request.host:
                return jsonify(error='forbidden'), 403
        u = db.user_by_token(request.cookies.get(COOKIE))
        if not u:
            return jsonify(error='no_session'), 401
        return fn(u, *a, **kw)
    return w


def set_cookie(resp, token):
    resp.set_cookie(COOKIE, token, max_age=60 * 60 * 24 * 365, httponly=True, samesite='Lax', secure=SECURE)
    return resp


def profile(u):
    free_left = 0
    if os.environ.get('OPENROUTER_API_KEY'):
        day = scheduler.local_now(u).strftime('%Y-%m-%d')
        free_left = max(0, scheduler.FREE_PER_DAY - (u['free_used'] if u['free_used_day'] == day else 0))
    return {'notes': u['notes'], 'sources': json.loads(u['sources'] or '[]'), 'drop_hour': u['drop_hour'], 'quality': u['quality'],
            'has_key': bool(db.decrypt(u['key_enc'])), 'free_left': free_left, 'push': bool(u['push_sub']),
            'last_drop_day': u['last_drop_day']}


# ---------- pages ----------
@app.route('/')
def index():
    return render_template('index.html', model_name=PRIMARY or 'offenes Modell', vapid=push.public_key())


@app.route('/sw.js')
def sw():
    r = make_response(send_from_directory(app.static_folder, 'sw.js'))
    r.headers['Service-Worker-Allowed'] = '/'
    r.headers['Cache-Control'] = 'no-cache'
    return r


@app.route('/datenschutz')
def privacy():
    return render_template('legal.html', page='privacy', imprint=os.environ.get('IMPRINT_TEXT', ''))


@app.route('/impressum')
def imprint():
    return render_template('legal.html', page='imprint', imprint=os.environ.get('IMPRINT_TEXT', ''))


@app.route('/healthz')
def healthz():
    return jsonify(ok=True, backup=backup.STATE)


# ---------- session ----------
@app.route('/api/start', methods=['POST'])
def start():
    if not rate_limit('start', 10, 3600):
        return jsonify(error='rate_limited'), 429
    if db.user_by_token(request.cookies.get(COOKIE)):
        return jsonify(error='exists'), 409
    uid, token, recovery = db.create_user()
    return set_cookie(make_response(jsonify(ok=True, recovery=recovery)), token)


@app.route('/api/restore', methods=['POST'])
def restore():
    if not rate_limit('restore', 8, 3600):
        return jsonify(error='rate_limited'), 429
    code = ((request.get_json(silent=True) or {}).get('code') or '').strip().lower()
    token = db.restore(code) if re.fullmatch(r'[0-9a-f]{4}(-[0-9a-f]{4}){3}', code) else None
    if not token:
        return jsonify(error='bad_code'), 404
    return set_cookie(make_response(jsonify(ok=True)), token)


@app.route('/api/me')
def me():
    u = db.user_by_token(request.cookies.get(COOKIE))
    if not u:
        return jsonify(session=False, model=PRIMARY, vapid=push.public_key())
    return jsonify(session=True, model=PRIMARY, vapid=push.public_key(), **profile(u))


@app.route('/api/me', methods=['DELETE'])
@api
def delete_me(u):
    db.delete_user(u['id'])
    r = make_response(jsonify(ok=True))
    r.delete_cookie(COOKIE)
    return r


@app.route('/api/export')
@api
def export(u):
    with db.conn() as c:
        d = [json.loads(r['data']) for r in c.execute('SELECT data FROM drops WHERE user_id=?', (u['id'],))]
        s = [json.loads(r['item']) for r in c.execute('SELECT item FROM saved WHERE user_id=?', (u['id'],))]
    r = make_response(jsonify(profile=profile(u), drops=d, saved=s))
    r.headers['Content-Disposition'] = 'attachment; filename=cypher-news-export.json'
    return r


# ---------- profile ----------
@app.route('/api/profile', methods=['PUT'])
@api
def put_profile(u):
    b = request.get_json(silent=True) or {}
    f = {}
    if 'notes' in b: f['notes'] = str(b['notes'])[:4000]
    if 'drop_hour' in b: f['drop_hour'] = max(0, min(23, int(b['drop_hour'])))
    if 'tz_offset' in b: f['tz_offset'] = max(-840, min(840, int(b['tz_offset'])))
    if b.get('quality') in ('fast', 'high'): f['quality'] = b['quality']
    if 'sources' in b and isinstance(b['sources'], list):
        clean = []
        for s in b['sources'][:40]:
            p, v = str(s.get('platform', '')), str(s.get('value', '')).strip()[:300]
            if p in sources.FETCHERS and p != 'news' and v and not any(c['platform'] == p and c['value'] == v for c in clean):
                clean.append({'platform': p, 'value': v})
        f['sources'] = json.dumps(clean)
    db.update_user(u['id'], **f)
    return jsonify(ok=True)


@app.route('/api/sources/detect', methods=['POST'])
@api
def detect(u):
    p, v = sources.detect((request.get_json(silent=True) or {}).get('value', ''))
    return jsonify(platform=p, value=v)


@app.route('/api/sources/test', methods=['POST'])
@api
def test_source(u):
    """Tries one source right now so the user sees whether it is reachable."""
    if not rate_limit('srctest:' + u['id'], 30, 600):
        return jsonify(error='rate_limited'), 429
    b = request.get_json(silent=True) or {}
    p, v = str(b.get('platform', '')), str(b.get('value', ''))[:300]
    if p not in sources.FETCHERS or p == 'news':
        return jsonify(error='bad_platform'), 400
    t = time.time()
    items = sources.FETCHERS[p](v)
    return jsonify(count=len(items), seconds=round(time.time() - t, 1), sample=(items[0]['text'][:90] if items else ''))


@app.route('/api/sources/import', methods=['POST'])
@api
def import_sources(u):
    """Bulk import handles/URLs (one per line) e.g. from an Instagram data export of the user's own follow list."""
    text = str((request.get_json(silent=True) or {}).get('text', ''))[:20000]
    platform = (request.get_json(silent=True) or {}).get('platform', '')
    found = []
    for tok in re.findall(r'https?://\S+|@?[\w.\-]+@[\w.\-]+\.\w+|@[\w.]{2,40}|^[\w.]{2,40}$', text, flags=re.M):
        p, v = sources.detect(tok) if tok.startswith(('http', 'r/')) or tok.count('@') == 2 else (platform, tok.lstrip('@'))
        if p in sources.FETCHERS and p != 'news' and v:
            found.append({'platform': p, 'value': v})
    return jsonify(found=found[:200])


@app.route('/api/key', methods=['POST'])
@api
def set_key(u):
    k = str((request.get_json(silent=True) or {}).get('key', '')).strip()
    if not re.fullmatch(r'sk-or-[\w\-]{20,200}', k):
        return jsonify(error='bad_format'), 400
    if not ai.check_key(k):
        return jsonify(error='key_rejected'), 400
    db.update_user(u['id'], key_enc=db.encrypt(k))
    return jsonify(ok=True)


@app.route('/api/key', methods=['DELETE'])
@api
def del_key(u):
    db.update_user(u['id'], key_enc='')
    return jsonify(ok=True)


# ---------- drops ----------
@app.route('/api/drop', methods=['POST'])
@api
def make_drop(u):
    if not rate_limit('drop:' + u['id'], 3, 3600):
        return jsonify(error='rate_limited'), 429
    ok, err, drop = scheduler.run_for_user(u['id'], manual=True)
    if not ok:
        return jsonify(error=err), (402 if err in ('no_key', 'no_credit') else 400 if err == 'no_profile' else 502)
    return jsonify(drop)


@app.route('/api/drops')
@api
def drops(u):
    with db.conn() as c:
        rows = c.execute('SELECT id,day,created,data FROM drops WHERE user_id=? ORDER BY created DESC LIMIT 30', (u['id'],)).fetchall()
    out = []
    for r in rows:
        d = json.loads(r['data'])
        out.append({'id': r['id'], 'day': r['day'], 'created': r['created'], 'title': d.get('title'), 'count': len(d.get('items', []))})
    return jsonify(drops=out)


@app.route('/api/drops/<int:i>')
@api
def one_drop(u, i):
    with db.conn() as c:
        r = c.execute('SELECT id,data FROM drops WHERE id=? AND user_id=?', (i, u['id'])).fetchone()
    if not r:
        return jsonify(error='not_found'), 404
    d = json.loads(r['data']); d['id'] = r['id']
    return jsonify(d)


@app.route('/api/saved', methods=['GET', 'POST', 'DELETE'])
@api
def saved(u):
    with db.conn() as c:
        if request.method == 'POST':
            it = request.get_json(silent=True) or {}
            it = {k: str(it.get(k, ''))[:600] for k in ('category', 'title', 'summary', 'source', 'url', 'when', 'image', 'platform', 'account', 'kind')}
            if it['image'] and not it['image'].startswith(('https://', 'http://')):
                it['image'] = ''
            if it['title'] and not c.execute('SELECT 1 FROM saved WHERE user_id=? AND json_extract(item,"$.title")=?', (u['id'], it['title'])).fetchone():
                c.execute('INSERT INTO saved(user_id,created,item) VALUES(?,?,?)', (u['id'], time.time(), json.dumps(it)))
            return jsonify(ok=True)
        if request.method == 'DELETE':
            c.execute('DELETE FROM saved WHERE user_id=? AND json_extract(item,"$.title")=?', (u['id'], (request.get_json(silent=True) or {}).get('title', '')))
            return jsonify(ok=True)
        rows = c.execute('SELECT item FROM saved WHERE user_id=? ORDER BY created DESC LIMIT 200', (u['id'],)).fetchall()
    return jsonify(saved=[json.loads(r['item']) for r in rows])


@app.route('/api/feedback', methods=['POST'])
@api
def feedback(u):
    b = request.get_json(silent=True) or {}
    vote = 1 if b.get('vote') == 1 else -1 if b.get('vote') == -1 else 0
    fb = json.loads(u['feedback'] or '{}')
    for k in (str(b.get('account', '')).lower(), str(b.get('category', ''))):
        if k and k != 'geteilt':
            fb[k] = max(-5, min(5, fb.get(k, 0) + vote))
    db.update_user(u['id'], feedback=json.dumps(dict(list(fb.items())[-80:])))
    return jsonify(ok=True)


# ---------- share into the app (Web Share Target) ----------
def _store_share(uid, text, url, file):
    img = ''
    if file and file.filename:
        try:
            from PIL import Image
            im = Image.open(file.stream).convert('RGB')
            im.thumbnail((768, 768))
            o = io.BytesIO(); im.save(o, 'JPEG', quality=72)
            img = base64.b64encode(o.getvalue()).decode()
        except Exception:
            img = ''
    url = url if re.match(r'https?://', url or '') else ''
    m = re.search(r'https?://\S+', text or '')
    if not url and m:
        url = m.group(0)
    if not (text or url or img):
        return False
    with db.conn() as c:
        c.execute('INSERT INTO shared(user_id,created,text,url,image_b64) VALUES(?,?,?,?,?)', (uid, time.time(), (text or '')[:800], url[:500], img))
    return True


@app.route('/share', methods=['POST'])
def share_target():
    u = db.user_by_token(request.cookies.get(COOKIE))
    if not u:
        return redirect('/?share=login')
    ok = _store_share(u['id'], ' '.join(x for x in (request.form.get('title', ''), request.form.get('text', '')) if x), request.form.get('url', ''),
                      request.files.get('media'))
    return redirect('/?share=ok' if ok else '/?share=empty', code=303)


@app.route('/api/shared', methods=['POST'])
@api
def shared(u):
    ok = _store_share(u['id'], request.form.get('text', ''), request.form.get('url', ''), request.files.get('media'))
    return jsonify(ok=ok), (200 if ok else 400)


# ---------- push + cron ----------
@app.route('/api/push', methods=['POST', 'DELETE'])
@api
def push_sub(u):
    if request.method == 'DELETE':
        db.update_user(u['id'], push_sub='')
        return jsonify(ok=True)
    s = request.get_json(silent=True) or {}
    if not str(s.get('endpoint', '')).startswith('https://'):
        return jsonify(error='bad_subscription'), 400
    db.update_user(u['id'], push_sub=json.dumps(s))
    return jsonify(ok=True)


@app.route('/api/cron', methods=['POST'])
def cron():
    secret = os.environ.get('CRON_SECRET')
    if not secret or request.headers.get('X-Cron-Secret') != secret:
        return jsonify(error='forbidden'), 403
    threading.Thread(target=scheduler.run_due, daemon=True).start()
    return jsonify(ok=True, due=len(scheduler.due_users()))


if backup.enabled():
    backup.restore()
    backup.start_thread()
if os.environ.get('SCHEDULER', '0') == '1':
    scheduler.start_thread()

if __name__ == '__main__':
    app.run(host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', '5000')), debug=False)
