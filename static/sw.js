const CACHE_STATIC = 'cypher-news-static-v3';
const CACHE_DROP = 'cypher-news-drop-v1';

const STATIC_URLS = [
  '/',
  '/static/css/style.css',
  '/static/js/rain.js',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/manifest.json',
  '/data/sample_newsletter.json',
  '/static/img/field_pix.jpg',
  '/static/img/field_duo.jpg',
  '/static/img/money_pix.jpg',
  '/static/img/money_duo.jpg',
  '/static/fonts/PressStart2P.ttf',
  '/static/fonts/VT323.ttf',
  '/static/fonts/SpaceGrotesk.ttf'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_STATIC)
      .then(cache => cache.addAll(STATIC_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names => {
      return Promise.all(
        names.filter(n => n !== CACHE_STATIC && n !== CACHE_DROP)
          .map(n => caches.delete(n))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  if (url.pathname === '/api/generate' && event.request.method === 'POST') {
    event.respondWith(
      fetch(event.request.clone())
        .then(response => {
          if (response.ok) {
            const cloned = response.clone();
            caches.open(CACHE_DROP).then(cache => {
              cache.put('/last-drop', cloned);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match('/last-drop').then(r => {
            return r || caches.match('/data/sample_newsletter.json');
          });
        })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(response => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          const cloned = response.clone();
          caches.open(CACHE_STATIC).then(cache => {
            cache.put(event.request, cloned);
          });
          return response;
        }).catch(() => {
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
        });
      })
  );
});

self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const opts = { body: data.body || '', icon: '/static/icon-192.png', badge: '/static/icon-192.png', vibrate: [200, 100, 200] };
    event.waitUntil(self.registration.showNotification(data.title || 'Cypher News', opts));
  }
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clients => {
      if (clients.length > 0) {
        clients[0].focus();
      } else {
        clients.openWindow('/');
      }
    })
  );
});