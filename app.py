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
        "title": "Dein personalisierter KI-Newsletter",
        "date": today,
        "intro": "Hier sind deine ausgewählten Themen aus öffentlichen Quellen, zusammengestellt von KI.",
        "items": [
            {
                "category": "Technologie",
                "title": "KI-Durchbruch in der Bildverarbeitung",
                "summary": "Neues Modell erreicht State-of-the-Art auf Benchmark.",
                "source": "TechBlog",
                "url": "https://example.com/ai-breakthrough",
                "when": today
            },
            {
                "category": "Kultur",
                "title": "Freiluftkonzert im Park heute Abend",
                "summary": "Kostenloses Konzert mit lokalen Bands ab 19 Uhr.",
                "source": "Eventkalender",
                "url": "https://example.com/concert-park",
                "when": today
            },
            {
                "category": "Giveaways",
                "title": "Gewinne ein Jahr lang kostenlosen Cloud-Speicher",
                "summary": "Teilnahme durch Eintragung des Newsletters bis Sonntag.",
                "source": "TechGiveaway",
                "url": "https://example.com/giveaway-cloud",
                "when": today
            }
        ]
    }
    return jsonify(mock_response)

@app.route('/data/sample_newsletter.json')
def sample_newsletter():
    data_dir = os.path.join(app.root_path, 'data')
    return send_from_directory(data_dir, 'sample_newsletter.json')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)