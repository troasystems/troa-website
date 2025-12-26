// TROA PWA Service Worker - High Performance Caching v2
const CACHE_VERSION = 'v2';
const STATIC_CACHE = `troa-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `troa-dynamic-${CACHE_VERSION}`;
const IMAGE_CACHE = `troa-images-${CACHE_VERSION}`;
const API_CACHE = `troa-api-${CACHE_VERSION}`;

// Cache expiration times (in milliseconds)
const CACHE_EXPIRY = {
  api: 5 * 60 * 1000,        // 5 minutes for API data
  apiStale: 60 * 60 * 1000,  // 1 hour stale-while-revalidate
  images: 30 * 24 * 60 * 60 * 1000, // 30 days for images
  static: 7 * 24 * 60 * 60 * 1000,  // 7 days for static assets
};

// Static assets to cache on install (app shell)
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.svg',
  '/offline.html',
  '/icons/icon-72x72.png',
  '/icons/icon-96x96.png',
  '/icons/icon-128x128.png',
  '/icons/icon-144x144.png',
  '/icons/icon-152x152.png',
  '/icons/icon-192x192.png',
  '/icons/icon-384x384.png',
  '/icons/icon-512x512.png'
];

// API endpoints that can be cached (read-only data)
const CACHEABLE_API_PATTERNS = [
  '/api/amenities',
  '/api/committee',
  '/api/gallery',
  '/api/events',
  '/api/auth/user'
];

// API endpoints that should NEVER be cached
// API endpoints that should NEVER be cached by service worker
// (Chat is cached via IndexedDB in chatCache.js for better control)
const NO_CACHE_API_PATTERNS = [
  '/api/auth/login',
  '/api/auth/register',
  '/api/auth/logout',
  '/api/payment',
  '/api/bookings',
  '/api/push'
];

// Chat endpoints use short cache for offline support
const CHAT_CACHE_PATTERNS = [
  '/api/chat/groups',
  '/api/chat/messages',
  '/api/chat/attachments'
];

// External image domains to cache
const CACHEABLE_IMAGE_DOMAINS = [
  'images.unsplash.com',
  'customer-assets.emergentagent.com',
  'lh3.googleusercontent.com' // Google profile pictures
];

// ============ INSTALL EVENT ============
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker v2...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Pre-caching app shell');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((err) => console.error('[SW] Pre-cache failed:', err))
  );
});

// ============ ACTIVATE EVENT ============
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker v2...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            // Delete old version caches
            return name.startsWith('troa-') && !name.includes(CACHE_VERSION);
          })
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// ============ FETCH EVENT ============
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Handle different request types
  if (isApiRequest(url)) {
    event.respondWith(handleApiRequest(request, url));
  } else if (isImageRequest(url, request)) {
    event.respondWith(handleImageRequest(request, url));
  } else if (isStaticAsset(url)) {
    event.respondWith(handleStaticRequest(request));
  } else if (isNavigationRequest(request)) {
    event.respondWith(handleNavigationRequest(request));
  } else {
    event.respondWith(handleDynamicRequest(request));
  }
});

// ============ REQUEST TYPE CHECKERS ============
function isApiRequest(url) {
  return url.pathname.startsWith('/api/');
}

function isImageRequest(url, request) {
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico'];
  const isImagePath = imageExtensions.some(ext => url.pathname.toLowerCase().endsWith(ext));
  const isImageType = request.destination === 'image';
  const isCacheableExternal = CACHEABLE_IMAGE_DOMAINS.some(domain => url.hostname.includes(domain));
  
  return isImagePath || isImageType || isCacheableExternal;
}

function isStaticAsset(url) {
  const staticExtensions = ['.js', '.css', '.woff', '.woff2', '.ttf', '.eot'];
  return staticExtensions.some(ext => url.pathname.endsWith(ext));
}

function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

// ============ REQUEST HANDLERS ============

// Stale-While-Revalidate for API requests
async function handleApiRequest(request, url) {
  const cacheKey = getCacheKey(request);
  
  // Check if this API should not be cached
  if (NO_CACHE_API_PATTERNS.some(pattern => url.pathname.includes(pattern))) {
    return fetch(request).catch(() => new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    }));
  }

  // Check if this API should be cached
  const shouldCache = CACHEABLE_API_PATTERNS.some(pattern => url.pathname.includes(pattern));
  
  if (!shouldCache) {
    // Network only for non-cacheable APIs
    return fetch(request).catch(() => caches.match(cacheKey));
  }

  // Stale-While-Revalidate strategy
  const cache = await caches.open(API_CACHE);
  const cachedResponse = await cache.match(cacheKey);
  
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        // Store with timestamp
        const responseToCache = response.clone();
        const headers = new Headers(responseToCache.headers);
        headers.set('sw-cache-time', Date.now().toString());
        
        cache.put(cacheKey, new Response(responseToCache.body, {
          status: responseToCache.status,
          statusText: responseToCache.statusText,
          headers: headers
        }));
      }
      return response;
    })
    .catch(() => null);

  // Return cached response immediately if available
  if (cachedResponse) {
    const cacheTime = parseInt(cachedResponse.headers.get('sw-cache-time') || '0');
    const age = Date.now() - cacheTime;
    
    // If cache is fresh, return it and update in background
    if (age < CACHE_EXPIRY.api) {
      fetchPromise; // Fire and forget background update
      return cachedResponse;
    }
    
    // If cache is stale but within stale limit, return it but wait for network
    if (age < CACHE_EXPIRY.apiStale) {
      const networkResponse = await fetchPromise;
      return networkResponse || cachedResponse;
    }
  }

  // No cache or too old - wait for network
  const networkResponse = await fetchPromise;
  return networkResponse || cachedResponse || new Response(JSON.stringify({ error: 'Offline' }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' }
  });
}

// Cache-First with long expiry for images
async function handleImageRequest(request, url) {
  const cache = await caches.open(IMAGE_CACHE);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    // Return cached image immediately
    // Background refresh only if older than 7 days
    const cacheTime = parseInt(cachedResponse.headers.get('sw-cache-time') || '0');
    if (Date.now() - cacheTime > 7 * 24 * 60 * 60 * 1000) {
      refreshImageCache(request, cache);
    }
    return cachedResponse;
  }

  // Fetch and cache
  try {
    const response = await fetch(request);
    if (response.ok) {
      const responseToCache = response.clone();
      const headers = new Headers(responseToCache.headers);
      headers.set('sw-cache-time', Date.now().toString());
      
      cache.put(request, new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers
      }));
    }
    return response;
  } catch (error) {
    // Return placeholder for failed image loads
    return new Response('', { status: 404 });
  }
}

// Background image refresh
async function refreshImageCache(request, cache) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const headers = new Headers(response.headers);
      headers.set('sw-cache-time', Date.now().toString());
      cache.put(request, new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: headers
      }));
    }
  } catch (e) {
    // Silently fail background refresh
  }
}

// Cache-First for static assets (JS, CSS, fonts)
async function handleStaticRequest(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return new Response('', { status: 404 });
  }
}

// Network-First with offline fallback for navigation
async function handleNavigationRequest(request) {
  try {
    const response = await fetch(request);
    // Cache the page for offline use
    const cache = await caches.open(DYNAMIC_CACHE);
    cache.put(request, response.clone());
    return response;
  } catch (error) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Fall back to offline page
    return caches.match('/offline.html');
  }
}

// Cache-First for other dynamic requests
async function handleDynamicRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return new Response('', { status: 404 });
  }
}

// ============ UTILITY FUNCTIONS ============
function getCacheKey(request) {
  const url = new URL(request.url);
  // Remove auth-related query params for cache key
  url.searchParams.delete('token');
  url.searchParams.delete('_t');
  return url.toString();
}

// ============ PUSH NOTIFICATIONS ============
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  let data = {
    title: 'TROA Notification',
    body: 'You have a new notification from The Retreat',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    tag: 'troa-notification',
    data: { url: '/' }
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag,
    vibrate: [100, 50, 100],
    data: data.data,
    actions: [
      { action: 'open', title: 'Open' },
      { action: 'close', title: 'Dismiss' }
    ],
    requireInteraction: false // Changed to false for less intrusive notifications
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// ============ NOTIFICATION CLICK ============
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(urlToOpen);
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// ============ BACKGROUND SYNC ============
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-bookings') {
    event.waitUntil(syncPendingBookings());
  }
});

async function syncPendingBookings() {
  console.log('[SW] Syncing pending bookings...');
  // Implementation for syncing pending offline bookings
}

// ============ PERIODIC BACKGROUND SYNC ============
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'refresh-data') {
    event.waitUntil(refreshCachedData());
  }
});

async function refreshCachedData() {
  console.log('[SW] Periodic data refresh');
  // Pre-fetch commonly accessed data
  const endpoints = ['/api/amenities', '/api/events', '/api/committee'];
  
  for (const endpoint of endpoints) {
    try {
      const response = await fetch(endpoint);
      if (response.ok) {
        const cache = await caches.open(API_CACHE);
        const headers = new Headers(response.headers);
        headers.set('sw-cache-time', Date.now().toString());
        cache.put(endpoint, new Response(response.clone().body, {
          status: response.status,
          statusText: response.statusText,
          headers: headers
        }));
      }
    } catch (e) {
      // Silently fail
    }
  }
}

// ============ MESSAGE HANDLER ============
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
  
  if (event.data === 'clearCache') {
    caches.keys().then((names) => {
      names.forEach((name) => caches.delete(name));
    });
  }
  
  if (event.data?.type === 'CACHE_URLS') {
    const urls = event.data.urls;
    caches.open(DYNAMIC_CACHE).then((cache) => {
      cache.addAll(urls);
    });
  }
});
