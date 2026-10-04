# DESIGN-BRIEFING: CYPHER NEWS (Untertitel: DAILY DROP)

Ziel: Die Oberfläche soll wirken wie eine Instagram-/Awwwards-würdige Retro-Pixel-App: mutig, lebendig, sofort wiedererkennbar. Jeder Bildschirm hat Bewegung.
**Der Produktname ist "CYPHER NEWS". Darunter, klein und mit Buchstabenabstand: "DAILY DROP".** Der Stil heißt "Cypher-Vibe": Underground, Retro-Pixel, warmes Schwarz, Orange/Rot/Gelb, Neongrün als Akzent, Körnung, Glitch. Es werden KEINE Fotos von Personen verwendet, nur die Motive in static/img und generierte Muster.

## Technik (hart)
Vanilla HTML/CSS/JS, kein Build-Schritt, KEIN CDN/Internet (Schule!). Schriften liegen lokal in static/fonts (PressStart2P.ttf nur für Logo und Mini-Labels, VT323.ttf für Terminal/Statuszeilen, SpaceGrotesk.ttf für Fließtext und Überschriften). `@font-face` mit `font-display: swap`. Mobile-first (360–430 px), auf dem Desktop zentrierte Phone-Spalte (max 460 px) vor großem animierten Hintergrund. `prefers-reduced-motion`: Canvas aus, Animationen kurz.

## Farben (CSS-Variablen in :root)
--bg:#130e0b; --bg2:#0e0a08; --card:#201710; --line:#3a2a20; --ink:#fff3df; --dim:#b9a78f;
--orange:#ff6a1a; --red:#e03a2b; --yellow:#ffc21a; --green:#39ff14; --cyan:#2fe6a6; --pink:#d6336c.
Kategorie-Farben: Konzerte=orange, Giveaways=green, Drops/Mode=pink, Tech=cyan, Trends=yellow, Sonstiges=red.

## Bausteine (alle umsetzen)
1. **Hintergrund:** Vollbild-`<canvas>` mit Matrix-Regen (Pixel-Zeichen, Farben Orange/Grün, Opacity 0.18, langsam), darüber SVG-Körnung (feTurbulence, mix-blend-mode: overlay, Opacity .12) und Vignette (radial-gradient). Dazu ein langsam wandernder Farbverlauf (conic/radial, 30 s Loop).
2. **Header:** Wortmarke "CYPHER NEWS" in Pixel-Optik (PressStart2P, Verlauf Gelb→Orange→Rot per `background-clip:text`), alle ~6 s ein kurzer Glitch (RGB-Split mit `text-shadow`, `clip-path`-Schnitte, 120 ms). Darunter "DAILY DROP" (VT323, letter-spacing .5em, blinkender Cursor `█`). Rechts oben Uhrzeit und Badge "HEUTE".
3. **Ticker:** Endlos laufende Marquee-Zeile (CSS `translateX` -50 %, 40 s linear infinite) mit den Schlagzeilen des Tages, getrennt durch `✦`, Farbe nach Kategorie. Pause bei Hover/Touch.
4. **Onboarding "Dein Drop":** große Textarea mit Platzhalter ("Sag, was dich interessiert: Konzerte in Berlin, Giveaways, Klamotten-Drops, Tech-News ..."), darunter **Chips** zum Antippen (Konzerte Berlin, Giveaways, Kleidungsdrops, Tech-News, Trends, Streetwear, Techno, Rap), die an/aus gehen (Pixel-Haken, kleine Bounce-Animation). Darunter "Quellen": Eingabefeld für @Accounts/URLs mit Plattform-Auswahl (Instagram, TikTok, YouTube, Reddit, RSS); hinzugefügte Quellen erscheinen als Chips mit Plattform-Icon (einfache SVG/Emoji) und Löschen-Kreuz. Der Hauptknopf **"DROP ERZEUGEN"** ist breit, orange, mit Pixel-Kante (box-shadow in Stufen), Press-Animation (translateY 4 px), Hover-Glow und Haptik `navigator.vibrate(15)`.
5. **Ladeanimation (mind. 3 s, fühlt sich lebendig an):** Terminal-Karte (VT323, Grün auf Schwarz) mit nacheinander erscheinenden Zeilen ("> scanne Instagram ...", "> lese YouTube-Feeds ...", "> filtere Rauschen ...", "> n8n-Workflow läuft ...", "> schreibe deinen Drop ..."), Fortschrittsbalken aus Pixelblöcken, Matrix-Burst im Hintergrund. Echte Antwort ersetzt die Animation, sobald sie da ist (nie künstlich länger als 8 s).
6. **Ergebnis als "Stories":** vertikal scroll-snap Vollbild-Karten (`scroll-snap-type:y mandatory`, jede Karte 100 dvh) ODER horizontal wischbar mit Fortschrittsbalken oben (wie Instagram-Stories). Jede Karte: Kategorie-Pill (Farbe nach Kategorie), große Überschrift (Space Grotesk 700, 28–34 px), Zusammenfassung, Quelle + "wann", Buttons "ÖFFNEN ↗", "★ MERKEN", "TEILEN". Kartenkopf mit Duotone-/Pixel-Bild aus static/img (field_pix, money_pix, *_duo) als Parallax-Layer (`transform: translateY` aus Scroll). Eintritt gestaffelt (Fade+Slide, 60 ms Versatz), Zahl großer "01/08" Index in VT323.
7. **Umschalter** oben: "STORIES | FEED". Feed = kompakte Kartenliste mit Kategorie-Filtern (Chips), 3D-Tilt auf Desktop (`mousemove` -> `rotateX/Y` max 6°).
8. **Intro-Karte des Drops:** "DEIN DROP · {Datum}" mit der n8n-`intro`, Zähler "8 Treffer aus 5 Quellen", Button "Nächster Drop um 08:00" (Countdown läuft).
9. **Push/Handy:** Button "AUF DEM HANDY ERHALTEN": registriert den Service Worker, fragt `Notification.requestPermission()`, zeigt Demo-Benachrichtigung "Dein Drop ist da"; Hinweis "App installieren" (beforeinstallprompt). Manifest: name "Cypher News", short_name "Cypher News", theme_color #130e0b, Icons 192/512 (mit ImageMagick aus Pixel-Wortmarke erzeugen).
10. **Verlauf & Gemerkt:** localStorage, Seite "Gemerkt" (★) und "Verlauf" der letzten 7 Drops.
11. **Mikro-Details:** Pixel-Cursor-Trail auf Desktop, Konfetti aus Pixelquadraten beim Fertigwerden, Toasts im Terminal-Stil, Tastatur-Fokus sichtbar, sinnvolle Leerzustände ("Noch kein Drop. Sag uns, was dich interessiert.").

## Code-Gerüste (als Ausgangspunkt, anpassen)
Matrix-Regen:
```js
const c=document.getElementById('rain'),x=c.getContext('2d');let w,h,cols,drops;
function size(){w=c.width=innerWidth;h=c.height=innerHeight;cols=Math.floor(w/16);drops=Array(cols).fill(0).map(()=>Math.random()*h/16)}
addEventListener('resize',size);size();const G='01ｱｲｳｴｵｶｷｸｹｺ<>/#$%&*+=-';
function tick(){x.fillStyle='rgba(19,14,11,.12)';x.fillRect(0,0,w,h);x.font='16px VT323';
 drops.forEach((d,i)=>{x.fillStyle=Math.random()<.15?'#39ff14':'#ff6a1a';x.fillText(G[Math.floor(Math.random()*G.length)],i*16,d*16);drops[i]=d*16>h&&Math.random()>.975?0:d+1});
 requestAnimationFrame(tick)}
if(!matchMedia('(prefers-reduced-motion: reduce)').matches)tick();
```
Glitch:
```css
.logo{position:relative}.logo.glitch{animation:gl .12s steps(2) 3}
@keyframes gl{0%{text-shadow:2px 0 #39ff14,-2px 0 #e03a2b;clip-path:inset(10% 0 55% 0)}50%{text-shadow:-3px 0 #39ff14,3px 0 #e03a2b;clip-path:inset(60% 0 8% 0)}100%{text-shadow:none;clip-path:none}}
```
Marquee: `.ticker__inner{display:inline-flex;gap:2rem;animation:mq 40s linear infinite}@keyframes mq{to{transform:translateX(-50%)}}` (Inhalt doppelt rendern).
Tilt: `card.onmousemove=e=>{const r=card.getBoundingClientRect();const px=(e.clientX-r.left)/r.width-.5,py=(e.clientY-r.top)/r.height-.5;card.style.transform=`perspective(700px) rotateY(${px*10}deg) rotateX(${-py*10}deg)`}`.

## Qualitätsregeln
Kein Platzhaltertext, kein "Lorem ipsum", keine kaputten Bilder, keine Konsolenfehler. Jede Animation läuft flüssig (nur transform/opacity). Deutsche Texte, kurze Sätze. Ladezeit < 2 s lokal. Die Demo muss mit `data/sample_newsletter.json` (8 realistische, abwechslungsreiche Einträge zu Konzerten in Berlin, Giveaways, Kleidungsdrops, Tech-News, Trends) offline perfekt aussehen und mit dem n8n-Webhook live funktionieren.
