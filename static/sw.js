const CACHE = 'cypher-news-v8';  // bump on every release that changes cached files
const SHELL = ['/static/css/style.css', '/static/css/app.css', '/static/css/landing.css', '/static/vendor/lenis.css', '/static/vendor/gsap.min.js', '/static/vendor/ScrollTrigger.min.js', '/static/vendor/lenis.min.js', '/static/js/rain.js', '/static/js/motion.js', '/static/js/app.js', '/static/icon-192.png', '/static/icon-512.png',
  '/static/fonts/Newsreader.woff2', '/static/fonts/Newsreader-Italic.woff2', '/static/fonts/VT323.ttf', '/static/fonts/SpaceGrotesk.ttf'];
const OFFLINE = '<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline - Cypher News</title>' +
  '<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0c0a08;color:#f4eee3;font:19px/1.5 Georgia,serif;text-align:center;padding:24px}' +
  'h1{font-size:34px;margin:0 0 8px}p{margin:0 0 18px;color:#d2c8b9}button{font:600 16px system-ui,sans-serif;background:#ff6a2b;color:#1a0d05;border:0;border-radius:12px;padding:14px 22px;min-height:48px}</style>' +
  '<main><h1>Gerade offline.</h1><p>Cypher News braucht eine Verbindung, um deinen Drop zu laden.</p><button onclick="location.reload()">Erneut versuchen</button></main></html>';

self.addEventListener('install', (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', (e) => e.waitUntil((async () => {
  const old = (await caches.keys()).filter((k) => k !== CACHE);
  await Promise.all(old.map((k) => caches.delete(k)));
  await self.clients.claim();
  if (old.length) { // upgrade: reload open pages so they run the new code instead of the old cached one
    for (const c of await self.clients.matchAll({type: 'window'})) { try { await c.navigate(c.url); } catch (err) {} }
  }
})()));

self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.startsWith('/api/')) return; // never cache user data
  if (/^\/static\/(js|css)\//.test(u.pathname) || u.pathname === '/static/manifest.json') {
    // code: network first (always the newest version), cache only as offline fallback
    e.respondWith(fetch(e.request).then((r) => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); } return r; })
      .catch(() => caches.match(e.request)));
  } else if (u.pathname.startsWith('/static/')) {
    e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));  // fonts and icons never change
  } else {
    e.respondWith(fetch(e.request).catch(() => e.request.mode === 'navigate'
      ? new Response(OFFLINE, {status: 503, headers: {'Content-Type': 'text/html; charset=utf-8'}}) : Response.error()));
  }
});

self.addEventListener('push', (e) => {
  let d = {}; try { d = e.data.json(); } catch (err) {}
  e.waitUntil(self.registration.showNotification(d.title || 'Cypher News', {body: d.body || '', icon: '/static/icon-192.png', badge: '/static/icon-192.png', data: {url: d.url || '/'}}));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  e.waitUntil(clients.matchAll({type: 'window'}).then((cs) => cs.length ? cs[0].focus() : clients.openWindow((e.notification.data && e.notification.data.url) || '/')));
});
