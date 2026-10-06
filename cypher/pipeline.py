"""Builds one personalised drop: collect -> dedupe -> rank -> vision -> write (open model) -> JSON."""
import json, os, re
from datetime import datetime, timezone

from . import ai, db, sources

CATS = ['Konzerte', 'Giveaways', 'Drops', 'Tech', 'Trends', 'News']


def topics_from_notes(notes):
    t = [s.strip() for s in re.split(r'[\n,;.]+|\s+und\s+', notes or '', flags=re.I) if 2 < len(s.strip()) < 80]
    return list(dict.fromkeys(t))[:5] or ['Konzerte Berlin', 'Giveaways', 'Tech News']


def guess_cat(t):
    t = t.lower()
    if re.search(r'konzert|live|tour|festival|club|\bdj\b|gig', t): return 'Konzerte'
    if re.search(r'gewinn|verlos|giveaway|raffle', t): return 'Giveaways'
    if re.search(r'\bdrop\b|release|kollektion|sneaker|streetwear|mode|sale', t): return 'Drops'
    if re.search(r'\bki\b|\bai\b|tech|app|software|handy|chip|open.?source', t): return 'Tech'
    return 'News'


def score(item, topics, fb):
    words = {w for t in topics for w in re.findall(r'\w{4,}', t.lower())}
    txt = item['text'].lower()
    s = sum(1 for w in words if w in txt)
    s += 2 if item['kind'] != 'news' else 0          # followed accounts beat generic news
    s += 3 if item.get('shared') else 0              # things the user shared explicitly
    s += fb.get(item['account'].lower(), 0) + fb.get(guess_cat(item['text']), 0)
    return s


def collect(user, topics, srcs):
    pool_key = None
    items, status = [], {}
    # shared topics are cached for 3h so many users with the same interest cost one fetch
    for t in topics:
        pool_key = 'news:' + t.lower()
        got = db.cache_get(pool_key, 3 * 3600)
        if got is None:
            got = sources.news(t)
            db.cache_set(pool_key, got)
        items.extend(got); status['news:' + t] = len(got)
    own = [s for s in srcs if s.get('platform') in sources.FETCHERS]
    got, st = sources.fetch_all([], own)
    items.extend(got); status.update(st)
    with db.conn() as c:
        rows = c.execute('SELECT * FROM shared WHERE user_id=? AND used=0 ORDER BY created DESC LIMIT 10', (user['id'],)).fetchall()
        for r in rows:
            items.append({'platform': 'shared', 'account': 'geteilt', 'kind': 'post', 'text': r['text'] or r['url'] or 'Geteiltes Bild',
                          'url': r['url'] or '', 'taken_at': datetime.fromtimestamp(r['created'], tz=timezone.utc).isoformat(),
                          'image_url': '', 'image_b64': r['image_b64'] or '', 'shared': True})
        c.execute('UPDATE shared SET used=1 WHERE user_id=? AND used=0', (user['id'],))
    return items, status


def seen_urls(uid):
    with db.conn() as c:
        rows = c.execute('SELECT data FROM drops WHERE user_id=? ORDER BY created DESC LIMIT 3', (uid,)).fetchall()
    out = set()
    for r in rows:
        try:
            out |= {i.get('url') for i in json.loads(r['data']).get('items', []) if i.get('url')}
        except Exception:
            pass
    return out


def build_drop(user, key, quality='fast', include_vision=True):
    """key: OpenRouter key to use. Raises ai.AIError('key_invalid'|'no_credit') so the caller can tell the user."""
    topics = topics_from_notes(user['notes'])
    srcs = json.loads(user['sources'] or '[]')
    fb = json.loads(user['feedback'] or '{}')
    items, status = collect(user, topics, srcs)

    seen, old, uniq = set(), seen_urls(user['id']), []
    for i in items:
        k = re.sub(r'\W+', ' ', i['text'].lower())[:70] or i['url']
        if k in seen or (i['url'] and i['url'] in old):
            continue
        seen.add(k); uniq.append(i)
    uniq.sort(key=lambda i: score(i, topics, fb), reverse=True)
    top = uniq[:32]

    vision_n, vmodels = 0, set()
    if include_vision and ai.vision_models():
        for i in [x for x in top if x.get('image_b64') or x.get('image_url')][:6]:
            b64 = i.get('image_b64') or sources.thumb_b64(i['image_url'])
            if not b64:
                continue
            d, m = ai.describe_image(key, b64)
            if d:
                i['vision'] = d; vision_n += 1; vmodels.add(m)

    lines = [f"[{n}] {i['kind'].upper()} {i['platform']} {i['account']} | {i['text'][:240]} | {i['taken_at'][:10]}"
             + (f" | BILDINHALT: {i['vision']}" if i.get('vision') else '') for n, i in enumerate(top)]
    liked = [k for k, v in fb.items() if v > 0][:8]; disliked = [k for k, v in fb.items() if v < 0][:8]
    system = ('Du bist die Redaktion von CYPHER NEWS (DAILY DROP), einem Tages-Newsletter, der Social-Media-Posts, Videos und News fuer den Nutzer '
              'zusammenfasst, damit er nicht scrollen muss. Antworte AUSSCHLIESSLICH mit gueltigem JSON.')
    prompt = (f"Notizen des Nutzers: \"{(user['notes'] or '')[:1500]}\"\nMag: {liked}. Mag nicht: {disliked}.\nDatum: {datetime.now().date()}\n\n"
              "Rohdaten:\n" + '\n'.join(lines) + "\n\nWaehle bis zu 10 passende, abwechslungsreiche Eintraege (Posts/Videos bevorzugen, wenn relevant). "
              "Deutsch, locker, praezise; nenne Datum/Ort/Deadline, wenn in den Daten. Format:\n"
              '{"title":"Schlagzeile","intro":"2 Saetze","items":[{"idx":0,"category":"Konzerte|Giveaways|Drops|Tech|Trends|News","title":"..","summary":"1-2 Saetze + was tun","when":"z.B. Heute"}]}\n'
              'Erfinde nichts, keine Links, nutze nur die Daten.')
    data, used = None, 'fallback-ohne-ki'
    if top:
        models = ai.text_models()
        if not models:
            raise ai.AIError('no_model_configured')
        try:
            text, used = ai.chat_chain(key, models, [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}], max_tokens=3500)
            data = ai.extract_json(text)
            if not isinstance(data.get('items'), list) or not data['items']:
                data = None
        except ai.AIError as e:
            if str(e) in ('key_invalid', 'no_credit', 'rate_limited'):
                raise
        except Exception:
            data = None

    out_items = []
    def build(src, x):
        img = src.get('image_url') or ''
        if img and src['platform'] in ('instagram', 'tiktok'):  # CDN links expire after a few days: keep a small copy
            small = sources.thumb_b64(img, size=480, quality=62)
            img = ('data:image/jpeg;base64,' + small) if small else img
        return {'category': x['category'] if x and x.get('category') in CATS else guess_cat(src['text']),
                'title': str((x or {}).get('title') or src['text'].split(':')[0])[:140],
                'summary': str((x or {}).get('summary') or src.get('vision') or src['text'])[:340],
                'source': f"{src['platform']} {src['account']}".strip() if src['platform'] not in ('news',) else src['account'],
                'url': src['url'], 'when': str((x or {}).get('when') or src['taken_at'][:10] or 'aktuell')[:30],
                'kind': src['kind'], 'platform': src['platform'], 'account': src['account'],
                'image': img or ('data:image/jpeg;base64,' + src['image_b64'] if src.get('image_b64') else '')}
    if data:
        for x in data['items'][:12]:
            try:
                src = top[int(x.get('idx'))]
            except Exception:
                continue
            out_items.append(build(src, x))
    if not out_items:
        used = 'fallback-ohne-ki'
        out_items = [build(s, None) for s in top[:10]]
    return {'title': (data or {}).get('title') or 'Dein Drop für heute', 'date': datetime.now().strftime('%Y-%m-%d'),
            'intro': (data or {}).get('intro') or 'Frisch gescannt: das Wichtigste zu deinen Themen.', 'items': out_items,
            'meta': {'model': used, 'sources_ok': sum(1 for v in status.values() if v), 'sources_total': len(status),
                     'failed': [k for k, v in status.items() if not v and not k.startswith('news:')], 'images_analyzed': vision_n, 'candidates': len(uniq)}}
