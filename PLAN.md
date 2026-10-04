# PLAN

## Idee (1-2 Sätze)
Ein personalisierter KI-Newsletter, der n8n als KI-Provider nutzt, um öffentliche Quellen zu durchsuchen und mit OpenRouter zusammenzufassen, damit Nutzer keine Events verpassen.
 
## Wer ist die Zielgruppe / welches Problem lösen wir?
Zielgruppe: Event-Interessierte, die aktuelle Konzerte, Giveaways, News zu Themen wie Technologie, Kultur usw. verpassen wollen.
Problem: Überflutung von Informationen und fehlende personalisierte Filterung öffentlicher Quellen.
 
## MVP (das Kleinste, das beeindruckt)
Eine Flask-Webapp (PWA) mit Eingabefeld für Themen, Button 'Newsletter erzeugen', Anzeige von Karten mit generierten Newsletter-Artikeln. Bei fehlender n8n-Verbindung wird ein Beispiel-Newsletter aus data/sample_newsletter.json gezeigt. Der KI-Teil erfolgt über den n8n-Workflow (Mock im MVP) mit Modell aus MODEL_PRIMARY.
 
## Demo-Pfad (max. 3 Klicks, den zeigen wir live)
1. App öffnen (Startseite)
2. Themen eingeben (z.B. 'Konzerte Berlin')
3. Button 'Newsletter erzeugen' klicken und Karten anzeigen lassen
 
## Aufgaben (je <= 20 Min.)
- [ ] Flask-Projekt initialisieren (requirements.txt, app.py, Verzeichnisstruktur) – Ran
- [ ] Startseite-Template mit Formular und Button erstellen – Ran
- [ ] Mock-Webhook-Endpunkt /mock/newsletter implementieren – Ran
- [ ] Frontend-Logik: Button-Klick → AJAX-Aufruf → Kartenanzeige – Ran
- [ ] Fallback auf sample_newsletter.json bei Fehler implementieren – Ran
- [ ] Mobile-first CSS und dunkles klares Design anwenden – Ran
- [ ] PWA Manifest und Service Worker Grundgerüst setzen – Ran
- [ ] Offline Test: Anwesenheit von Formular und Button – Edgar
- [ ] Offline Test: Mock-Endpunkt liefert erwartetes JSON – Edgar
- [ ] Offline Test: Fallback lädt sample_newsletter.json – Edgar
- [ ] Test: Modellname wird aus MODEL_PRIMARY gelesen – Edgar
- [ ] Server-Konfiguration prüfen (127.0.0.1, debug aus) – Edgar
- [ ] Server startet mit timeout und antwortet auf Health-Check – Edgar
- [ ] Kleine Fehler beheben und commits nach jedem Schritt – Beide

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
