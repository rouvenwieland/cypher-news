#!/usr/bin/env python3
"""Erzeugt n8n/workflow.json (Cypher News - Daily Drop). Ausfuehren: python3 n8n/build_workflow.py"""
import json, os

PLAN_JS = r"""
const b = $input.first().json.body || $input.first().json;
const prefsText = String(b.preferences || '').trim();
const sources = Array.isArray(b.sources) ? b.sources : [];
const date = b.date || new Date().toISOString().slice(0,10);
const enc = encodeURIComponent;
let topics = prefsText.split(/[\n,;]+|\s+und\s+/i).map(s => s.trim()).filter(s => s.length > 2);
if (!topics.length) topics = ['Konzerte Berlin', 'Giveaways', 'Tech News', 'Trends'];
topics = [...new Set(topics)].slice(0, 5);
const feeds = [];
for (const t of topics) {
  feeds.push({ url: `https://news.google.com/rss/search?q=${enc(t + ' when:7d')}&hl=de&gl=DE&ceid=DE:de`, label: t });
}
for (const s of sources.slice(0, 6)) {
  const v = String(s).trim(); if (!v) continue;
  if (/^https?:\/\//i.test(v) && /(rss|feed|atom|\.xml)/i.test(v)) feeds.push({ url: v, label: v });
  else if (/reddit\.com\/r\/(\w+)/i.test(v)) feeds.push({ url: `https://www.reddit.com/r/${v.match(/r\/(\w+)/i)[1]}/top/.rss?t=week`, label: v });
  else feeds.push({ url: `https://www.bing.com/news/search?q=${enc(v.replace(/^@/, '') + ' ' + prefsText)}&format=rss&setlang=de`, label: v });
}
return feeds.slice(0, 9).map(f => ({ json: { url: f.url, label: f.label, prefs: prefsText, topics, date, sources } }));
"""

COLLECT_JS = r"""
const plan = $('Plan').first().json;
const seen = new Set(); const items = [];
for (const it of $input.all()) {
  const j = it.json; if (!j || !j.title || !j.link) continue;
  const key = String(j.title).toLowerCase().replace(/[^a-z0-9äöüß]+/g, ' ').slice(0, 60);
  if (seen.has(key)) continue; seen.add(key);
  let host = ''; try { host = new URL(j.link).hostname.replace(/^www\./, ''); } catch (e) {}
  const src = (j.title.match(/ - ([^-]{3,40})$/) || [])[1] || host || 'Web';
  items.push({ title: String(j.title).replace(/ - [^-]{3,40}$/, '').slice(0, 160), link: j.link, source: src,
               date: j.isoDate || j.pubDate || '', snippet: String(j.contentSnippet || j.content || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 220) });
}
items.sort((a, b) => String(b.date).localeCompare(String(a.date)));
const top = items.slice(0, 26);
const list = top.map((x, i) => `[${i}] ${x.title} | ${x.source} | ${String(x.date).slice(0, 10)} | ${x.snippet}`).join('\n');
const system = 'Du bist die Redaktion von CYPHER NEWS (DAILY DROP), einem personalisierten Tages-Newsletter. Antworte AUSSCHLIESSLICH mit gueltigem JSON, ohne Text davor oder danach.';
const user = `Wunsch des Nutzers: "${plan.prefs}"\nDatum: ${plan.date}\n\nRohmeldungen (Index | Titel | Quelle | Datum | Ausschnitt):\n${list}\n\nWaehle die 8 besten, zum Wunsch passenden, abwechslungsreichen Meldungen. Schreibe auf Deutsch, locker und praezise. Gib JSON in genau diesem Format zurueck:\n{"title":"kurze Schlagzeile des Tages","intro":"2 Saetze Einleitung","items":[{"idx":<Index aus der Liste>,"category":"Konzerte|Giveaways|Drops|Tech|Trends|News","title":"Titel","summary":"1-2 Saetze, was ist passiert und warum relevant","when":"z.B. Heute, Sa 12.10., diese Woche"}]}\nErfinde keine Fakten und keine Links; nutze nur die Meldungen.`;
return [{ json: { prefs: plan.prefs, date: plan.date, top, messages: [{ role: 'system', content: system }, { role: 'user', content: user }] } }];
"""

PARSE_JS = r"""
const col = $('Collect').first().json; const top = col.top || [];
const resp = $input.first().json;
let text = ''; try { text = resp.choices[0].message.content || ''; } catch (e) {}
let data = null;
try { const m = text.match(/\{[\s\S]*\}/); if (m) data = JSON.parse(m[0]); } catch (e) { data = null; }
const cats = { Konzerte: 1, Giveaways: 1, Drops: 1, Tech: 1, Trends: 1, News: 1 };
const guess = (t) => /konzert|live|tour|festival|club|dj/i.test(t) ? 'Konzerte' : /gewinn|verlos|giveaway/i.test(t) ? 'Giveaways' : /drop|release|kollektion|sneaker|streetwear|mode/i.test(t) ? 'Drops' : /ki|ai|tech|app|software|handy|chip|apple|google/i.test(t) ? 'Tech' : 'News';
let items = [];
if (data && Array.isArray(data.items)) {
  for (const x of data.items) {
    const src = top[Number(x.idx)] || null; if (!src) continue;
    items.push({ category: cats[x.category] ? x.category : guess(src.title), title: String(x.title || src.title).slice(0, 140),
      summary: String(x.summary || src.snippet || '').slice(0, 320), source: src.source, url: src.link, when: String(x.when || '').slice(0, 30) || 'aktuell' });
  }
}
const ai = items.length > 0;
if (!ai) items = top.slice(0, 8).map(s => ({ category: guess(s.title), title: s.title, summary: s.snippet || 'Mehr dazu in der Quelle.', source: s.source, url: s.link, when: String(s.date).slice(0, 10) || 'aktuell' }));
const out = { title: (data && data.title) || 'Dein Drop für heute', date: col.date, intro: (data && data.intro) || 'Frisch gescannt: das Wichtigste zu deinen Themen.',
  items, meta: { engine: 'n8n', model: ai ? 'openrouter' : 'fallback-ohne-ki', sources: top.length, debug: ai ? undefined : JSON.stringify(resp).slice(0, 400) } };
return [{ json: out }];
"""

def node(name, type_, ver, pos, params, **kw):
    n = {"parameters": params, "id": name.lower().replace(' ', '-'), "name": name, "type": type_, "typeVersion": ver, "position": pos}
    n.update(kw); return n

nodes = [
 node("Webhook", "n8n-nodes-base.webhook", 2, [0, 200], {"httpMethod": "POST", "path": "newsletter", "responseMode": "responseNode", "options": {"allowedOrigins": "*"}}, webhookId="cypher-news-newsletter"),
 node("Plan", "n8n-nodes-base.code", 2, [220, 200], {"jsCode": PLAN_JS}),
 node("RSS Read", "n8n-nodes-base.rssFeedRead", 1.2, [440, 200], {"url": "={{ $json.url }}", "options": {}}, onError="continueRegularOutput", alwaysOutputData=True),
 node("Collect", "n8n-nodes-base.code", 2, [660, 200], {"jsCode": COLLECT_JS}),
 node("OpenRouter", "n8n-nodes-base.httpRequest", 4.2, [880, 200], {
     "method": "POST", "url": "https://openrouter.ai/api/v1/chat/completions", "sendHeaders": True,
     "headerParameters": {"parameters": [{"name": "Authorization", "value": "=Bearer {{ $env.OPENROUTER_API_KEY }}"}, {"name": "Content-Type", "value": "application/json"}]},
     "sendBody": True, "specifyBody": "json",
     "jsonBody": "={{ JSON.stringify({ model: $env.MODEL_PRIMARY, max_tokens: 4000, temperature: 0.4, reasoning: { enabled: false }, messages: $json.messages }) }}",
     "options": {"timeout": 90000}}, onError="continueRegularOutput", retryOnFail=True, maxTries=2, waitBetweenTries=2000),
 node("Parse", "n8n-nodes-base.code", 2, [1100, 200], {"jsCode": PARSE_JS}),
 node("Respond", "n8n-nodes-base.respondToWebhook", 1.1, [1320, 200], {"respondWith": "json", "responseBody": "={{ $json }}", "options": {"responseCode": 200, "responseHeaders": {"entries": [{"name": "Access-Control-Allow-Origin", "value": "*"}]}}}),
]
conn = {"Webhook": [["Plan"]], "Plan": [["RSS Read"]], "RSS Read": [["Collect"]], "Collect": [["OpenRouter"]], "OpenRouter": [["Parse"]], "Parse": [["Respond"]]}
connections = {k: {"main": [[{"node": t, "type": "main", "index": 0} for t in outs[0]]]} for k, outs in conn.items()}
wf = {"name": "Cypher News - Daily Drop", "nodes": nodes, "connections": connections, "active": False, "settings": {"executionOrder": "v1"}, "pinData": {}, "id": "cypherNewsDrop001"}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow.json")
json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
print("geschrieben:", out)
