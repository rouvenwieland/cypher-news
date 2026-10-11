# DESIGN: CYPHER NEWS (Untertitel: DAILY DROP)

Stand Oktober 2026, überarbeitet. Das erste Design (Retro-Pixel, Matrix-Regen, Neon-Orange, PressStart2P) stammt vom Hackathon: wiedererkennbar, aber laut, schwer lesbar (7-px-Pixelschrift, Kleintext), rechenintensiv (Vollbild-Filter, Dauerschleifen) und es sah nach Hackathon aus. Ein täglicher Newsletter wird gelesen. Deshalb ein neuer Ansatz, der den "Cypher"-Charakter behält, aber als Detail statt als Kulisse.

## Richtung: die Morgenausgabe
Zweck: einmal am Tag lesen, merken, bewerten; Interessen und Quellen pflegen. Zielgruppe: Rouven und Freunde, Handy zuerst (PWA), Desktop ebenfalls.
Ton: redaktionell, ruhig, präzise. Zeitung statt Spielhalle.
Einprägsames Detail: die Wortmarke "Cypher News" mit blinkendem Cursor-Block, die sich beim Laden "entschlüsselt" (Zeichen-Scramble, 0,9 s), dazu das Terminal als Ladezustand. Der Matrix-Regen läuft nur noch auf dem Willkommen-Screen und beim Erzeugen, sonst steht er still.

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
| Fehler | dauerhafte Meldung (`role=alert`) plus Toast; früherer Drop bleibt sichtbar |
| Teilweise | "Nicht erreichbar: ..." mit gelbem Punkt unter dem Titelblatt |
| Erfolg | Toast "Dein Drop ist fertig", Fokus auf Titel, Merken/Daumen mit Zustand und kleiner Bestätigungsbewegung |
| Offline | eigene Offline-Seite im Service Worker |

## Bewegung
Easing `cubic-bezier(.22,.9,.24,1)`, Eintritt gestaffelt (55 ms), Segment-Schalter mit gleitendem Daumen, Tab-Balken, Press-Zustand `scale(.97)`. Nur transform/opacity. Hover nur auf Zeigergeräten. `prefers-reduced-motion`: alles auf Minimum, Regen und Scramble aus.

## Technik (hart)
Vanilla HTML/CSS/JS, kein Build-Schritt, keine Laufzeit-Fremdanfragen. CSP ohne `unsafe-inline` (keine Inline-Styles, keine Inline-Skripte). Mobile: `viewport-fit=cover`, `100dvh`, `env(safe-area-inset-*)`, 44-px-Ziele bei grobem Zeiger. `theme.js` setzt das Farbschema vor dem ersten Zeichnen.

## Qualitätsregeln
Keine Konsolenfehler, kein horizontaler Überlauf bei 375 px, lange Titel und fremde Schriftzeichen brechen sauber. Kontraste der Textpaare mindestens 4,5:1 in beiden Modi. Neue Schriften nur lokal einbinden und Lizenz beilegen (`Newsreader-OFL.txt`).
