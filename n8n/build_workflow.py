#!/usr/bin/env python3
"""Erzeugt n8n/workflow.json (Cypher News - Daily Drop, v2). Ausfuehren: python3 n8n/build_workflow.py
Knoten: Webhook -> Plan -> RSS Read -> Collect -> Vision -> Writer Prompt -> Writer (Nemotron Ultra) -> Router (Ausweichkette) -> Parse -> Respond"""
import json, os

PLAN_JS = r"""
const b = $input.first().json.body || $input.first().json;
const prefsText = String(b.preferences || '').trim();
const sources = Array.isArray(b.sources) ? b.sources : [];
const accounts = b.accounts || {};
const social = Array.isArray(b.social_items) ? b.social_items : [];
const date = b.date || new Date().toISOString().slice(0,10);
const enc = encodeURIComponent;
let topics = prefsText.split(/[\n,;.]+|\s+und\s+/i).map(s => s.trim()).filter(s => s.length > 2 && s.length < 80);
if (!topics.length) topics = ['Konzerte Berlin', 'Giveaways', 'Tech News', 'Trends'];
topics = [...new Set(topics)].slice(0, 5);
const feeds = [];
for (const t of topics) feeds.push({ url: `https://news.google.com/rss/search?q=${enc(t + ' when:7d')}&hl=de&gl=DE&ceid=DE:de`, label: t });
for (const s of sources.slice(0, 6)) {
  const v = String(s).trim(); if (!v) continue;
  if (/^https?:\/\//i.test(v) && /(rss|feed|atom|\.xml)/i.test(v)) feeds.push({ url: v, label: v });
  else if (/reddit\.com\/r\/(\w+)/i.test(v)) feeds.push({ url: `https://www.reddit.com/r/${v.match(/r\/(\w+)/i)[1]}/top/.rss?t=week`, label: v });
  else feeds.push({ url: `https://www.bing.com/news/search?q=${enc(v.replace(/^@/, '') + ' ' + prefsText)}&format=rss&setlang=de`, label: v });
}
if (!social.length) for (const [plat, list] of Object.entries(accounts)) for (const h of (Array.isArray(list) ? list : []).slice(0, 2))
  feeds.push({ url: `https://www.bing.com/news/search?q=${enc(String(h).replace(/^@/, '') + ' ' + plat)}&format=rss&setlang=de`, label: plat + ':' + h });
const out = feeds.slice(0, 10).map(f => ({ json: { url: f.url, label: f.label, prefs: prefsText, topics, date, sources } }));
out[0].json.social_items = social; out[0].json.accounts = accounts; out[0].json.quality = (b.quality === 'high') ? 'high' : 'fast';
return out;
"""

COLLECT_JS = r"""
const plan = $('Plan').first().json;
const seen = new Set(); const items = [];
for (const sx of (plan.social_items || []).slice(0, 30)) {
  items.push({ title: String(sx.text || '').split('\n')[0].slice(0, 140) || ((sx.kind || 'post') + ' von @' + (sx.account || '')), link: sx.url || '',
    source: (sx.platform || 'social') + ' @' + (sx.account || ''), date: sx.taken_at || '', snippet: String(sx.text || '').replace(/\s+/g, ' ').slice(0, 260),
    kind: sx.kind || 'post', platform: sx.platform || '', account: sx.account || '', image_b64: sx.image_b64 || '' });
}
const social = items.slice();
for (const it of $input.all()) {
  const j = it.json; if (!j || !j.title || !j.link) continue;
  const key = String(j.title).toLowerCase().replace(/[^a-z0-9äöüß]+/g, ' ').slice(0, 60);
  if (seen.has(key)) continue; seen.add(key);
  let host = ''; try { host = new URL(j.link).hostname.replace(/^www\./, ''); } catch (e) {}
  const src = (j.title.match(/ - ([^-]{3,40})$/) || [])[1] || host || 'Web';
  items.push({ title: String(j.title).replace(/ - [^-]{3,40}$/, '').slice(0, 160), link: j.link, source: src, kind: 'news', platform: '', account: '',
    date: j.isoDate || j.pubDate || '', snippet: String(j.contentSnippet || j.content || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 220) });
}
const news = items.filter(x => x.kind === 'news').sort((a, b) => String(b.date).localeCompare(String(a.date)));
const top = social.concat(news).slice(0, 34);
return [{ json: { prefs: plan.prefs, date: plan.date, top, socialN: social.length, quality: plan.quality || 'fast' } }];
"""

VISION_JS = r"""
const col = $input.first().json; const top = col.top;
const key = $env.OPENROUTER_API_KEY;
const chain = ['qwen/qwen3.8-27b:free', 'google/gemma-4-31b-it:free', 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free'];
const ask = 'Beschreibe in 1-2 Saetzen auf Deutsch, was auf dem Bild zu sehen ist. Lies sichtbaren Text vor. Nenne Event-Infos (Datum, Ort, Anlass), Giveaway-/Drop-/Preis-Hinweise, falls erkennbar.';
async function describe(b64) {
  for (const model of chain) {
    try {
      const r = await this.helpers.httpRequest({ method: 'POST', url: 'https://openrouter.ai/api/v1/chat/completions', json: true, timeout: 40000,
        headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
        body: { model, max_tokens: 300, reasoning: { enabled: false }, messages: [{ role: 'user', content: [{ type: 'text', text: ask }, { type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + b64 } }] }] } });
      const t = r && r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content;
      if (t && t.trim()) return { text: t.trim().slice(0, 400), model };
    } catch (e) { /* naechstes Modell */ }
  }
  return null;
}
const withImg = top.map((x, i) => [x, i]).filter(([x]) => x.image_b64).slice(0, 6);
const res = await Promise.all(withImg.map(([x]) => describe.call(this, x.image_b64)));
let n = 0; const models = [];
withImg.forEach(([x], k) => { if (res[k]) { x.vision = res[k].text; n++; models.push(res[k].model); } });
return [{ json: { ...col, top, images_analyzed: n, vision_models: [...new Set(models)] } }];
"""

WRITER_PROMPT_JS = r"""
const col = $input.first().json; const top = col.top;
const list = top.map((x, i) => `[${i}] ${x.kind.toUpperCase()}${x.platform ? ' ' + x.platform + ' @' + x.account : ''} | ${x.title} | ${x.source} | ${String(x.date).slice(0, 10)} | ${x.snippet}${x.vision ? ' | BILDINHALT: ' + x.vision : ''}`).join('\n');
const system = 'Du bist die Redaktion von CYPHER NEWS (DAILY DROP), einem personalisierten Tages-Newsletter, der Social-Media-Posts, Stories, Reels und News fuer den Nutzer zusammenfasst, damit er nicht scrollen muss. Antworte AUSSCHLIESSLICH mit gueltigem JSON, ohne Text davor oder danach.';
const user = `Notizen/Wuensche des Nutzers: "${col.prefs}"\nDatum: ${col.date}\n\nRohdaten (Index | Art/Plattform | Titel | Quelle | Datum | Ausschnitt | Bildinhalt):\n${list}\n\nWaehle die 8 besten, zu den Notizen passenden, abwechslungsreichen Eintraege (Social-Posts/Stories bevorzugen, wenn sie relevant sind; Konzerte, Giveaways, Drops, Tech, Trends). Schreibe auf Deutsch, locker und praezise; nutze Bildinhalte, um Datum/Ort/Aktion zu nennen. JSON-Format:\n{"title":"kurze Schlagzeile des Tages","intro":"2 Saetze Einleitung","items":[{"idx":<Index>,"category":"Konzerte|Giveaways|Drops|Tech|Trends|News","title":"Titel","summary":"1-2 Saetze: was ist passiert, warum relevant, was tun (Deadline/Datum)","when":"z.B. Heute, Sa 12.10., diese Woche"}]}\nErfinde keine Fakten und keine Links; nutze nur die Daten oben.`;
return [{ json: { ...col, messages: [{ role: 'system', content: system }, { role: 'user', content: user }] } }];
"""

ROUTER_JS = r"""
const wp = $('Writer Prompt').first().json;
const first = $input.first().json;
const key = $env.OPENROUTER_API_KEY;
function content(r) { try { return (r.choices[0].message.content || '').trim(); } catch (e) { return ''; } }
function valid(t) { try { const m = t.match(/\{[\s\S]*\}/); const d = JSON.parse(m[0]); return Array.isArray(d.items) && d.items.length > 0; } catch (e) { return false; } }
const ULTRA = 'nvidia/nemotron-3-ultra-550b-a55b:free'; const SUPER = 'nvidia/nemotron-3-super-120b-a12b:free';
let text = content(first); let used = wp.quality === 'high' ? ULTRA : SUPER;
if (!valid(text)) {
  const chain = [used === SUPER ? ULTRA : SUPER, $env.MODEL_PAID || 'deepseek/deepseek-v4-pro'];
  for (const model of chain) {
    if (!model) continue;
    try {
      const r = await this.helpers.httpRequest({ method: 'POST', url: 'https://openrouter.ai/api/v1/chat/completions', json: true, timeout: 80000,
        headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
        body: { model, max_tokens: 4000, temperature: 0.4, reasoning: { enabled: false }, messages: wp.messages } });
      const t = content(r); if (valid(t)) { text = t; used = model; break; }
    } catch (e) { /* naechstes Modell */ }
  }
  if (!valid(text)) { text = ''; used = 'fallback-ohne-ki'; }
}
return [{ json: { text, used } }];
"""

PARSE_JS = r"""
const wp = $('Writer Prompt').first().json; const top = wp.top || [];
const r = $input.first().json; const text = r.text || '';
let data = null; try { const m = text.match(/\{[\s\S]*\}/); if (m) data = JSON.parse(m[0]); } catch (e) { data = null; }
const cats = { Konzerte: 1, Giveaways: 1, Drops: 1, Tech: 1, Trends: 1, News: 1 };
const guess = (t) => /konzert|live|tour|festival|club|dj/i.test(t) ? 'Konzerte' : /gewinn|verlos|giveaway/i.test(t) ? 'Giveaways' : /drop|release|kollektion|sneaker|streetwear|mode/i.test(t) ? 'Drops' : /ki|ai|tech|app|software|handy|chip|apple|google/i.test(t) ? 'Tech' : 'News';
const build = (src, x) => ({ category: x && cats[x.category] ? x.category : guess(src.title), title: String((x && x.title) || src.title).slice(0, 140),
  summary: String((x && x.summary) || src.vision || src.snippet || 'Mehr dazu in der Quelle.').slice(0, 340), source: src.source, url: src.link,
  when: String((x && x.when) || String(src.date).slice(0, 10) || 'aktuell').slice(0, 30), kind: src.kind || 'news', platform: src.platform || '', account: src.account || '',
  image: src.image_b64 ? 'data:image/jpeg;base64,' + src.image_b64 : '' });
let items = [];
if (data && Array.isArray(data.items)) for (const x of data.items) { const src = top[Number(x.idx)]; if (src) items.push(build(src, x)); }
const ai = items.length > 0;
if (!ai) items = top.slice(0, 8).map(s => build(s, null));
return [{ json: { title: (data && data.title) || 'Dein Drop für heute', date: wp.date, intro: (data && data.intro) || 'Frisch gescannt: das Wichtigste zu deinen Themen.', items,
  meta: { engine: 'n8n', model: ai ? r.used : 'fallback-ohne-ki', sources: top.length, social_items: wp.socialN || 0, images_analyzed: wp.images_analyzed || 0, vision_models: wp.vision_models || [] } } }];
"""

def node(name, type_, ver, pos, params, **kw):
    n = {"parameters": params, "id": name.lower().replace(' ', '-'), "name": name, "type": type_, "typeVersion": ver, "position": pos}
    n.update(kw); return n

x = lambda i: [i * 230, 200]
nodes = [
 node("Webhook", "n8n-nodes-base.webhook", 2, x(0), {"httpMethod": "POST", "path": "newsletter", "responseMode": "responseNode", "options": {"allowedOrigins": "*"}}, webhookId="cypher-news-newsletter"),
 node("Plan", "n8n-nodes-base.code", 2, x(1), {"jsCode": PLAN_JS}),
 node("RSS Read", "n8n-nodes-base.rssFeedRead", 1.2, x(2), {"url": "={{ $json.url }}", "options": {}}, onError="continueRegularOutput", alwaysOutputData=True),
 node("Collect", "n8n-nodes-base.code", 2, x(3), {"jsCode": COLLECT_JS}),
 node("Vision", "n8n-nodes-base.code", 2, x(4), {"jsCode": VISION_JS}),
 node("Writer Prompt", "n8n-nodes-base.code", 2, x(5), {"jsCode": WRITER_PROMPT_JS}),
 node("Writer", "n8n-nodes-base.httpRequest", 4.2, x(6), {
     "method": "POST", "url": "https://openrouter.ai/api/v1/chat/completions", "sendHeaders": True,
     "headerParameters": {"parameters": [{"name": "Authorization", "value": "=Bearer {{ $env.OPENROUTER_API_KEY }}"}, {"name": "Content-Type", "value": "application/json"}]},
     "sendBody": True, "specifyBody": "json",
     "jsonBody": "={{ JSON.stringify({ model: ($json.quality === 'high' ? 'nvidia/nemotron-3-ultra-550b-a55b:free' : 'nvidia/nemotron-3-super-120b-a12b:free'), max_tokens: 4000, temperature: 0.4, reasoning: { enabled: false }, messages: $json.messages }) }}",
     "options": {"timeout": 60000}}, onError="continueRegularOutput"),
 node("Router", "n8n-nodes-base.code", 2, x(7), {"jsCode": ROUTER_JS}),
 node("Parse", "n8n-nodes-base.code", 2, x(8), {"jsCode": PARSE_JS}),
 node("Respond", "n8n-nodes-base.respondToWebhook", 1.1, x(9), {"respondWith": "json", "responseBody": "={{ $json }}", "options": {"responseCode": 200, "responseHeaders": {"entries": [{"name": "Access-Control-Allow-Origin", "value": "*"}]}}}),
]
order = ["Webhook", "Plan", "RSS Read", "Collect", "Vision", "Writer Prompt", "Writer", "Router", "Parse", "Respond"]
connections = {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(order, order[1:])}
wf = {"name": "Cypher News - Daily Drop", "nodes": nodes, "connections": connections, "active": False, "settings": {"executionOrder": "v1", "executionTimeout": 150}, "pinData": {}, "id": "cypherNewsDrop001"}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow.json")
json.dump(wf, open(out, "w"), indent=2, ensure_ascii=False)
print("geschrieben:", out, len(nodes), "Knoten")
