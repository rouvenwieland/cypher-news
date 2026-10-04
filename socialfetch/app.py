from flask import Flask, request, jsonify
import json
import os
import base64
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
IMG_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'img')

DEMO_FILE = os.path.join(DATA_DIR, 'demo_social.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'connections.json')

os.makedirs(os.path.join(DATA_DIR, 'sessions'), exist_ok=True)


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


def thumbnail_b64():
    paths = [os.path.join(IMG_DIR, f) for f in ['field_pix.jpg', 'money_pix.jpg', 'field_duo.jpg', 'money_duo.jpg']]
    for p in paths:
        if os.path.exists(p):
            try:
                import subprocess
                result = subprocess.run(
                    ['convert', p, '-resize', '80x80^', '-gravity', 'center', '-extent', '80x80',
                     '-quality', '60', 'jpeg:-'],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0 and len(result.stdout) < 81920:
                    return base64.b64encode(result.stdout).decode('ascii')
            except Exception:
                pass
    return None


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
        thumb = thumbnail_b64()
        entry = dict(item)
        if thumb:
            entry['image_b64'] = thumb
        items.append(entry)
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
        all_accounts = demo_accounts()
        return jsonify({'accounts': all_accounts.get(platform, []), 'demo': True})
    return jsonify({'accounts': demo_accounts(), 'demo': True})


@app.route('/feed', methods=['GET'])
def feed():
    platform = request.args.get('platform', '')
    accounts = request.args.get('accounts', '')
    hours = int(request.args.get('hours', '48'))
    items = demo_feed(platform=platform or None, accounts=accounts, hours=hours)
    return jsonify({'items': items, 'count': len(items), 'demo': True, '_note': 'DEMO DATA – sample posts only'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'ok': True, 'demo': True})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5090, debug=False)