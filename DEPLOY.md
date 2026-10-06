# Kostenlos veröffentlichen (Hugging Face Space)

Der Space holt den Code beim Bauen selbst von GitHub. Du lädst keinen Code hoch. Schlüssel für Push erzeugt die App selbst.

1. huggingface.co → **New Space** → Name `cypher-news`, SDK **Docker → Blank**, Hardware *CPU basic (free)*, **Public**.
2. Im Space unter **Files → Add file → Create a new file** zwei Dateien anlegen und den Inhalt aus dem Ordner `hf-space/` dieses Repos hineinkopieren: `Dockerfile` und `README.md` (ersetzen). Speichern: der Space baut sich (ca. 3 bis 5 Minuten).
3. Im Space unter **Settings → Variables and secrets**:
   | Typ | Name | Wert |
   |---|---|---|
   | Secret | `SECRET_KEY` | ein langer, zufälliger Text (40+ Zeichen, selbst tippen), verschlüsselt die gespeicherten Nutzer-Schlüssel |
   | Variable | `IMPRINT_TEXT` | Impressumstext (Name, Kontakt) |
   | Secret | `HF_TOKEN` | Token mit Schreibrecht (huggingface.co/settings/tokens, Typ *Write*): sichert die Datenbank, sonst gehen Nutzerdaten bei jedem Neustart verloren |
   | Variable | `BACKUP_REPO` | `rouvenwieland/cypher-news-data` (wird automatisch als privates Dataset angelegt) |
   | Secret | `OPENROUTER_API_KEY` | optional: Server-Schlüssel für 1 Gratis-Drop pro Nutzer und Tag (`FREE_DROPS_PER_DAY`) |
4. Aufrufen unter `https://rouvenwieland-cypher-news.hf.space` (direkt, nicht auf der huggingface.co-Seite: dort laufen Cookies im Rahmen nicht).
5. Der GitHub-Workflow `keep-awake` pingt die App alle 20 Minuten, damit der eingebaute Scheduler Drops zur Uhrzeit bauen kann. Dafür sind keine Secrets nötig.

Modelle stehen im `Dockerfile` (`MODEL_PRIMARY`, `MODEL_FALLBACK`, `MODEL_VISION`). Prüfe sie gelegentlich auf openrouter.ai/models; Free-Modelle verschwinden. Nach einer Änderung: Datei im Space bearbeiten.
App aktualisieren: Space → Settings → **Factory rebuild** (zieht den neuesten Code von GitHub).

Grenzen: Free-Modelle bei OpenRouter haben Tageslimits (ca. 50 Anfragen ohne Guthaben, ca. 1000 mit 10 $ Guthaben), deshalb trägt jeder Nutzer seinen eigenen kostenlosen Schlüssel ein. Instagram und TikTok werden öffentlich und inoffiziell gelesen und können jederzeit blockiert werden. Native Apps (Google Play 25 $ einmalig, App Store 99 $/Jahr) erst, wenn die PWA genutzt wird.
