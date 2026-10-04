#!/usr/bin/env bash
# Startet alles fuer die Demo: n8n (Port 5678), Social-Dienst (5090), App (5000) und oeffnet den Browser.
# Nutzung: ./start.sh      Beenden: Strg+C
cd "$(dirname "$0")"
source ~/.config/hackathon/env 2>/dev/null; source ~/.config/hackathon/models.env 2>/dev/null; export MODEL_PRIMARY MODEL_PAID
PY=python3; [ -x venv/bin/python ] && PY=venv/bin/python
curl -s -m 2 localhost:5678/healthz >/dev/null || { echo "n8n startet ..."; squad up >/dev/null 2>&1; for i in $(seq 1 30); do curl -s -m 2 localhost:5678/healthz >/dev/null && break; sleep 2; done; }
curl -s -m 2 localhost:5678/healthz >/dev/null && echo "n8n laeuft" || echo "WARNUNG: n8n nicht erreichbar - die App nutzt den Fallback"
(cd socialfetch && exec $PY app.py) >/tmp/socialfetch.log 2>&1 & SF=$!
trap 'kill $SF 2>/dev/null' EXIT
sleep 2; (sleep 3; omarchy launch browser http://127.0.0.1:5000 >/dev/null 2>&1) &
echo "Cypher News laeuft auf http://127.0.0.1:5000  (Strg+C beendet alles)"
exec $PY app.py
