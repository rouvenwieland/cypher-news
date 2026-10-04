from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
from datetime import datetime

app = Flask(__name__)

MODEL_PRIMARY = os.environ.get('MODEL_PRIMARY', 'unknown')

@app.route('/')
def index():
    return render_template('index.html', model_name=MODEL_PRIMARY)

@app.route('/mock/newsletter', methods=['POST'])
def mock_newsletter():
    # Mock endpoint returning sample data matching n8n contract
    # Expected input: {preferences: str, sources: [str], date: 'YYYY-MM-DD'}
    # We ignore input for mock but could echo
    data = request.get_json(silent=True) or {}
    # Build mock response
    today = datetime.now().strftime('%Y-%m-%d')
    mock_response = {
        "title": "DEIN DROP",
        "date": today,
        "intro": "8 Treffer aus 5 Quellen — kuratiert von KI für dich.",
        "items": [
            {"category": "Konzerte", "title": "Freiluftkonzert im Park heute Abend", "summary": "Kostenloses Konzert mit lokalen Bands ab 19 Uhr im Mauerpark.", "source": "Eventkalender", "url": "https://example.com/concert-park", "when": today},
            {"category": "Konzerte", "title": "Techno-Nacht im Tresor", "summary": "Lokale DJs legen ab 23 Uhr auf. Eintritt frei bis Mitternacht.", "source": "Tresor Berlin", "url": "https://example.com/tresor-night", "when": today},
            {"category": "Giveaways", "title": "Gewinne ein Jahr lang kostenlosen Cloud-Speicher", "summary": "Teilnahme durch Newsletter-Eintragung bis Sonntag.", "source": "TechGiveaway", "url": "https://example.com/giveaway-cloud", "when": today},
            {"category": "Giveaways", "title": "SNEAKRS Raffle: Limited Edition Release", "summary": "Neue Kollaboration droppt heute um 10 Uhr. Anmeldung in der App.", "source": "SNEAKRS", "url": "https://example.com/sneakrs-raffle", "when": today},
            {"category": "Tech", "title": "KI-Durchbruch in der Bildverarbeitung", "summary": "Neues Open-Source-Modell erreicht State-of-the-Art auf mehreren Benchmarks.", "source": "TechBlog", "url": "https://example.com/ai-breakthrough", "when": today},
            {"category": "Tech", "title": "Raspberry Pi 6 geleakt: Neue Specs enthüllt", "summary": "Gerüchte über doppelte Rechenleistung und integrierte NPU.", "source": "Reddit r/programming", "url": "https://example.com/raspberry6-leak", "when": today},
            {"category": "Mode", "title": "Streetwear-Brand öffnet Popup-Store in Berlin", "summary": "Limitierte Kollektion nur dieses Wochenende in Mitte.", "source": "tiktok", "url": "https://example.com/popup-store", "when": today},
            {"category": "Trends", "title": "5 Trends, die diese Woche jeder teilt", "summary": "Von Open-Source-Apps bis nachhaltiger Mode: Was gerade viral geht.", "source": "YouTube TrendCheck", "url": "https://example.com/weekly-trends", "when": today}
        ]
    }
    return jsonify(mock_response)

@app.route('/data/sample_newsletter.json')
def sample_newsletter():
    data_dir = os.path.join(app.root_path, 'data')
    return send_from_directory(data_dir, 'sample_newsletter.json')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)