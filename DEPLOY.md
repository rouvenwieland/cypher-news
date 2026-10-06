# Kostenlos veröffentlichen (Hugging Face Space)

Nur Dinge, die du selbst einmal anlegen musst. Keine Kreditkarte nötig.

1. **Hugging Face Konto** (huggingface.co) → *New Space* → SDK **Docker**, Hardware *CPU basic (free)*, Sichtbarkeit *Public*.
2. Den Code in den Space pushen (Space ist ein Git-Repo) **oder** den GitHub-Repo verknüpfen. Die erste Zeile der `README.md` des Space braucht diesen Kopf:
   ```
   ---
   title: Cypher News
   sdk: docker
   app_port: 7860
   ---
   ```
3. **Secrets** im Space (Settings → Variables and secrets), nie ins Repo:
   | Name | Wert |
   |---|---|
   | `SECRET_KEY` | aus `python -m cypher.vapid` |
   | `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` | aus `python -m cypher.vapid` (für Push) |
   | `VAPID_SUBJECT` | `mailto:deine@mail` |
   | `MODEL_PRIMARY`, `MODEL_VISION`, `MODEL_FALLBACK` | geprüft am 6.10.2026 (existieren bei OpenRouter): `nvidia/nemotron-3-super-120b-a12b:free`, `google/gemma-4-31b-it:free` (Bilder), `nvidia/nemotron-3-ultra-550b-a55b:free`. Immer vorher auf openrouter.ai/models gegenprüfen |
   | `CRON_SECRET` | langer Zufallstext |
   | `OPENROUTER_API_KEY` | optional: Server-Schlüssel für das Gratis-Kontingent (`FREE_DROPS_PER_DAY`, Standard 1) |
   | `IMPRINT_TEXT` | dein Impressum (Pflicht in Deutschland für öffentliche Angebote) |
   | `HF_TOKEN` + `BACKUP_REPO` | **wichtig:** Free Spaces verlieren ihre Dateien bei Neustart. Mit einem Schreib-Token und z. B. `deinname/cypher-news-data` sichert die App die Datenbank alle 5 Minuten in ein privates Dataset und stellt sie beim Start wieder her. |
4. **Täglicher Drop:** Free Spaces schlafen nach Inaktivität. Im GitHub-Repo unter Settings → Secrets die Werte `APP_URL` (z. B. `https://deinname-cypher-news.hf.space`) und `CRON_SECRET` setzen. Der Workflow `daily-drop.yml` weckt die App alle 30 Minuten und stößt fällige Drops an.
5. Nutzer öffnen den Link und tippen "Zum Home-Bildschirm" (iPhone: Teilen → Zum Home-Bildschirm; Android: Installieren). Push auf dem iPhone geht nur für die installierte App.

Grenzen (ehrlich): Free-Modelle bei OpenRouter haben Tageslimits (ca. 50 Anfragen ohne Guthaben, ca. 1000 mit 10 $ Guthaben); deshalb trägt jeder Nutzer seinen eigenen kostenlosen Schlüssel ein. Native Apps (Google Play 25 $ einmalig, App Store 99 $/Jahr) sind erst sinnvoll, wenn die PWA genutzt wird; die PWA lässt sich später mit Capacitor oder TWA verpacken.
