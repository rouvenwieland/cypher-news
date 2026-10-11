"""Public, login-free sources. No passwords, no scraping behind logins.
Every function returns a list of items: {platform, account, kind, text, url, taken_at, image_url} and never raises."""
import base64, io, ipaddress, re, socket, time
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
    """GET with SSRF guard on every redirect hop. Returns (response, body bytes, max 3 MB)."""
    headers = dict(kw.pop('headers', {}) or {})
    headers.setdefault('User-Agent', UA)
    retried = False
    for _ in range(5):
        if not is_public_url(url):
            raise ValueError('blocked url')
        r = requests.get(url, timeout=TIMEOUT, stream=True, headers=headers, allow_redirects=False, **kw)
        if r.status_code == 429 and not retried:  # rate limited (Reddit): wait once and retry
            r.close(); retried = True; time.sleep(2.5)
            continue
        if r.status_code in (301, 302, 303, 307, 308) and r.headers.get('Location'):
            url = requests.compat.urljoin(url, r.headers['Location'])
            r.close()
            continue
        return r, r.raw.read(MAX_BYTES, decode_content=True)
    raise ValueError('too many redirects')


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
            m = re.search(rb'channel_id=(UC[\w-]{22})', buf)
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
            s = s.get('reblog') or s
            media = s.get('media_attachments') or []
            text = _strip(s.get('content', ''))[:400]
            if not text and not media:
                continue
            out.append({'platform': 'mastodon', 'account': f'@{user}@{host}', 'kind': 'post', 'text': text or 'Bild-Post',
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
    import json, subprocess, sys
    try:
        res = subprocess.run([sys.executable, '-m', 'yt_dlp', '--impersonate', 'chrome', '--flat-playlist', '--dump-json', '--playlist-end', '5', f'https://www.tiktok.com/@{handle}'],
                             capture_output=True, text=True, timeout=25)
        out = []
        for line in res.stdout.splitlines():
            try:
                v = json.loads(line)
            except Exception:
                continue
            ts = v.get('timestamp')
            if not v.get('thumbnail') and len(out) < 3 and v.get('url'):
                try:  # oEmbed gives a thumbnail without login
                    r, buf = get('https://www.tiktok.com/oembed?url=' + quote(v['url'], safe=''))
                    v['thumbnail'] = json.loads(buf).get('thumbnail_url', '')
                except Exception:
                    pass
            out.append({'platform': 'tiktok', 'account': '@' + handle, 'kind': 'video', 'text': (v.get('title') or v.get('description') or '')[:400],
                        'url': v.get('webpage_url') or v.get('url') or '', 'image_url': v.get('thumbnail') or '',
                        'taken_at': datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ''})
        return out
    except Exception:
        return []


def instagram(handle):
    """Latest public posts via Instagram's public embed page (no login, no password). Unofficial: may break or be rate limited."""
    handle = handle.strip().lstrip('@')
    if not re.fullmatch(r'[\w.]{2,30}', handle):
        return []
    try:
        import json
        r, buf = get(f'https://www.instagram.com/{handle}/embed/',
                     headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'})
        m = re.search(rb'"contextJSON":"((?:[^"\\]|\\.)*)"', buf)
        if r.status_code != 200 or not m:
            return []
        ctx = json.loads(json.loads('"' + m.group(1).decode('utf8') + '"'))['context']
        out = []
        for g in ctx.get('graphql_media', [])[:6]:
            n = g.get('shortcode_media') or {}
            cap = ((n.get('edge_media_to_caption', {}).get('edges') or [{}])[0].get('node') or {}).get('text', '')
            res = n.get('display_resources') or []
            out.append({'platform': 'instagram', 'account': '@' + handle, 'kind': 'reel' if n.get('is_video') else 'post',
                        'text': cap[:400] or 'Bild-Post', 'url': f"https://www.instagram.com/p/{n.get('shortcode')}/",
                        'image_url': (res[0]['src'] if res else n.get('display_url', '')),
                        'taken_at': datetime.fromtimestamp(n['taken_at_timestamp'], tz=timezone.utc).isoformat()})
        return out
    except Exception:
        return []


def _walk_tweets(o, out):
    """Finds tweet-like dicts anywhere in the syndication JSON (tolerates format drift)."""
    if isinstance(o, dict):
        if o.get('id_str') and (o.get('full_text') or o.get('text')) and o.get('user'):
            out.append(o)
        for v in o.values():
            _walk_tweets(v, out)
    elif isinstance(o, list):
        for v in o:
            _walk_tweets(v, out)


def _tweet_item(t, handle):
    try:
        ts = datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S %z %Y').isoformat() if t.get('created_at') else ''
    except Exception:
        ts = t.get('created_at', '')
    media = (t.get('extended_entities') or t.get('entities') or {}).get('media') or []
    text = re.sub(r'\s+', ' ', t.get('full_text') or t.get('text') or '')
    text = re.sub(r'\s*https://t\.co/\w+', '', text).strip()  # t.co short links carry no information
    user = (t.get('user') or {}).get('screen_name') or handle
    return {'platform': 'x', 'account': '@' + handle, 'kind': 'post', 'text': text[:400] or 'Post mit Bild', 'url': f"https://x.com/{user}/status/{t['id_str']}",
            'taken_at': ts, 'image_url': (media[0].get('media_url_https') if media else '') or ''}


def x_official(handle, token):
    """Official X API v2 (pay-per-use, the user's own bearer token). Reliable but costs about $0.005 per post read."""
    import json
    h = {'Authorization': 'Bearer ' + token}
    r, buf = get(f'https://api.x.com/2/users/by/username/{quote(handle)}', headers=h)
    uid = json.loads(buf)['data']['id']
    r, buf = get(f'https://api.x.com/2/users/{uid}/tweets?max_results=5&exclude=replies,retweets&tweet.fields=created_at&expansions=attachments.media_keys&media.fields=url,preview_image_url', headers=h)
    d = json.loads(buf)
    media = {m['media_key']: (m.get('url') or m.get('preview_image_url') or '') for m in (d.get('includes') or {}).get('media', [])}
    out = []
    for t in d.get('data', []):
        keys = (t.get('attachments') or {}).get('media_keys') or []
        out.append({'platform': 'x', 'account': '@' + handle, 'kind': 'post', 'text': re.sub(r'\s*https://t\.co/\w+', '', t['text']).strip()[:400],
                    'url': f"https://x.com/{handle}/status/{t['id']}", 'taken_at': t.get('created_at', ''), 'image_url': media.get(keys[0], '') if keys else ''})
    return out


def x_tweet(url):
    """One public post by link (x.com/<user>/status/<id>): works without login and is not rate-limited like timelines.
    Returns an item dict or None."""
    m = re.search(r'(?:x|twitter)\.com/(?:#!/)?(\w+)/status(?:es)?/(\d{1,20})', url or '', re.I)
    if not m:
        return None
    try:
        import json
        r, buf = get(f'https://cdn.syndication.twimg.com/tweet-result?id={m.group(2)}&token=a')
        t = json.loads(buf)
        if r.status_code != 200 or not t.get('text'):
            return None
        photos = t.get('photos') or t.get('mediaDetails') or []
        img = (photos[0].get('url') or photos[0].get('media_url_https') or '') if photos else ''
        user = (t.get('user') or {}).get('screen_name') or m.group(1)
        text = re.sub(r'\s*https://t\.co/\w+', '', t['text']).strip()
        return {'platform': 'x', 'account': '@' + user, 'kind': 'post', 'text': text[:400] or 'Post mit Bild', 'url': f'https://x.com/{user}/status/{m.group(2)}',
                'taken_at': t.get('created_at', ''), 'image_url': img}
    except Exception:
        return None


def x_diagnose(handle):
    """Why does the public X embed return nothing? Returns a short, secret-free description (shown by the source test)."""
    try:
        r, buf = get(f'https://syndication.twitter.com/srv/timeline-profile/screen-name/{re.sub(r"[^A-Za-z0-9_]", "", handle)}?showReplies=false',
                     headers={'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://publish.twitter.com/'})
        has = bool(re.search(rb'<script id="__NEXT_DATA__"', buf))
        return {'http': r.status_code, 'bytes': len(buf), 'has_data': has, 'start': re.sub(r'\s+', ' ', buf[:90].decode('utf8', 'replace'))}
    except Exception as e:
        return {'error': f'{type(e).__name__}: {str(e)[:100]}'}


def x(handle, token=None):
    """X (Twitter). With the user's own API token: official API. Without: the public embed timeline (free, unofficial, X rate-limits it)."""
    handle = re.sub(r'^(https?://)?(www\.)?(x|twitter)\.com/', '', handle.strip()).lstrip('@').split('/')[0].split('?')[0]
    if not re.fullmatch(r'\w{1,15}', handle):
        return []
    try:
        if token:
            items = x_official(handle, token)
            if items:
                return items
        import json
        r, buf = get(f'https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}?showReplies=false',
                     headers={'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://publish.twitter.com/'})
        m = re.search(rb'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', buf, re.S)
        if r.status_code != 200 or not m:
            return []
        found = []
        _walk_tweets(json.loads(m.group(1)), found)
        seen, out = set(), []
        for t in found:
            if t['id_str'] in seen or (t.get('user') or {}).get('screen_name', '').lower() != handle.lower():
                continue  # skip quoted tweets of other accounts and duplicates
            seen.add(t['id_str']); out.append(_tweet_item(t, handle))
        out.sort(key=lambda i: i['taken_at'], reverse=True)
        return out[:5]
    except Exception:
        return []


FETCHERS = {'news': news, 'reddit': reddit, 'youtube': youtube, 'bluesky': bluesky, 'mastodon': mastodon,
            'rss': rss, 'tiktok': tiktok, 'instagram': instagram, 'x': x}


def detect(value):
    """Guess the platform from pasted text: URL, @handle@instance, r/sub ..."""
    v = value.strip()
    if re.search(r'instagram\.com', v, re.I): return 'instagram', re.sub(r'.*instagram\.com/([\w.]+).*', r'\1', v, flags=re.I)
    if re.search(r'tiktok\.com', v, re.I): return 'tiktok', re.sub(r'.*tiktok\.com/@?([\w.]+).*', r'\1', v, flags=re.I)
    if re.search(r'youtube\.com|youtu\.be', v, re.I): return 'youtube', v
    if re.search(r'reddit\.com|^r/', v, re.I): return 'reddit', v
    if re.search(r'(^|//)(www\.)?(x|twitter)\.com/', v, re.I): return 'x', re.sub(r'.*(?:x|twitter)\.com/@?(\w+).*', r'\1', v, flags=re.I)
    if re.fullmatch(r'(x|twitter):@?\w+', v, re.I): return 'x', v.split(':', 1)[1].lstrip('@')
    if re.search(r'bsky\.app', v, re.I): return 'bluesky', re.sub(r'.*profile/([\w.\-]+).*', r'\1', v)
    if re.fullmatch(r'@?[\w.\-]+@[\w.\-]+\.\w+', v): return 'mastodon', v
    if v.startswith('http'): return 'rss', v
    return None, v


def fetch_all(topics, sources, workers=8, x_token=None):
    """sources: [{platform, value}]. Returns (items, status) where status[platform:value] = count."""
    jobs = [('news', t) for t in topics[:5]] + [(s['platform'], s['value']) for s in sources[:25] if s.get('platform') in FETCHERS]

    def run(j):
        return j, (FETCHERS['x'](j[1], x_token) if j[0] == 'x' else FETCHERS[j[0]](j[1]))
    items, status = [], {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for j, res in ex.map(run, jobs):
            status[f'{j[0]}:{j[1]}'] = len(res)
            items.extend(res)
    return items, status


def thumb_b64(image_url, size=512, quality=70):
    """Download + shrink an image to a small JPEG for the vision model. Returns base64 or ''."""
    try:
        from PIL import Image
        r, buf = get(image_url)
        if r.status_code != 200:
            return ''
        im = Image.open(io.BytesIO(buf)).convert('RGB')
        im.thumbnail((size, size))
        out = io.BytesIO()
        im.save(out, 'JPEG', quality=quality)
        return base64.b64encode(out.getvalue()).decode()
    except Exception:
        return ''
