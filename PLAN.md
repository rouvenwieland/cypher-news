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

### Komplett-Durchlauf 13:53 (8 Min.)
- GET `/` → HTTP 200, 39 KB. Modellname `nvidia/nemotron-3-super-120b-a12b:free` im Footer, kein harter Modellname. ✓
- POST `/api/generate` (mit n8n live!) → HTTP 200, 8 echte Items (Konzerte Berlin), source=n8n. N8N läuft tatsächlich! ✓
- POST `/api/generate` (ohne n8n, via N8N_WEBHOOK_URL=http://127.0.0.1:9999) → HTTP 200, 8 Items, source=fallback. ✓
- POST `/mock/newsletter` → HTTP 200, 8 Items. ✓
- GET `/data/sample_newsletter.json` → HTTP 200, 2.7 KB. ✓
- Statische Dateien alle HTTP 200: ✓
  - CSS: `/static/css/style.css` (524 Zeilen)
  - JS: `/static/js/rain.js` (34 Zeilen, IIFE)
  - Fonts: PressStart2P.ttf, VT323.ttf, SpaceGrotesk.ttf
  - Icons: icon-192.png, icon-512.png
  - Bilder: field_pix.jpg, field_duo.jpg, money_pix.jpg, money_duo.jpg
  - PWA: manifest.json, sw.js
- Server-Konfiguration: `host='127.0.0.1', debug=False, port=5000`. ✓
- DESIGN.md-Check: Alle CSS-Variablen, Schriften, Animationen (Matrix-Regen, Glitch, Ticker, Terminal, Stories, Feed, Konfetti) 1:1 umgesetzt. ✓
- Python-Syntax-Check: app.py kompiliert ohne Fehler. ✓

### Bugs gefunden & behoben
- Keine neuen Bugs. Vorheriger Bugfix (Route `/data/sample_newsletter.json`) hält.

### Verbleibende Risiken
- **n8n-Timeout 22s**: Wenn n8n nicht läuft, wartet `/api/generate` 22s bevor Fallback greift. In der Live-Demo (n8n läuft) aber kein Problem.
- Dummy-URLs `https://example.com/...` in Mock-/Fallback-Daten. Bei echter n8n-Antwort kommen gültige URLs. Nicht demo-blockierend.
- localStorage-Duplikat-Risiko von vorher entwarnt: `renderHistory()` auf load ruft KEIN `addToHistory()` auf, kein Duplikat. Risiko war Fehleinschätzung.
- **WOW-Moment bestätigt**: Live-n8n-Antwort kam in <5s mit echten Konzerte-in-Berlin-Daten. Demo-Pfad funktioniert komplett.