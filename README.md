# KI-Newsletter

## Was ist das?
Ein personalisierter KI-Newsletter, der öffentliche Quellen durchsucht und sie mit KI zusammenträgt, damit Nutzer keine Events verpassen. Built specifically for the Hacktoberfest Hack Day Berlin 2026 with the theme "Building with open-source AI".

## Starten
1. Abhängigkeiten installieren: `pip install -r requirements.txt`
2. Modellumgebung setzen (bereits gesetzt in $MODEL_PRIMARY): `export MODEL_PRIMARY=nvidia/nemotron-3-super-120b-a12b:free`
3. App starten: `python app.py`
4. Im Browser öffnen: http://127.0.0.1:5000

## Verwendete offene Modelle
| Modell | Lizenz | Wo läuft es |
|---|---|---|
| {{ model_name }} | OpenRouter Free-Lizenz | OpenRouter API |

## Demo-Pfad (live)
1. App öffnen und lesen
2. Themen eingeben (z.B. "Konzerte Berlin")
3. Quellen auswählen und auf "Newsletter jetzt erzeugen" klicken
4. Karten mit Titeln, Zusammenfassungen, Links und Datum anzeigen
5. Verlauf in der History-Sektion sehen

## Open-Source-KI-Nutzung
- Modellname wird automatisch aus $MODEL_PRIMARY gelesen
- Keine Modellnamen im Code hardgecodet
- Das Modell läuft vollständig in der Cloud via OpenRouter API
- Explizite Integration von n8n als KI-Provider gemäß Hackathon-Thema
- Alle Datenquellen sind öffentlich (RSS, YouTube-Kanäle, Reddit) ohne Authentifizierung
