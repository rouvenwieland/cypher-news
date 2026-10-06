"""Public, login-free sources. No passwords, no scraping behind logins.
Every function returns a list of items: {platform, account, kind, text, url, taken_at, image_url} and never raises."""
import base64, io, ipaddress, re, socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlparse

import feedparser
import requests

UA = 'Mozilla/5.0 (compatible; CypherNews/1.0; +https://github.com/rouvenwieland/cypher-news)'
TIMEOUT = 12
MAX_BYTES = 3_000_000


def is_public_url(url):
    """SSRF guard: only http(s) to public IPs."""
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https') or not p.hostname:
            return False
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        return False


def get(url, **kw):
    if not is_public_url(url):
        raise ValueError('blocked url')
    kw.setdefault('headers', {})['User-Agent'] = kw['headers'].get('User-Agent', UA)
    r = requests.get(url, timeout=TIMEOUT, stream=True, **kw)
    buf = r.raw.read(MAX_BYTES, decode_content=True)
    r.status_code_ok = r.status_code == 200
    return r, buf


def _iso(t):
    if not t:
        return ''
    try:
        return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
    except Exception:
        return ''


def _strip(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html or '')).strip()


def _img_from_html(html):
    m = re.search(r'<img[^>]+src="([^"]+)"', html or '')
    return m.group(1) if m else ''


def parse_feed(buf, platform, account, kind, limit=8, hours=96):
    out, cutoff = [], datetime.now(timezone.utc) - timedelta(hours=hours)
    d = feedparser.parse(buf)
    for e in d.entries[:limit * 2]:
        ts = e.get('published_parsed') or e.get('updated_parsed')
        iso = _iso(ts)
        if iso and datetime.fromisoformat(iso) < cutoff:
            continue
        html = (e.get('content') or [{}])[0].get('value') or e.get('summary', '')
        img = ''
        for key in ('media_thumbnail', 'media_content'):
            if e.get(key):
                img = e[key][0].get('url', '')
                break
        img = img or _img_from_html(html)
        title = _strip(e.get('title', ''))
        body = _strip(html)
        out.append({'platform': platform, 'account': account, 'kind': kind,
                    'text': (title + (': ' + body[:300] if body and body[:60] != title[:60] else ''))[:400],
                    'url': e.get('link', ''), 'taken_at': iso, 'image_url': img})
        if len(out) >= limit:
            break
    return out


def news(topic):
    try:
        r, buf = get(f'https://news.google.com/rss/search?q={quote(topic + " when:7d")}&hl=de&gl=DE&ceid=DE:de')
        items = parse_feed(buf, 'news', topic, 'news', limit=6, hours=24 * 7)
        for i in items:  # Google appends " - Publisher"
            m = re.search(r' - ([^-]{3,40})$', i['text'].split(':')[0])
            i['account'] = m.group(1) if m else 'News'
            i['text'] = re.sub(r' - [^-]{3,40}(?=:|$)', '', i['text'], count=1)
        return items
    except Exception:
        return []


def reddit(sub):
    sub = re.sub(r'^(https?://[^/]*reddit\.com)?/?r/', '', sub.strip()).strip('/').split('/')[0]
    if not re.fullmatch(r'\w{2,40}', sub):
        return []
    try:
        r, buf = get(f'https://www.reddit.com/r/{sub}/top/.rss?t=day&limit=10')
        return parse_feed(buf, 'reddit', f'r/{sub}', 'post', limit=5) if r.status_code == 200 else []
    except Exception:
        return []


def youtube(handle):
    handle = handle.strip().rstrip('/').split('/')[-1].lstrip('@')
    if not re.fullmatch(r'[\w.\-]{2,60}', handle):
        return []
    try:
        cid = handle if re.fullmatch(r'UC[\w-]{22}', handle) else None
        if not cid:
            r, buf = get(f'https://www.youtube.com/@{handle}')
            m = re.search(rb'"(?:channelId|externalId)":"(UC[\w-]{22})"', buf)
            cid = m.group(1).decode() if m else None
        if not cid:
            return []
        r, buf = get(f'https://www.youtube.com/feeds/videos.xml?channel_id={cid}')
        return parse_feed(buf, 'youtube', '@' + handle, 'video', limit=4, hours=24 * 5) if r.status_code == 200 else []
    except Exception:
        return []


def bluesky(handle):
    handle = handle.strip().lstrip('@')
    try:
        r, buf = get(f'https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor={quote(handle)}&limit=8&filter=posts_no_replies')
        import json
        out = []
        for f in json.loads(buf).get('feed', []):
            p = f.get('post', {})
            rec = p.get('record', {})
            emb = p.get('embed') or {}
            imgs = emb.get('images') or []
            rkey = p.get('uri', '').rsplit('/', 1)[-1]
            out.append({'platform': 'bluesky', 'account': '@' + handle, 'kind': 'post', 'text': rec.get('text', '')[:400],
                        'url': f'https://bsky.app/profile/{handle}/post/{rkey}', 'taken_at': rec.get('createdAt', ''),
                        'image_url': imgs[0].get('thumb', '') if imgs else ''})
        return out[:5]
    except Exception:
        return []


def mastodon(handle):
    """handle like user@instance.social"""
    m = re.fullmatch(r'@?([\w.\-]+)@([\w.\-]+\.\w+)', handle.strip())
    if not m:
        return []
    user, host = m.groups()
    try:
        import json
        r, buf = get(f'https://{host}/api/v1/accounts/lookup?acct={quote(user)}')
        aid = json.loads(buf)['id']
        r, buf = get(f'https://{host}/api/v1/accounts/{aid}/statuses?limit=6&exclude_replies=true')
        out = []
        for s in json.loads(buf):
            media = s.get('media_attachments') or []
            out.append({'platform': 'mastodon', 'account': f'@{user}@{host}', 'kind': 'post', 'text': _strip(s.get('content', ''))[:400],
                        'url': s.get('url', ''), 'taken_at': s.get('created_at', ''), 'image_url': (media[0].get('preview_url') if media else '') or ''})
        return out[:5]
    except Exception:
        return []


def rss(url):
    try:
        r, buf = get(url.strip())
        host = urlparse(url).hostname or 'rss'
        return parse_feed(buf, 'rss', host.replace('www.', ''), 'news', limit=5, hours=24 * 7) if r.status_code == 200 else []
    except Exception:
        return []


def tiktok(handle):
    """Public profile via yt-dlp, best effort. TikTok may block; then we return [] and the drop says so."""
    handle = handle.strip().lstrip('@')
    if not re.fullmatch(r'[\w.]{2,40}', handle):
        return []
    import json, subprocess
    try:
        res = subprocess.run(['yt-dlp', '--flat-playlist', '--dump-json', '--playlist-end', '5', f'https://www.tiktok.com/@{handle}'],
                             capture_output=True, text=True, timeout=25)
        out = []
        for line in res.stdout.splitlines():
            try:
                v = json.loads(line)
            except Exception:
                continue
            ts = v.get('timestamp')
            out.append({'platform': 'tiktok', 'account': '@' + handle, 'kind': 'video', 'text': (v.get('title') or v.get('description') or '')[:400],
                        'url': v.get('webpage_url') or v.get('url') or '', 'image_url': v.get('thumbnail') or '',
                        'taken_at': datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ''})
        return out
    except Exception:
        return []


def instagram(handle):
    """Public profile JSON without login. Instagram often blocks this; then [] (no login fallback by design)."""
    handle = handle.strip().lstrip('@')
    if not re.fullmatch(r'[\w.]{2,30}', handle):
        return []
    try:
        import json
        r, buf = get(f'https://i.instagram.com/api/v1/users/web_profile_info/?username={handle}',
                     headers={'x-ig-app-id': '936619743392459', 'User-Agent': UA})
        if r.status_code != 200:
            return []
        edges = json.loads(buf)['data']['user']['edge_owner_to_timeline_media']['edges']
        out = []
        for e in edges[:5]:
            n = e['node']
            cap = ((n.get('edge_media_to_caption', {}).get('edges') or [{}])[0].get('node') or {}).get('text', '')
            out.append({'platform': 'instagram', 'account': '@' + handle, 'kind': 'reel' if n.get('is_video') else 'post', 'text': cap[:400],
                        'url': f"https://www.instagram.com/p/{n.get('shortcode')}/", 'image_url': n.get('thumbnail_src') or n.get('display_url') or '',
                        'taken_at': datetime.fromtimestamp(n['taken_at_timestamp'], tz=timezone.utc).isoformat()})
        return out
    except Exception:
        return []


FETCHERS = {'news': news, 'reddit': reddit, 'youtube': youtube, 'bluesky': bluesky, 'mastodon': mastodon,
            'rss': rss, 'tiktok': tiktok, 'instagram': instagram}


def detect(value):
    """Guess the platform from pasted text: URL, @handle@instance, r/sub ..."""
    v = value.strip()
    if re.search(r'instagram\.com', v, re.I): return 'instagram', re.sub(r'.*instagram\.com/([\w.]+).*', r'\1', v, flags=re.I)
    if re.search(r'tiktok\.com', v, re.I): return 'tiktok', re.sub(r'.*tiktok\.com/@?([\w.]+).*', r'\1', v, flags=re.I)
    if re.search(r'youtube\.com|youtu\.be', v, re.I): return 'youtube', v
    if re.search(r'reddit\.com|^r/', v, re.I): return 'reddit', v
    if re.search(r'bsky\.app', v, re.I): return 'bluesky', re.sub(r'.*profile/([\w.\-]+).*', r'\1', v)
    if re.fullmatch(r'@?[\w.\-]+@[\w.\-]+\.\w+', v): return 'mastodon', v
    if v.startswith('http'): return 'rss', v
    return None, v


def fetch_all(topics, sources, workers=8):
    """sources: [{platform, value}]. Returns (items, status) where status[platform:value] = count."""
    jobs = [('news', t) for t in topics[:5]] + [(s['platform'], s['value']) for s in sources[:25] if s.get('platform') in FETCHERS]

    def run(j):
        return j, FETCHERS[j[0]](j[1])
    items, status = [], {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for j, res in ex.map(run, jobs):
            status[f'{j[0]}:{j[1]}'] = len(res)
            items.extend(res)
    return items, status


def thumb_b64(image_url, size=512):
    """Download + shrink an image to a small JPEG for the vision model. Returns base64 or ''."""
    try:
        from PIL import Image
        r, buf = get(image_url)
        if r.status_code != 200:
            return ''
        im = Image.open(io.BytesIO(buf)).convert('RGB')
        im.thumbnail((size, size))
        out = io.BytesIO()
        im.save(out, 'JPEG', quality=70)
        return base64.b64encode(out.getvalue()).decode()
    except Exception:
        return ''
