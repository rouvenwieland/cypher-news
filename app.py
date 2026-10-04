from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import threading
from datetime import datetime, timezone

import requests

app = Flask(__name__)

MODEL_PRIMARY = os.environ.get('MODEL_PRIMARY', 'unknown')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', 'http://127.0.0.1:5678/webhook/newsletter')
SOCIALFETCH_URL = os.environ.get('SOCIALFETCH_URL', 'http://127.0.0.1:5090')

CONNECTIONS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'connections.json')
CONNECTIONS_LOCK = threading.Lock()

MOCK_ITEMS = [
    {"category": "Konzerte", "title": "Freiluftkonzert im Mauerpark heute Abend", "summary": "Kostenloses Konzert mit drei lokalen Indie-Bands ab 19 Uhr. Picknickdecke nicht vergessen – Eintritt frei.", "source": "Eventkalender Berlin", "url": "https://example.com/concert-mauerpark", "when": ""},
    {"category": "Konzerte", "title": "Techno-Nacht im Club OST", "summary": "Lokale DJs legen ab 23 Uhr auf. Eintritt frei bis Mitternacht, danach 10 €. Line-up: DJ Spacer, MIRA, KX6000.", "source": "Club OST Berlin", "url": "https://example.com/club-ost", "when": ""},
    {"category": "Giveaways", "title": "Gewinne ein Jahr lang kostenlosen Cloud-Speicher", "summary": "TechStartup verlost 50× 2TB Cloud-Speicher. Teilnahme per Newsletter-Anmeldung bis Sonntag 23:59 Uhr.", "source": "TechGiveaway", "url": "https://example.com/giveaway-cloud", "when": ""},
    {"category": "Giveaways", "title": "SNEAKRS Raffle: Travis Scott x Nike Air Max", "summary": "Die neue Kollaboration droppt heute um 10 Uhr exklusiv in der SNEAKRS-App. 3.000 Paare weltweit.", "source": "SNEAKRS App", "url": "https://example.com/sneakrs-travis", "when": ""},
    {"category": "Mode", "title": "ACRONYM® öffnet Popup-Store in Berlin-Mitte", "summary": "Limitierte Herbstkollektion nur dieses Wochenende in der Rosenthaler Straße. Early-Access ab 9 Uhr.", "source": "Highsnobiety", "url": "https://example.com/acronym-popup", "when": ""},
    {"category": "Mode", "title": "Vivienne Westwood Archive Sale Online", "summary": "Bis zu 70% auf ausgewählte Archiv-Stücke. Nur 48 Stunden online – Code ARCHIVE48 beim Checkout.", "source": "Vivienne Westwood", "url": "https://example.com/vw-archive-sale", "when": ""},
    {"category": "Tech", "title": "OpenAI leakt Verse 2: Open-Source-Bildmodell mit 8B Parametern", "summary": "Neues Modell erreicht State-of-the-Art auf 5 Benchmarks. Apache-2.0-Lizenz, läuft auf einzelner RTX 4090.", "source": "Hacker News", "url": "https://example.com/verse-2-oss", "when": ""},
    {"category": "Trends", "title": "5 Trends, die diese Woche jeder teilt", "summary": "Von KI-generierten Avataren bis Bio-3D-Druck: Das sind die Themen, die gerade viral gehen.", "source": "YouTube TrendCheck", "url": "https://example.com/weekly-trends", "when": ""}
]

CATEGORY_MAP = {
    'konzerte': 'Konzerte', 'concert': 'Konzerte', 'gig': 'Konzerte', 'club': 'Konzerte',
    'giveaway': 'Giveaways', 'gewinnspiel': 'Giveaways', 'raffle': 'Giveaways',
    'mode': 'Mode', 'fashion': 'Mode', 'drop': 'Mode', 'sneaker': 'Mode', 'streetwear': 'Mode',
    'tech': 'Tech', 'ai': 'Tech', 'opensource': 'Tech',
    'snack': 'Trends', 'food': 'Trends', 'trends': 'Trends',
    'hackathon': 'Tech',
}


def classify_social(text):
    t = text.lower()
    for key, cat in CATEGORY_MAP.items():
        if key in t:
            return cat
    return 'Sonstiges'


def social_items_from_raw(raw_items):
    items = []
    for s in (raw_items or []):
        img = s.get('image_b64', '')
        img_src = s.get('image', '')
        items.append({
            'category': classify_social(s.get('text', '')),
            'title': s.get('text', '')[:80] + ('...' if len(s.get('text', '')) > 80 else ''),
            'summary': s.get('text', ''),
            'source': f"{s.get('platform', '')}: @{s.get('account', '')}",
            'url': s.get('url', ''),
            'when': s.get('taken_at', '')[:10] if s.get('taken_at') else '',
            'kind': s.get('kind', 'post'),
            'platform': s.get('platform', ''),
            'account': s.get('account', ''),
            'image': img_src or (f'data:image/jpeg;base64,{img}' if img else ''),
            '_demo': s.get('_demo', False),
        })
    return items


def load_demo_social_raw():
    try:
        path = os.path.join(app.root_path, 'data', 'demo_social.json')
        with open(path, 'r') as f:
            d = json.load(f)
        items = d.get('social_items', [])
        for item in items:
            item['_demo'] = True
        return items
    except Exception:
        return []


def demo_social_items():
    return social_items_from_raw(load_demo_social_raw())


def load_connections():
    try:
        with CONNECTIONS_LOCK:
            with open(CONNECTIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        return {}


def save_connections(conns):
    with CONNECTIONS_LOCK:
        os.makedirs(os.path.dirname(CONNECTIONS_FILE), exist_ok=True)
        with open(CONNECTIONS_FILE, 'w') as f:
            json.dump(conns, f)


def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def mock_response(include_social=True):
    t = today_str()
    items = [{**i, "when": t} for i in MOCK_ITEMS]
    if include_social:
        social = demo_social_items()
        items = items + social
    return {"title": "DEIN DROP", "date": t, "intro": f"{len(items)} Treffer aus 5+ Quellen – kuratiert von KI für dich.", "items": items, "source": "mock"}

def fallback_from_file():
    data_path = os.path.join(app.root_path, 'data', 'sample_newsletter.json')
    with open(data_path, 'r') as f:
        d = json.load(f)
    items = [{"category": i["category"], "title": i["title"], "summary": i["summary"],
              "source": i["source"], "url": i["link"], "when": i["date"]} for i in d.get("newsletter", [])]
    social = demo_social_items()
    items = items + social
    return {"title": "DEIN DROP (Offline)", "date": today_str(),
            "intro": f"Fallback: Beispiel-Drop mit {len(items)} Treffern.", "items": items, "source": "fallback"}

@app.route('/')
def index():
    return render_template('index.html', model_name=MODEL_PRIMARY)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    body = request.get_json(silent=True) or {}
    preferences = body.get('preferences', '')
    sources = body.get('sources', [])
    date = body.get('date', today_str())
    accounts = body.get('accounts', {})
    use_demo = body.get('demo', False)

    social_items = []
    social_source = 'none'

    if accounts:
        acct_list = sum(accounts.values(), [])
        if not use_demo and acct_list:
            try:
                resp = requests.get(f'{SOCIALFETCH_URL}/feed', params={
                    'hours': 48,
                    'accounts': ','.join(acct_list)
                }, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    social_items = data.get('items', [])
                    if data.get('demo'):
                        social_source = 'demo'
                        for item in social_items:
                            item['_demo'] = True
                    else:
                        social_source = 'live'
            except Exception:
                social_source = 'demo_fallback'
        if not social_items and (use_demo or social_source == 'demo_fallback' or not acct_list):
            all_demo = load_demo_social_raw()
            if acct_list:
                requested = set(a.lstrip('@').lower() for a in acct_list)
                social_items = [s for s in all_demo if s.get('account', '').lstrip('@').lower() in requested]
                if not social_items:
                    social_items = all_demo
            else:
                social_items = all_demo
            social_source = social_source or 'demo'

    payload = {
        "preferences": preferences,
        "sources": sources,
        "date": date,
        "accounts": accounts,
        "social_items": social_items
    }

    n8n_result = None
    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=40)
        if resp.status_code == 200:
            n8n_result = resp.json()
    except Exception:
        pass

    if n8n_result:
        items = n8n_result.get('items', [])
        seen = set()
        for item in items:
            if 'url' not in item:
                item['url'] = ''
            if 'when' not in item:
                item['when'] = ''
            if 'kind' not in item:
                item['kind'] = 'news'
            if social_source in ('demo', 'demo_fallback') and item.get('platform'):
                item['_demo'] = True
            if item.get('platform') and item.get('account'):
                seen.add((item['platform'], item['account']))
        if social_items:
            processed = social_items_from_raw(social_items)
            for si in processed:
                key = (si.get('platform', ''), si.get('account', ''))
                if key not in seen:
                    items.append(si)
                    seen.add(key)
        return jsonify({
            "title": n8n_result.get('title', 'DEIN DROP'),
            "date": n8n_result.get('date', today_str()),
            "intro": n8n_result.get('intro', ''),
            "items": items,
            "meta": n8n_result.get('meta', {}),
            "source": "n8n",
            "social_source": social_source
        })

    try:
        return jsonify(fallback_from_file())
    except Exception:
        return jsonify(mock_response())

@app.route('/mock/newsletter', methods=['POST'])
def mock_newsletter():
    return jsonify(mock_response())

@app.route('/data/sample_newsletter.json')
def sample_newsletter():
    data_dir = os.path.join(app.root_path, 'data')
    return send_from_directory(data_dir, 'sample_newsletter.json')

@app.route('/data/demo_social.json')
def demo_social():
    data_dir = os.path.join(app.root_path, 'data')
    return send_from_directory(data_dir, 'demo_social.json')

@app.route('/api/social/accounts')
def api_social_accounts():
    try:
        resp = requests.get(f'{SOCIALFETCH_URL}/accounts', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({'accounts': data.get('accounts', {}), 'demo': data.get('demo', False)})
    except Exception:
        pass

    items = demo_social_items()
    accounts = {}
    for item in items:
        plat = item.get('platform', '')
        if plat not in accounts:
            accounts[plat] = []
        acc = item.get('source', '').replace(f'{plat}: @', '')
        if acc and acc not in accounts[plat]:
            accounts[plat].append(acc)
    return jsonify({'accounts': accounts, 'demo': True})

@app.route('/api/social/connect', methods=['POST'])
def api_social_connect():
    body = request.get_json(silent=True) or {}
    platform = body.get('platform', '')
    username = body.get('username', '')
    password = body.get('password', '')

    if not platform or not username:
        return jsonify({'ok': False, 'error': 'platform and username required'}), 400

    local_result = None
    try:
        resp = requests.post(f'{SOCIALFETCH_URL}/connect', json=body, timeout=10)
        if resp.status_code == 200:
            local_result = resp.json()
    except Exception:
        pass

    conns = load_connections()
    key = f"{platform}:{username}"
    conns[key] = {
        'platform': platform,
        'username': username,
        'connected_at': datetime.now(timezone.utc).isoformat(),
        'display_name': username
    }
    save_connections(conns)

    if local_result:
        return jsonify(local_result)
    return jsonify({'ok': True, 'display_name': username, 'platform': platform, 'demo': True})


@app.route('/api/connections', methods=['GET'])
def api_connections():
    conns = load_connections()
    by_platform = {}
    for key, info in conns.items():
        plat = info.get('platform', '')
        name = info.get('display_name') or info.get('username', '')
        by_platform.setdefault(plat, []).append(name)
    return jsonify({'connections': by_platform})


@app.route('/api/connections', methods=['DELETE'])
def api_connections_delete():
    body = request.get_json(silent=True) or {}
    platform = body.get('platform', '')
    username = body.get('username', '')
    conns = load_connections()
    key = f"{platform}:{username}"
    if key in conns:
        del conns[key]
        save_connections(conns)
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'not found'}), 404


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)