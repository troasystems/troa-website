import { useState, useEffect, useCallback, useRef } from 'react';

// In-memory cache with TTL
const memoryCache = new Map();
const CACHE_TTL = {
  short: 60 * 1000,       // 1 minute
  medium: 5 * 60 * 1000,  // 5 minutes
  long: 30 * 60 * 1000,   // 30 minutes
  veryLong: 60 * 60 * 1000 // 1 hour
};

// Cache entry structure
class CacheEntry {
  constructor(data, ttl = CACHE_TTL.medium) {
    this.data = data;
    this.timestamp = Date.now();
    this.ttl = ttl;
  }

  isValid() {
    return Date.now() - this.timestamp < this.ttl;
  }

  isStale() {
    return Date.now() - this.timestamp > this.ttl / 2;
  }
}

// Get from memory cache
export function getFromCache(key) {
  const entry = memoryCache.get(key);
  if (entry && entry.isValid()) {
    return entry.data;
  }
  if (entry && !entry.isValid()) {
    memoryCache.delete(key);
  }
  return null;
}

// Set to memory cache
export function setToCache(key, data, ttl = CACHE_TTL.medium) {
  memoryCache.set(key, new CacheEntry(data, ttl));
}

// Check if cache is stale (needs background refresh)
export function isCacheStale(key) {
  const entry = memoryCache.get(key);
  return entry ? entry.isStale() : true;
}

// Clear specific cache key
export function clearCache(key) {
  memoryCache.delete(key);
}

// Clear all cache
export function clearAllCache() {
  memoryCache.clear();
}

// Hook for cached API calls with stale-while-revalidate
export function useCachedFetch(url, options = {}) {
  const {
    ttl = CACHE_TTL.medium,
    enabled = true,
    staleWhileRevalidate = true,
    onSuccess,
    onError,
    dependencies = []
  } = options;

  const [data, setData] = useState(() => getFromCache(url));
  const [loading, setLoading] = useState(!getFromCache(url));
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  const fetchData = useCallback(async (forceRefresh = false) => {
    if (!enabled || !url) return;

    // Check cache first
    const cachedData = getFromCache(url);
    if (cachedData && !forceRefresh) {
      setData(cachedData);
      setLoading(false);
      
      // Background refresh if stale
      if (staleWhileRevalidate && isCacheStale(url)) {
        backgroundFetch();
      }
      return;
    }

    setLoading(true);
    setError(null);

    // Abort previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const token = localStorage.getItem('session_token');
      const response = await fetch(url, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      setToCache(url, result, ttl);
      setData(result);
      onSuccess?.(result);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err);
        onError?.(err);
        // Use stale cache on error
        if (cachedData) {
          setData(cachedData);
        }
      }
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, enabled, ttl, staleWhileRevalidate, onSuccess, onError]);

  const backgroundFetch = useCallback(async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      if (response.ok) {
        const result = await response.json();
        setToCache(url, result, ttl);
        setData(result);
      }
    } catch (e) {
      // Silently fail background refresh
    }
  }, [url, ttl]);

  const refetch = useCallback(() => fetchData(true), [fetchData]);

  useEffect(() => {
    fetchData();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  return { data, loading, error, refetch };
}

// Hook for prefetching data
export function usePrefetch() {
  const prefetch = useCallback(async (urls, ttl = CACHE_TTL.medium) => {
    const token = localStorage.getItem('session_token');
    
    const promises = urls.map(async (url) => {
      // Skip if already cached and valid
      if (getFromCache(url)) return;

      try {
        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        });
        if (response.ok) {
          const data = await response.json();
          setToCache(url, data, ttl);
        }
      } catch (e) {
        // Silently fail prefetch
      }
    });

    await Promise.allSettled(promises);
  }, []);

  return prefetch;
}

// Hook for image preloading
export function useImagePreload() {
  const preloadedRef = useRef(new Set());

  const preload = useCallback((urls) => {
    const urlList = Array.isArray(urls) ? urls : [urls];
    
    urlList.forEach((url) => {
      if (!url || preloadedRef.current.has(url)) return;
      
      const img = new Image();
      img.src = url;
      preloadedRef.current.add(url);
    });
  }, []);

  return preload;
}

// Prefetch common routes data
export async function prefetchCommonData() {
  const baseUrl = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? window.location.origin
    : process.env.REACT_APP_BACKEND_URL || '';
  
  const endpoints = [
    `${baseUrl}/api/amenities`,
    `${baseUrl}/api/committee`,
    `${baseUrl}/api/events`
  ];

  const token = localStorage.getItem('session_token');

  for (const url of endpoints) {
    if (getFromCache(url)) continue;

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      if (response.ok) {
        const data = await response.json();
        setToCache(url, data, CACHE_TTL.long);
      }
    } catch (e) {
      // Silently fail
    }
  }
}

// Cache TTL constants export
export { CACHE_TTL };

export default {
  useCachedFetch,
  usePrefetch,
  useImagePreload,
  prefetchCommonData,
  getFromCache,
  setToCache,
  clearCache,
  clearAllCache,
  CACHE_TTL
};
