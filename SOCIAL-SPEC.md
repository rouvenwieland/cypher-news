# SOCIAL-SPEC (verbindlich, 14:15) – Connectors, Social-Scraping, Bilder, Modell-Routing

## Konzept (so meint Rouven es)
CYPHER NEWS ist ein **All-in-one-Connector-Newsletter**. Man verbindet seine **eigenen Konten** (Instagram, TikTok, YouTube, Reddit, dazu freie RSS/Web-Quellen) und bekommt täglich einen KI-Newsletter über **alles, was dort passiert ist**: Posts, Reels/Videos **und Stories**, nicht nur Artikel. Nutzen: Man muss nicht mehr durch Stories und Feeds scrollen, ist trotzdem up to date (Event-/Konzert-Hinweise, Giveaways, Drops, Trends) – weniger Bildschirmzeit, trotzdem keine FOMO.
UI-Idee: (1) **Verbinden-Seite**: je Plattform eine Karte mit Status ("nicht verbunden" / "verbunden als @name") und Knopf VERBINDEN (Login-Dialog). (2) Nach dem Verbinden ein **Auswahlfeld mit Accounts, denen man folgt** (Mehrfachauswahl, Suche, Chips), pro Plattform; zusätzlich Handle manuell hinzufügen. (3) **Ein riesiges Notiz-Textfeld** ("Schreib alles rein, was dich juckt – wie in Notizen"): Interessen, Orte, Künstler, Marken, No-Gos. (4) DROP ERZEUGEN.

## Architektur
`Browser (Flask-PWA)` → `Flask /api/*` → (a) `socialfetch` (lokaler Dienst 127.0.0.1:5090, hält Sessions/Logins) holt Posts/Stories → (b) n8n-Webhook (`N8N_WEBHOOK_URL`) mit allen Rohdaten → n8n: Plan, RSS/News-Quellen, **Bild-Auswertung (Vision-Modell)**, **Modell-Routing mit Ausweichmodellen**, Newsletter-Text → JSON zurück.
Zugangsdaten bleiben NUR in `data/sessions/` und `data/connections.json` (in .gitignore!), nie im Git, nie an n8n/Modelle.

### Vertrag Flask → n8n (POST JSON)
`{preferences:str, sources:[str], accounts:{instagram:[handle], tiktok:[handle], youtube:[handle], reddit:[handle]}, date:'YYYY-MM-DD', social_items:[{platform,account,kind:'post'|'story'|'reel'|'video',text,url,taken_at,image_b64?}]}`
(`image_b64` = kleines JPEG ≤ 80 KB, base64, ohne Prefix.)
### Antwort n8n → Flask → UI
`{title,date,intro,items:[{category,title,summary,source,url,when,kind:'news'|'post'|'story'|'reel'|'video',platform?,account?,image?:'data:image/jpeg;base64,...'}],meta:{engine,model,sources,images_analyzed}}`

### socialfetch (Python/Flask, 127.0.0.1:5090) – wird von Ran gebaut (Ordner `socialfetch/`)
- `POST /connect {platform,username,password}`: Instagram per `instaloader` (Login, Session-Datei in data/sessions, 2FA-Fehler sauber melden), TikTok/YouTube/Reddit: nur Handle speichern ("verbunden"), da öffentlich lesbar. Antwort `{ok, display_name}`.
- `GET /accounts?platform=instagram`: Instagram: `Profile.get_followees()` (max 150, mit Pause/Cache 10 min); sonst Vorschlagsliste + manuelle Eingabe.
- `GET /feed?platform=..&accounts=a,b&hours=48`: Instagram: Posts + **Stories** (`get_stories`, nur mit Login) per instaloader; TikTok: `yt-dlp --dump-json --playlist-end 5 https://www.tiktok.com/@handle` (Beschreibung, Thumbnail); YouTube: Kanal-RSS (Handle über die Kanalseite zu channelId auflösen); Reddit: `/r/x/top/.rss?t=day`. Jedes Item mit Thumbnail als kleines JPEG (`image_b64`, per Pillow/ImageMagick verkleinert).
- Alle Aufrufe mit Timeout (je Account ≤ 15 s), Fehler pro Account abfangen (ein kaputter Account darf nichts stoppen), Rate-Limit-Schutz.
- **Demo-Sicherheit:** `data/demo_social.json` enthält ~12 realistische, **klar als Beispieldaten markierte** Posts/Stories (Konzerte in Berlin, Giveaways, Kleidungsdrops, Tech) mit generierten Pixel-Thumbnails (ImageMagick, keine Personen). Wenn Live-Scraping fehlschlägt oder ein Demo-Schalter aktiv ist, nutzt Flask diese Daten; die UI zeigt dann dezent "Beispieldaten".

### Modell-Routing in n8n (macht Claude)
Text: `nvidia/nemotron-3-ultra-550b-a55b:free` → bei Fehler/Leerantwort `deepseek/deepseek-v4-pro` (offen, billig) → `nvidia/nemotron-3-super-120b-a12b:free` → regelbasierter Fallback. Bilder: `qwen/qwen3.8-27b:free` → `google/gemma-4-31b-it:free` → `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`. Max. 6 Bilder pro Drop.

## Rechtliches/Ehrlichkeit (in README und UI-Hinweis)
Instagram-Login-Scraping verstößt gegen die Nutzungsbedingungen der Plattform; nur eigenes (Zweit-)Konto, Zugangsdaten bleiben lokal. Im Pitch als "Prototyp-Connector" benennen; Produktionsweg wäre die offizielle Graph-API.
