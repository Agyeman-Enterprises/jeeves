// Jeeves Service Worker — enables PWA install + offline shell
const CACHE_NAME = 'jeeves-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Network-first for API calls, cache-first for static
  if (e.request.url.includes('/app')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
  }
});
