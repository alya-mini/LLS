const CACHE = 'aura-scanner-v1';
const ASSETS = ['/', '/static/css/mystic.css', '/static/js/main.js'];
self.addEventListener('install', (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS))));
self.addEventListener('fetch', (e) => {
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
