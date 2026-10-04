# Fallback Demo für KI-Newsletter

Wenn die Live-Demo fehlschlägt (Netzwerkprobleme, Serverabstürze usw.), kann der Fallback so verwendet werden:

## Lokaler Fallback

### Methode 1: Verwenden Sie das Fallback-Skript
Führen Sie das Skript aus, das die Live-Demo automatisch testet:

```bash
./run_fallback_demo.sh
```

### Methode 2: Erstellen Sie Screenshots manuell
```bash
# Für einen einzelnen Screenshot
scrot -s -o /tmp/screenshot_$(date +%Y%m%d_%H%M%S).png

# Für eine kurze Videoaufnahme (erfordert gnome-terminal)
#recordmydesktop --width=800 --height=600 --delay=2 \
#  -o /tmp/demo_video.ogv
```

### Methode 3: Automatisierte Screenshots
Fügen Sie diese Python-Skripte zur Flask-App hinzu, um Screenshots zu erstellen:

```python
# scripts/screenshots.py
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def capture_demo_screenshot():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    driver.get('http://127.0.0.1:5000')
    time.sleep(2)
    
    # Füllen Sie das Formular aus
    driver.find_element(By.ID, 'topics').send_keys('Testthema Berlin')
    driver.find_element(By.ID, 'generateBtn').click()
    
    time.sleep(3)
    
    # Speichern Sie den Screenshot
    driver.save_screenshot('/tmp/demo_screenshot.png')
    driver.quit()
```

## Checkliste für den Fallback
- [ ] Flask-App funktioniert lokal
- [ ] Mock-Endpoint antwortet korrekt
- [ ] Offline-Fallback lädt Beispiel-Newsletter
- [ ] Screenshots/Video werden erstellt
- [ ] Demo-Pfad manuell dokumentiert

## Bereitstellungs-Anleitung

Wenn die Live-Demo fehlschlägt, führen Sie Folgendes aus:

```bash
cd /home/rouven/hack/newsletter
./run_fallback_demo.sh
```

Erstellen Sie dann Screenshots der Demo in der Web-UI und fügen Sie sie der Präsentation als Ersatz für die Live-Demo hinzu.
