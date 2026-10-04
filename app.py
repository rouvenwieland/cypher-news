from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import time
from datetime import datetime

import requests

app = Flask(__name__)

MODEL_PRIMARY = os.environ.get('MODEL_PRIMARY', 'unknown')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', 'http://127.0.0.1:5678/webhook/newsletter')

MOCK_ITEMS = [
    {"category": "Konzerte", "title": "Freiluftkonzert im Park heute Abend", "summary": "Kostenloses Konzert mit lokalen Bands ab 19 Uhr im Mauerpark.", "source": "Eventkalender", "url": "https://example.com/concert-park", "when": ""},
    {"category": "Konzerte", "title": "Techno-Nacht im Tresor", "summary": "Lokale DJs legen ab 23 Uhr auf. Eintritt frei bis Mitternacht.", "source": "Tresor Berlin", "url": "https://example.com/tresor-night", "when": ""},
    {"category": "Giveaways", "title": "Gewinne ein Jahr lang kostenlosen Cloud-Speicher", "summary": "Teilnahme durch Newsletter-Eintragung bis Sonntag.", "source": "TechGiveaway", "url": "https://example.com/giveaway-cloud", "when": ""},
    {"category": "Giveaways", "title": "SNEAKRS Raffle: Limited Edition Release", "summary": "Neue Kollaboration droppt heute um 10 Uhr. Anmeldung in der App.", "source": "SNEAKRS", "url": "https://example.com/sneakrs-raffle", "when": ""},
    {"category": "Tech", "title": "KI-Durchbruch in der Bildverarbeitung", "summary": "Neues Open-Source-Modell erreicht State-of-the-Art auf mehreren Benchmarks.", "source": "TechBlog", "url": "https://example.com/ai-breakthrough", "when": ""},
    {"category": "Tech", "title": "Raspberry Pi 6 geleakt: Neue Specs enthüllt", "summary": "Gerüchte über doppelte Rechenleistung und integrierte NPU.", "source": "Reddit r/programming", "url": "https://example.com/raspberry6-leak", "when": ""},
    {"category": "Mode", "title": "Streetwear-Brand öffnet Popup-Store in Berlin", "summary": "Limitierte Kollektion nur dieses Wochenende in Mitte.", "source": "tiktok", "url": "https://example.com/popup-store", "when": ""},
    {"category": "Trends", "title": "5 Trends, die diese Woche jeder teilt", "summary": "Von Open-Source-Apps bis nachhaltiger Mode: Was gerade viral geht.", "source": "YouTube TrendCheck", "url": "https://example.com/weekly-trends", "when": ""}
]

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def mock_response():
    t = today_str()
    items = [{**i, "when": t} for i in MOCK_ITEMS]
    return {"title": "DEIN DROP", "date": t, "intro": "8 Treffer aus 5 Quellen — kuratiert von KI für dich.", "items": items, "source": "mock"}

def fallback_from_file():
    data_path = os.path.join(app.root_path, 'data', 'sample_newsletter.json')
    with open(data_path, 'r') as f:
        d = json.load(f)
    items = [{"category": i["category"], "title": i["title"], "summary": i["summary"],
              "source": i["source"], "url": i["link"], "when": i["date"]} for i in d.get("newsletter", [])]
    return {"title": "DEIN DROP (Offline)", "date": today_str(),
            "intro": "Fallback: Beispiel-Drop aus lokalen Daten.", "items": items, "source": "fallback"}

@app.route('/')
def index():
    return render_template('index.html', model_name=MODEL_PRIMARY)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    body = request.get_json(silent=True) or {}
    preferences = body.get('preferences', '')
    sources = body.get('sources', [])
    date = body.get('date', today_str())

    payload = {"preferences": preferences, "sources": sources, "date": date}

    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=22)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('items', [])
            for item in items:
                if 'url' not in item:
                    item['url'] = ''
                if 'when' not in item:
                    item['when'] = ''
            return jsonify({"title": data.get('title', 'DEIN DROP'), "date": data.get('date', today_str()),
                           "intro": data.get('intro', ''), "items": items, "source": "n8n"})
    except Exception:
        pass

    return jsonify(mock_response())

@app.route('/mock/newsletter', methods=['POST'])
def mock_newsletter():
    return jsonify(mock_response())

@app.route('/data/sample_newsletter.json')
def sample_newsletter():
    data_dir = os.path.join(app.root_path, 'data')
    return send_from_directory(data_dir, 'sample_newsletter.json')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)