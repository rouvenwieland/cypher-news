# PLAN

## Idee (1-2 Sätze)
Ein personalisierter KI-Newsletter, der n8n als KI-Provider nutzt, um öffentliche Quellen zu durchsuchen und mit OpenRouter zusammenzufassen, damit Nutzer keine Events verpassen.

## Wer ist die Zielgruppe / welches Problem lösen wir?
Zielgruppe: Event-Interessierte, die aktuelle Konzerte, Giveaways, News zu Themen wie Technologie, Kultur usw. verpassen wollen.
Problem: Überflutung von Informationen und fehlende personalisierte Filterung öffentlicher Quellen.

## MVP (das Kleinste, das beeindruckt)
Eine Flask-Webapp (PWA) mit:
- Eingabefeld für freie Themen
- Liste von auswählbaren Quellen/Accounts/Themen (z.B. YouTube-Kanäle, RSS-Feeds, Reddit)
- Button 'Newsletter jetzt erzeugen'
- Anzeige des heutigen Newsletters als Karten (Kategorie, Titel, Zusammenfassung, Quelle, Link, Datum)
- Verlaufsbereich mit früheren Newslettern (falls verfügbar)
Bei fehlender n8n-Verbindung wird ein Beispiel-Newsletter aus data/sample_newsletter.json gezeigt.
Der KI-Teil erfolgt über den n8n-Workflow (Mock im MVP) mit Modell aus MODEL_PRIMARY.

## Demo-Pfad (max. 3 Klicks, den zeigen wir live)
1. App öffnen (Startseite)
2. Themen eingeben und ggf. Quellen auswählen (z.B. 'Konzerte Berlin', YouTube-Kanal 'TechNews')
3. Button 'Newsletter jetzt erzeugen' klicken und Kartenanzeige sowie Verlauf sehen

## Aufgaben (je <= 20 Min.)
- [x] Flask-Projekt initialisieren (requirements.txt, app.py, Verzeichnisstruktur) – Ran
- [x] Startseite-Template mit Formular (freier Text + Mehrfachauswahl für Quellen) und Button erstellen – Ran
- [x] Mock-Webhook-Endpunkt /mock/newsletter implementieren, der den erwarteten Vertrag einhält – Ran
- [x] Frontend-Logik: Button-Klick → AJAX-Aufruf → Kartenanzeige + Verlauf aktualisieren – Ran
- [x] Fallback auf sample_newsletter.json bei Fehler implementieren – Ran
- [x] Mobile-first CSS und dunkles klares Design anwenden – Ran
- [x] PWA Manifest und Service Worker Grundgerüst setzen – Ran
- [x] Verlaufsspeicherung (z.B. in localStorage oder einfache Liste) implementieren – Ran
- [x] Offline Test: Anwesenheit von Formular und Button – Edgar
- [x] Offline Test: Mock-Endpunkt liefert erwartetes JSON – Edgar
- [x] Offline Test: Fallback lädt sample_newsletter.json – Edgar
- [x] Test: Modellname wird aus MODEL_PRIMARY gelesen (prüfen, dass kein harter Modellname vorkommt) – Edgar
- [x] Server-Konfiguration prüfen (127.0.0.1, debug aus) – Edgar
- [x] Server startet mit timeout und antwortet auf Health-Check – Edgar
- [x] Kleine Fehler beheben und commits nach jedem Schritt – Beide

## Zeitplan
- 12:00-12:20  Idee schärfen, Planner erzeugt diesen Plan
- 12:20-13:30  MVP bauen (Builder), Tester läuft parallel
- 13:30-14:00  Mittag - Agenten pausieren (spart Anfragen)
- 14:00-15:30  Features, Tester, Fehler
- 15:30        FEATURE-FREEZE
- 15:30-16:15  Bugs, README, Pitch, Backup-Demo
- 16:15-16:45  Pitch proben (2x), alles pushen

## Risiken
- **NICHT MEHR:** n8n-Webhook läuft live (13:53 getestet) und liefert echte, relevante Daten in <5s.
- n8n-Timeout 22s bei Ausfall → Fallback zeigt Beispiel-Newsletter (Demo bleibt funktionierend, aber 22s Wartezeit).
- Dummy-URLs (`https://example.com/...`) in Mock-/Fallback-Daten; bei echter n8n-Antwort kommen gültige URLs. MVP-Nutzwert gegeben.
- ~~localStorage-Duplikat~~ → entwarnt: `renderHistory()` auf load ruft kein `addToHistory()` auf.

## Tester-Status (Edgar)

### Komplett-Durchlauf 14:16 (Build 96d0633, ~5 Min.)
- GET `/` → HTTP 200, 47 KB. Modellname `nvidia/nemotron-3-super-120b-a12b` im Footer, kein harter Modellname. ✓
- POST `/mock/newsletter` → HTTP 200, **20 Items** (8 core + 12 social aus demo_social.json). ✓
- GET `/data/sample_newsletter.json` → HTTP 200, 8 newsletter entries. ✓
- GET `/data/demo_social.json` → HTTP 200, 12 social items. ✓
- GET `/api/social/accounts` → HTTP 200, 5 Plattformen (Instagram, Reddit, TikTok, YouTube), demo=true. ✓
- Statische Dateien alle HTTP 200: ✓
  - CSS, JS, Fonts (3), Icons (2), Bilder (4), PWA (manifest.json, sw.js)
- Server-Konfiguration: `host='127.0.0.1', debug=False, port=5000`. ✓
- Python-Syntax-Check: app.py (152 Zeilen) kompiliert ohne Fehler. ✓
- Kein harter Modellname in app.py (kein grep-Treffer). ✓

### Vorheriger Durchlauf 13:53
- GET `/` → HTTP 200, 39 KB. ✓
- POST `/api/generate` (mit n8n live!) → HTTP 200, 8 echte Items, source=n8n. ✓
- POST `/api/generate` (ohne n8n) → HTTP 200, source=fallback. ✓
- DESIGN.md-Check, alle Animationen 1:1. ✓

### Bugs gefunden & behoben
- Keine neuen Bugs. App läuft sauber mit Social-Integration.

### Verbleibende Risiken
- **n8n nicht live**: N8N_WEBHOOK_URL aktuell nicht gesetzt → /api/generate hängt 22s im Timeout, dann Fallback. Für Demo vorher n8n starten oder N8N_WEBHOOK_URL setzen.
- Dummy-URLs `https://example.com/...` in Mock-/Fallback-Daten. Bei echter n8n-Antwort kommen gültige URLs. Nicht demo-blockierend.
- demo_social.json enthält 12 Beispieldaten — ausreichend für Demo, aber keine echten Live-Daten von Social-APIs (socialfetch baut Ran gerade).
- **WOW-Moment live getestet** (13:53): n8n-Antwort <5s mit echten Konzerte-in-Berlin-Daten. Muss vor Demo verifiziert werden.