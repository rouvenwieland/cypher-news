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
    {"category": "Konzerte", "title": "Freiluftkonzert im Mauerpark heute Abend", "summary": "Kostenloses Konzert mit drei lokalen Indie-Bands ab 19 Uhr. Picknickdecke nicht vergessen – Eintritt frei.", "source": "Eventkalender Berlin", "url": "https://example.com/concert-mauerpark", "when": ""},
    {"category": "Konzerte", "title": "Techno-Nacht im Club OST", "summary": "Lokale DJs legen ab 23 Uhr auf. Eintritt frei bis Mitternacht, danach 10 €. Line-up: DJ Spacer, MIRA, KX6000.", "source": "Club OST Berlin", "url": "https://example.com/club-ost", "when": ""},
    {"category": "Giveaways", "title": "Gewinne ein Jahr lang kostenlosen Cloud-Speicher", "summary": "TechStartup verlost 50× 2TB Cloud-Speicher. Teilnahme per Newsletter-Anmeldung bis Sonntag 23:59 Uhr.", "source": "TechGiveaway", "url": "https://example.com/giveaway-cloud", "when": ""},
    {"category": "Giveaways", "title": "SNEAKRS Raffle: Travis Scott x Nike Air Max", "summary": "Die neue Kollaboration droppt heute um 10 Uhr exklusiv in der SNEAKRS-App. 3.000 Paare weltweit.", "source": "SNEAKRS App", "url": "https://example.com/sneakrs-travis", "when": ""},
    {"category": "Mode", "title": "ACRONYM® öffnet Popup-Store in Berlin-Mitte", "summary": "Limitierte Herbstkollektion nur dieses Wochenende in der Rosenthaler Straße. Early-Access ab 9 Uhr.", "source": "Highsnobiety", "url": "https://example.com/acronym-popup", "when": ""},
    {"category": "Mode", "title": "Vivienne Westwood Archive Sale Online", "summary": "Bis zu 70% auf ausgewählte Archiv-Stücke. Nur 48 Stunden online – Code ARCHIVE48 beim Checkout.", "source": "Vivienne Westwood", "url": "https://example.com/vw-archive-sale", "when": ""},
    {"category": "Tech", "title": "OpenAI leakt Verse 2: Open-Source-Bildmodell mit 8B Parametern", "summary": "Neues Modell erreicht State-of-the-Art auf 5 Benchmarks. Apache-2.0-Lizenz, läuft auf einzelner RTX 4090.", "source": "Hacker News", "url": "https://example.com/verse-2-oss", "when": ""},
    {"category": "Trends", "title": "5 Trends, die diese Woche jeder teilt", "summary": "Von KI-generierten Avataren bis Bio-3D-Druck: Das sind die Themen, die gerade viral gehen.", "source": "YouTube TrendCheck", "url": "https://example.com/weekly-trends", "when": ""}
]

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def mock_response():
    t = today_str()
    items = [{**i, "when": t} for i in MOCK_ITEMS]
    return {"title": "DEIN DROP", "date": t, "intro": f"{len(items)} Treffer aus 5 Quellen – kuratiert von KI für dich.", "items": items, "source": "mock"}

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