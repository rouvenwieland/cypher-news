const CACHE_NAME = 'ki-newsletter-cache-v1';
const urlsToCache = [
  '/',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/manifest.json',
  '/data/sample_newsletter.json'
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