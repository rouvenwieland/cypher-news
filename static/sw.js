const CACHE = 'cypher-news-v5';  // bump on every release that changes cached files
const SHELL = ['/static/css/style.css', '/static/css/app.css', '/static/js/rain.js', '/static/js/app.js', '/static/icon-192.png', '/static/icon-512.png',
  '/static/fonts/PressStart2P.ttf', '/static/fonts/VT323.ttf', '/static/fonts/SpaceGrotesk.ttf'];

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
    e.respondWith(fetch(e.request).catch(() => caches.match('/static/icon-192.png')));
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
