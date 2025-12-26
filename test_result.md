# PWA & Chat Caching Test Plan

## Features to Test

### 1. Service Worker Caching
- Service worker registration
- Static assets caching (JS, CSS, fonts)
- API response caching (amenities, events, committee)
- Image caching from external domains

### 2. Chat Caching (IndexedDB + Memory)
- Groups list caching
- Messages caching per group
- Attachments/images caching
- Cache invalidation on new messages

### 3. Lazy Loading & Code Splitting
- Pages load on demand
- Suspense fallback shows during load

### 4. API Cache Headers
- Backend returns proper Cache-Control headers
- Stale-while-revalidate for public endpoints

## Test Credentials
- Use existing test user or create new one via signup

## Test Status
- Backend testing: PENDING
- Frontend testing: PENDING
