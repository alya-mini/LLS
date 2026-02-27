const CACHE_NAME = 'voice-avatar-v1';
const ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/voice.js',
  '/static/js/avatar.js',
  '/static/js/animation.js',
  '/static/js/video.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener('fetch', (event) => {
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
});
