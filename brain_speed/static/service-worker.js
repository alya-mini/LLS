const CACHE_NAME = 'brain-speed-v1';
const URLS = ['/', '/static/css/style.css', '/static/js/main.js', '/static/js/tests.js', '/static/js/multiplayer.js'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS)));
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).catch(() => caches.match('/')))
  );
});
