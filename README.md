# newsletter

Hackathon-Projekt (Hacktoberfest Hack Day Berlin 2026).

## Was ist das?
Ein personalisierter KI-Newsletter, der n8n als KI-Provider nutzt, um öffentliche Quellen zu durchsuchen und mit OpenRouter zusammenzufassen, damit Nutzer keine Events verpassen.

## Starten
1. Abhängigkeiten installieren: `pip install -r requirements.txt`
2. Umgebung setzen: `export MODEL_PRIMARY=nvidia/nemotron-3-super-120b-a12b:free` (bereits gesetzt)
3. App starten: `python app.py`
4. Im Browser öffnen: http://127.0.0.1:5000

## Verwendete offene Modelle
| Modell | Lizenz | Wo läuft es |
|---|---|---|
| nvidia/nemotron-3-super-120b-a12b:free | OpenRouter Free-Lizenz | OpenRouter API |
