from flask import Flask, request, jsonify
import json
import os
import base64
import subprocess
import hashlib
import time
import re
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from PIL import Image

import requests

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
IMG_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'img')

DEMO_FILE = os.path.join(DATA_DIR, 'demo_social.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'connections.json')

os.makedirs(os.path.join(DATA_DIR, 'sessions'), exist_ok=True)

NS = {'atom': 'http://www.w3.org/2005/Atom'}

_cache = {}
CACHE_TTL = 600
USER_AGENT = 'CypherNews/1.0 (Hackathon Demo; contact@example.com)'

INSTAGRAM_SESSION_FILE = os.path.join(DATA_DIR, 'sessions', 'instagram.session')
SOCIAL_ENV_FILE = os.path.join(os.path.expanduser('~'), '.config', 'hackathon', 'social.env')

_ig_user = None
_ig_pass = None
_ig_logged_in = False
_ig_login_attempted = False
_ig_login_error = None
_ig_instance = None
_ig_profile = None


def cache_get(key):
    entry = _cache.get(key)
    if entry and time.time() - entry['ts'] < CACHE_TTL:
        return entry['data']
    return None


def cache_set(key, data):
    _cache[key] = {'ts': time.time(), 'data': data}


def _parse_social_env():
    """Parse ~/.config/hackathon/social.env for IG_USER and IG_PASS.
    Custom parser: handles values with $-signs, quotes, whitespace.
    Never logs or returns the password."""
    global _ig_user, _ig_pass
    if _ig_user is not None:
        return
    try:
        with open(SOCIAL_ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue
                key, _, val = line.partition('=')
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                if key == 'IG_USER':
                    _ig_user = val
                elif key == 'IG_PASS':
                    _ig_pass = val
    except FileNotFoundError:
        app.logger.error(f"social.env not found at {SOCIAL_ENV_FILE}")
    except Exception as e:
        app.logger.error(f"Failed to parse social.env: {e}")


def _init_instaloader():
    """One-time Instaloader login with session persistence.
    Never retries on failure (Challenge, 2FA, checkpoint, Rate-Limit)."""
    global _ig_logged_in, _ig_login_attempted, _ig_login_error, _ig_instance, _ig_profile

    if _ig_login_attempted:
        return

    _parse_social_env()
    _ig_login_attempted = True

    if not _ig_user or not _ig_pass:
        _ig_login_error = 'social.env: IG_USER or IG_PASS missing'
        return

    import instaloader

    L = instaloader.Instaloader(
        user_agent=USER_AGENT,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    if os.path.exists(INSTAGRAM_SESSION_FILE):
        try:
            L.load_session_from_file(_ig_user, INSTAGRAM_SESSION_FILE)
            _ig_instance = L
            _ig_logged_in = True
            try:
                _ig_profile = instaloader.Profile.from_username(L.context, _ig_user)
            except Exception:
                _ig_profile = None
            return
        except Exception:
            os.unlink(INSTAGRAM_SESSION_FILE)

    try:
        L.login(_ig_user, _ig_pass)
        os.makedirs(os.path.dirname(INSTAGRAM_SESSION_FILE), exist_ok=True)
        L.save_session_to_file(INSTAGRAM_SESSION_FILE)
        _ig_instance = L
        _ig_logged_in = True
        try:
            _ig_profile = instaloader.Profile.from_username(L.context, _ig_user)
        except Exception:
            _ig_profile = None
    except instaloader.exceptions.BadCredentialsException:
        _ig_login_error = 'Bad credentials'
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        _ig_login_error = '2FA required – cannot login with burner account'
    except instaloader.exceptions.LoginException:
        _ig_login_error = 'Challenge required – cannot proceed'
    except instaloader.exceptions.ConnectionException as e:
        _ig_login_error = f'Connection error: {e}'
    except Exception as e:
        err_msg = str(e).lower()
        if 'checkpoint' in err_msg:
            _ig_login_error = 'Account checkpoint triggered – cannot proceed'
        elif 'rate' in err_msg and 'limit' in err_msg:
            _ig_login_error = 'Rate limited – try again later'
        elif 'login' in err_msg and 'required' in err_msg:
            _ig_login_error = 'Login required'
        else:
            _ig_login_error = f'Login failed: {e}'


def ig_login_status():
    _init_instaloader()
    return {
        'logged_in': _ig_logged_in,
        'error': _ig_login_error,
        'display_name': _ig_user if _ig_logged_in else None,
    }


def load_demo():
    try:
        with open(DEMO_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"social_items": []}


def load_connections():
    try:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_connections(conns):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(conns, f)


def make_thumbnail(url_or_path, platform=''):
    cache_key = f"thumb_{hashlib.md5(url_or_path.encode()).hexdigest()}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    tmp_in = f"/tmp/socialfetch_thumb_{os.getpid()}_{int(time.time()*1000)}"
    try:
        if url_or_path.startswith('http'):
            r = requests.get(url_or_path, headers={'User-Agent': USER_AGENT}, timeout=10)
            if r.status_code != 200:
                return None
            ext = '.jpg'
            ct = r.headers.get('content-type', '')
            if 'png' in ct:
                ext = '.png'
            elif 'webp' in ct:
                ext = '.webp'
            tmp_in += ext
            with open(tmp_in, 'wb') as f:
                f.write(r.content)
        else:
            tmp_in = url_or_path

        result = subprocess.run(
            ['convert', tmp_in, '-resize', '80x80^', '-gravity', 'center',
             '-extent', '80x80', '-quality', '60', 'jpeg:-'],
            capture_output=True, timeout=8
        )
        if result.returncode == 0 and 0 < len(result.stdout) < 81920:
            b64 = base64.b64encode(result.stdout).decode('ascii')
            cache_set(cache_key, b64)
            return b64
    except Exception:
        pass
    finally:
        if tmp_in != url_or_path:
            try:
                os.unlink(tmp_in)
            except Exception:
                pass
    return None


def demo_thumbnail():
    paths = [os.path.join(IMG_DIR, f) for f in ['field_pix.jpg', 'money_pix.jpg', 'field_duo.jpg', 'money_duo.jpg']]
    for p in paths:
        if os.path.exists(p):
            thumb = make_thumbnail(p)
            if thumb:
                return thumb
    return None


def parse_rss_date(text):
    if not text:
        return datetime.now(timezone.utc).isoformat()
    for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S.%fZ']:
        try:
            return datetime.strptime(text.strip(), fmt).isoformat()
        except Exception:
            continue
    return datetime.now(timezone.utc).isoformat()


def text_element(el, tag):
    child = el.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ''


def scrape_youtube_channel(handle, hours=48):
    handle = handle.lstrip('@')
    cache_key = f"yt_{handle}_{hours}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    items = []
    rss_items = []

    def try_ytdlp():
        nonlocal items
        try:
            result = subprocess.run(
                ['yt-dlp', '--flat-playlist', '--dump-json', '--playlist-end', '5',
                 f'https://www.youtube.com/@{handle}'],
                capture_output=True, text=True, timeout=20
            )
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    v = json.loads(line)
                    vi = scrape_youtube_video(v, handle, hours)
                    if vi:
                        items.append(vi)
                except Exception:
                    continue
        except Exception:
            pass

    try:
        urls = [
            f'https://www.youtube.com/feeds/videos.xml?channel_id={handle}',
            f'https://www.youtube.com/feeds/videos.xml?user={handle}',
        ]
        rss_xml = None
        for url in urls:
            try:
                r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
                if r.status_code == 200 and '<feed' in r.text:
                    rss_xml = r.text
                    break
            except Exception:
                continue

        if rss_xml:
            root = ET.fromstring(rss_xml)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                try:
                    published = parse_rss_date(entry.find('{http://www.w3.org/2005/Atom}published').text if entry.find('{http://www.w3.org/2005/Atom}published') is not None else '')
                    try:
                        pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    except Exception:
                        pub_dt = datetime.now(timezone.utc)
                    if pub_dt < cutoff:
                        continue

                    title = text_element(entry, '{http://www.w3.org/2005/Atom}title')
                    link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                    url = link_el.get('href', '') if link_el is not None else ''

                    media_group = entry.find('{http://search.yahoo.com/mrss/}group')
                    thumb_b64 = None
                    if media_group is not None:
                        thumb_el = media_group.find('{http://search.yahoo.com/mrss/}thumbnail')
                        if thumb_el is not None:
                            thumb_url = thumb_el.get('url', '')
                            if thumb_url:
                                thumb_b64 = make_thumbnail(thumb_url)

                    item = {
                        'platform': 'youtube',
                        'account': f'@{handle}',
                        'kind': 'video',
                        'text': title,
                        'url': url,
                        'taken_at': published,
                    }
                    if thumb_b64:
                        item['image_b64'] = thumb_b64
                    rss_items.append(item)
                except Exception:
                    continue

        items = rss_items
        if not items:
            try_ytdlp()

        cache_set(cache_key, items)
    except Exception:
        try_ytdlp()
    return items


def scrape_youtube_video(video_json, handle, hours):
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        ts = video_json.get('timestamp') or video_json.get('upload_date')
        if ts:
            try:
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    dt = datetime.strptime(str(ts), '%Y%m%d').replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    return None
                published = dt.isoformat()
            except Exception:
                published = datetime.now(timezone.utc).isoformat()
        else:
            published = datetime.now(timezone.utc).isoformat()

        vid = video_json.get('id', '')
        url = f'https://www.youtube.com/watch?v={vid}' if vid else ''
        title = video_json.get('title', '')

        thumb_b64 = None
        thumb_url = video_json.get('thumbnail') or video_json.get('thumbnails', [{}])[0].get('url', '')
        if thumb_url:
            thumb_b64 = make_thumbnail(thumb_url)

        item = {
            'platform': 'youtube',
            'account': f'@{handle}',
            'kind': 'video',
            'text': title,
            'url': url,
            'taken_at': published,
        }
        if thumb_b64:
            item['image_b64'] = thumb_b64
        return item
    except Exception:
        return None


def scrape_reddit(subreddit, hours=48):
    subreddit = subreddit.lstrip('/r/').lstrip('r/')
    cache_key = f"reddit_{subreddit}_{hours}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    items = []
    try:
        url = f'https://www.reddit.com/r/{subreddit}/top/.rss?t=day&limit=10'
        r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
        if r.status_code != 200:
            return []

        root = ET.fromstring(r.text)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            try:
                published = parse_rss_date(
                    entry.find('{http://www.w3.org/2005/Atom}updated').text
                    if entry.find('{http://www.w3.org/2005/Atom}updated') is not None else ''
                )
                try:
                    pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                except Exception:
                    pub_dt = datetime.now(timezone.utc)
                if pub_dt < cutoff:
                    continue

                title = text_element(entry, '{http://www.w3.org/2005/Atom}title')
                link_el = entry.find('{http://www.w3.org/2005/Atom}link')
                url = link_el.get('href', '') if link_el is not None else ''

                content_el = entry.find('{http://www.w3.org/2005/Atom}content')
                text = ''
                if content_el is not None and content_el.text:
                    text = re.sub(r'<[^>]+>', ' ', content_el.text)[:300].strip()

                item = {
                    'platform': 'reddit',
                    'account': f'r/{subreddit}',
                    'kind': 'post',
                    'text': f'{title}: {text}' if text else title,
                    'url': url,
                    'taken_at': published,
                }
                items.append(item)
            except Exception:
                continue

        cache_set(cache_key, items)
    except Exception:
        pass
    return items


def scrape_tiktok(handle, hours=48):
    handle = handle.lstrip('@')
    cache_key = f"tt_{handle}_{hours}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    items = []
    try:
        result = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--dump-json', '--playlist-end', '5',
             f'https://www.tiktok.com/@{handle}'],
            capture_output=True, text=True, timeout=20
        )
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                v = json.loads(line)
                ts = v.get('timestamp')
                if ts:
                    try:
                        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                        if dt < cutoff:
                            continue
                        published = dt.isoformat()
                    except Exception:
                        published = datetime.now(timezone.utc).isoformat()
                else:
                    published = datetime.now(timezone.utc).isoformat()

                title = v.get('title') or v.get('description', '')
                vid = v.get('id', '')
                url = v.get('webpage_url') or f'https://www.tiktok.com/@{handle}/video/{vid}'

                thumb_b64 = None
                thumb_url = v.get('thumbnail') or (v.get('thumbnails', [{}])[0].get('url') if v.get('thumbnails') else '')
                if not thumb_url:
                    try:
                        info = subprocess.run(
                            ['yt-dlp', '--dump-json', '--playlist-end', '1', url],
                            capture_output=True, text=True, timeout=15
                        )
                        vi = json.loads(info.stdout)
                        thumb_url = vi.get('thumbnail', '')
                    except Exception:
                        pass
                if thumb_url:
                    thumb_b64 = make_thumbnail(thumb_url)

                item = {
                    'platform': 'tiktok',
                    'account': f'@{handle}',
                    'kind': 'video',
                    'text': title,
                    'url': url,
                    'taken_at': published,
                }
                if thumb_b64:
                    item['image_b64'] = thumb_b64
                items.append(item)
            except Exception:
                continue

        cache_set(cache_key, items)
    except Exception:
        pass
    return items


def scrape_instagram(handle, hours=48):
    """Scrape up to 4 posts/reels and current stories for an Instagram profile.
    Requires successful login via _init_instaloader(). Falls back to empty list on error."""
    handle = handle.lstrip('@')
    cache_key = f"ig_{handle}_{hours}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    _init_instaloader()
    items = []

    if not _ig_logged_in or not _ig_instance:
        return items

    import instaloader

    try:
        profile = instaloader.Profile.from_username(_ig_instance.context, handle)
    except Exception:
        return items

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    try:
        post_count = 0
        for post in profile.get_posts():
            if post_count >= 4:
                break
            try:
                if post.date_utc.replace(tzinfo=timezone.utc) < cutoff:
                    continue

                caption = (post.caption[:300] if post.caption else '').replace('\n', ' ').strip()
                post_url = f'https://www.instagram.com/p/{post.shortcode}/'

                thumb_b64 = None
                thumb_url = post.thumbnail_url if hasattr(post, 'thumbnail_url') and post.thumbnail_url else post.url
                if thumb_url:
                    thumb_b64 = make_thumbnail(thumb_url)

                kind = 'reel' if post.is_video else 'post'

                item = {
                    'platform': 'instagram',
                    'account': f'@{handle}',
                    'kind': kind,
                    'text': caption,
                    'url': post_url,
                    'taken_at': post.date_utc.replace(tzinfo=timezone.utc).isoformat(),
                }
                if thumb_b64:
                    item['image_b64'] = thumb_b64
                items.append(item)
                post_count += 1
            except Exception:
                continue
    except Exception:
        pass

    try:
        profile_uid = profile.userid
        for story_obj in _ig_instance.get_stories(userids=[profile_uid]):
            for story_item in story_obj.get_items():
                try:
                    if story_item.date_utc.replace(tzinfo=timezone.utc) < cutoff:
                        continue
                    thumb_b64 = None
                    if hasattr(story_item, 'thumbnail_url') and story_item.thumbnail_url:
                        thumb_b64 = make_thumbnail(story_item.thumbnail_url)
                    elif hasattr(story_item, 'url') and story_item.url:
                        thumb_b64 = make_thumbnail(story_item.url)

                    story_entry = {
                        'platform': 'instagram',
                        'account': f'@{handle}',
                        'kind': 'story',
                        'text': '',
                        'url': f'https://www.instagram.com/stories/{handle}/',
                        'taken_at': story_item.date_utc.replace(tzinfo=timezone.utc).isoformat(),
                    }
                    if thumb_b64:
                        story_entry['image_b64'] = thumb_b64
                    items.append(story_entry)
                except Exception:
                    continue
    except Exception:
        pass

    cache_set(cache_key, items)
    time.sleep(3)
    return items


SCRAPERS = {
    'youtube': scrape_youtube_channel,
    'reddit': scrape_reddit,
    'tiktok': scrape_tiktok,
    'instagram': scrape_instagram,
}


def demo_accounts():
    data = load_demo()
    accounts = {}
    for item in data.get('social_items', []):
        plat = item.get('platform', '')
        acc = item.get('account', '')
        if plat and acc:
            accounts.setdefault(plat, [])
            if acc not in accounts[plat]:
                accounts[plat].append(acc)
    return accounts


def demo_feed(platform=None, accounts=None, hours=48):
    data = load_demo()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items = []
    requested_accounts = [a.strip().lstrip('@') for a in (accounts or '').split(',')] if accounts else []
    for item in data.get('social_items', []):
        if platform and item.get('platform', '') != platform:
            continue
        if requested_accounts:
            item_acc = item.get('account', '').lstrip('@')
            if item_acc not in requested_accounts:
                continue
        taken = item.get('taken_at', '')
        if taken:
            try:
                dt = datetime.fromisoformat(taken.replace('Z', '+00:00'))
                if dt < cutoff:
                    continue
            except Exception:
                pass
        thumb = demo_thumbnail()
        entry = dict(item)
        if thumb and 'image_b64' not in entry:
            entry['image_b64'] = thumb
        items.append(entry)
    return items


def live_feed(platform, accounts_list, hours):
    scraper = SCRAPERS.get(platform)
    if not scraper:
        return []
    items = []
    for acc in accounts_list:
        try:
            result = scraper(acc, hours)
            if result:
                items.extend(result)
        except Exception:
            continue
    return items


@app.route('/connect', methods=['POST'])
def connect():
    body = request.get_json(silent=True) or {}
    platform = body.get('platform', '')
    username = body.get('username', '')
    password = body.get('password', '')

    if not platform or not username:
        return jsonify({'ok': False, 'error': 'platform and username required'}), 400

    conns = load_connections()
    key = f"{platform}:{username}"
    conns[key] = {
        'platform': platform,
        'username': username,
        'connected_at': datetime.now(timezone.utc).isoformat(),
        'display_name': username
    }
    save_connections(conns)

    return jsonify({'ok': True, 'display_name': username, 'platform': platform})


@app.route('/accounts', methods=['GET'])
def accounts():
    platform = request.args.get('platform', '')
    if platform:
        demo_accs = demo_accounts()
        return jsonify({'accounts': demo_accs.get(platform, []), 'demo': True})
    return jsonify({'accounts': demo_accounts(), 'demo': True})


@app.route('/feed', methods=['GET'])
def feed():
    platform = request.args.get('platform', '')
    accounts_str = request.args.get('accounts', '')
    hours = int(request.args.get('hours', '48'))
    try_live = request.args.get('live', '0') == '1'

    live_items = []
    if try_live:
        accounts_list = [a.strip().lstrip('@') for a in accounts_str.split(',') if a.strip()] if accounts_str else []
        for plat in SCRAPERS:
            if platform and plat != platform:
                continue
            if accounts_list:
                plat_accounts = accounts_list
            else:
                plat_accounts = demo_accounts().get(plat, [])
            if plat_accounts:
                plat_items = live_feed(plat, plat_accounts, hours)
                if plat_items:
                    live_items.extend(plat_items)

    if live_items:
        return jsonify({'items': live_items, 'count': len(live_items), 'demo': False})

    demo_items = demo_feed(platform=platform or None, accounts=accounts_str, hours=hours)
    return jsonify({'items': demo_items, 'count': len(demo_items), 'demo': True,
                    '_note': 'DEMO DATA – sample posts only'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'ok': True, 'demo': True})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5090, debug=False)