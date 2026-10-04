# Regeln für alle Agenten in diesem Projekt

- Kontext: Hackathon, Thema "Building with open-source AI". Hackingzeit: 12:00-16:45. Team: 3 Personen, keine Experten.
- Antworte dem Team auf Deutsch, kurz und konkret. Code, Kommentare und Commit-Messages dürfen Englisch sein.
- Das Produkt MUSS ein offenes Modell (open weights) sichtbar nutzen. 
  Nutze OpenRouter (https://openrouter.ai/api/v1, Key aus $OPENROUTER_API_KEY) mit ':free'-Modellen. Kein lokales Modell.
  Modellname IMMER aus der Umgebungsvariable lesen (os.environ['MODEL_PRIMARY'], ist bereits gesetzt und geprueft). NIEMALS einen Modellnamen selbst ausdenken oder aus dem Gedaechtnis eintragen: viele Free-Modelle existieren nicht mehr (404). Im README steht, welches Modell mit welcher Lizenz.
- Einfachster Stack, der eine funktionierende Demo zeigt. Keine Frameworks "für später".
- Erst lauffähig, dann schön. Nach jedem funktionierenden Schritt: git commit.
- Keine Geheimnisse (API-Keys, Passwörter) in Dateien oder Commits. Keys kommen aus Umgebungsvariablen.
- Keine personenbezogenen Daten an Free-Modelle schicken (OpenRouter-Free kann Prompts protokollieren).
- Feature-Freeze ist um 15:30. Danach nur noch Fehler beheben, README und Pitch.
