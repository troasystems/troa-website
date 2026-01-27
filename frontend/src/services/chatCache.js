/**
 * Chat Cache Service
 * Provides aggressive client-side caching for chat functionality
 */

// IndexedDB setup for persistent chat storage
const DB_NAME = 'troa-chat-cache';
const DB_VERSION = 1;
const STORES = {
  groups: 'groups',
  messages: 'messages',
  attachments: 'attachments'
};

let dbInstance = null;

// Initialize IndexedDB
async function initDB() {
  if (dbInstance) return dbInstance;

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      dbInstance = request.result;
      resolve(dbInstance);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Groups store
      if (!db.objectStoreNames.contains(STORES.groups)) {
        const groupStore = db.createObjectStore(STORES.groups, { keyPath: 'id' });
        groupStore.createIndex('timestamp', 'cachedAt', { unique: false });
      }

      // Messages store
      if (!db.objectStoreNames.contains(STORES.messages)) {
        const messageStore = db.createObjectStore(STORES.messages, { keyPath: 'id' });
        messageStore.createIndex('groupId', 'group_id', { unique: false });
        messageStore.createIndex('timestamp', 'created_at', { unique: false });
      }

      // Attachments store (for images/files)
      if (!db.objectStoreNames.contains(STORES.attachments)) {
        const attachStore = db.createObjectStore(STORES.attachments, { keyPath: 'id' });
        attachStore.createIndex('timestamp', 'cachedAt', { unique: false });
      }
    };
  });
}

// Generic store operations
async function putInStore(storeName, data) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.put({ ...data, cachedAt: Date.now() });
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function getFromStore(storeName, key) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.get(key);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getAllFromStore(storeName) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function deleteFromStore(storeName, key) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(key);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// ============ GROUP CACHING ============

// Cache expiry times
const CACHE_EXPIRY = {
  groups: 5 * 60 * 1000,      // 5 minutes
  messages: 2 * 60 * 1000,     // 2 minutes  
  attachments: 24 * 60 * 60 * 1000  // 24 hours for attachments
};

// In-memory cache for ultra-fast access
const memoryCache = {
  groups: null,
  groupsTimestamp: 0,
  messages: new Map(), // groupId -> { messages, timestamp }
  attachments: new Map() // attachmentId -> { data, timestamp }
};

/**
 * Cache chat groups
 */
export async function cacheGroups(groups) {
  // Memory cache
  memoryCache.groups = groups;
  memoryCache.groupsTimestamp = Date.now();

  // IndexedDB cache
  try {
    for (const group of groups) {
      await putInStore(STORES.groups, group);
    }
  } catch (e) {
    console.warn('[ChatCache] Failed to persist groups to IndexedDB:', e);
  }
}

/**
 * Get cached groups
 * Returns null if cache is stale
 */
export async function getCachedGroups() {
  // Check memory cache first
  if (memoryCache.groups && Date.now() - memoryCache.groupsTimestamp < CACHE_EXPIRY.groups) {
    return memoryCache.groups;
  }

  // Try IndexedDB
  try {
    const groups = await getAllFromStore(STORES.groups);
    if (groups && groups.length > 0) {
      const isStale = groups.some(g => Date.now() - (g.cachedAt || 0) > CACHE_EXPIRY.groups);
      if (!isStale) {
        memoryCache.groups = groups;
        memoryCache.groupsTimestamp = Date.now();
        return groups;
      }
    }
  } catch (e) {
    console.warn('[ChatCache] Failed to read groups from IndexedDB:', e);
  }

  return null;
}

/**
 * Check if groups cache is valid
 */
export function isGroupsCacheValid() {
  return memoryCache.groups && Date.now() - memoryCache.groupsTimestamp < CACHE_EXPIRY.groups;
}

// ============ MESSAGE CACHING ============

/**
 * Cache messages for a group
 */
export async function cacheMessages(groupId, messages) {
  // Memory cache
  memoryCache.messages.set(groupId, {
    messages,
    timestamp: Date.now()
  });

  // IndexedDB cache
  try {
    for (const message of messages) {
      await putInStore(STORES.messages, message);
    }
  } catch (e) {
    console.warn('[ChatCache] Failed to persist messages to IndexedDB:', e);
  }
}

/**
 * Get cached messages for a group
 */
export async function getCachedMessages(groupId) {
  // Check memory cache first
  const cached = memoryCache.messages.get(groupId);
  if (cached && Date.now() - cached.timestamp < CACHE_EXPIRY.messages) {
    return cached.messages;
  }

  // Try IndexedDB
  try {
    const db = await initDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORES.messages, 'readonly');
      const store = transaction.objectStore(STORES.messages);
      const index = store.index('groupId');
      const request = index.getAll(groupId);

      request.onsuccess = () => {
        const messages = request.result;
        if (messages && messages.length > 0) {
          // Sort by created_at
          messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
          
          // Check if stale
          const isStale = messages.some(m => Date.now() - (m.cachedAt || 0) > CACHE_EXPIRY.messages);
          if (!isStale) {
            memoryCache.messages.set(groupId, { messages, timestamp: Date.now() });
            return resolve(messages);
          }
        }
        resolve(null);
      };
      request.onerror = () => reject(request.error);
    });
  } catch (e) {
    console.warn('[ChatCache] Failed to read messages from IndexedDB:', e);
    return null;
  }
}

/**
 * Add a single message to cache (optimistic update)
 */
export function addMessageToCache(groupId, message) {
  const cached = memoryCache.messages.get(groupId);
  if (cached) {
    cached.messages = [...cached.messages, message];
    cached.timestamp = Date.now();
  }
  
  // Also persist to IndexedDB
  putInStore(STORES.messages, message).catch(e => 
    console.warn('[ChatCache] Failed to persist message:', e)
  );
}

/**
 * Update a message in cache
 */
export function updateMessageInCache(groupId, messageId, updates) {
  const cached = memoryCache.messages.get(groupId);
  if (cached) {
    cached.messages = cached.messages.map(m => 
      m.id === messageId ? { ...m, ...updates } : m
    );
  }
}

/**
 * Check if messages cache is valid for a group
 */
export function isMessagesCacheValid(groupId) {
  const cached = memoryCache.messages.get(groupId);
  return cached && Date.now() - cached.timestamp < CACHE_EXPIRY.messages;
}

// ============ ATTACHMENT CACHING ============

/**
 * Cache an attachment (image/file data)
 */
export async function cacheAttachment(attachmentId, data) {
  // Memory cache
  memoryCache.attachments.set(attachmentId, {
    data,
    timestamp: Date.now()
  });

  // IndexedDB cache for persistence
  try {
    await putInStore(STORES.attachments, { id: attachmentId, ...data });
  } catch (e) {
    console.warn('[ChatCache] Failed to persist attachment:', e);
  }
}

/**
 * Get cached attachment
 */
export async function getCachedAttachment(attachmentId) {
  // Check memory cache first
  const cached = memoryCache.attachments.get(attachmentId);
  if (cached && Date.now() - cached.timestamp < CACHE_EXPIRY.attachments) {
    return cached.data;
  }

  // Try IndexedDB
  try {
    const data = await getFromStore(STORES.attachments, attachmentId);
    if (data && Date.now() - (data.cachedAt || 0) < CACHE_EXPIRY.attachments) {
      memoryCache.attachments.set(attachmentId, { data, timestamp: Date.now() });
      return data;
    }
  } catch (e) {
    console.warn('[ChatCache] Failed to read attachment from IndexedDB:', e);
  }

  return null;
}

// ============ CACHE MANAGEMENT ============

/**
 * Clear all chat caches
 */
export async function clearAllChatCache() {
  // Clear memory cache
  memoryCache.groups = null;
  memoryCache.groupsTimestamp = 0;
  memoryCache.messages.clear();
  memoryCache.attachments.clear();

  // Clear IndexedDB
  try {
    const db = await initDB();
    const transaction = db.transaction([STORES.groups, STORES.messages, STORES.attachments], 'readwrite');
    transaction.objectStore(STORES.groups).clear();
    transaction.objectStore(STORES.messages).clear();
    transaction.objectStore(STORES.attachments).clear();
  } catch (e) {
    console.warn('[ChatCache] Failed to clear IndexedDB:', e);
  }
}

/**
 * Clear messages cache for a specific group
 */
export function clearGroupMessagesCache(groupId) {
  memoryCache.messages.delete(groupId);
}

/**
 * Invalidate groups cache
 */
export function invalidateGroupsCache() {
  memoryCache.groups = null;
  memoryCache.groupsTimestamp = 0;
}

/**
 * Prune old cached data
 */
export async function pruneOldCache() {
  const now = Date.now();
  
  // Prune old attachments (older than 7 days)
  const maxAge = 7 * 24 * 60 * 60 * 1000;
  
  try {
    const db = await initDB();
    const transaction = db.transaction(STORES.attachments, 'readwrite');
    const store = transaction.objectStore(STORES.attachments);
    const request = store.openCursor();
    
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        if (now - (cursor.value.cachedAt || 0) > maxAge) {
          cursor.delete();
        }
        cursor.continue();
      }
    };
  } catch (e) {
    console.warn('[ChatCache] Failed to prune old cache:', e);
  }
}

// Initialize and prune on load
if (typeof window !== 'undefined') {
  initDB().then(() => pruneOldCache()).catch(console.warn);
}

export default {
  cacheGroups,
  getCachedGroups,
  isGroupsCacheValid,
  cacheMessages,
  getCachedMessages,
  addMessageToCache,
  updateMessageInCache,
  isMessagesCacheValid,
  cacheAttachment,
  getCachedAttachment,
  clearAllChatCache,
  clearGroupMessagesCache,
  invalidateGroupsCache,
  pruneOldCache
};
