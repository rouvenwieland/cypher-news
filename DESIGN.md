# DESIGN: CYPHER NEWS (Untertitel: DAILY DROP)

Stand Oktober 2026, Fassung 2 ("Signal"). Fassung 1 (Retro-Pixel) war laut und schwer lesbar, Fassung 1b ("Morgenausgabe") ruhig und redaktionell. Rouvens Auftrag für Fassung 2: dunkel, cinematic, "giga geil", die Seite soll Spaß machen. Deshalb: die Redaktions-Typografie der Morgenausgabe bleibt (sie trägt das Lesen), darüber liegt eine Kino-Schicht für die öffentliche Seite und eine ruhigere Variante derselben Bewegungssprache in der App.

## Richtung: Signal
Idee: aus Rauschen wird Signal. Das ist das Produkt (viel Feed rein, wenige Treffer raus) und zugleich die Bewegungsmetapher: Zeichen werden entschlüsselt, Text steigt aus Masken, Rauschen verblasst und die Treffer bleiben stehen. Ton: nachts, Terminal-Glut, aber gedruckt gesetzt. Matrix-Motiv nur gezielt: Regen im Hintergrund des Heros und beim Erzeugen, die Terminalzeile im Hero, die Uhr "08:00", die sich entschlüsselt.
Dunkel ist Standard (`theme.js`: ohne gespeicherte Wahl `data-theme="dark"`). Hell und Auto bleiben unter Profil > Darstellung wählbar, auf der Startseite gibt es einen Umschalter in der Kopfzeile.

## Typografie (alles lokal)
Newsreader (Überschriften, Lesetext, riesige Ziffern, kursiver Akzent), Space Grotesk (Oberfläche), VT323 (Terminal, Preloader-Etiketten, Rauschen). Hero bis 148 px, Enge Laufweite (-.04em), `text-wrap: balance`. Lesetext in der App unverändert 18 px/1,58.

## Farben
Dunkel: `--bg #0c0a08`, Fläche `#15120f`, Text `#f4eee3`, Akzent Glut-Orange `#ff6a2b`, Terminal-Grün `#b6d65a` nur für Terminalzeilen. Hell (Papier) unverändert. Ein Signalton, Kategorien als Punkte.

## Seiten und Szenen (Willkommen, `templates/index.html` `#welcome`, `static/css/landing.css`, `static/js/motion.js`)
0. Preloader: schwarz, Wortmarke entschlüsselt sich, Zähler 000 bis 100, Orange-Balken, fährt nach oben weg (Angemeldete: nur kurzes Ausblenden, 0,45 s Minimum). Endet immer (Schutz 4,5 s in JS, 6 s per CSS).
1. Hero: Überschrift Wort für Wort aus Masken, Terminalzeile wechselt alle 3,4 s, riesige Outline-Uhr "08:00" (entschlüsselt sich), Glut mit Parallax und Zeigerfolge, Regen.
2. Manifest: Wörter werden beim Scrollen hell (gescrubbt).
3. "Wie dein Drop entsteht": Sticky-Karten-Stapel (Quellen, Auswahl, Drop), vorige Karte tritt skaliert zurück.
4. "Rauschen wird Signal": Desktop angeheftet und gescrubbt (Rauschwörter verblassen, 7 Treffer bleiben, Zähler 1248 bis 7), Mobil frei laufend ohne Pinning.
5. Fakten, Abschluss-CTA, Footer-Enthüllung (Wortmarke fährt wie ein Vorhang hoch).
Lenis nur auf dieser Seite, wird mit dem Login zerstört.

## App (ruhiger, gleiche Sprache)
- Drop-Enthüllung beim Öffnen/Erzeugen: Titel aus Masken, Trefferzahl zählt hoch, Karten decken sich gestaffelt per Abtastlinie auf (Abdeckung fährt weg, orange Kante); Karten außerhalb des Sichtfelds beim Hineinscrollen.
- Tabs: gleitende Marke (`#tabInd`), Seiteninhalt blendet gestaffelt ein.
- Mikrointeraktionen: Merken (Lesezeichen federt, Funken), Daumen hoch/runter kippen.
- Ladezustände: Terminal beim Erzeugen, Platzhalterzeilen mit Schimmer bei Gemerkt/Verlauf.

## Technik (hart)
Vanilla HTML/CSS/JS, kein Build. GSAP 3.15 + ScrollTrigger und Lenis 1.3.26 lokal in `static/vendor/` (aus den npm-Paketen, Lizenzdateien dabei), klassische Skripte mit `defer`, kein CDN. CSP unverändert streng (`script-src 'self'`, `style-src 'self'`): GSAP setzt Stile per CSSOM, das erlaubt die CSP. Nur transform/opacity animiert. Fehlen die Bibliotheken, läuft die App ohne Bewegung (`window.CNMotion`-Stubs in `app.js`).
Ohne JavaScript: Landingpage lesbar (kein Preloader, alles sichtbar), Anmelden braucht JS (Hinweis per noscript). `prefers-reduced-motion`: kein Preloader, kein Lenis, kein Scrub, keine Wortmasken, statische Seite; Terminalzeile statisch.
Geteilter Text: Original als `sr-only`, sichtbare Wörter `aria-hidden`. Touch-Ziele mindestens 44 px, `100svh/dvh`, Safe-Area.

## Qualitätsregeln
Keine Konsolenfehler, kein horizontaler Überlauf bei 375 px, Kontrast der Textpaare mindestens 4,5:1 in beiden Modi, Fokus sichtbar. Neue Schriften nur lokal.

## Barrierefreiheit: bewusste Entscheidungen
- Segment-Schalter: Auswahl = 2-px-Rahmen in `--accent` + Fettdruck + Haken, nicht nur ein blasser Daumen (Nicht-Text-Kontrast mindestens 3:1).
- Fehler an Feldern sind dauerhaft (`role=alert`, `aria-describedby`, `aria-invalid`) und verschwinden erst beim Tippen oder bei Erfolg. Toasts sind nur noch Bestätigungen (`role=status`) oder kurze Fehler ohne Feld (`role=alert`, 8 s).
- Gesperrte Knöpfe (Drop erzeugen, Speichern, Kartenpfeil am Ende) nutzen `aria-disabled` und ignorieren Klicks. `disabled` würde den Fokus verlieren.
- Tabwechsel setzt den Fokus auf die Überschrift der neuen Seite. Entfernen in "Gemerkt" geschieht an Ort und Stelle, der Fokus springt auf den nächsten Eintrag.
- Code-Dialog: Der Wiederherstellungscode wird nur einmal gezeigt. Der Dialog schließt deshalb **nur** mit "Gespeichert", nicht mit Escape oder Klick auf den Hintergrund. Escape erklärt das in einer Statuszeile und setzt den Fokus auf "Gespeichert". Startfokus ist die Überschrift (ein versehentliches Enter schließt nichts), Tab bleibt im Dialog.
- Karten wachsen mit ihrem Text (Mindesthöhe statt fester Höhe, keine Zeilenbegrenzung): nichts wird bei Zoom, Textabstand oder 400 % abgeschnitten.
- Touch-Ziele (Chips, Segment-Schalter, Quellen-Chips) sind für jeden Zeiger mindestens 44 px hoch.
- Prüfung: `tests/e2e_a11y.py` (Browser, axe optional) und `tests/test_a11y_static.py`.

---
## Anhang: Fassung 1b (Morgenausgabe), weiterhin gültig für die App
## Typografie (alles lokal, keine Anfragen an Dritte)
- **Newsreader** (variabel, opsz+wght, OFL, `static/fonts/`): Überschriften, Lesetext, Titelblatt, Ziffern. Kursiv für die Einleitung des Drops.
- **Space Grotesk**: Oberfläche, Beschriftungen, Metazeilen.
- **VT323**: nur Terminal und Wiederherstellungscode.
- Skala: Lesetext 18 px/1.58, Artikeltitel 23 bis 28 px/1.16, Titelblatt 34 bis 46 px, Kleintext nie unter 11,5 px. Eingaben 16 px (kein iOS-Zoom).

## Farben (Tokens in `style.css`, Dunkel und Hell, manuell umschaltbar unter Profil > Darstellung)
Dunkel: Hintergrund `#12100d`, Fläche `#1b1814`, Text `#f4eee3`, gedämpft `#a3988b`, Akzent `#ff6a2b`.
Hell (Papier): Hintergrund `#f5efe3`, Text `#1c1712`, Akzent `#c0400c`.
Ein Signalton (Orange) für Aktionen und Zahl. Kategorien sind kleine Punkte mit Text in eigener Farbe (Konzerte Bernstein, Giveaways Lind, Drops Rosé, Tech Aqua, Trends Gelb, News Stein), nie Flächen. `--control` gibt Bedienelementen einen Rahmen mit mindestens 3:1.

## Aufbau
- Mobil: Kopf mit Wortmarke und Ausgabedatum, Doppellinie, Inhalt, feste Tableiste unten (Heute, Gemerkt, Verlauf, Profil) mit Safe-Area.
- Desktop ab 960 px: Rail links (Wortmarke, Navigation, Fußzeile), Lesespalte rechts (max. 660 px).
- Heute: Titelblatt (Datum, große Trefferzahl, kursive Einleitung, Hinweis auf nicht erreichbare Quellen), Umschalter **Lesen | Karten** (Wahl wird lokal gemerkt), Kategorie-Filter. Lesen = nummerierte Artikel mit Haarlinien. Karten = wischbare Karten mit Zahl als Bild, Pfeile am Desktop.
- Profil: nummerierte Abschnitte statt Karten in Karten; Notizfeld mit Linienpapier.

## Zustände
| Zustand | Umsetzung |
|---|---|
| Leer (kein Drop) | großes "00", Erklärung, Button "Zum Profil" |
| Leer (Gemerkt, Verlauf, keine Treffer) | Serif-Satz mit Akzentstrich und nächstem Schritt |
| Laden | Terminal mit Zeilen alle 6 s, Zeitzähler, Hinweis "meist 30 bis 90 Sekunden", Regen an, Button gesperrt mit Spinner |
| Fehler | dauerhafte Meldung (`role=alert`) direkt am Feld oder auf der Seite, kein zweiter Toast; früherer Drop bleibt sichtbar |
| Teilweise | "Nicht erreichbar: ..." mit gelbem Punkt unter dem Titelblatt |
| Erfolg | Toast "Dein Drop ist fertig", Fokus auf Titel, Merken/Daumen mit Zustand und kleiner Bestätigungsbewegung |
| Offline | eigene Offline-Seite im Service Worker |

## Bewegung
Easing `cubic-bezier(.22,.9,.24,1)`, Eintritt gestaffelt (55 ms), Segment-Schalter mit gleitendem Daumen, Tab-Balken, Press-Zustand `scale(.97)`. Nur transform/opacity. Hover nur auf Zeigergeräten. `prefers-reduced-motion`: alles auf Minimum, Regen und Scramble aus.

## Technik (hart)
Vanilla HTML/CSS/JS, kein Build-Schritt, keine Laufzeit-Fremdanfragen. CSP ohne `unsafe-inline` (keine Inline-Styles, keine Inline-Skripte). Mobile: `viewport-fit=cover`, `100dvh`, `env(safe-area-inset-*)`, 44-px-Ziele bei grobem Zeiger. `theme.js` setzt das Farbschema vor dem ersten Zeichnen.

## Qualitätsregeln
Keine Konsolenfehler, kein horizontaler Überlauf bei 375 px, lange Titel und fremde Schriftzeichen brechen sauber. Kontraste der Textpaare mindestens 4,5:1 in beiden Modi. Neue Schriften nur lokal einbinden und Lizenz beilegen (`Newsreader-OFL.txt`).
