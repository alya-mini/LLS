const CACHE = 'time-travel-v1';
const ASSETS = ['/', '/static/css/timeline.css', '/static/js/chat.js', '/static/js/age.js', '/static/js/timeline.js', '/static/js/pivot.js'];
self.addEventListener('install', (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS))));
self.addEventListener('fetch', (e) => e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request))));
