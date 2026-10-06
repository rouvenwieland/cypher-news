# Cypher News — Daily Drop

Dein persönlicher KI-Newsletter. Du schreibst einmal, was dich interessiert, und sagst, welchen öffentlichen Accounts du folgst (Instagram, TikTok, YouTube, Reddit, Bluesky, Mastodon, RSS). Jeden Tag scannt Cypher News diese Quellen plus Google News, lässt ein **offenes Sprachmodell** (über OpenRouter) auswerten und schickt dir einen kurzen "Drop" als installierbare Web-App (PWA) mit Push-Nachricht. Weniger Scrollen, keine FOMO.

## Was die App kann
- Mehrere Nutzer, **ohne E-Mail und ohne Passwort**: Konto = Cookie + Wiederherstellungscode (Daten-Export und Konto löschen inklusive).
- Quellen: Google News, Reddit, YouTube, Bluesky, Mastodon, RSS, TikTok und Instagram (öffentliche Profile, best effort), Massen-Import einer Follow-Liste.
- **Teilen in die App** (Web Share Target): Posts, Links und Story-Screenshots direkt aus Instagram/TikTok an Cypher News teilen; das Vision-Modell liest Datum, Ort, Aktion aus.
- KI: Texte und Bildauswertung mit offenen Modellen, Modellnamen nur aus Umgebungsvariablen. **Eigener OpenRouter-Schlüssel pro Nutzer** (verschlüsselt gespeichert) oder optionales Gratis-Kontingent über den Server-Schlüssel.
- Täglicher Drop zur gewählten Uhrzeit (Scheduler), Web-Push, Verlauf, Merken, 👍/👎-Feedback fließt ins Ranking, Deduplizierung über Tage.
- Datenschutz: keine Passwörter fremder Dienste, kein Login-Scraping, SSRF-Schutz, CSP, Rate-Limits.

## Bewusst NICHT enthalten
Anmeldung mit Instagram/TikTok-Passwort. Das verstößt gegen die AGB der Plattformen, führt zu Kontosperren und wäre ein Sicherheitsrisiko. Stattdessen: öffentliche Profile + "Teilen in die App". Öffentliche Instagram-/TikTok-Abrufe werden von den Plattformen oft blockiert; was nicht erreichbar war, zeigt der Drop an.

## Lokal starten
```bash
pip install -r requirements.txt
python -m cypher.vapid            # gibt SECRET_KEY und VAPID-Schlüssel aus (nicht committen!)
export SECRET_KEY=...  MODEL_PRIMARY=<Modell-ID von openrouter.ai/models>  MODEL_VISION=<Vision-Modell>
export COOKIE_SECURE=0            # nur lokal ohne https
python app.py                     # http://127.0.0.1:5000
python -m pytest -q tests         # Tests
```
Modell-IDs ändern sich oft (Free-Modelle verschwinden): immer in den Umgebungsvariablen setzen, nie im Code. `MODEL_FALLBACK` ist optional.

## Veröffentlichen (kostenlos)
Siehe [DEPLOY.md](DEPLOY.md) (Hugging Face Space mit Docker, Backup der Datenbank, täglicher Cron per GitHub Actions).

## Technik
Flask + SQLite, Vanilla JS-PWA, kein Build-Schritt. Ordner: `cypher/` (Quellen, KI, Pipeline, Scheduler, Push, Backup), `templates/`, `static/`, `tests/`. `n8n/` und `pitch/` stammen vom Hackathon (n8n-Workflow-Prototyp, Pitch-Präsentation) und sind nicht Teil der App.

Lizenz: MIT. Verwendete Modelle laufen unter ihren eigenen Lizenzen (siehe Modellseite bei OpenRouter).
