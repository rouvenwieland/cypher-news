// content.js — Slide content, speaker texts, code snippets (all English)
// Paired with script.js for spoken audio and manifest.js for timing

var SLIDES = [
  // s01: Title
  {
    id: "s01",
    speaker: "jaro",
    title: "CYPHER NEWS",
    subtitle: "DAILY DROP",
    extra: "Hacktoberfest Hack Day Berlin \u00b7 October 4, 2026",
    tagline: "Built in 4 hours by an AI team",
    html: function () {
      return '<div class="slide-title-cover">'
        + '<h1 class="glitch-title" data-text="CYPHER NEWS">CYPHER NEWS</h1>'
        + '<p class="subtitle-drop">DAILY DROP</p>'
        + '<p class="event-info">Hacktoberfest Hack Day Berlin &middot; October 4, 2026</p>'
        + '<p class="tagline">Built in 4 hours by an AI team</p>'
        + '</div>';
    }
  },

  // s02: Problem
  {
    id: "s02",
    speaker: "jaro",
    title: "The Problem",
    html: function () {
      return '<div class="slide-problem">'
        + '<h2 class="slide-heading">Sound familiar?</h2>'
        + '<ul class="problem-list">'
        + '<li><span class="icon-scroll">📱</span>You scroll 45 minutes through Instagram stories and remember nothing.</li>'
        + '<li><span class="icon-fomo">😰</span>FOMO: The concert was yesterday. The giveaway ended 2 hours ago.</li>'
        + '<li><span class="icon-time">⏳</span>Five apps, two hundred feeds \u2014 the one thing you need is missing.</li>'
        + '<li><span class="icon-miss">💔</span>Drops, gigs, tickets \u2014 gone because you never saw them.</li>'
        + '</ul>'
        + '<div class="stat-box">'
        + '<span class="stat-big">2.5h</span>'
        + '<span class="stat-label">daily screen time on social feeds</span>'
        + '</div>'
        + '</div>';
    }
  },

  // s03: Solution
  {
    id: "s03",
    speaker: "ran",
    title: "The Solution",
    html: function () {
      return '<div class="slide-solution">'
        + '<h2 class="slide-heading">One Drop a Day. Everything That Matters.</h2>'
        + '<div class="solution-cards">'
        + '<div class="sol-card"><span class="sol-num">1</span> Connect your accounts</div>'
        + '<div class="sol-card"><span class="sol-num">2</span> Write what you care about</div>'
        + '<div class="sol-card"><span class="sol-num">3</span> AI scans stories, posts &amp; news</div>'
        + '<div class="sol-card"><span class="sol-num">4</span> One drop. No scrolling. No missing out.</div>'
        + '</div>'
        + '<p class="solution-punch">Your timeline, curated by open AI \u2014 in under 15 seconds.</p>'
        + '</div>';
    }
  },

  // s04: The App
  {
    id: "s04",
    speaker: "ran",
    title: "The App",
    html: function () {
      return '<div class="slide-app">'
        + '<h2 class="slide-heading">Cypher News Hands-On</h2>'
        + '<div class="phone-mockup">'
        + '<div class="phone-frame">'
        + '<div class="phone-notch"></div>'
        + '<div class="phone-screen">'
        + '<div class="mock-header">CYPHER NEWS <span class="mock-badge">TODAY</span></div>'
        + '<div class="mock-card card-orange"><span class="mock-cat">Concerts</span><strong>Open Air at Mauerpark</strong><small>Today 19:00 &middot; Free entry</small></div>'
        + '<div class="mock-card card-green"><span class="mock-cat">Giveaways</span><strong>SNEAKRS Raffle: Travis Scott x Nike</strong><small>3 hours left</small></div>'
        + '<div class="mock-card card-pink"><span class="mock-cat">Drops</span><strong>Palace Skateboards Secret Drop</strong><small>Saturday &middot; Berlin Store</small></div>'
        + '<div class="mock-card card-cyan"><span class="mock-cat">Tech</span><strong>OpenAI Leak: Verse 2 Image Model</strong><small>Open Source &middot; Apache 2.0</small></div>'
        + '</div></div></div>'
        + '</div>';
    }
  },

  // s05: Architecture
  {
    id: "s05",
    speaker: "ran",
    title: "How It Works",
    html: function () {
      return '<div class="slide-arch">'
        + '<h2 class="slide-heading">Architecture Diagram</h2>'
        + '<div class="arch-diagram">'
        + '<svg viewBox="0 0 900 340" class="arch-svg">'
        + '<defs>'
        + '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#ff6a1a"/></marker>'
        + '<linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#ff6a1a"/><stop offset="100%" stop-color="#39ff14"/></linearGradient>'
        + '</defs>'
        + '<rect x="10" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#ff6a1a" stroke-width="2"/>'
        + '<text x="80" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">📱 Accounts</text>'
        + '<text x="80" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Instagram · TikTok</text>'
        + '<text x="80" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">YouTube · Reddit</text>'
        + '<rect x="220" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#ff6a1a" stroke-width="2"/>'
        + '<text x="290" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">🔄 socialfetch</text>'
        + '<text x="290" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Sessions · Stories</text>'
        + '<text x="290" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Posts · Reels</text>'
        + '<rect x="430" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#e03a2b" stroke-width="2"/>'
        + '<text x="500" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">⚡ n8n</text>'
        + '<text x="500" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Orchestrator</text>'
        + '<text x="500" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">RSS · Plan · Vision</text>'
        + '<rect x="640" y="120" width="140" height="80" rx="8" fill="#201710" stroke="#39ff14" stroke-width="2"/>'
        + '<text x="710" y="155" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">🧠 AI Models</text>'
        + '<text x="710" y="180" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Vision · Text</text>'
        + '<text x="710" y="193" text-anchor="middle" fill="#b9a78f" font-family="VT323" font-size="11">Routing</text>'
        + '<rect x="640" y="230" width="140" height="60" rx="8" fill="#201710" stroke="#39ff14" stroke-width="2"/>'
        + '<text x="710" y="265" text-anchor="middle" fill="#ffc21a" font-family="VT323" font-size="16">📬 YOUR DROP</text>'
        + '<line x1="150" y1="160" x2="218" y2="160" stroke="url(#flowGrad)" stroke-width="2" marker-end="url(#arrowhead)"/>'
        + '<line x1="360" y1="160" x2="428" y2="160" stroke="url(#flowGrad)" stroke-width="2" marker-end="url(#arrowhead)"/>'
        + '<line x1="570" y1="160" x2="638" y2="160" stroke="url(#flowGrad)" stroke-width="2" marker-end="url(#arrowhead)"/>'
        + '<line x1="710" y1="200" x2="710" y2="228" stroke="#39ff14" stroke-width="2" marker-end="url(#arrowhead)"/>'
        + '<text x="185" y="235" text-anchor="middle" fill="#b9a78f" font-family="PressStart2P" font-size="7">Stories+Posts</text>'
        + '<text x="395" y="235" text-anchor="middle" fill="#b9a78f" font-family="PressStart2P" font-size="7">Raw data</text>'
        + '<text x="605" y="235" text-anchor="middle" fill="#b9a78f" font-family="PressStart2P" font-size="7">Text+Images</text>'
        + '</svg>'
        + '</div>'
        + '<p class="arch-note">Connect accounts \u2192 socialfetch scrapes \u2192 n8n orchestrates \u2192 AI evaluates \u2192 Drop on your phone</p>'
        + '</div>';
    }
  },

  // s06: n8n explained
  {
    id: "s06",
    speaker: "ran",
    title: "n8n \u2014 Our AI Orchestrator",
    html: function () {
      var nodes = [
        { name: "Webhook", desc: "Receives POST from the app (preferences, accounts)", pos: "col1" },
        { name: "Plan", desc: "Builds RSS feeds from topics &amp; sources", pos: "col1" },
        { name: "RSS Read", desc: "Reads 10+ sources in parallel", pos: "col1" },
        { name: "Collect", desc: "Collects, filters, deduplicates up to 34 items", pos: "col2" },
        { name: "Vision", desc: "Analyzes up to 6 images with vision AI", pos: "col2" },
        { name: "Writer Prompt", desc: "Builds the prompt for the text model", pos: "col2" },
        { name: "Writer", desc: "Generates the newsletter via OpenRouter", pos: "col3" },
        { name: "Router", desc: "Switches model on error \u2014 3-stage failover", pos: "col3" },
        { name: "Parse", desc: "Parses JSON, builds items, inserts images", pos: "col3" },
        { name: "Respond", desc: "Sends JSON response back to the app", pos: "col4" }
      ];
      var html = '<div class="slide-n8n"><h2 class="slide-heading">The n8n Workflow</h2><p class="n8n-sub">10 nodes \u2014 n8n is our AI provider and orchestrator</p><div class="n8n-flow">';
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        html += '<div class="n8n-node ' + n.pos + '" style="animation-delay:' + (i * 0.15) + 's">'
          + '<div class="n8n-node-dot"></div>'
          + '<span class="n8n-node-num">' + String(i + 1).padStart(2, '0') + '</span>'
          + '<span class="n8n-node-name">' + n.name + '</span>'
          + '<span class="n8n-node-desc">' + n.desc + '</span>'
          + '</div>';
      }
      html += '</div><p class="n8n-total">n8n/workflow.json &middot; executionTimeout: 150s &middot; License: Sustainable Use</p></div>';
      return html;
    }
  },

  // s07: Social Connectors
  {
    id: "s07",
    speaker: "jaro",
    title: "Social Connectors",
    html: function () {
      return '<div class="slide-social">'
        + '<h2 class="slide-heading">Your Accounts, Your Stories</h2>'
        + '<div class="platform-grid">'
        + '<div class="plat-card"><span class="plat-icon">📸</span><strong>Instagram</strong><small>Posts &middot; Stories &middot; Reels via instaloader</small></div>'
        + '<div class="plat-card"><span class="plat-icon">🎵</span><strong>TikTok</strong><small>Videos &amp; descriptions via yt-dlp</small></div>'
        + '<div class="plat-card"><span class="plat-icon">▶️</span><strong>YouTube</strong><small>Channel RSS &amp; video details</small></div>'
        + '<div class="plat-card"><span class="plat-icon">🤖</span><strong>Reddit</strong><small>Top posts via /r/.rss</small></div>'
        + '</div>'
        + '<div class="social-details">'
        + '<div class="social-point"><span class="dot-ok"></span> Login is local \u2014 credentials stay on your device</div>'
        + '<div class="social-point"><span class="dot-ok"></span> Account picker: choose who you follow</div>'
        + '<div class="social-point"><span class="dot-ok"></span> Stories, posts &amp; reels \u2014 all in your drop</div>'
        + '</div>'
        + '<div class="social-warning">'
        + '\u26a0\ufe0f Honest: Instagram scraping violates ToS. Recommendation: use a burner account. Production-ready with official Graph API.'
        + '</div>'
        + '</div>';
    }
  },

  // s08: AI & Model Routing
  {
    id: "s08",
    speaker: "rufus",
    title: "AI &amp; Model Routing",
    html: function () {
      return '<div class="slide-ki">'
        + '<h2 class="slide-heading">Open Models in Action</h2>'
        + '<div class="model-grid">'
        + '<div class="model-card"><span class="model-badge">Text (Fast)</span><strong>Nemotron 3 Super</strong><code>nvidia/nemotron-3-super-120b-a12b:free</code><small>Apache 2.0 &middot; ~6s</small></div>'
        + '<div class="model-card"><span class="model-badge">Text (High)</span><strong>Nemotron 3 Ultra</strong><code>nvidia/nemotron-3-ultra-550b-a55b:free</code><small>Apache 2.0 &middot; ~20s</small></div>'
        + '<div class="model-card"><span class="model-badge">Vision</span><strong>Qwen 3.8 27B</strong><code>qwen/qwen3.8-27b:free</code><small>Apache 2.0 &middot; reads images</small></div>'
        + '<div class="model-card"><span class="model-badge">Fallback</span><strong>DeepSeek V4 Pro</strong><code>deepseek/deepseek-v4-pro</code><small>Open Weights &middot; cheap</small></div>'
        + '</div>'
        + '<div class="routing-chain">'
        + '<span class="chain-label">Failover chain:</span>'
        + '<span class="chain-step">Nemotron Super</span><span class="chain-arrow">\u2192</span>'
        + '<span class="chain-step">Nemotron Ultra</span><span class="chain-arrow">\u2192</span>'
        + '<span class="chain-step">DeepSeek V4</span><span class="chain-arrow">\u2192</span>'
        + '<span class="chain-step fallback">Rule-based fallback</span>'
        + '</div>'
        + '<p class="ki-why">Why open? No single-vendor dependency. Fully auditable. No data sent to proprietary APIs.</p>'
        + '</div>';
    }
  },

  // s09: Code Tour
  {
    id: "s09",
    speaker: "ran",
    title: "Code Tour",
    html: function () {
      var snippets = CODE_SNIPPETS;
      var html = '<div class="slide-code"><h2 class="slide-heading">A Look at the Code</h2><div class="code-cards">';
      for (var _i = 0; _i < snippets.length; _i++) {
        var s = snippets[_i];
        html += '<div class="code-card">'
          + '<div class="code-card-header"><span class="code-file">' + s.file + '</span><span class="code-label">' + s.label + '</span></div>'
          + '<pre class="code-block"><code>' + s.code + '</code></pre>'
          + '<p class="code-explain">' + s.explain + '</p>'
          + '</div>';
      }
      html += '</div></div>';
      return html;
    }
  },

  // s10: The Team
  {
    id: "s10",
    speaker: "jaro",
    title: "The Team",
    html: function () {
      var members = [
        { name: "Timio", role: "Planner", emoji: "\ud83e\udde0" },
        { name: "Ran", role: "Builder", emoji: "\u2692\ufe0f" },
        { name: "Edgar", role: "Tester", emoji: "\ud83e\uddea" },
        { name: "Jaro", role: "Presenter", emoji: "\ud83c\udfa4" },
        { name: "Rufus", role: "CFO", emoji: "\ud83d\udcb0" }
      ];
      var html = '<div class="slide-team">'
        + '<h2 class="slide-heading">Who Built This?</h2>'
        + '<p class="team-intro">A collective of 5 AI agents \u2014 coordinated through Paperclip</p>'
        + '<div class="team-grid">';
      for (var _k = 0; _k < members.length; _k++) {
        var m = members[_k];
        html += '<div class="team-card">'
          + '<canvas class="team-avatar-canvas" data-agent="' + m.name.toLowerCase() + '" width="64" height="64"></canvas>'
          + '<strong>' + m.name + ' ' + m.emoji + '</strong>'
          + '<span class="team-role">' + m.role + '</span>'
          + '</div>';
      }
      html += '<div class="team-card cto">'
        + '<canvas class="team-avatar-canvas" data-agent="rouven" width="64" height="64"></canvas>'
        + '<strong>Rouven \ud83d\ude80</strong>'
        + '<span class="team-role">CTO &amp; Board</span>'
        + '</div>';
      html += '</div>'
        + '<div class="team-stats">'
        + '<span class="stat-item"><strong>45</strong> Commits</span>'
        + '<span class="stat-item"><strong>4.5</strong> Hours</span>'
        + '<span class="stat-item"><strong>5</strong> Agents</span>'
        + '<span class="stat-item"><strong>1</strong> Hackathon</span>'
        + '</div>'
        + '</div>';
      return html;
    }
  },

  // s11: Demo & Outlook
  {
    id: "s11",
    speaker: "jaro",
    title: "Demo &amp; Outlook",
    html: function () {
      return '<div class="slide-outro">'
        + '<h2 class="slide-heading">Let\u2019s See It Live!</h2>'
        + '<div class="outro-demo">'
        + '<div class="outro-qr">'
        + '<div class="qr-placeholder">'
        + '<span>Cypher News</span>'
        + '<small>Daily Drop</small>'
        + '<code>127.0.0.1:5000</code>'
        + '</div>'
        + '</div>'
        + '<p class="outro-link">\u2192 Live demo at localhost:5000 \u2190</p>'
        + '</div>'
        + '<div class="outro-next">'
        + '<h3>Next Steps</h3>'
        + '<ul>'
        + '<li><span class="dot-green"></span> Official Graph API for Instagram/TikTok</li>'
        + '<li><span class="dot-green"></span> Push notifications via Service Worker</li>'
        + '<li><span class="dot-green"></span> More platforms: X, Bluesky, Discord</li>'
        + '<li><span class="dot-green"></span> Email delivery as alternative</li>'
        + '</ul>'
        + '</div>'
        + '<p class="outro-thanks">Thank You! Questions?</p>'
        + '</div>';
    }
  }
];

// ── Code Snippets (English) ──
var CODE_SNIPPETS = [
  {
    file: "app.py",
    label: "API Generate with n8n + Fallback",
    code: '@app.route(\'/api/generate\', methods=[\'POST\'])\ndef api_generate():\n    body = request.get_json(silent=True) or {}\n    preferences = body.get(\'preferences\', \'\')\n    sources = body.get(\'sources\', [])\n    accounts = body.get(\'accounts\', {})\n\n    payload = {"preferences": preferences,\n               "sources": sources,\n               "accounts": accounts}\n\n    try:\n        resp = requests.post(N8N_WEBHOOK_URL,\n            json=payload, timeout=22)\n        if resp.status_code == 200:\n            data = resp.json()\n            return jsonify(data)\n    except Exception:\n        pass\n\n    try:\n        return jsonify(fallback_from_file())\n    except Exception:\n        return jsonify(mock_response())',
    explain: 'The /api/generate endpoint calls n8n (22s timeout). On failure it loads sample_newsletter.json. If that fails too, built-in mock data kicks in. Three-stage fallback, never empty.'
  },
  {
    file: "n8n/workflow.json",
    label: "Model Routing with Failover Chain",
    code: '// Router node: model failover chain\nif (!valid(text)) {\n  const chain = [\n    used === SUPER ? ULTRA : SUPER,\n    $env.MODEL_PAID || \'deepseek/deepseek-v4-pro\'\n  ];\n  for (const model of chain) {\n    const r = await httpRequest({\n      url: \'https://openrouter.ai/api/v1/...\',\n      body: { model, max_tokens: 4000 }\n    });\n    if (valid(r.choices[0].message.content)) {\n      text = r.choices[0].message.content;\n      used = model;\n      break;\n    }\n  }\n}',
    explain: 'The Router node checks the Writer response. If invalid, it automatically cycles through the failover chain: Nemotron Super \u2194 Ultra \u2192 DeepSeek V4. Never less than one result.'
  },
  {
    file: "data/demo_social.json",
    label: "Demo Data with Social Items",
    code: '{\n  "_demo": true,\n  "_note": "DEMO DATA \u2013 realistic but fabricated",\n  "social_items": [\n    {\n      "platform": "Instagram",\n      "account": "berghain_ost",\n      "kind": "story",\n      "text": "FLINTA* night this Friday.\n              Lineup drops tomorrow.",\n      "taken_at": "2026-10-03T18:30:00Z"\n    },\n    {\n      "platform": "TikTok",\n      "account": "@streetweardrops",\n      "kind": "reel",\n      "text": "Palace Skateboards secret\n              drop Berlin store."\n    }\n    // ... 10 more entries\n  ]\n}',
    explain: '12 realistic, clearly marked demo entries: concerts, giveaways, drops, and tech from Berlin. Always available \u2014 even without internet and without n8n. Perfect for the stage demo.'
  }
];

// ── Agent Definitions ──
var AGENTS = {
  timo: { name: "Timio", role: "Planner", emoji: "\ud83e\udde0" },
  ran: { name: "Ran", role: "Builder", emoji: "\u2692\ufe0f" },
  edgar: { name: "Edgar", role: "Tester", emoji: "\ud83e\uddea" },
  jaro: { name: "Jaro", role: "Presenter", emoji: "\ud83c\udfa4" },
  rufus: { name: "Rufus", role: "CFO", emoji: "\ud83d\udcb0" }
};