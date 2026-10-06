# PRODUCT-HANDOVER: Von der Hackathon-Demo zur echten App (Cypher News · Daily Drop)

Stand: 6.10.2026. Dieses Dokument ist die Übergabe an eine neue Claude-Code-Sitzung. Lies es komplett, dann `README.md`, `SOCIAL-SPEC.md`, `n8n/build_workflow.py`, `app.py`, `socialfetch/app.py`.
Antworte Rouven auf **Deutsch**, kurz und konkret (kein Profi-Entwickler, Mathe-Student in Berlin). Code, Kommentare und Commits dürfen Englisch sein.

## 1. Ziel
Aus dem Hackathon-Prototyp (gewonnen: "Best Use of n8n") soll eine **echte, öffentlich nutzbare App** werden, **möglichst kostenlos im Betrieb**, die **jeder** benutzen kann.
Idee: Ein **personalisierter KI-Newsletter ("Daily Drop")**. Nutzer geben in einem großen Notizfeld an, was sie interessiert (Konzerte in Berlin, Giveaways, Kleidungs-Drops, Tech-News, Trends ...), wählen Quellen/Accounts, und bekommen jeden Tag einen Drop, der Posts, Videos, Stories und News zusammenfasst, inklusive Bildinhalt, damit sie nicht scrollen müssen und kein Event/Giveaway verpassen (weniger Bildschirmzeit, keine FOMO). Zustellung als installierbare Handy-Web-App (PWA) mit Push, optional Telegram/E-Mail.

## 2. Was bereits existiert (funktioniert, getestet)
- **Web-App** (Flask, `app.py`, Port 5000), mobile-first PWA im "Cypher-Vibe" (warmes Schwarz, Orange/Rot/Gelb, Neongrün, Matrix-Regen, Pixel-Schrift). Seiten: Onboarding (Notizfeld, Chips, Quellen), Verbinden, Ladeanimation, Ergebnis als Stories/Feed, Gemerkt, Verlauf. Design-Vorgaben: `DESIGN.md`. Offline-Fallback `data/sample_newsletter.json`.
- **n8n-Workflow** `n8n/workflow.json` (erzeugt aus `n8n/build_workflow.py`): Webhook → Plan → RSS Read → Collect → Vision → Writer Prompt → Writer → Router → Parse → Respond. Er sammelt Google-News/Bing-News/Reddit-RSS-Meldungen plus die von der App mitgeschickten Social-Items, lässt ein Vision-Modell bis zu 6 Bilder auswerten (Qwen 3.8 27B, Ausweichkette Gemma 4 / Nemotron Omni), schreibt den Newsletter (schnell: Nemotron 3 Super ~6 s, genau: Nemotron 3 Ultra ~20 s, Ausweichkette über DeepSeek V4) und liefert JSON. Vertrag siehe `SOCIAL-SPEC.md`.
- **socialfetch** (`socialfetch/app.py`, Port 5090): liest **öffentlich ohne Login** Reddit (RSS), YouTube (Kanal-Feeds) und TikTok (yt-dlp, öffentliche Profile) inkl. Thumbnails; Instagram per instaloader mit Login (siehe Schwächen). Beispieldaten-Fallback `data/demo_social.json`.
- **Pitch-Präsentation** `pitch/` (11 Folien, Englisch, gesprochen mit lokalem Piper-TTS, Pixelfiguren). Nicht Teil des Produkts.
- Tests im Browser: Das Werkzeug `browsertest.js` liegt nur im privaten Setup des Entwicklungsrechners; nutze stattdessen Playwright.

**Starten (lokal):** Node ≥ 24, Python 3.12+. `npm i n8n` (in einem eigenen Ordner), n8n starten mit `N8N_BLOCK_ENV_ACCESS_IN_NODE=false N8N_LISTEN_ADDRESS=127.0.0.1 n8n start`, Workflow importieren (`n8n import:workflow --input=n8n/workflow.json`, dann `n8n publish:workflow --id=cypherNewsDrop001`, n8n neu starten). Umgebungsvariablen: `OPENROUTER_API_KEY`, `MODEL_PRIMARY` (z. B. `nvidia/nemotron-3-super-120b-a12b:free`), optional `MODEL_PAID` (z. B. `deepseek/deepseek-v4-pro`), `N8N_WEBHOOK_URL` (Standard `http://127.0.0.1:5678/webhook/newsletter`). Dann `python3 socialfetch/app.py` und `python3 app.py`. (`start.sh` setzt den Entwicklungsrechner voraus; für andere Umgebungen anpassen.)
**Wichtig bei n8n-Code-Knoten:** `this.helpers.httpRequest` und `$env` funktionieren nur mit `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`. Gratismodelle bei OpenRouter denken oft lange: `reasoning: { enabled: false }` setzen, sonst bleibt `content` leer.

## 3. Bekannte Schwächen / Lehren
1. **Instagram/TikTok-Scraping mit Login ist für ein öffentliches Produkt keine Lösung:** verstößt gegen die Nutzungsbedingungen, Instagram verlangt Sicherheits-Checkpoints (`Checkpoint required`), Konten werden gesperrt, und fremde Passwörter zu speichern ist ein Datenschutz- und Sicherheitsrisiko. **Passwort-basierte Connectors für Fremdnutzer NICHT bauen.** Zugangsdaten gehören nie ins Repo.
2. Das Backend ist ein **Ein-Nutzer-Prototyp** (`data/connections.json`, kein Login, kein Mehrnutzer-Betrieb, kein Scheduler, kein echter Push-Server).
3. Gratismodelle haben Limits (OpenRouter: ohne Guthaben ~50 Anfragen/Tag, mit mindestens 10 $ Guthaben ~1000/Tag, ca. 20/Minute) und sind unzuverlässig. Für viele Nutzer braucht es Caching, Batch-Betrieb und Fairness-Limits.
4. Der Newsletter-Text wird bei dünnen Daten holprig; Kategorien/Ranking sind einfach; keine Deduplizierung über Tage.
5. Alle Quellen sind "Pull" über Suchanfragen/Feeds; es gibt keine echten Event-Daten (Datum/Ort/Ticketlink).

## 4. Empfohlener Weg zum echten Produkt (bitte mit Rouven abstimmen)
**Leitprinzip: legal, kostenlos, skalierbar.** Statt fremde Konten zu scrapen:
- **Offizielle/offene Quellen:** RSS/Atom, YouTube-Kanal-Feeds (kein Key) und YouTube Data API (OAuth, Gratis-Kontingent), Reddit (OAuth/RSS), Mastodon/Bluesky (offene APIs), Event-APIs mit Gratis-Key (Ticketmaster Discovery, Bandsintown, Eventbrite, ggf. Songkick), Google News RSS, Wetter/Orts-Filter.
- **"Teilen statt Scrapen" für Instagram/TikTok/Stories (Herzstück):** Die PWA bekommt ein **Web-Share-Target** (`share_target` im Manifest) und eine Telegram-Bot-/E-Mail-Weiterleitung: Nutzer teilen einen Post, Story-Screenshot oder Link in die App; das Vision-Modell liest Datum/Ort/Aktion aus und legt es in den nächsten Drop. Das ist legal, funktioniert für jede Plattform und braucht keine fremden Passwörter. Optional: Browser-Erweiterung, die nur auf Klick des Nutzers die gerade offene Seite schickt.
- **Mehrnutzer-Backend:** Konten (Magic-Link/OAuth, z. B. Supabase Auth, Gratis-Tarif), Postgres/SQLite (Supabase oder Turso), pro Nutzer Profil (Notizen, Quellen, Uhrzeit, Zeitzone, Sprache), Verlauf, Gemerkt. Datenschutz: nur nötige Daten, Löschfunktion, Datenschutzerklärung (DSGVO), Mindestalter beachten.
- **Täglicher Betrieb:** n8n **Schedule-Trigger** (z. B. 06:00 je Zeitzone) erzeugt Drops im Batch statt bei jeder Anfrage; **Caching/Gemeinsame Themen:** gleiche Themen/Orte (z. B. "Konzerte Berlin") werden einmal gesammelt und für alle Nutzer wiederverwendet, nur das Ranking/Schreiben ist personalisiert. So bleiben die KI-Kosten klein.
- **Zustellung:** Web-Push (VAPID, Service Worker; iOS nur für installierte PWA), Telegram-Bot, E-Mail (Resend/Brevo Gratis-Tarif), RSS-Feed pro Nutzer.
- **KI-Kosten:** Gratismodelle über OpenRouter mit Ausweichkette und Rate-Limit pro Nutzer; Option "Bring your own key" (Nutzer trägt eigenen OpenRouter-Schlüssel ein) für Power-User; später ggf. kleines Abo. Alternativ eigene offene Modelle (Ollama/llama.cpp) auf einer Gratis-VM, nur wenn die Last es erlaubt.
- **Gratis-Hosting (prüfen, Konditionen ändern sich!):** Oracle Cloud "Always Free" (ARM-VM, gut für n8n + App), Hugging Face Spaces (Docker, passt zu "open source AI"), Render/Fly.io/Cloudflare je nach aktuellen Gratis-Limits. n8n: selbst hosten (open source) oder n8n Cloud (Rouvens Team hat als Preis ein Jahr n8n Cloud Pro gewonnen; Ausführungslimits prüfen, bevor man darauf aufbaut). Domain optional kostenlos (Subdomain).
- **Qualität:** echte Ranking-Logik (Relevanz zu den Notizen, Frische, Quellenvielfalt), Deduplizierung, Datums-/Ortserkennung für Events, "Verpasst nichts"-Erinnerungen (z. B. Deadline eines Giveaways), Feedback-Knöpfe (👍/👎) zur Personalisierung, Tests (pytest + Playwright), CI (GitHub Actions).

## 5. Vorgeschlagene Phasen
1. **Phase 0 (Klärung, 15 min):** Fragen an Rouven (siehe unten), Architekturentscheidung festhalten, Lizenz/Name prüfen.
2. **Phase 1 (MVP "für Freunde", Ziel: 1 bis 2 Sitzungen):** Mehrnutzer mit Login, Profil, täglicher Drop per n8n-Schedule, Quellen: RSS + YouTube + Reddit + Events-API, Share-Target in der PWA (Vision auf geteilte Bilder/Links), Web-Push. Deployment auf einem Gratis-Host, öffentlicher Link.
3. **Phase 2:** Telegram-Bot/E-Mail-Zustellung, Caching/Themen-Pool, Ranking, Feedback, Admin-Übersicht (Kosten/Fehler), Datenschutzerklärung/Impressum, Rate-Limits.
4. **Phase 3:** Mehrsprachigkeit, Landingpage, Open-Source-Doku (CONTRIBUTING), optional BYO-Key/Abo.

## 6. Arbeitsregeln
- **Keine Geheimnisse im Repo oder Chat:** Schlüssel (OpenRouter, n8n, Supabase ...) nur als Umgebungsvariablen/Secrets der Sitzung bzw. des Hosts; `.env`, `data/sessions/`, `data/connections.json` bleiben in `.gitignore`. Passwörter aus früheren Chats oder Testkonten **nicht verwenden und nicht speichern**.
- Keine Fake-Konten anlegen, keine Captchas/Verifizierungen umgehen, keine Passwörter fremder Nutzer speichern.
- Zerstörerische Befehle (`rm -rf`, Force-Push, Löschen von Daten) nur nach ausdrücklicher Zustimmung. Das Repo `rouvenwieland/cypher-news` ist **öffentlich** (MIT): nichts Privates committen (keine Fotos von Personen, keine Namen von Freunden, keine Zugangsdaten).
- Erst testen, dann "fertig" sagen: echte Anfrage, Browser-Test, Screenshot. Fehlschläge und Ungeprüftes offen benennen.
- Kleine, lauffähige Schritte; nach jedem funktionierenden Schritt committen.

## 7. Erste Fragen an Rouven
1. Zielgruppe/Umfang: Freunde und Bekannte (klein) oder wirklich öffentlich (viele Nutzer)? Wie viele Nutzer in den ersten 3 Monaten?
2. Quellen-Prioritäten: Welche 3 Quellen sind für dich Pflicht (YouTube, Reddit, Events, ...)? Ist das **"Teilen in die App"** für Instagram/TikTok/Stories für dich ok als Ersatz zum Scrapen?
3. Zustellung: Push, Telegram, E-Mail, alle?
4. Hosting: Hast du eine Kreditkarte für Gratis-Tarife (Oracle verlangt sie zur Verifizierung)? Soll n8n selbst gehostet werden oder auf n8n Cloud laufen?
5. Name/Branding: "Cypher News · Daily Drop" bleiben? Domain gewünscht?
6. Wer pflegt das Projekt (Zeit pro Woche)? Soll es Open Source bleiben?
