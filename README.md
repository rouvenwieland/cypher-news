# Cypher News — Daily Drop

Ein personalisierter KI-Newsletter im Retro-Pixel-Look. Nutzer geben Themen ein, wählen Quellen und bekommen einen täglichen "Drop" mit Events, Giveaways und Trends — kuratiert von offener KI. Gebaut für den Hacktoberfest Hack Day Berlin 2026.

## Starten

1. Abhängigkeiten installieren: `pip install -r requirements.txt`
2. App starten: `python app.py`
3. Im Browser öffnen: http://127.0.0.1:5000

## Verwendetes offenes Modell

| Modell | Lizenz | Anbieter |
|---|---|---|
| `{{ model_name }}` | OpenRouter Free | OpenRouter API |

Das Modell wird aus der Umgebungsvariable `$MODEL_PRIMARY` gelesen — kein Modellname ist im Code hardgecodet.

## Demo-Pfad (3 Klicks)

1. App öffnen → Matrix-Rain-Hintergrund, Ticker, "Cypher News" Logo
2. Themen eintippen und Quellen-Chips antippen
3. "DROP ERZEUGEN" klicken → Terminal-Animation → Story-Karten mit Events

## Architektur (5 Sätze)

- **Frontend**: Vanilla HTML/CSS/JS mit Matrix-Rain-Canvas, CSS-Animationen und localStorage.
- **Backend**: Python Flask mit zwei Routen: `GET /` (Template-Rendering) und `POST /mock/newsletter` (Mock-Webhook).
- **Mock-Endpunkt**: Simuliert den erwarteten n8n-Webhook-Vertrag und liefert 8 Items mit Kategorie, Titel, Summary, Quelle, URL und Datum.
- **Fallback**: Bei Fehlern lädt der Client `data/sample_newsletter.json` — 8 offline verfügbare Beispiel-Einträge.
- **KI-Modell**: Modellname aus `$MODEL_PRIMARY` wird im Footer und in der Terminal-Animation angezeigt.

## Open-Source-KI-Nutzung

- Modellname aus `$MODEL_PRIMARY` (nie hardgecodet)
- n8n als KI-Provider gemäß Hackathon-Thema
- Alle Datenquellen öffentlich (RSS, YouTube, Reddit, TikTok, Instagram)
- Keine personenbezogenen Daten in Prompts