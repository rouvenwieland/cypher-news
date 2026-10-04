// content.js — Alle Folientexte, Sprechtexte und Code-Ausschnitte als Daten
// Jaro kann hier leicht Inhalte anpassen ohne Code zu ändern.

const SLIDES = [
  // ── Folie 1: Titel ──
  {
    id: "title",
    speaker: "jaro",
    title: "CYPHER NEWS",
    subtitle: "DAILY DROP",
    extra: "Hacktoberfest Hack Day Berlin · 4. Oktober 2026",
    tagline: "Gebaut in 4 Stunden von einem KI-Team",
    html: function () {
      return `<div class="slide-title-cover">
        <h1 class="glitch-title" data-text="CYPHER NEWS">CYPHER NEWS</h1>
        <p class="subtitle-drop">DAILY DROP</p>
        <p class="event-info">Hacktoberfest Hack Day Berlin · 4. Oktober 2026</p>
        <p class="tagline">Gebaut in 4 Stunden von einem KI-Team</p>
      </div>`;
    }
  },

  // ── Folie 2: Problem ──
  {
    id: "problem",
    speaker: "timo",
    title: "Das Problem",
    html: function () {
      return `<div class="slide-problem">
        <h2 class="slide-heading">Kennst du das?</h2>
        <ul class="problem-list">
          <li><span class="icon-scroll">📱</span>Du scrollst 45 Minuten durch Instagram-Stories und hast nichts behalten.</li>
          <li><span class="icon-fomo">😰</span>FOMO: Das Konzert war gestern. Das Giveaway endete vor 2 Stunden.</li>
          <li><span class="icon-time">⏳</span>5 Apps, 200 Feeds — aber die eine wichtige Info fehlt.</li>
          <li><span class="icon-miss">💔</span>Drops, Konzerte, Tickets — verpasst, weil du's nicht wusstest.</li>
        </ul>
        <div class="stat-box">
          <span class="stat-big">2.5h</span>
          <span class="stat-label">tägliche Screen-Time für Social Feeds</span>
        </div>
      </div>`;
    }
  },

  // ── Folie 3: Lösung ──
  {
    id: "solution",
    speaker: "timo",
    title: "Die Lösung",
    html: function () {
      return `<div class="slide-solution">
        <h2 class="slide-heading">Ein Drop pro Tag. Alles, was zählt.</h2>
        <div class="solution-cards">
          <div class="sol-card"><span class="sol-num">1</span> Verbinde deine Konten</div>
          <div class="sol-card"><span class="sol-num">2</span> Schreib, was dich interessiert</div>
          <div class="sol-card"><span class="sol-num">3</span> KI scannt Stories, Posts & News</div>
          <div class="sol-card"><span class="sol-num">4</span> Ein Drop. Kein Scrollen. Kein Verpassen.</div>
        </div>
        <p class="solution-punch">Deine Timeline, kuratiert von offener KI — in unter 15 Sekunden.</p>
      </div>`;
    }
  },

  // ── Folie 4: Die App ──
  {
    id: "app",
    speaker: "ran",
    title: "Die App",
    html: function () {
      return `<div class="slide-app">
        <h2 class="slide-heading">Cypher News im Hands-On</h2>
        <div class="phone-mockup">
          <div class="phone-frame">
            <div class="phone-notch"></div>
            <div class="phone-screen">
              <div class="mock-header">CYPHER NEWS <span class="mock-badge">HEUTE</span></div>
              <div class="mock-card card-orange">
                <span class="mock-cat">Konzerte</span>
                <strong>Freiluftkonzert im Mauerpark</strong>
                <small>Heute 19:00 · Eintritt frei</small>
              </div>
              <div class="mock-card card-green">
                <span class="mock-cat">Giveaways</span>
                <strong>SNEAKRS Raffle: Travis Scott x Nike</strong>
                <small>Noch 3 Stunden</small>
              </div>
              <div class="mock-card card-pink">
                <span class="mock-cat">Drops</span>
                <strong>Palace Skateboards Secret Drop</strong>
                <small>Samstag · Berlin Store</small>
              </div>
              <div class="mock-card card-cyan">
                <span class="mock-cat">Tech</span>
                <strong>OpenAI leak: Verse 2 Bildmodell</strong>
                <small>Open Source · Apache 2.0</small>
              </div>
            </div>
          </div>
        </div>
      </div>`;
    }
  },

  // ── Folie 5: So funktioniert's ──
  {
    id: "architecture",
    speaker: "ran",
    title: "So funktioniert's",
    html: function () {
      return `<div class="slide-arch">
        <h2 class="slide-heading">Architektur-Diagramm</h2>
        <div class="arch-diagram">
          <svg viewBox="0 0 900 340" class="arch-svg">
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#ff6a1a"/>
              </marker>
              <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff6a1a"/>
                <stop offset="100%" stop-color="#39ff14"/>
              </linearGradient>
            </defs>
            <!-- Box 1: Konten -->
            <rect x="10" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#ff6a1a" stroke-width="2"/>
            <text x="80" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">📱 Konten</text>
            <text x="80" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Instagram · TikTok</text>
            <text x="80" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">YouTube · Reddit</text>
            <!-- Box 2: socialfetch -->
            <rect x="220" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#ff6a1a" stroke-width="2"/>
            <text x="290" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">🔄 socialfetch</text>
            <text x="290" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Sessions · Stories</text>
            <text x="290" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Posts · Reels</text>
            <!-- Box 3: n8n -->
            <rect x="430" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#e03a2b" stroke-width="2"/>
            <text x="500" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">⚡ n8n</text>
            <text x="500" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Orchestrator</text>
            <text x="500" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">RSS · Plan · Vision</text>
            <!-- Box 4: KI-Modelle -->
            <rect x="640" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#39ff14" stroke-width="2"/>
            <text x="710" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">🧠 KI-Modelle</text>
            <text x="710" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Vision · Text</text>
            <text x="710" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Routing</text>
            <!-- Box 5: Drop -->
            <rect x="640" y="230" width="140" height="60" rx="8" fill="#201710" stroke="#39ff14" stroke-width="2"/>
            <text x="710" y="265" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">📬 DEIN DROP</text>
            <!-- Arrows -->
            <line x1="150" y1="160" x2="218" y2="160" stroke="url(#flowGrad)" stroke-width="2" marker-end="url(#arrowhead)"/>
            <line x1="360" y1="160" x2="428" y2="160" stroke="url(#flowGrad)" stroke-width="2" marker-end="url(#arrowhead)"/>
            <line x1="570" y1="160" x2="638" y2="160" stroke="url(#flowGrad)" stroke-width="2" marker-end="url(#arrowhead)"/>
            <line x1="710" y1="200" x2="710" y2="228" stroke="#39ff14" stroke-width="2" marker-end="url(#arrowhead)"/>
            <!-- Labels -->
            <text x="185" y="235" text-anchor="middle" fill="#b9a78f" font-family="PressStart2P" font-size="7">Stories+Posts</text>
            <text x="395" y="235" text-anchor="middle" fill="#b9a78f" font-family="PressStart2P" font-size="7">Rohdaten</text>
            <text x="605" y="235" text-anchor="middle" fill="#b9a78f" font-family="PressStart2P" font-size="7">Texte+Bilder</text>
          </svg>
        </div>
        <p class="arch-note">Konten verbinden → socialfetch scraped → n8n orchestriert → KI wertet aus → Drop aufs Handy</p>
      </div>`;
    }
  },

  // ── Folie 6: n8n erklärt ──
  {
    id: "n8n",
    speaker: "ran",
    title: "n8n — unser KI-Orchestrator",
    html: function () {
      const nodes = [
        { name: "Webhook", desc: "Empfängt POST von der App (Themen, Konten)", pos: "col1" },
        { name: "Plan", desc: "Baut RSS-Feeds aus Themen & Quellen", pos: "col1" },
        { name: "RSS Read", desc: "Liest 10+ Quellen parallel ein", pos: "col1" },
        { name: "Collect", desc: "Sammelt, filtert, dedupliziert bis zu 34 Items", pos: "col2" },
        { name: "Vision", desc: "Wertet bis zu 6 Bilder mit Vision-KI aus", pos: "col2" },
        { name: "Writer Prompt", desc: "Erstellt den Prompt für das Text-Modell", pos: "col2" },
        { name: "Writer", desc: "Erzeugt den Newsletter via OpenRouter", pos: "col3" },
        { name: "Router", desc: "Wechselt Modell bei Fehler — 3-stufiges Fallback", pos: "col3" },
        { name: "Parse", desc: "Parst JSON, baut Items, fügt Bilder ein", pos: "col3" },
        { name: "Respond", desc: "Sendet JSON-Antwort zurück an die App", pos: "col4" }
      ];
      let html = `<div class="slide-n8n"><h2 class="slide-heading">Der n8n-Workflow</h2><p class="n8n-sub">10 Knoten — n8n ist unser KI-Provider und Orchestrator</p><div class="n8n-flow">`;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        html += `<div class="n8n-node ${n.pos}" style="animation-delay:${i * 0.15}s">
          <div class="n8n-node-dot"></div>
          <span class="n8n-node-num">${String(i + 1).padStart(2, '0')}</span>
          <span class="n8n-node-name">${n.name}</span>
          <span class="n8n-node-desc">${n.desc}</span>
        </div>`;
      }
      html += `</div><p class="n8n-total">n8n/workflow.json · executionTimeout: 150s · Lizenz: Sustainable Use</p></div>`;
      return html;
    }
  },

  // ── Folie 7: Social Connectoren ──
  {
    id: "social",
    speaker: "jaro",
    title: "Social Connectoren",
    html: function () {
      return `<div class="slide-social">
        <h2 class="slide-heading">Deine Konten, deine Stories</h2>
        <div class="platform-grid">
          <div class="plat-card"><span class="plat-icon">📸</span><strong>Instagram</strong><small>Posts · Stories · Reels via instaloader</small></div>
          <div class="plat-card"><span class="plat-icon">🎵</span><strong>TikTok</strong><small>Videos & Beschreibungen via yt-dlp</small></div>
          <div class="plat-card"><span class="plat-icon">▶️</span><strong>YouTube</strong><small>Kanal-RSS & Video-Details</small></div>
          <div class="plat-card"><span class="plat-icon">🤖</span><strong>Reddit</strong><small>Top Posts via /r/.rss</small></div>
        </div>
        <div class="social-details">
          <div class="social-point"><span class="dot-ok"></span> Login lokal — Zugangsdaten bleiben auf deinem Gerät</div>
          <div class="social-point"><span class="dot-ok"></span> Account-Auswahl: Wähle, wem du folgst</div>
          <div class="social-point"><span class="dot-ok"></span> Stories, Posts & Reels — alles in deinem Drop</div>
        </div>
        <div class="social-warning">
          ⚠️ Ehrlich: Instagram-Scraping verstößt gegen Nutzungsbedingungen. Empfehlung: Zweitkonto verwenden. Produktionsreif mit offizieller Graph-API.
        </div>
      </div>`;
    }
  },

  // ── Folie 8: KI & Modell-Routing ──
  {
    id: "ki",
    speaker: "rufus",
    title: "KI & Modell-Routing",
    html: function () {
      return `<div class="slide-ki">
        <h2 class="slide-heading">Offene Modelle im Einsatz</h2>
        <div class="model-grid">
          <div class="model-card">
            <span class="model-badge">Text (Fast)</span>
            <strong>Nemotron 3 Super</strong>
            <code>nvidia/nemotron-3-super-120b-a12b:free</code>
            <small>Apache 2.0 · ~6s</small>
          </div>
          <div class="model-card">
            <span class="model-badge">Text (High)</span>
            <strong>Nemotron 3 Ultra</strong>
            <code>nvidia/nemotron-3-ultra-550b-a55b:free</code>
            <small>Apache 2.0 · ~20s</small>
          </div>
          <div class="model-card">
            <span class="model-badge">Vision</span>
            <strong>Qwen 3.8 27B</strong>
            <code>qwen/qwen3.8-27b:free</code>
            <small>Apache 2.0 · liest Bilder</small>
          </div>
          <div class="model-card">
            <span class="model-badge">Fallback</span>
            <strong>DeepSeek V4 Pro</strong>
            <code>deepseek/deepseek-v4-pro</code>
            <small>Open Weights · billig</small>
          </div>
        </div>
        <div class="routing-chain">
          <span class="chain-label">Ausweichkette:</span>
          <span class="chain-step">Nemotron Super</span><span class="chain-arrow">→</span>
          <span class="chain-step">Nemotron Ultra</span><span class="chain-arrow">→</span>
          <span class="chain-step">DeepSeek V4</span><span class="chain-arrow">→</span>
          <span class="chain-step fallback">Regelbasierter Fallback</span>
        </div>
        <p class="ki-why">Warum offen? Keine Abhängigkeit von einem Anbieter. Nachvollziehbar. Keine Daten an proprietäre APIs.</p>
      </div>`;
    }
  },

  // ── Folie 9: Code-Tour ──
  {
    id: "code",
    speaker: "ran",
    title: "Code-Tour",
    html: function () {
      const snippets = CODE_SNIPPETS;
      let html = `<div class="slide-code"><h2 class="slide-heading">Ein Blick in den Code</h2><div class="code-cards">`;
      for (const s of snippets) {
        html += `<div class="code-card">
          <div class="code-card-header"><span class="code-file">${s.file}</span><span class="code-label">${s.label}</span></div>
          <pre class="code-block"><code>${s.code}</code></pre>
          <p class="code-explain">${s.explain}</p>
        </div>`;
      }
      html += `</div></div>`;
      return html;
    }
  },

  // ── Folie 10: Das Team ──
  {
    id: "team",
    speaker: "jaro",
    title: "Das Team",
    html: function () {
      const members = [
        { name: "Timio", role: "Planner", emoji: "🧠" },
        { name: "Ran", role: "Builder", emoji: "⚒️" },
        { name: "Edgar", role: "Tester", emoji: "🧪" },
        { name: "Jaro", role: "Presenter", emoji: "🎤" },
        { name: "Rufus", role: "CFO", emoji: "💰" },
      ];
      let html = `<div class="slide-team">
        <h2 class="slide-heading">Wer hat's gebaut?</h2>
        <p class="team-intro">Ein Kollektiv aus 5 KI-Agenten — koordiniert über Paperclip</p>
        <div class="team-grid">`;
      for (const m of members) {
        html += `<div class="team-card">
          <canvas class="team-avatar-canvas" data-agent="${m.name.toLowerCase()}" width="64" height="64"></canvas>
          <strong>${m.name} ${m.emoji}</strong>
          <span class="team-role">${m.role}</span>
        </div>`;
      }
      html += `<div class="team-card cto">
          <canvas class="team-avatar-canvas" data-agent="rouven" width="64" height="64"></canvas>
          <strong>Rouven 🚀</strong>
          <span class="team-role">CTO & Board</span>
        </div>`;
      html += `</div>
        <div class="team-stats">
          <span class="stat-item"><strong>45</strong> Commits</span>
          <span class="stat-item"><strong>4.5</strong> Stunden</span>
          <span class="stat-item"><strong>5</strong> Agenten</span>
          <span class="stat-item"><strong>1</strong> Hackathon</span>
        </div>
      </div>`;
      return html;
    }
  },

  // ── Folie 11: Demo & Ausblick ──
  {
    id: "outro",
    speaker: "jaro",
    title: "Demo & Ausblick",
    html: function () {
      return `<div class="slide-outro">
        <h2 class="slide-heading">Lasst es uns zeigen!</h2>
        <div class="outro-demo">
          <div class="outro-qr">
            <div class="qr-placeholder">
              <span>Cypher News</span>
              <small>Daily Drop</small>
              <code>127.0.0.1:5000</code>
            </div>
          </div>
          <p class="outro-link">→ Live-Demo auf localhost:5000 ←</p>
        </div>
        <div class="outro-next">
          <h3>Nächste Schritte</h3>
          <ul>
            <li><span class="dot-green"></span> Offizielle Graph-API für Instagram/TikTok</li>
            <li><span class="dot-green"></span> Push-Benachrichtigungen per Service Worker</li>
            <li><span class="dot-green"></span> Mehr Plattformen: X, Bluesky, Discord</li>
            <li><span class="dot-green"></span> E-Mail-Zustellung als Alternative</li>
          </ul>
        </div>
        <p class="outro-thanks">Danke! Fragen?</p>
      </div>`;
    }
  }
];

// ── Sprechtexte pro Folie ──
const SPEAKER_TEXTS = {
  title: "Willkommen zu CYPHER NEWS! Wir sind ein Team aus fünf KI-Agenten und haben in 4,5 Stunden einen KI-Newsletter gebaut, der deine Timeline zusammenfasst. Kein Scrollen, kein Verpassen. Legen wir los!",
  problem: "Im Schnitt scrollen Leute 2,5 Stunden am Tag durch Instagram, TikTok und YouTube. Konzerte? Verpasst. Giveaways? Vorbei. Drops? Ausverkauft. Das ist das Problem, das wir lösen.",
  solution: "Cypher News macht genau einen Drop pro Tag. Du verbindest deine Konten, sagst was dich interessiert — und eine offene KI fasst alles Wichtige zusammen. In 15 Sekunden bist du up to date.",
  app: "So sieht's aus: eine PWA mit Matrix-Regen-Hintergrund, Story-Karten, jede mit Kategorie-Farbe. Oben ein Ticker mit Schlagzeilen. Alles im Retro-Pixel-Look — cool genug, dass man's installieren will.",
  architecture: "Der Datenfluss: Konten verbinden → socialfetch scraped Stories und Posts → n8n orchestriert alles → KI wertet Text und Bilder aus → der Drop landet auf dem Handy. Fünf Stationen, eine Pipeline.",
  n8n: "Zehn Knoten im n8n-Workflow: Webhook, Plan, RSS, Collect, Vision, Writer Prompt, Writer, Router, Parse, Respond. n8n ist unser KI-Provider — es steuert die Modelle, macht das Routing und fängt Fehler ab.",
  social: "Instagram, TikTok, YouTube, Reddit — alle vier Plattformen sind angebunden. Stories, Posts, Reels, Videos. Der Login bleibt lokal auf deinem Gerät. Fairer Hinweis: Instagram ist Prototyp, produktiv braucht's die Graph-API.",
  ki: "Vier offene Modelle im Einsatz: Nemotron Super und Ultra für Text, Qwen 3.8 für Bildauswertung, DeepSeek V4 als Fallback. Alle über OpenRouter. Warum offen? Unabhängig vom Anbieter, nachvollziehbar, keine Daten an geschlossene APIs.",
  code: "Drei Dateien, die zusammenarbeiten: app.py ist der Flask-Server mit 152 Zeilen, workflow.json ist der n8n-Graph mit Routing und Vision, und demo_social.json enthält 12 realistische Beispieldaten für die Demo.",
  team: "Timio hat den Plan gemacht, Ran hat gebaut, ich — Edgar — habe getestet, Jaro präsentiert und Rufus behält die Kosten im Blick. Zusammen mit Rouven als CTO: 5 KI-Agenten, 45 Commits, 4,5 Stunden.",
  outro: "Jetzt zeigen wir's live! Nächste Schritte: offizielle APIs, Push-Benachrichtigungen, mehr Plattformen. Die App läuft auf localhost:5000 — Matrix-Regen, Ticker, Drop-Button, alles da. Fragen?"
};

// ── Code-Ausschnitte ──
const CODE_SNIPPETS = [
  {
    file: "app.py",
    label: "API-Generate mit n8n + Fallback",
    code: `@app.route('/api/generate', methods=['POST'])
def api_generate():
    body = request.get_json(silent=True) or {}
    preferences = body.get('preferences', '')
    sources = body.get('sources', [])
    accounts = body.get('accounts', {})

    payload = {"preferences": preferences,
               "sources": sources,
               "accounts": accounts}

    try:
        resp = requests.post(N8N_WEBHOOK_URL,
            json=payload, timeout=22)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify(data)
    except Exception:
        pass

    try:
        return jsonify(fallback_from_file())
    except Exception:
        return jsonify(mock_response())`,
    explain: "Der /api/generate-Endpoint ruft n8n auf (22s Timeout). Bei Fehler lädt er sample_newsletter.json vom Server. Wenn auch das fehlschlägt, gibt's eingebaute Mock-Daten. 3-stufig, nie leer."
  },
  {
    file: "n8n/workflow.json",
    label: "Modell-Routing mit Ausweichkette",
    code: `// Router-Knoten: Modell-Ausweichkette
if (!valid(text)) {
  const chain = [
    used === SUPER ? ULTRA : SUPER,
    $env.MODEL_PAID || 'deepseek/deepseek-v4-pro'
  ];
  for (const model of chain) {
    const r = await httpRequest({
      url: 'https://openrouter.ai/api/v1/...',
      body: { model, max_tokens: 4000 }
    });
    if (valid(r.choices[0].message.content)) {
      text = r.choices[0].message.content;
      used = model;
      break;
    }
  }
}`,
    explain: "Der Router-Knoten prüft die Antwort vom Writer. Wenn sie ungültig ist, wechselt er automatisch durch die Ausweichkette: Nemotron Super ↔ Ultra → DeepSeek V4. Nie weniger als ein Ergebnis."
  },
  {
    file: "data/demo_social.json",
    label: "Demo-Daten mit Social Items",
    code: `{
  "_demo": true,
  "_note": "DEMO DATA – realistic but fabricated",
  "social_items": [
    {
      "platform": "Instagram",
      "account": "berghain_ost",
      "kind": "story",
      "text": "FLINTA* night this Friday.
              Lineup drops tomorrow.",
      "taken_at": "2026-10-03T18:30:00Z"
    },
    {
      "platform": "TikTok",
      "account": "@streetweardrops",
      "kind": "reel",
      "text": "Palace Skateboards secret
              drop Berlin store."
    }
    // ... 10 weitere Einträge
  ]
}`,
    explain: "12 realistische, klar markierte Demo-Daten: Konzerte, Giveaways, Drops und Tech aus Berlin. Immer da — auch ohne Internet und ohne n8n. Perfekt für die Bühnen-Demo."
  }
];

// ── Agent-Definitionen ──
const AGENTS = {
  timo: { name: "Timio", role: "Planner", emoji: "🧠" },
  ran: { name: "Ran", role: "Builder", emoji: "⚒️" },
  edgar: { name: "Edgar", role: "Tester", emoji: "🧪" },
  jaro: { name: "Jaro", role: "Presenter", emoji: "🎤" },
  rufus: { name: "Rufus", role: "CFO", emoji: "💰" }
};

// Pixel-Avatar-Generator (16×16 Roboter mit Augen)
function drawPixelAvatar(canvas, agentId) {
  const ctx = canvas.getContext('2d');
  const colors = {
    timo: { body: '#4a90d9', eye: '#c0e0ff' },
    ran: { body: '#ff6a1a', eye: '#ffccaa' },
    edgar: { body: '#39ff14', eye: '#ccffcc' },
    jaro: { body: '#b44bc0', eye: '#e8c0ff' },
    rufus: { body: '#ffc21a', eye: '#fff8cc' },
    rouven: { body: '#e03a2b', eye: '#ffccbb' }
  };
  const c = colors[agentId] || colors['timo'];
  const size = canvas.width;
  const pixel = Math.floor(size / 16);
  ctx.clearRect(0, 0, size, size);

  // Head (6x7)
  ctx.fillStyle = c.body;
  for (let y = 1; y < 8; y++)
    for (let x = 4; x < 12; x++) ctx.fillRect(x * pixel, y * pixel, pixel, pixel);

  // Antenna
  ctx.fillRect(7 * pixel, 0, 2 * pixel, 2 * pixel);

  // Eyes (white then pupil)
  ctx.fillStyle = c.eye;
  ctx.fillRect(5 * pixel, 3 * pixel, 2 * pixel, 2 * pixel);
  ctx.fillRect(9 * pixel, 3 * pixel, 2 * pixel, 2 * pixel);

  // Pupils (dark)
  ctx.fillStyle = '#130e0b';
  ctx.fillRect(6 * pixel, 3.5 * pixel, pixel * 0.6, pixel * 0.6);
  ctx.fillRect(10 * pixel, 3.5 * pixel, pixel * 0.6, pixel * 0.6);

  // Mouth
  ctx.fillRect(6 * pixel, 6 * pixel, 4 * pixel, 1 * pixel);

  // Body (6x6)
  for (let y = 8; y < 14; y++)
    for (let x = 4; x < 12; x++) ctx.fillRect(x * pixel, y * pixel, pixel, pixel);

  // Arms
  ctx.fillRect(2 * pixel, 9 * pixel, 2 * pixel, 3 * pixel);
  ctx.fillRect(12 * pixel, 9 * pixel, 2 * pixel, 3 * pixel);

  // Legs
  ctx.fillRect(5 * pixel, 14 * pixel, 2 * pixel, 2 * pixel);
  ctx.fillRect(9 * pixel, 14 * pixel, 2 * pixel, 2 * pixel);
}