// Coinnect — Service Worker
// Cache-first for static assets, network-first for API, offline fallback

const CACHE_NAME = 'coinnect-v1';
const STATIC_CACHE = 'coinnect-static-v1';

const PRECACHE_URLS = [
  '/',
  '/static/logo.svg',
  '/static/logo-192.png',
  '/static/logo-512.png',
  '/static/tailwind.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(PRECACHE_URLS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME && key !== STATIC_CACHE)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  if (event.request.method !== 'GET') return;
  if (url.origin !== location.origin) return;

  // API calls: network-first, cached fallback
  if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  // Static assets: cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  // HTML: network-first with offline fallback
  event.respondWith(networkFirstWithOffline(event.request));
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 503, statusText: 'Offline' });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response(JSON.stringify({ error: 'offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(offlineHTML(), {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }
}

function offlineHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offline — Coinnect</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0F172A; color: #f1f5f9; font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; text-align: center; padding: 24px; }
  .wrap { max-width: 360px; }
  .icon { font-size: 64px; margin-bottom: 16px; }
  h1 { font-size: 24px; margin-bottom: 12px; }
  p { color: #94a3b8; font-size: 15px; line-height: 1.6; margin-bottom: 24px; }
  button { background: #6366f1; color: #fff; border: none; padding: 14px 32px; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; }
</style>
</head>
<body>
<div class="wrap">
  <div class="icon">&#128241;</div>
  <h1>You're offline</h1>
  <p>Coinnect needs an internet connection to fetch live exchange rates. Reconnect and try again.</p>
  <button onclick="location.reload()">Retry</button>
</div>
</body>
</html>`;
}
