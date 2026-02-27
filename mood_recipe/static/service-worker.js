const CACHE_NAME = 'mood-recipe-v1';
const ASSETS = [
  '/',
  '/static/css/restaurant.css',
  '/static/js/main.js',
  '/static/js/recipe.js',
  '/static/js/food3d.js',
  '/static/js/nutrition.js',
  '/static/js/emotion.js'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
});

self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
