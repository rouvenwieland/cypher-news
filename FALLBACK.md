# Fallback Demo Documentation

## Live Demo Alternative

When the live demo fails, use this fallback documentation and the curl commands below to demonstrate the same functionality.

### Demo Steps (Same as live)
1. Open the web app at http://127.0.0.1:5000
2. Enter topics: "Konzerte Berlin"
3. Select sources: "YouTube: TechNews"
4. Click "Newsletter jetzt erzeugen"
5. View newsletter cards with titles, summaries, links, dates
6. Check history section for past newsletters

### API Calls for Demo

**Step 1: Access the main page**
```bash
timeout 5 curl -s http://127.0.0.1:5000
```

**Step 2: Generate a newsletter**
```bash
timeout 5 curl -s -X POST http://127.0.0.1:5000/mock/newsletter -H "Content-Type: application/json" -d '{"preferences": "Konzerte Berlin", "sources": ["youtube_tech"], "date": "2026-10-04"}'
```

**Step 3: Load fallback sample data**
```bash
timeout 5 curl -s http://127.0.0.1:5000/data/sample_newsletter.json
```

### Expected Output
The API calls will return newsletter data in JSON format with:
- Title and introduction
- 3 card items with category, title, summary, source, URL, and date
- All dates are set to current date (2026-10-04)

### Open-Source AI Model Information
- Model: nvidia/nemotron-3-super-120b-a12b:free
- License: OpenRouter Free-Lizenz
- Accessed via environment variable MODEL_PRIMARY
- Runs through OpenRouter API

### UI Features
- Theme toggle (Dunkelmodus/Hellmodus)
- Service Worker for offline support
- History storage in localStorage
- Responsive cards layout
- Mobile-first design with dark theme support
