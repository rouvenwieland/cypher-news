const CACHE_NAME = 'cypher-news-v2';
const urlsToCache = [
  '/',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/manifest.json',
  '/data/sample_newsletter.json',
  '/static/fonts/PressStart2P.ttf',
  '/static/fonts/VT323.ttf',
  '/static/fonts/SpaceGrotesk.ttf'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});