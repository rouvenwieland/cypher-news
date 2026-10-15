# Kostenlos veröffentlichen (Render, ohne Kreditkarte)

Hugging Face verlangt für Docker-Spaces inzwischen ein PRO-Abo (9 $/Monat), deshalb läuft die App auf Render (Free-Tarif, geprüft 6.10.2026: 750 Std./Monat, 512 MB, schläft nach 15 Min. ohne Besucher, Aufwachen ca. 1 Min.).

1. render.com → mit GitHub anmelden (kostenlos, keine Karte).
2. **New → Blueprint** → Repo `rouvenwieland/cypher-news` wählen. Render liest `render.yaml` und legt den Dienst `cypher-news` an. Modelle und `SECRET_KEY` (zufällig, von Render erzeugt) sind schon gesetzt.
3. Render fragt nach zwei Werten:
   - `HF_TOKEN`: ein Hugging-Face-Token mit Schreibrecht auf das Dataset `rouvenwieland/cypher-news-data`. Die App sichert damit die Datenbank (Render löscht Dateien bei jedem Neustart). Ohne ihn gehen Nutzerdaten verloren.
   - `IMPRINT_TEXT`: dein Impressumstext (Name, Kontakt).
4. Nach dem Bauen (ca. 5 Min.) steht die App unter `https://cypher-news.onrender.com` (ist der Name vergeben, zeigt Render die echte Adresse; dann `APP_URL` in `.github/workflows/daily-drop.yml` anpassen).
5. Der GitHub-Workflow `keep-awake` hält die App **nur von 05:50 bis 23:50 Uhr Berlin-Zeit** wach, damit der eingebaute Scheduler jeden Drop zur gewählten Uhrzeit baut. Nachts schläft der Dienst (15 Min. nach dem letzten Aufruf) und verbraucht keine Render-Stunden. Ablauf: alle 2 Stunden (Minute 23) startet ein Lauf, jeder Lauf führt `.github/keepawake.py` aus und ruft `/healthz` alle 10 Minuten für 5 Std. 40 Min. auf (GitHub begrenzt einen Job auf 6 Std.), aber nur, solange die Berlin-Uhr im Fenster steht; außerhalb wartet der Lauf bis 05:50. Das Fenster folgt der Berlin-Uhr (Zeitzonendatenbank des Runners), Sommer- und Winterzeit brauchen keine Anpassung des Workflows (er selbst läuft in UTC). Die Concurrency-Gruppe lässt immer nur einen Lauf arbeiten und reiht den nächsten ein, so entsteht eine lückenlose Kette, auch wenn GitHub einmal einen geplanten Start auslässt. Abgebrochene ("cancelled") Läufe in der Liste sind normal: ein neuer wartender Lauf ersetzt den älteren wartenden. GitHub schaltet geplante Workflows in öffentlichen Repos nach 60 Tagen ohne Commit ab (vorher kommt eine E-Mail); dann im Actions-Tab wieder einschalten. Das Repo ist öffentlich, die Actions-Minuten sind kostenlos. Tests (`tests/test_keepawake.py`) simulieren mehrere Tage inkl. beider Zeitumstellungen und prüfen: Aufrufe nur im Fenster, nie dichter als alle 10 Min., keine Lücke im Fenster, Render-Stunden pro Tag.
6. **Drop-Uhrzeiten:** Die App bietet nur 06:00 bis 23:00 Uhr (Berlin-Zeit) an. Der erste Drop (06:00) hat 10 Minuten Vorlauf zum Aufwachen (Backup laden), nach dem letzten (23:00) bleibt fast eine Stunde zum Bauen und für Wiederholungen. Wer die App in einer anderen Zeitzone nutzt, sieht die entsprechenden Ortszeiten (die Auswahl rechnet mit der Zeitzonendatenbank des Browsers). Ältere Einstellungen von 00:00 bis 05:00 bleiben gespeichert und werden beim Aufwachen nachgeholt (Anzeige: 06:00). Wer 14 Tage die App nicht geöffnet hat, bekommt keine Drops mehr, bis er sie wieder öffnet ("Willkommen zurück – Drops laufen wieder").

## Render-Gratisstunden (Rechnung)

Render gibt **750 Instanzstunden pro Monat für das ganze Konto**. Dort läuft auch `kartenrunde`; beide Dienste teilen sich die Stunden. Nur Zeit, in der ein Dienst läuft, zählt (schlafende Dienste nicht).

| Variante | Stunden pro Tag | Stunden pro 31-Tage-Monat | Rest für `kartenrunde` |
|---|---|---|---|
| bisher: ganztägig wach | 24 | ca. 730 bis 744 | 6 bis 20 (reicht nicht) |
| jetzt: 05:50 bis 23:50 Berlin | 18 Std. Fenster + 15 Min. Auslauf, höchstens 18,5 | höchstens 31 × 18,5 = **574** | mindestens **176** (ca. 5,7 Std./Tag) |

Die Simulation im Test misst 17,5 bis 18,5 Std. pro Tag, auch an den Tagen der Zeitumstellung. Nutzer, die nachts die App öffnen, wecken den Dienst zusätzlich (ca. 1 Min. Start, dann 15 Min. wach); das geht vom Rest ab. Wer mehr Luft braucht: Fenster verkürzen (`WINDOW_START`/`WINDOW_END` in `.github/keepawake.py`, und `DROP_FROM_MIN`/`DROP_TO_MIN` in `static/js/app.js` passend; der Test `test_window_allows_every_selectable_drop_hour_with_a_build_reserve` prüft, dass beides zusammenpasst).

Übergangslösung: Cypher News soll langfristig auf Cloudflare umziehen. Dort entfällt die Stundengrenze, das Fenster und die Einschränkung der Drop-Uhrzeiten können dann entfernt werden.

Optional: Secret `OPENROUTER_API_KEY` für 1 Gratis-Drop pro Nutzer und Tag (`FREE_DROPS_PER_DAY`).
Modelle ändern: Werte in `render.yaml` bzw. im Render-Dashboard unter Environment. Free-Modelle verschwinden gelegentlich: auf openrouter.ai/models prüfen.

Grenzen: Free-Modelle bei OpenRouter haben Tageslimits (ca. 50 Anfragen ohne Guthaben, ca. 1000 mit 10 $ Guthaben), deshalb trägt jeder Nutzer seinen eigenen kostenlosen Schlüssel ein. Instagram und TikTok werden öffentlich und inoffiziell gelesen und können jederzeit blockiert werden. Native Apps (Google Play 25 $ einmalig, App Store 99 $/Jahr) erst, wenn die PWA genutzt wird.
