'use strict';
const $ = (id) => document.getElementById(id);
const CATS = {Konzerte: 'konzerte', Giveaways: 'giveaways', Drops: 'drops', Tech: 'tech', Trends: 'trends', News: 'sonstiges'};
const PLAT = {instagram: ['IG', 'Instagram'], tiktok: ['TT', 'TikTok'], youtube: ['YT', 'YouTube'], reddit: ['RD', 'Reddit'], bluesky: ['BS', 'Bluesky'], x: ['X', 'X'],
  mastodon: ['MA', 'Mastodon'], rss: ['RSS', 'RSS'], news: ['NEWS', 'Nachrichten'], shared: ['APP', 'Geteilt in die App']};
const CHIPS = ['Konzerte Berlin', 'Giveaways', 'Kleidungsdrops', 'Tech-News', 'Trends', 'Streetwear', 'Techno', 'Rap'];
const ERR = {
  no_key: 'Du brauchst einen OpenRouter-Schlüssel (Profil > KI-Schlüssel) oder das Gratis-Kontingent ist für heute aufgebraucht.',
  no_credit: 'Dein OpenRouter-Konto hat kein Guthaben mehr oder das Tageslimit der Gratis-Modelle ist erreicht.',
  key_invalid: 'Dein OpenRouter-Schlüssel wurde abgelehnt. Bitte neu eintragen.',
  busy: 'Dein Drop wird gerade gebaut. Schau gleich noch einmal in den Verlauf.',
  rate_limited: 'Zu viele Anfragen. Warte kurz und versuche es erneut.',
  no_profile: 'Schreib zuerst unter Profil, was dich interessiert, und speichere.',
  no_model_configured: 'Der Betreiber hat noch kein KI-Modell eingestellt.',
  internal: 'Da ist etwas schiefgelaufen. Versuche es gleich noch einmal.',
  all_models_failed: 'Alle KI-Modelle sind gerade überlastet. Versuche es in ein paar Minuten noch einmal.'
};
const M = window.CNMotion || {live: () => false, ready: Promise.resolve(), boot: () => { const p = document.getElementById('preloader'); if (p) p.classList.add('gone'); return Promise.resolve(); }, scramble: (el) => { if (el && el.dataset.final) el.textContent = el.dataset.final; },
  landingStart: () => ({play() {}}), landingStop() {}, pageIn() {}, tabInd() {}, revealDrop() {}, burst() {}, refresh() {}};  // motion.js missing: app still works
const fontsReady = (document.fonts && document.fonts.ready) || Promise.resolve();
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
let me = null, sources = [], topics = new Set(), quality = 'fast', current = null, view = 'feed', savedTitles = new Set(), votes = {};
try { const v = localStorage.getItem('cn-view'); if (v === 'stories' || v === 'feed') view = v; } catch (e) { /* storage may be blocked */ }

function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c])); }
function safeUrl(u) { return /^https?:\/\//i.test(u || '') ? u : ''; }
function ico(n) { return `<svg class="ico" aria-hidden="true"><use href="#i-${n}"/></svg>`; }
function toast(msg, bad) { const t = $('toast'); t.textContent = msg; t.className = 'toast show' + (bad ? ' error' : ''); clearTimeout(toast.t); toast.t = setTimeout(() => { t.className = 'toast'; setTimeout(() => { if (!t.classList.contains('show')) t.textContent = ''; }, 400); }, 3800); }
async function api(path, method = 'GET', body) {
  const o = {method, credentials: 'same-origin', headers: {'X-Client': '2'}};
  if (body instanceof FormData) o.body = body; else if (body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(body); }
  const r = await fetch(path, o);
  let data = {}; try { data = await r.json(); } catch (e) {}
  if (!r.ok) { const e = new Error(data.error || 'http_' + r.status); e.code = data.error || ''; e.status = r.status; throw e; }
  return data;
}
function setBusy(btn, on) { btn.disabled = on; btn.classList.toggle('is-busy', on); btn.setAttribute('aria-busy', on ? 'true' : 'false'); }
function stagger(container) { [...container.children].forEach((el, i) => el.style.setProperty('--i', Math.min(i, 9))); }
function rain(on) { document.body.classList.toggle('rain-on', on); if (window.CypherRain) on ? window.CypherRain.start() : window.CypherRain.stop(); }

// ---------- masthead: edition date and "decrypt" of the logo ----------
function setEdition() { try { $('editionDate').textContent = new Date().toLocaleDateString('de-DE', {weekday: 'short', day: 'numeric', month: 'short'}).replace(/\./g, ''); } catch (e) {} }
$('logo').addEventListener('click', (e) => { e.preventDefault(); M.scramble($('logoWord'), 700); });

// ---------- tabs ----------
function showTab(name, focus = true, quiet = false) {
  document.querySelectorAll('.tab-btn').forEach((b) => { const on = b.dataset.tab === name; b.classList.toggle('active', on); if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
  document.querySelectorAll('.tab-page').forEach((p) => p.hidden = true);
  $('page' + name[0].toUpperCase() + name.slice(1)).hidden = false;
  window.scrollTo(0, 0);
  M.tabInd(document.querySelector(`.tab-btn[data-tab="${name}"]`));
  if (!quiet) M.pageIn($('page' + name[0].toUpperCase() + name.slice(1)));
  if (focus) $('main').focus({preventScroll: true});
  document.title = {drop: 'Heute', saved: 'Gemerkt', history: 'Verlauf', profile: 'Profil'}[name] + ' - Cypher News';
  if (name === 'saved') loadSaved();
  if (name === 'history') loadHistory();
}
$('tabNav').addEventListener('click', (e) => { const b = e.target.closest('.tab-btn'); if (b) showTab(b.dataset.tab); });
$('goProfile').addEventListener('click', () => showTab('profile'));

// ---------- boot ----------
async function boot() {
  const hrs = $('dropHour'); hrs.innerHTML = ''; for (let h = 0; h < 24; h++) hrs.insertAdjacentHTML('beforeend', `<option value="${h}">${String(h).padStart(2, '0')}:00 Uhr</option>`);
  try { me = await api('/api/me'); } catch (e) { me = {session: false}; }
  if (!me.session) {
    document.body.classList.remove('is-boot', 'is-app'); document.body.classList.add('is-landing');
    $('mainApp').hidden = true; $('tabNav').hidden = true; $('skipLink').setAttribute('href', '#landMain'); rain(true);
    const hero = M.landingStart();                 // Startzustände setzen, solange der Preloader noch deckt
    await M.boot(false, fontsReady, () => hero.play());
    return;
  }
  try { await bootApp(); } finally { M.boot(true, fontsReady); }
}
async function bootApp() {
  M.landingStop(); rain(false);
  document.body.classList.remove('is-boot', 'is-landing'); document.body.classList.add('is-app'); $('skipLink').setAttribute('href', '#main');
  $('mainApp').hidden = false; $('tabNav').hidden = false;
  M.tabInd(document.querySelector('.tab-btn.active'));
  applyProfile();
  // the stored UTC offset is a fixed number: refresh it when the clock changed (summer/winter time, travel), so drops keep arriving at the chosen local hour
  const tzNow = -new Date().getTimezoneOffset();
  if (me.tz_offset !== tzNow) api('/api/profile', 'PUT', {tz_offset: tzNow}).catch(() => {});
  const sh = new URLSearchParams(location.search).get('share');
  if (sh) { toast(sh === 'ok' ? 'Geteilt! Kommt in deinen nächsten Drop.' : sh === 'login' ? 'Bitte erst die App öffnen und loslegen.' : 'Nichts zum Teilen gefunden.', sh !== 'ok'); history.replaceState(null, '', '/'); }
  try { (await api('/api/saved')).saved.forEach((s) => savedTitles.add(s.title)); } catch (e) {}
  try { const ds = (await api('/api/drops')).drops; if (ds.length) renderDrop(await api('/api/drops/' + ds[0].id)); } catch (e) {}
  syncEmpty();
  if (!me.notes && !sources.length) showTab('profile', false);
}
function syncEmpty() { $('todayEmpty').hidden = !!current; $('dropBar').classList.toggle('compact', !!current); }

function applyProfile(keepForm) {
  // keepForm: only refresh status labels. Used after key/push changes, so unsaved text in the profile form is NOT overwritten.
  if (!keepForm) {
    $('notes').value = me.notes || '';
    sources = me.sources || []; quality = me.quality || 'fast';
    topics = new Set(CHIPS.filter((c) => (me.notes || '').toLowerCase().includes(c.toLowerCase())));
    $('dropHour').value = me.drop_hour == null ? 8 : me.drop_hour;
    setQuality(quality);
    renderChips(); renderSources();
  }
  $('keyStatus').textContent = me.has_key ? 'Schlüssel gespeichert (verschlüsselt).' : (me.free_left > 0 ? `Kein Schlüssel. Heute noch ${me.free_left} Gratis-Drop über den Server.` : 'Noch kein Schlüssel eingetragen.');
  $('pushBtn').textContent = me.push ? 'Push ausschalten' : 'Push aktivieren';
  const need = !me.has_key && me.free_left <= 0;
  const hint = $('setupHint'); hint.hidden = !need;
  if (need) hint.innerHTML = '<b>Fast fertig.</b> Trag unter <b>Profil &gt; KI-Schlüssel</b> deinen kostenlosen OpenRouter-Schlüssel ein, dann kann es losgehen.';
  $('dropInfo').textContent = `Dein täglicher Drop kommt um ${String(me.drop_hour == null ? 8 : me.drop_hour).padStart(2, '0')}:00 Uhr.`;
}

// ---------- welcome ----------
document.querySelectorAll('[data-start]').forEach((b) => b.addEventListener('click', () => $('btnStart').click()));
$('btnStart').addEventListener('click', async () => {
  try { const r = await api('/api/start', 'POST'); $('recoveryCode').textContent = r.recovery; openRecovery(); }
  catch (e) { toast(e.status === 409 ? 'Du hast schon ein Konto.' : 'Das hat nicht geklappt. Später noch einmal versuchen.', true); if (e.status === 409) boot(); }
});
function setInert(on) { document.querySelector('.shell').inert = on; $('welcome').inert = on; }
function openRecovery() { $('recoveryModal').hidden = false; setInert(true); $('closeCode').focus(); }
$('closeCode').addEventListener('click', () => { $('recoveryModal').hidden = true; setInert(false); boot().then(() => $('main').focus({preventScroll: true})); });
$('copyCode').addEventListener('click', async () => { try { await navigator.clipboard.writeText($('recoveryCode').textContent); toast('Kopiert'); } catch (e) { toast('Kopieren nicht möglich. Markiere den Code und kopiere ihn von Hand.', true); } });
$('btnShowRestore').addEventListener('click', () => { const r = $('restoreBox'); r.hidden = !r.hidden; $('btnShowRestore').setAttribute('aria-expanded', String(!r.hidden)); if (!r.hidden) $('restoreCode').focus(); });
$('btnRestore').addEventListener('click', async () => {
  try { await api('/api/restore', 'POST', {code: $('restoreCode').value}); boot(); } catch (e) { toast('Code nicht gefunden.', true); }
});
$('restoreCode').addEventListener('keydown', (e) => { if (e.key === 'Enter') $('btnRestore').click(); });

// ---------- profile ----------
function renderChips() {
  $('topicChips').innerHTML = CHIPS.map((c) => `<button type="button" class="chip ${topics.has(c) ? 'active' : ''}" data-topic="${esc(c)}" aria-pressed="${topics.has(c)}">${esc(c)}</button>`).join('');
}
$('topicChips').addEventListener('click', (e) => {
  const c = e.target.closest('.chip'); if (!c) return; const t = c.dataset.topic;
  const ta = $('notes');
  if (topics.has(t)) { topics.delete(t); ta.value = ta.value.split(/\n/).filter((l) => l.trim() !== t).join('\n'); }
  else { topics.add(t); ta.value = (ta.value.trim() ? ta.value.trim() + '\n' : '') + t; }
  c.classList.toggle('active', topics.has(t)); c.setAttribute('aria-pressed', String(topics.has(t)));
});
function renderSources() {
  $('sourceChips').innerHTML = sources.map((s, i) => { const p = PLAT[s.platform] || ['?', s.platform];
    return `<span class="source-chip"><span class="plat" title="${esc(p[1])}">${esc(p[0])}</span><span class="val">${esc(s.value)}</span><button type="button" class="remove" data-i="${i}" aria-label="${esc(s.value)} entfernen">${ico('x')}</button></span>`; }).join('');
}
$('sourceChips').addEventListener('click', (e) => { const r = e.target.closest('.remove'); if (r) { sources.splice(+r.dataset.i, 1); renderSources(); } });
async function addSource() {
  const v = $('sourceInput').value.trim(); if (!v) return;
  try {
    const d = await api('/api/sources/detect', 'POST', {value: v, platform: $('sourcePlatform').value});
    if (!d.platform) { toast('Plattform nicht erkannt. Wähle sie links aus oder nutze einen Link.', true); return; }
    if (!sources.some((s) => s.platform === d.platform && s.value === d.value)) sources.push({platform: d.platform, value: d.value});
    $('sourceInput').value = ''; renderSources();
    toast('Prüfe ' + d.value + ' …');
    try {
      const t = await api('/api/sources/test', 'POST', {platform: d.platform, value: d.value});
      toast(t.count ? `${t.count} aktuelle Beiträge gefunden`
        : (d.platform === 'x' ? 'Hinzugefügt. Die öffentlichen X-Spiegel sind gerade nicht erreichbar. Tipp: X-Links in die App teilen.'
          : 'Hinzugefügt, aber gerade nicht erreichbar. Tipp: Teile Posts direkt in die App.'), !t.count);
    } catch (e) { /* adding already worked */ }
  } catch (e) { toast('Konnte Quelle nicht hinzufügen.', true); }
}
$('sourceAdd').addEventListener('click', addSource);
$('sourceInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); addSource(); } });
$('importBtn').addEventListener('click', async () => {
  try {
    const d = await api('/api/sources/import', 'POST', {text: $('importText').value, platform: $('importPlatform').value});
    let n = 0; d.found.forEach((f) => { if (!sources.some((s) => s.platform === f.platform && s.value === f.value)) { sources.push(f); n++; } });
    renderSources(); $('importText').value = ''; toast(n + ' Quellen importiert. Zum Übernehmen unten speichern.');
  } catch (e) { toast('Import fehlgeschlagen.', true); }
});
function setQuality(q) {
  quality = q;
  document.querySelectorAll('.q-btn').forEach((b) => { const on = b.dataset.q === q; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
  $('qualitySeg').style.setProperty('--idx', q === 'high' ? 1 : 0);
}
document.querySelectorAll('.q-btn').forEach((b) => b.addEventListener('click', () => setQuality(b.dataset.q)));
async function saveProfile(quiet) {
  await api('/api/profile', 'PUT', {notes: $('notes').value, sources, drop_hour: +$('dropHour').value, quality, tz_offset: -new Date().getTimezoneOffset()});
  me = await api('/api/me'); applyProfile(); if (!quiet) toast('Gespeichert');
}
$('saveProfile').addEventListener('click', async () => { const b = $('saveProfile'); setBusy(b, true); try { await saveProfile(); } catch (e) { toast('Speichern fehlgeschlagen.', true); } finally { setBusy(b, false); } });

// ---------- key / account ----------
$('keySave').addEventListener('click', async () => {
  try { await api('/api/key', 'POST', {key: $('keyInput').value}); $('keyInput').value = ''; me = await api('/api/me'); applyProfile(true); toast('Schlüssel gespeichert'); }
  catch (e) { toast(e.code === 'key_rejected' ? 'OpenRouter lehnt diesen Schlüssel ab.' : 'Das sieht nicht wie ein OpenRouter-Schlüssel aus (sk-or-...).', true); }
});
$('keyDelete').addEventListener('click', async () => { try { await api('/api/key', 'DELETE'); me = await api('/api/me'); applyProfile(true); toast('Schlüssel entfernt'); } catch (e) { toast('Das hat nicht geklappt.', true); } });
$('deleteAccount').addEventListener('click', async () => {
  if (!confirm('Konto und alle Daten wirklich unwiderruflich löschen?')) return;
  try { await api('/api/me', 'DELETE'); location.reload(); } catch (e) { toast('Konto konnte nicht gelöscht werden.', true); }
});

// ---------- push ----------
function b64ToU8(s) { const p = '='.repeat((4 - s.length % 4) % 4); const r = atob((s + p).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...r].map((c) => c.charCodeAt(0))); }
$('pushBtn').addEventListener('click', async () => {
  try {
    if (me.push) { await api('/api/push', 'DELETE'); me.push = false; applyProfile(true); return; }
    const key = document.body.dataset.vapid;
    if (!key || !('serviceWorker' in navigator) || !('PushManager' in window)) { toast('Push wird hier nicht unterstützt (iPhone: erst zum Home-Bildschirm hinzufügen).', true); return; }
    if (await Notification.requestPermission() !== 'granted') { toast('Benachrichtigungen nicht erlaubt.', true); return; }
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: b64ToU8(key)});
    await api('/api/push', 'POST', sub.toJSON()); me.push = true; applyProfile(true); toast('Push aktiv');
  } catch (e) { toast('Push konnte nicht aktiviert werden.', true); }
});

// ---------- generate ----------
const STEPS = ['> lese deine Quellen …', '> filtere Rauschen …', '> schaue Bilder an …', '> offenes Modell schreibt deinen Drop …', '> gleich fertig …'];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function generateDrop() {
  await api('/api/drop', 'POST');                       // starts the job (returns at once)
  const t0 = Date.now(); let seen = false;
  while (Date.now() - t0 < 6 * 60 * 1000) {             // a drop takes 30-90 s
    await sleep(3000);
    let st; try { st = await api('/api/drop/status'); } catch (e) { if (e.status === 401) throw e; continue; }  // short network hiccup: keep waiting
    if (st.state === 'running') seen = true;
    else if (st.state === 'done') { if (!st.drop || !Array.isArray(st.drop.items)) { const e = new Error('bad'); e.code = 'internal'; throw e; } return st.drop; }
    else if (st.state === 'error') { const e = new Error(st.error); e.code = st.error; throw e; }
    else if (seen) { const e = new Error('lost'); e.code = 'internal'; throw e; }   // server restarted mid-job
  }
  const e = new Error('timeout'); e.code = 'internal'; throw e;
}
function showDropError(msg) { const n = $('dropError'); n.textContent = msg; n.hidden = false; n.scrollIntoView({block: 'nearest', behavior: reduced() ? 'auto' : 'smooth'}); }
$('dropBtn').addEventListener('click', async () => {
  const btn = $('dropBtn'); setBusy(btn, true); $('resultsArea').hidden = true; $('todayEmpty').hidden = true; $('dropError').hidden = true;
  const term = $('terminal'); $('terminalWrapper').classList.add('visible'); term.innerHTML = ''; rain(true);
  const t0 = Date.now(); $('elapsed').textContent = '0:00';
  const clock = setInterval(() => { const s = Math.floor((Date.now() - t0) / 1000); $('elapsed').textContent = Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }, 1000);
  let i = 0; const tick = setInterval(() => { if (i < STEPS.length) term.insertAdjacentHTML('beforeend', `<div class="line">${esc(STEPS[i++])}</div>`); }, 6000);
  term.insertAdjacentHTML('beforeend', `<div class="line">${esc('> starte …')}</div>`);
  let failed = false;
  try {
    await saveProfile(true);
    renderDrop(await generateDrop());
    me = await api('/api/me'); applyProfile(true);
    toast(`Dein Drop ist fertig: ${current.items.length} Treffer`);
  } catch (e) {
    failed = true;
    const msg = ERR[e.code] || (e.status === 401 ? 'Du bist nicht mehr angemeldet. Seite neu laden.' : 'Das hat nicht geklappt. Versuche es gleich noch einmal.');
    toast(msg, true); showDropError(msg);
    if (e.code === 'no_key' || e.code === 'key_invalid') showTab('profile');
  } finally {
    clearInterval(tick); clearInterval(clock); setBusy(btn, false); $('terminalWrapper').classList.remove('visible'); rain(false);
    if (failed && current) $('resultsArea').hidden = false;  // keep showing the previous drop
    syncEmpty();
    if (!failed) { $('resultsArea').scrollIntoView({block: 'start', behavior: reduced() ? 'auto' : 'smooth'}); $('introTitle').focus({preventScroll: true}); }
    else btn.focus();
  }
});

// ---------- render ----------
function imgOf(item) { return safeUrl(item.image) || (/^data:image\/jpeg;base64,/.test(item.image || '') ? item.image : ''); }
function platTag(item) { const p = PLAT[item.platform]; return p ? `<span class="plat" aria-hidden="true">${esc(p[0])}</span><span class="sr-only">${esc(p[1])}: </span>` : ''; }
function actions(item, i, o = {}) {
  const url = safeUrl(item.url), t = esc(item.title);
  const saved = o.unsave || savedTitles.has(item.title);
  return `<div class="acts">${url ? `<a class="act open" href="${esc(url)}" target="_blank" rel="noopener noreferrer" aria-label="Öffnen: ${t} (neues Fenster)">Öffnen ${ico('open')}</a>` : ''}
    <button type="button" class="act ${saved ? 'saved' : ''}" ${o.unsave ? `data-act="unsave" data-title="${t}"` : `data-act="save" data-i="${i}"`} aria-pressed="${saved}" aria-label="${o.unsave ? 'Gemerkt, zum Entfernen tippen' : 'Merken'}: ${t}">${ico('saved')}</button>
    ${o.votes ? `<button type="button" class="act ${votes[i] === 1 ? 'on' : ''}" data-act="up" data-i="${i}" aria-pressed="${votes[i] === 1}" aria-label="Mehr davon: ${t}">${ico('up')}</button><button type="button" class="act ${votes[i] === -1 ? 'on' : ''}" data-act="down" data-i="${i}" aria-pressed="${votes[i] === -1}" aria-label="Weniger davon: ${t}">${ico('down')}</button>` : ''}</div>`;
}
function card(item, i, n) {
  const cat = CATS[item.category] || 'sonstiges', img = imgOf(item), no = String(i + 1).padStart(2, '0');
  return `<article class="story-card cat-${cat}" data-cat="${esc(item.category)}" role="group" aria-roledescription="Karte" aria-label="Karte ${i + 1} von ${n}">
    <div class="story-visual ${img ? 'has-img' : ''}">${img ? `<img src="${esc(img)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">` : ''}<span class="story-no" aria-hidden="true">${no}</span><span class="story-of" aria-hidden="true">${no} / ${String(n).padStart(2, '0')}</span></div>
    <div class="story-body">
      <div class="head"><span class="cat-pill">${esc(item.category)}</span><span class="art-when">${esc(item.when)}</span></div>
      <h2>${esc(item.title)}</h2><p class="summary">${esc(item.summary)}</p>
      <div class="art-foot"><span class="src">${platTag(item)}<span>${esc(item.account || item.source)}</span></span>${actions(item, i, {votes: true})}</div>
    </div></article>`;
}
function article(item, i, o = {}) {
  const cat = CATS[item.category] || 'sonstiges', img = imgOf(item);
  return `<article class="feed-card cat-${cat}" data-cat="${esc(item.category)}">
    <div class="art-head">${o.no ? `<span class="art-no" aria-hidden="true">${String(i + 1).padStart(2, '0')}</span>` : ''}<span class="cat-pill">${esc(item.category)}</span><span class="art-when">${esc(item.when)}</span></div>
    <h2 class="art-title">${esc(item.title)}</h2>
    ${img && !o.compact ? `<div class="art-img"><img src="${esc(img)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer"></div>` : ''}
    <p class="fsum">${esc(item.summary)}</p>
    <div class="art-foot"><span class="src">${platTag(item)}<span>${esc(item.source)}</span></span>${actions(item, i, o)}</div></article>`;
}
function renderDrop(d) {
  if (!d || !Array.isArray(d.items)) { toast('Unerwartete Antwort vom Server. Seite neu laden.', true); return; }
  current = d; votes = {}; const items = d.items;
  $('resultsArea').hidden = false; $('todayEmpty').hidden = true; $('dropError').hidden = true;
  $('introTitle').textContent = d.title || 'Dein Drop'; $('introDate').textContent = d.date || ''; $('introText').textContent = d.intro || '';
  const m = d.meta || {};
  $('introCount').innerHTML = `<strong>${items.length}</strong> ${items.length === 1 ? 'Treffer' : 'Treffer'} aus ${+m.sources_ok || 0} von ${+m.sources_total || 0} Quellen`;
  let info = m.model && m.model !== 'fallback-ohne-ki' ? `Geschrieben von ${m.model}` : 'Ohne KI zusammengestellt (Modell nicht erreichbar)';
  if (m.images_analyzed) info += ` · ${m.images_analyzed} Bilder ausgewertet`;
  $('introModel').textContent = info;
  const failed = $('introFailed');
  if (m.failed && m.failed.length) { failed.hidden = false; failed.textContent = `Nicht erreichbar: ${m.failed.slice(0, 4).join(', ')}${m.failed.length > 4 ? ` und ${m.failed.length - 4} weitere` : ''}`; } else failed.hidden = true;
  const cats = [...new Set(items.map((x) => x.category))];
  $('catFilters').innerHTML = cats.length > 1 ? cats.map((c) => `<button type="button" class="chip active cat-${CATS[c] || 'sonstiges'}" data-cat="${esc(c)}" aria-pressed="true"><span class="dot"></span>${esc(c)}</button>`).join('') : '';
  $('storiesInner').innerHTML = items.map((x, i) => card(x, i, items.length)).join('');
  $('feedContainer').innerHTML = items.length ? items.map((x, i) => article(x, i, {no: true, votes: true})).join('') : '<div class="empty"><p>Diesmal nichts Passendes gefunden.<small>Füge unter Profil mehr Quellen hinzu oder beschreibe deine Interessen genauer.</small></p></div>';
  stagger($('feedContainer'));
  $('storyProgress').innerHTML = items.map((_, i) => `<span class="prog-seg ${i === 0 ? 'active' : ''}"></span>`).join('');
  $('storiesContainer').scrollLeft = 0; updateStepper();
  setView(view);
  M.revealDrop(view === 'feed');
}
function setView(v) {
  view = v; try { localStorage.setItem('cn-view', v); } catch (e) {}
  $('btnStories').setAttribute('aria-pressed', String(v === 'stories')); $('btnFeed').setAttribute('aria-pressed', String(v === 'feed'));
  $('viewSeg').style.setProperty('--idx', v === 'stories' ? 1 : 0);
  const has = current && current.items && current.items.length;
  $('storiesContainer').classList.toggle('hidden', v !== 'stories' || !has); $('storyProgress').hidden = !(v === 'stories' && has);
  $('storyNav').hidden = !(v === 'stories' && has);
  $('feedContainer').hidden = !(v === 'feed' || !has); $('catFilters').hidden = v !== 'feed';
}
$('btnStories').addEventListener('click', () => setView('stories')); $('btnFeed').addEventListener('click', () => setView('feed'));
function updateStepper() {
  const c = $('storiesContainer'), n = current ? current.items.length : 0, idx = Math.round(c.scrollLeft / (c.clientWidth || 1));
  document.querySelectorAll('.prog-seg').forEach((s, i) => s.classList.toggle('active', i <= idx));
  $('storyPrev').disabled = idx <= 0; $('storyNext').disabled = idx >= n - 1;
}
$('storiesContainer').addEventListener('scroll', () => requestAnimationFrame(updateStepper), {passive: true});
function stepStory(dir) { const c = $('storiesContainer'); c.scrollBy({left: dir * c.clientWidth, behavior: reduced() ? 'auto' : 'smooth'}); }
$('storyPrev').addEventListener('click', () => stepStory(-1)); $('storyNext').addEventListener('click', () => stepStory(1));
$('catFilters').addEventListener('click', (e) => {
  const c = e.target.closest('.chip'); if (!c) return; const on = c.classList.toggle('active'); c.setAttribute('aria-pressed', String(on));
  const act = new Set([...document.querySelectorAll('#catFilters .chip.active')].map((x) => x.dataset.cat));
  let shown = 0; document.querySelectorAll('#feedContainer .feed-card').forEach((f) => { f.hidden = !act.has(f.dataset.cat); if (!f.hidden) shown++; });
  $('filterStatus').textContent = `${shown} von ${current.items.length} Meldungen angezeigt`;
});
function pop(b) { b.classList.remove('pop'); void b.offsetWidth; b.classList.add('pop'); }
$('resultsArea').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-act]'); if (!b || !current) return;
  const i = +b.dataset.i, it = current.items[i];
  try {
    if (b.dataset.act === 'save') {
      const was = savedTitles.has(it.title);
      await api('/api/saved', was ? 'DELETE' : 'POST', it);
      was ? savedTitles.delete(it.title) : savedTitles.add(it.title);
      document.querySelectorAll(`#resultsArea [data-act="save"][data-i="${i}"]`).forEach((x) => { x.classList.toggle('saved', !was); x.setAttribute('aria-pressed', String(!was)); if (!was) { pop(x); M.burst(x, 'save'); } });
      toast(was ? 'Nicht mehr gemerkt' : 'Gemerkt');
    } else {
      const vote = b.dataset.act === 'up' ? 1 : -1;
      await api('/api/feedback', 'POST', {account: it.account, category: it.category, vote});
      votes[i] = vote;
      document.querySelectorAll(`#resultsArea [data-i="${i}"][data-act="up"], #resultsArea [data-i="${i}"][data-act="down"]`).forEach((x) => { const on = (x.dataset.act === 'up') === (vote === 1); x.classList.toggle('on', on); x.setAttribute('aria-pressed', String(on)); if (on) { pop(x); M.burst(x, vote === 1 ? 'up' : 'down'); } });
      toast(vote === 1 ? 'Mehr davon.' : 'Weniger davon.');
    }
  } catch (err) { toast('Das hat nicht geklappt.', true); }
});

// ---------- saved + history ----------
async function loadSaved() {
  const c = $('savedContainer');
  try {
    const s = (await api('/api/saved')).saved;
    savedTitles = new Set(s.map((x) => x.title));
    c.innerHTML = s.length ? s.map((x, i) => article(x, i, {unsave: true})).join('') : '<div class="empty"><p>Noch nichts gemerkt.<small>Tippe auf das Lesezeichen an einer Meldung, dann liegt sie hier.</small></p></div>';
    stagger(c);
  } catch (e) { c.innerHTML = '<div class="empty"><p>Gemerktes konnte nicht geladen werden.<small>Prüfe deine Verbindung und öffne den Bereich noch einmal.</small></p></div>'; }
}
$('savedContainer').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-act="unsave"]'); if (!b) return;
  try { await api('/api/saved', 'DELETE', {title: b.dataset.title}); loadSaved(); } catch (err) { toast('Das hat nicht geklappt.', true); }
});
function dayParts(day) { const d = new Date(String(day) + 'T12:00:00'); return isNaN(d) ? {d: '', m: esc(day), long: esc(day)} : {d: d.getDate(), m: esc(d.toLocaleDateString('de-DE', {month: 'short'}).replace('.', '')), long: esc(d.toLocaleDateString('de-DE', {weekday: 'long', day: 'numeric', month: 'long'}))}; }
async function loadHistory() {
  const c = $('historyContainer');
  try {
    const ds = (await api('/api/drops')).drops;
    c.innerHTML = ds.length ? ds.map((d) => { const p = dayParts(d.day);
      return `<button type="button" class="feed-card hist" data-id="${+d.id}"><span class="day">${p.d}<small>${p.m}</small></span><span><span class="t">${p.long}</span><span class="src">${+d.count} Treffer</span></span>${ico('next')}</button>`; }).join('')
      : '<div class="empty"><p>Noch kein Drop.<small>Sag uns unter Profil, was dich interessiert, und erzeuge deinen ersten Drop.</small></p><button class="btn-small" data-go="profile" type="button">Zum Profil</button></div>';
    stagger(c);
  } catch (e) { c.innerHTML = '<div class="empty"><p>Verlauf konnte nicht geladen werden.<small>Prüfe deine Verbindung und öffne den Bereich noch einmal.</small></p></div>'; }
}
$('historyContainer').addEventListener('click', async (e) => {
  const g = e.target.closest('[data-go]'); if (g) { showTab(g.dataset.go); return; }
  const h = e.target.closest('.hist'); if (!h) return;
  try { const d = await api('/api/drops/' + h.dataset.id); showTab('drop', true, true); renderDrop(d); syncEmpty(); } catch (err) { toast('Dieser Drop konnte nicht geladen werden.', true); }
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
  let hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (hadController) location.reload(); hadController = true; });
}
function setTheme(t, save) {
  const meta = {light: '#f5efe3', dark: '#12100d'};
  if (t === 'auto') document.documentElement.removeAttribute('data-theme'); else document.documentElement.setAttribute('data-theme', t);
  document.querySelectorAll('#themeSeg [data-theme-pick]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.themePick === t)));
  $('themeSeg').style.setProperty('--idx', ['auto', 'light', 'dark'].indexOf(t));
  document.querySelectorAll('meta[name="theme-color"]').forEach((m, i) => { m.content = t === 'auto' ? (i === 0 ? meta.dark : meta.light) : meta[t]; if (t !== 'auto') m.removeAttribute('media'); else m.setAttribute('media', i === 0 ? '(prefers-color-scheme: dark)' : '(prefers-color-scheme: light)'); });
  if (save) { try { localStorage.setItem('cn-theme', t); } catch (e) {} }
}
$('landTheme').addEventListener('click', () => { const el = document.documentElement.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'); setTheme(el === 'dark' ? 'light' : 'dark', true); });
$('themeSeg').addEventListener('click', (e) => { const b = e.target.closest('[data-theme-pick]'); if (b) setTheme(b.dataset.themePick, true); });
let savedTheme = 'dark'; try { savedTheme = localStorage.getItem('cn-theme') || 'dark'; } catch (e) {}
setTheme(savedTheme, false);
setEdition();
fontsReady.then(() => M.scramble($('logoWord'), 900));
boot();
