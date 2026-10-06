'use strict';
const $ = (id) => document.getElementById(id);
const CATS = {Konzerte: 'konzerte', Giveaways: 'giveaways', Drops: 'drops', Tech: 'tech', Trends: 'trends', News: 'sonstiges'};
const PLAT = {instagram: '📷', tiktok: '🎵', youtube: '▶️', reddit: '🤖', bluesky: '🦋', mastodon: '🐘', rss: '📡', news: '📰', shared: '📲'};
const CHIPS = ['Konzerte Berlin', 'Giveaways', 'Kleidungsdrops', 'Tech-News', 'Trends', 'Streetwear', 'Techno', 'Rap'];
const ERR = {
  no_key: 'Du brauchst einen OpenRouter-Schlüssel (Profil > KI-Schlüssel) oder das Gratis-Kontingent ist für heute aufgebraucht.',
  no_credit: 'Dein OpenRouter-Konto hat kein Guthaben mehr oder das Tageslimit der Gratis-Modelle ist erreicht.',
  key_invalid: 'Dein OpenRouter-Schlüssel wurde abgelehnt. Bitte neu eintragen.',
  rate_limited: 'Zu viele Anfragen. Warte kurz und versuche es erneut.',
  no_profile: 'Schreib zuerst unter Profil, was dich interessiert, und speichere.',
  no_model_configured: 'Der Betreiber hat noch kein KI-Modell eingestellt.',
  internal: 'Da ist etwas schiefgelaufen. Versuche es gleich noch einmal.'
};
let me = null, sources = [], topics = new Set(), quality = 'fast', current = null, view = 'stories';

function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c])); }
function safeUrl(u) { return /^https?:\/\//i.test(u || '') ? u : ''; }
function toast(msg, bad) { const t = $('toast'); t.textContent = msg; t.className = 'toast show' + (bad ? ' error' : ''); clearTimeout(toast.t); toast.t = setTimeout(() => t.className = 'toast', 3500); }
async function api(path, method = 'GET', body) {
  const o = {method, credentials: 'same-origin', headers: {}};
  if (body instanceof FormData) o.body = body; else if (body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(body); }
  const r = await fetch(path, o);
  let data = {}; try { data = await r.json(); } catch (e) {}
  if (!r.ok) { const e = new Error(data.error || 'http_' + r.status); e.code = data.error || ''; e.status = r.status; throw e; }
  return data;
}

// ---------- logo glitch ----------
setInterval(() => { if (matchMedia('(prefers-reduced-motion: reduce)').matches) return; $('logo').classList.add('glitch'); setTimeout(() => $('logo').classList.remove('glitch'), 500); }, 6000);

// ---------- tabs ----------
function showTab(name) {
  document.querySelectorAll('.tab-btn').forEach((b) => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-page').forEach((p) => p.style.display = 'none');
  $('page' + name[0].toUpperCase() + name.slice(1)).style.display = 'block';
  if (name === 'saved') loadSaved();
  if (name === 'history') loadHistory();
}
$('tabNav').addEventListener('click', (e) => { const b = e.target.closest('.tab-btn'); if (b) showTab(b.dataset.tab); });

// ---------- boot ----------
async function boot() {
  const hrs = $('dropHour'); for (let h = 0; h < 24; h++) hrs.insertAdjacentHTML('beforeend', `<option value="${h}">${String(h).padStart(2, '0')}:00 Uhr</option>`);
  try { me = await api('/api/me'); } catch (e) { me = {session: false}; }
  if (!me.session) { $('welcome').hidden = false; $('mainApp').hidden = true; return; }
  $('welcome').hidden = true; $('mainApp').hidden = false;
  applyProfile();
  const sh = new URLSearchParams(location.search).get('share');
  if (sh) { toast(sh === 'ok' ? 'Geteilt! Kommt in deinen nächsten Drop.' : sh === 'login' ? 'Bitte erst die App öffnen und loslegen.' : 'Nichts zum Teilen gefunden.', sh !== 'ok'); history.replaceState(null, '', '/'); }
  try { const ds = (await api('/api/drops')).drops; if (ds.length) renderDrop(await api('/api/drops/' + ds[0].id)); } catch (e) {}
  if (!me.notes && !sources.length) showTab('profile');
}

function applyProfile() {
  $('notes').value = me.notes || '';
  sources = me.sources || []; quality = me.quality || 'fast';
  topics = new Set(CHIPS.filter((c) => (me.notes || '').toLowerCase().includes(c.toLowerCase())));
  $('dropHour').value = me.drop_hour == null ? 8 : me.drop_hour;
  document.querySelectorAll('.q-btn').forEach((b) => b.classList.toggle('active', b.dataset.q === quality));
  renderChips(); renderSources();
  $('keyStatus').textContent = me.has_key ? '✔ Schlüssel gespeichert (verschlüsselt).' : (me.free_left > 0 ? `Kein Schlüssel. Heute noch ${me.free_left} Gratis-Drop über den Server.` : 'Noch kein Schlüssel eingetragen.');
  $('pushBtn').textContent = me.push ? 'PUSH AUSSCHALTEN' : 'PUSH AKTIVIEREN';
  const need = !me.has_key && me.free_left <= 0;
  const hint = $('setupHint'); hint.hidden = !need;
  if (need) hint.innerHTML = '<b>Fast fertig:</b> Trag unter <b>Profil &gt; KI-Schlüssel</b> deinen kostenlosen OpenRouter-Schlüssel ein, dann kann es losgehen.';
  $('dropInfo').textContent = `Dein täglicher Drop kommt um ${String(me.drop_hour == null ? 8 : me.drop_hour).padStart(2, '0')}:00 Uhr.`;
}

// ---------- welcome ----------
$('btnStart').addEventListener('click', async () => {
  try { const r = await api('/api/start', 'POST'); $('recoveryCode').textContent = r.recovery; $('recoveryModal').style.display = 'flex'; }
  catch (e) { toast(e.status === 409 ? 'Du hast schon ein Konto.' : 'Das hat nicht geklappt. Später noch einmal versuchen.', true); if (e.status === 409) boot(); }
});
$('closeCode').addEventListener('click', () => { $('recoveryModal').style.display = 'none'; boot(); });
$('copyCode').addEventListener('click', () => { try { navigator.clipboard.writeText($('recoveryCode').textContent); toast('Kopiert'); } catch (e) {} });
$('btnShowRestore').addEventListener('click', () => $('restoreBox').hidden = false);
$('btnRestore').addEventListener('click', async () => {
  try { await api('/api/restore', 'POST', {code: $('restoreCode').value}); boot(); } catch (e) { toast('Code nicht gefunden.', true); }
});

// ---------- profile ----------
function renderChips() {
  $('topicChips').innerHTML = CHIPS.map((c) => `<span class="chip ${topics.has(c) ? 'active' : ''}" data-topic="${esc(c)}" role="button" tabindex="0">${esc(c)}<span class="check">✓</span></span>`).join('');
}
$('topicChips').addEventListener('click', (e) => {
  const c = e.target.closest('.chip'); if (!c) return; const t = c.dataset.topic;
  const ta = $('notes');
  if (topics.has(t)) { topics.delete(t); ta.value = ta.value.split(/\n/).filter((l) => l.trim() !== t).join('\n'); }
  else { topics.add(t); ta.value = (ta.value.trim() ? ta.value.trim() + '\n' : '') + t; }
  renderChips();
});
function renderSources() {
  $('sourceChips').innerHTML = sources.map((s, i) => `<span class="source-chip">${PLAT[s.platform] || ''} ${esc(s.value)}<span class="remove" data-i="${i}" role="button" aria-label="entfernen">&times;</span></span>`).join('');
}
$('sourceChips').addEventListener('click', (e) => { const r = e.target.closest('.remove'); if (r) { sources.splice(+r.dataset.i, 1); renderSources(); } });
async function addSource() {
  const v = $('sourceInput').value.trim(); if (!v) return;
  try {
    const d = await api('/api/sources/detect', 'POST', {value: v});
    if (!d.platform) { toast('Plattform nicht erkannt. Nutze einen Link, r/name oder name@instanz.', true); return; }
    if (!sources.some((s) => s.platform === d.platform && s.value === d.value)) sources.push({platform: d.platform, value: d.value});
    $('sourceInput').value = ''; renderSources();
  } catch (e) { toast('Konnte Quelle nicht hinzufügen.', true); }
}
$('sourceAdd').addEventListener('click', addSource);
$('sourceInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') addSource(); });
$('importBtn').addEventListener('click', async () => {
  try {
    const d = await api('/api/sources/import', 'POST', {text: $('importText').value, platform: $('importPlatform').value});
    let n = 0; d.found.forEach((f) => { if (!sources.some((s) => s.platform === f.platform && s.value === f.value)) { sources.push(f); n++; } });
    renderSources(); $('importText').value = ''; toast(n + ' Quellen importiert. Zum Übernehmen unten speichern.');
  } catch (e) { toast('Import fehlgeschlagen.', true); }
});
document.querySelectorAll('.q-btn').forEach((b) => b.addEventListener('click', () => { quality = b.dataset.q; document.querySelectorAll('.q-btn').forEach((x) => x.classList.toggle('active', x === b)); }));
async function saveProfile(quiet) {
  await api('/api/profile', 'PUT', {notes: $('notes').value, sources, drop_hour: +$('dropHour').value, quality, tz_offset: -new Date().getTimezoneOffset()});
  me = await api('/api/me'); applyProfile(); if (!quiet) toast('Gespeichert');
}
$('saveProfile').addEventListener('click', async () => { try { await saveProfile(); } catch (e) { toast('Speichern fehlgeschlagen.', true); } });

// ---------- key / account ----------
$('keySave').addEventListener('click', async () => {
  try { await api('/api/key', 'POST', {key: $('keyInput').value}); $('keyInput').value = ''; me = await api('/api/me'); applyProfile(); toast('Schlüssel gespeichert'); }
  catch (e) { toast(e.code === 'key_rejected' ? 'OpenRouter lehnt diesen Schlüssel ab.' : 'Das sieht nicht wie ein OpenRouter-Schlüssel aus (sk-or-...).', true); }
});
$('keyDelete').addEventListener('click', async () => { await api('/api/key', 'DELETE'); me = await api('/api/me'); applyProfile(); toast('Schlüssel entfernt'); });
$('deleteAccount').addEventListener('click', async () => {
  if (!confirm('Konto und alle Daten wirklich unwiderruflich löschen?')) return;
  await api('/api/me', 'DELETE'); location.reload();
});

// ---------- push ----------
function b64ToU8(s) { const p = '='.repeat((4 - s.length % 4) % 4); const r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...r].map((c) => c.charCodeAt(0))); }
$('pushBtn').addEventListener('click', async () => {
  try {
    if (me.push) { await api('/api/push', 'DELETE'); me.push = false; applyProfile(); return; }
    const key = document.body.dataset.vapid;
    if (!key || !('serviceWorker' in navigator) || !('PushManager' in window)) { toast('Push wird hier nicht unterstützt (iPhone: erst zum Home-Bildschirm hinzufügen).', true); return; }
    if (await Notification.requestPermission() !== 'granted') { toast('Benachrichtigungen nicht erlaubt.', true); return; }
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: b64ToU8(key)});
    await api('/api/push', 'POST', sub.toJSON()); me.push = true; applyProfile(); toast('Push aktiv');
  } catch (e) { toast('Push konnte nicht aktiviert werden.', true); }
});

// ---------- generate ----------
const STEPS = ['> lese deine Quellen …', '> filtere Rauschen …', '> schaue Bilder an …', '> offenes Modell schreibt deinen Drop …', '> gleich fertig …'];
$('dropBtn').addEventListener('click', async () => {
  const btn = $('dropBtn'); btn.disabled = true; $('resultsArea').hidden = true;
  const term = $('terminal'); $('terminalWrapper').classList.add('visible'); term.innerHTML = '';
  let i = 0; const tick = setInterval(() => { if (i < STEPS.length) term.insertAdjacentHTML('beforeend', `<div class="line">${esc(STEPS[i++])}</div>`); }, 4000);
  term.insertAdjacentHTML('beforeend', `<div class="line">${esc('> starte …')}</div>`);
  try {
    await saveProfile(true);
    renderDrop(await api('/api/drop', 'POST'));
    me = await api('/api/me'); applyProfile();
  } catch (e) { toast(ERR[e.code] || 'Das hat nicht geklappt.', true); if (e.code === 'no_key' || e.code === 'key_invalid') showTab('profile'); }
  finally { clearInterval(tick); btn.disabled = false; $('terminalWrapper').classList.remove('visible'); }
});

// ---------- render ----------
function card(item, i, n) {
  const cat = CATS[item.category] || 'sonstiges', img = safeUrl(item.image) || (/^data:image\/jpeg;base64,/.test(item.image || '') ? item.image : '');
  const url = safeUrl(item.url);
  return `<div class="story-card cat-${cat}" data-cat="${esc(item.category)}">
    <div class="card-parallax">${img ? `<img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<div class="pattern pat-${cat}"></div>`}</div>
    <div class="card-body">
      <div class="card-header"><span class="cat-pill">${esc(item.category)}</span><span class="social-badge">${PLAT[item.platform] || ''} ${esc(item.account || item.source)}</span><span class="card-index">${String(i + 1).padStart(2, '0')}/${String(n).padStart(2, '0')}</span></div>
      <h3>${esc(item.title)}</h3><p class="summary">${esc(item.summary)}</p>
      <div class="meta-row"><span>${esc(item.source)}</span><span>${esc(item.when)}</span></div>
      <div class="actions">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="btn-open-wrap"><button class="btn-open">ÖFFNEN ↗</button></a>` : ''}
        <button data-act="save" data-i="${i}">★</button><button data-act="up" data-i="${i}">👍</button><button data-act="down" data-i="${i}">👎</button></div>
    </div></div>`;
}
function feedCard(item, i) {
  const cat = CATS[item.category] || 'sonstiges', img = safeUrl(item.image) || (/^data:image\/jpeg;base64,/.test(item.image || '') ? item.image : ''), url = safeUrl(item.url);
  return `<div class="feed-card cat-${cat}" data-cat="${esc(item.category)}"><div class="feed-card-img">${img ? `<img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<div class="pattern pat-${cat}"></div>`}</div>
    <div class="feed-card-body"><span class="cat-pill">${esc(item.category)}</span><h4>${esc(item.title)}</h4><p class="fsum">${esc(item.summary)}</p><span class="src">${esc(item.source)} · ${esc(item.when)}</span></div>
    <div class="feed-card-actions">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="feed-link">↗</a>` : ''}<button class="btn-save-inline" data-act="save" data-i="${i}">★</button></div></div>`;
}
function renderDrop(d) {
  current = d; const items = d.items || [];
  $('resultsArea').hidden = false;
  $('introTitle').textContent = d.title || 'DEIN DROP'; $('introDate').textContent = d.date || ''; $('introText').textContent = d.intro || '';
  const m = d.meta || {};
  $('introCount').textContent = `${items.length} Treffer aus ${m.sources_ok || 0} von ${m.sources_total || 0} Quellen`;
  let info = m.model && m.model !== 'fallback-ohne-ki' ? `Geschrieben von ${m.model}` : 'Ohne KI zusammengestellt (Modell nicht erreichbar)';
  if (m.images_analyzed) info += ` · ${m.images_analyzed} Bilder ausgewertet`;
  if (m.failed && m.failed.length) info += ` · nicht erreichbar: ${m.failed.slice(0, 4).join(', ')}`;
  $('introModel').textContent = info;
  const cats = [...new Set(items.map((x) => x.category))];
  $('catFilters').innerHTML = cats.map((c) => `<span class="chip active" data-cat="${esc(c)}">${esc(c)}</span>`).join('');
  $('storiesInner').innerHTML = items.length ? items.map((x, i) => card(x, i, items.length)).join('') : '';
  $('feedContainer').innerHTML = items.length ? items.map(feedCard).join('') : '<p class="empty">Diesmal nichts Passendes gefunden. Füge unter Profil mehr Quellen hinzu.</p>';
  $('storyProgress').innerHTML = items.map((_, i) => `<span class="prog-seg ${i === 0 ? 'active' : ''}"></span>`).join('');
  setView(view);
}
function setView(v) {
  view = v; $('btnStories').classList.toggle('active', v === 'stories'); $('btnFeed').classList.toggle('active', v === 'feed');
  const has = current && current.items && current.items.length;
  $('storiesContainer').classList.toggle('hidden', v !== 'stories' || !has); $('storyProgress').style.display = v === 'stories' && has ? 'flex' : 'none';
  $('feedContainer').style.display = v === 'feed' || !has ? 'flex' : 'none'; $('catFilters').style.display = v === 'feed' ? 'flex' : 'none';
}
$('btnStories').addEventListener('click', () => setView('stories')); $('btnFeed').addEventListener('click', () => setView('feed'));
$('storiesContainer').addEventListener('scroll', () => {
  const c = $('storiesContainer'), idx = Math.round(c.scrollLeft / c.clientWidth);
  document.querySelectorAll('.prog-seg').forEach((s, i) => s.classList.toggle('active', i <= idx));
});
$('catFilters').addEventListener('click', (e) => {
  const c = e.target.closest('.chip'); if (!c) return; c.classList.toggle('active');
  const on = new Set([...document.querySelectorAll('#catFilters .chip.active')].map((x) => x.dataset.cat));
  document.querySelectorAll('#feedContainer .feed-card').forEach((f) => f.style.display = on.has(f.dataset.cat) ? '' : 'none');
});
$('resultsArea').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-act]'); if (!b || !current) return;
  const it = current.items[+b.dataset.i];
  try {
    if (b.dataset.act === 'save') { await api('/api/saved', 'POST', it); b.classList.add('saved'); toast('Gemerkt ★'); }
    else { await api('/api/feedback', 'POST', {account: it.account, category: it.category, vote: b.dataset.act === 'up' ? 1 : -1}); toast(b.dataset.act === 'up' ? 'Mehr davon.' : 'Weniger davon.'); }
  } catch (err) { toast('Das hat nicht geklappt.', true); }
});

// ---------- saved + history ----------
async function loadSaved() {
  const c = $('savedContainer');
  try {
    const s = (await api('/api/saved')).saved;
    c.innerHTML = s.length ? s.map((x, i) => feedCard(x, i).replace('data-act="save"', 'data-act="unsave"').replace(/data-i="\d+"/, `data-title="${esc(x.title)}"`)).join('') : '<p class="empty">Noch nichts gemerkt. Tippe ★ auf einer Karte.</p>';
  } catch (e) { c.innerHTML = ''; }
}
$('savedContainer').addEventListener('click', async (e) => { const b = e.target.closest('[data-act="unsave"]'); if (!b) return; await api('/api/saved', 'DELETE', {title: b.dataset.title}); loadSaved(); });
async function loadHistory() {
  const c = $('historyContainer');
  try {
    const ds = (await api('/api/drops')).drops;
    c.innerHTML = ds.length ? ds.map((d) => `<div class="feed-card hist" data-id="${d.id}"><div class="feed-card-body"><span class="src">${esc(d.day)}</span><h4>${esc(d.title)}</h4><span class="src">${d.count} Treffer</span></div></div>`).join('') : '<p class="empty">Noch kein Drop. Sag uns, was dich interessiert.</p>';
  } catch (e) { c.innerHTML = ''; }
}
$('historyContainer').addEventListener('click', async (e) => { const h = e.target.closest('.hist'); if (!h) return; renderDrop(await api('/api/drops/' + h.dataset.id)); showTab('drop'); });

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
boot();
