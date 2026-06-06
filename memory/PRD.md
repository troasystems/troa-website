# TROA Website — Product Requirements & State

## Original Problem Statement (latest fork)
1. Sync codebase to latest `main` of `https://github.com/troasystems/troa-website`. (DONE prior)
2. Fix bug: invoice PDF download not working in production on `my-invoices` page. (DONE — this fork)
3. Implement WebSockets for real-time chat (read receipts + HTTP polling fallback). (DONE prior, awaiting user verification)

## App Overview
React (CRA, PWA) + FastAPI + MongoDB (Motor). Resident community portal for "The Retreat Owners Association":
amenities booking, community chat (WebSockets), invoices (clubhouse + maintenance), Razorpay online payments,
offline/QR payments with admin approval, Google OAuth + email/password auth, push notifications.

## Architecture
- backend/server.py — main FastAPI app, invoice + payment + QR routes
- backend/auth.py — auth (cookie `session_token` OR `X-Session-Token: Bearer` header), sessions in Mongo
- backend/pdf_service.py — ReportLab invoice PDF generation (self-contained, Helvetica, no external files)
- backend/community_chat.py + websocket_manager.py — chat WS + HTTP
- frontend/src/pages/MyInvoices.jsx — invoice list/download/pay
- frontend/src/utils/api.js — getBackendUrl() = window.location.origin in prod
- frontend/public/service-worker.js — PWA caching SW (intercepts /api/ GET)

## Changelog
### 2026-06-06
- **FIXED (P0): Invoice PDF download failing in production.**
  - Root cause: the PWA service worker intercepted ALL `/api/` GET requests including the binary
    `/api/invoices/{id}/pdf` download, wrapping/re-fetching the blob response which corrupted the
    `Content-Disposition` native download in production browsers. Worked in preview/curl because those
    bypass the SW. Stale `v2` SW in production browsers made it worse.
  - Fix: `service-worker.js` now early-returns (no `respondWith`) for any `/api/.../pdf` request so the
    browser handles the native download. Bumped `CACHE_VERSION` v2 -> v3 to evict stale SWs.
  - Also: `MyInvoices.jsx` `downloadInvoicePdf` now parses Blob error bodies to surface the real server
    error (401/403/detail) instead of a generic message; added `data-testid` to download button.
  - Verified end-to-end in browser with SW active+controlling: download succeeds, valid 3099-byte PDF.
  - NOTE: existing production users must let the new SW (v3) activate (UpdateNotification prompts; install
    uses skipWaiting + clients.claim) — i.e. a redeploy is required for the fix to reach prod.

## 3rd-Party Integrations
- Razorpay (payments) — user API key
- Google OAuth (auth) — user API key
- AWS SES (email) — sandbox mode (deprioritized by user)

## Backlog / Next
- P1: User to verify WebSocket chat (real-time messages, read receipts, online presence, fallback).
- P2: Move AWS SES out of sandbox to unblock email notifications.
- Refactor: split server.py into routers (routes/, models/) for scalability.
