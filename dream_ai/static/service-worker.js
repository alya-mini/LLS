const CACHE='dream-ai-v1';
const ASSETS=['/','/static/css/dream.css','/static/js/dream.js','/static/js/astro.js','/static/js/fractal.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS))));
self.addEventListener('fetch',e=>e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request))));
