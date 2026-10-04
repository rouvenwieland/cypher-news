from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

MODEL_PRIMARY = os.environ.get('MODEL_PRIMARY', 'unknown')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mock/newsletter', methods=['POST'])
def mock_newsletter():
    # Mock endpoint returning sample data
    sample_data = {
        "newsletter": [
            {
                "category": "Technologie",
                "title": "KI-Durchbruch in der Bildverarbeitung",
                "summary": "Neues Modell erreicht State-of-the-Art auf Benchmark.",
                "source": "TechBlog",
                "link": "https://example.com/ai-breakthrough",
                "date": "2026-10-04"
            }
        ]
    }
    return jsonify(sample_data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)