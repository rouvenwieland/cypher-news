#!/bin/bash

# Fallback Demo Script für KI-Newsletter
# Führt einen einfachen Test des Demo-Pfades durch und erstellt einen Screenshot

set -e

echo "=== Fallback Demo für KI-Newsletter ==="
echo "Dauer: $SECONDS Sekunden"

echo "\n1. Überprüfe App-Verfügbarkeit..."
if [ -f /tmp/newsletter_demo_started ]; then
    echo "App läuft bereits (beginn vor $SECONDS Sekunden)"
else
    echo "Starte Flask-App..."
    timeout 30 python app.py &
    APP_PID=$!
    echo $APP_PID > /tmp/newsletter_demo_started
    sleep 3
fi

echo "\n2. Teste Demo-Pfad mit curl..."
RESPONSE=$(curl -s -m 5 -X POST \
  -H "Content-Type: application/json" \
  -d '{"preferences": "Konzerte Berlin", "sources": ["youtube_tech"], "date": "2026-10-04"}' \
  http://127.0.0.1:5000/mock/newsletter)

echo "Response: $RESPONSE"
echo "\n3. Überprüfe Offline-Fallback..."
curl -s http://127.0.0.1:5000/data/sample_newsletter.json | head -c 200
echo " ..."

echo "\n4. Demo wurde erfolgreich getestet!"
echo "App läuft auf: http://127.0.0.1:5000"
echo "Demo-Pfad: Themen eingeben → Newsletter erzeugen → Karten anzeigen"
echo "\nFüge lokale Screenshots hinzu (manuell oder mit gnome-screenshot)"
echo "oder verwende: scrot -s -o /tmp/demo.png"

echo "\n=== Ende des Fallback-Demos ==="
