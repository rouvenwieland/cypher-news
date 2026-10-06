const CACHE = 'cypher-news-v4';
const SHELL = ['/static/css/style.css', '/static/css/app.css', '/static/js/rain.js', '/static/js/app.js', '/static/icon-192.png', '/static/icon-512.png',
  '/static/fonts/PressStart2P.ttf', '/static/fonts/VT323.ttf', '/static/fonts/SpaceGrotesk.ttf'];

self.addEventListener('install', (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', (e) => e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));

self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.startsWith('/api/')) return; // never cache user data
  if (u.pathname.startsWith('/static/')) {
    e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
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
