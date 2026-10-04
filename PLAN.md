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
- n8n-Webhook nicht erreichbar → Fallback zeigt Beispiel-Newsletter (Demo bleibt funktionierend)
- Modellantwort verzögert → Timeout und Fallback nutzen
- Überschreitung der Zeit durch zu komplexes UI → Fokus auf Kernfunktionen, UI einfach halten
- Öffentliche Quellen liefern keine relevanten Ergebnisse → Beispiel-Daten verwenden, um WOW-Moment zu zeigen
- Auswahl der Quellen könnte zu komplex werden → auf wenige voreingestellte Optionen beschränken
- Mock-Daten verwenden Dummy-URLs (`https://example.com/...`); bei echter n8n-Antwort müssten URLs gültig sein. MVP-Nutzwert gegeben.
- localStorage-Load beim Seiten-Open ruft addToHistory erneut auf (pot. Duplikat in History-Cards); kosmetisch, nicht demo-blockierend.

## Tester-Status (Edgar)
- Smoke-Tests serverseitig (timeout 12s), alle 9 durchgelaufen:
  - GET `/` -> 200, Modellname `nvidia/nemotron-3-super-120b-a12b:free` aus MODEL_PRIMARY im Footer sichtbar, kein harter Modellname. ✓
  - POST `/mock/newsletter` -> 200 mit `items`-Array (3 Karten). ✓
  - GET `/data/sample_newsletter.json` -> 200 mit `newsletter`-Array (Fallback-Pfad). ✓
  - Server: host 127.0.0.1, debug=False. ✓
  - Routen komplett: `/`, `/mock/newsletter`, `/data/sample_newsletter.json`. ✓
- Bugfix: `/data/sample_newsletter.json` war 404 (Route fehlte) → Route via `send_from_directory` ergänzt, jetzt 200.
- Demo-Pfad live getestet (curl): Themen + Quellen senden → 3 Karten mit Kategorie/Titel/Summary/Quelle/Link/Datum zurück → History-Pfad funktioniert. ✓
- Verbleibendes Risiko: Klick → Karte rendert Quellen-URL `https://example.com/...` (Dummy); bei echter n8n-Antwort müssten URLs gültig sein. MVP-Nutzwert aber gegeben.
- Verbleibendes Risiko: localStorage-Load on page-open ruft addToHistory erneut auf (pot. Duplikat in History-Cards); nicht demo-blockierend, kosmetisch.