const CACHE = 'scent-ai-v1';
const ASSETS = [
  '/',
  '/static/css/molecular.css',
  '/static/js/main.js',
  '/static/js/camera.js',
  '/static/js/scent.js',
  '/static/js/molecule.js',
  '/static/js/slider.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener('fetch', (e) => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
