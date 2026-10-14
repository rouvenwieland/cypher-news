# Kostenlos veröffentlichen (Render, ohne Kreditkarte)

Hugging Face verlangt für Docker-Spaces inzwischen ein PRO-Abo (9 $/Monat), deshalb läuft die App auf Render (Free-Tarif, geprüft 6.10.2026: 750 Std./Monat, 512 MB, schläft nach 15 Min. ohne Besucher, Aufwachen ca. 1 Min.).

1. render.com → mit GitHub anmelden (kostenlos, keine Karte).
2. **New → Blueprint** → Repo `rouvenwieland/cypher-news` wählen. Render liest `render.yaml` und legt den Dienst `cypher-news` an. Modelle und `SECRET_KEY` (zufällig, von Render erzeugt) sind schon gesetzt.
3. Render fragt nach zwei Werten:
   - `HF_TOKEN`: ein Hugging-Face-Token mit Schreibrecht auf das Dataset `rouvenwieland/cypher-news-data`. Die App sichert damit die Datenbank (Render löscht Dateien bei jedem Neustart). Ohne ihn gehen Nutzerdaten verloren.
   - `IMPRINT_TEXT`: dein Impressumstext (Name, Kontakt).
4. Nach dem Bauen (ca. 5 Min.) steht die App unter `https://cypher-news.onrender.com` (ist der Name vergeben, zeigt Render die echte Adresse; dann `APP_URL` in `.github/workflows/daily-drop.yml` anpassen).
5. Der GitHub-Workflow `keep-awake` hält die App ganztägig wach, damit der eingebaute Scheduler jeden Drop zur gewählten Uhrzeit baut (auch am Nachmittag und Abend). Ablauf: alle 2 Stunden (Minute 23) startet ein Lauf, jeder Lauf ruft `/healthz` alle 10 Minuten für 5 Std. 40 Min. auf (GitHub begrenzt einen Job auf 6 Std.). Die Concurrency-Gruppe lässt immer nur einen Lauf arbeiten und reiht den nächsten ein, so entsteht eine lückenlose Kette, auch wenn GitHub einmal einen geplanten Start auslässt. Abgebrochene ("cancelled") Läufe in der Liste sind normal: ein neuer wartender Lauf ersetzt den älteren wartenden. GitHub schaltet geplante Workflows in öffentlichen Repos nach 60 Tagen ohne Commit ab (vorher kommt eine E-Mail); dann im Actions-Tab wieder einschalten. Das Repo ist öffentlich, die Actions-Minuten sind kostenlos. Ein Test (`tests/test_keepawake.py`) prüft Takt (mindestens 10 Min.), Laufzeit (unter 6 Std.) und Abdeckung. Achtung: Ein rund um die Uhr wacher Dienst verbraucht ca. 730 von 750 freien Render-Stunden pro Monat; hast du weitere kostenlose Render-Dienste im selben Konto, teilen sie sich diese Stunden. Verpasste Drops werden beim Aufwachen weiterhin nachgeholt.

Optional: Secret `OPENROUTER_API_KEY` für 1 Gratis-Drop pro Nutzer und Tag (`FREE_DROPS_PER_DAY`).
Modelle ändern: Werte in `render.yaml` bzw. im Render-Dashboard unter Environment. Free-Modelle verschwinden gelegentlich: auf openrouter.ai/models prüfen.

Grenzen: Free-Modelle bei OpenRouter haben Tageslimits (ca. 50 Anfragen ohne Guthaben, ca. 1000 mit 10 $ Guthaben), deshalb trägt jeder Nutzer seinen eigenen kostenlosen Schlüssel ein. Instagram und TikTok werden öffentlich und inoffiziell gelesen und können jederzeit blockiert werden. Native Apps (Google Play 25 $ einmalig, App Store 99 $/Jahr) erst, wenn die PWA genutzt wird.
