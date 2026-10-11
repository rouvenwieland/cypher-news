# Regeln für alle Agenten in diesem Projekt

- Kontext: Persönliches Projekt von Rouven (Cypher News, Daily Drop), auch für Freunde. Ursprünglich ein Hackathon-Projekt (Thema "Building with open-source AI"); die Hackathon-Zeitgrenzen (Hackingzeit, Feature-Freeze) gelten nicht mehr.
- Antworte auf Deutsch, kurz und konkret. Code, Kommentare und Commit-Messages dürfen Englisch sein.
- Das Produkt nutzt sichtbar ein offenes Modell (open weights) über OpenRouter (https://openrouter.ai/api/v1, Key aus $OPENROUTER_API_KEY), bevorzugt ':free'-Modelle. Kein lokales Modell.
  Modellname IMMER aus der Umgebungsvariable lesen (os.environ['MODEL_PRIMARY']). NIEMALS einen Modellnamen selbst ausdenken oder aus dem Gedächtnis eintragen: viele Free-Modelle existieren nicht mehr (404). Im README steht, welches Modell mit welcher Lizenz.
- Stack: Flask + SQLite + Vanilla-JS-PWA, kein Build-Schritt. Neue Frameworks oder Abhängigkeiten nur mit Begründung und nach Rückfrage.
- Qualität: Erst lauffähig, dann gründlich. Tests laufen lassen (`python -m pytest -q tests`), nach jedem funktionierenden Schritt committen.
- Oberfläche: hochwertiges, eigenständiges Design, kein generischer KI-Look. Vorgehen: `DESIGN.md` im Projekt beachten (Änderungen daran mit Begründung), Referenzen aus der Design-Bibliothek im Vault (`ComputerOptimierung\Design-Bibliothek.md`), Impeccable-Befehle für Kritik und Feinschliff, Ergebnis mit Playwright mobil und auf dem Desktop screenshotten und selbst prüfen. Die PWA muss auf dem Handy gut wirken.
- Keine Geheimnisse (API-Keys, Passwörter) in Dateien oder Commits. Keys kommen aus Umgebungsvariablen.
- Keine personenbezogenen Daten an Free-Modelle schicken (OpenRouter-Free kann Prompts protokollieren).
