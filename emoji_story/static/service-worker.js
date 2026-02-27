const CACHE = 'emoji-story-v1';
const ASSETS = [
  '/',
  '/manifest.json',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/speech.js',
  '/static/js/animation.js',
  '/static/js/video.js'
];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
});
self.addEventListener('fetch', (event) => {
  event.respondWith(caches.match(event.request).then((res) => res || fetch(event.request).catch(() => caches.match('/'))));
});
