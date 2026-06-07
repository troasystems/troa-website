# TROA Website — Product Requirements & State

## Original Problem Statement (latest fork)
1. Sync codebase to latest `main` of `https://github.com/troasystems/troa-website`. (DONE prior)
2. Fix bug: invoice PDF download not working in production on `my-invoices` page. (DONE prior)
3. Implement WebSockets for real-time chat (read receipts + HTTP polling fallback). (DONE prior)

## App Overview
React (CRA, PWA) + FastAPI + MongoDB (Motor). Resident community portal for "The Retreat Owners Association":
amenities booking, community chat (WebSockets), invoices (clubhouse + maintenance), Razorpay online payments,
offline/QR payments with admin approval, Google OAuth + email/password auth, push notifications.

## Architecture
```
backend/
  server.py             — FastAPI app setup, middleware, CORS, lifecycle events (~279 lines)
  database.py           — Shared MongoDB connection (Motor client + db)
  routes/
    committee.py        — Committee CRUD (admin-only write)
    amenities.py        — Amenities CRUD (admin-only write)
    gallery.py          — Gallery CRUD
    membership.py       — Membership applications (public submit, admin review)
    users.py            — User management (admin-only)
    feedback.py         — Feedback CRUD (auth required)
    bookings.py         — Amenity bookings + Clubhouse staff routes + PDF reports
    invoices.py         — Invoices (clubhouse/maintenance) + offline payments + multi-payment
  auth.py               — Auth (cookie session_token OR X-Session-Token header), sessions in Mongo
  pdf_service.py        — ReportLab invoice/booking PDF generation
  community_chat.py     — Chat WebSocket + HTTP endpoints
  websocket_manager.py  — Manages active WebSocket connections
  payment.py            — Razorpay payment integration
  events.py             — Events CRUD
  villas.py             — Villas management
  email_service.py      — Email notifications (AWS SES/SendGrid)
  push_notifications.py — PWA push notifications
  chatbot.py            — Chatbot endpoints
  instagram.py          — Instagram feed
  gridfs_upload.py      — GridFS file upload
  bulk_upload.py        — Bulk upload operations
  models.py             — Pydantic models

frontend/
  src/pages/
    CommunityChat.jsx   — Chat UI with WebSocket integration
    MyInvoices.jsx       — Invoice management + PDF download
  src/services/
    chatWebSocket.js    — Frontend WebSocket client
  public/
    service-worker.js   — PWA Service Worker (bypasses /api/.../pdf for native download)
```

## Changelog
### 2026-06-07
- **REFACTOR: Split server.py into modular route files.**
  - Reduced server.py from 2,709 lines to 279 lines (90% reduction)
  - Created `database.py` for shared MongoDB connection
  - Created 8 route modules under `routes/`: committee, amenities, gallery, membership,
    users, feedback, bookings, invoices
  - All URL paths preserved — no frontend changes needed
  - Fixed membership notification bug (stale attribute names: name→firstName/lastName, villa_no→villaNo)
  - Verified: 17/17 backend tests passed, 100% frontend pages load correctly

### 2026-06-06
- **FIXED (P0): Invoice PDF download failing in production.**
  - Root cause: PWA service worker intercepted `/api/` GET requests including binary PDF download
  - Fix: service-worker.js early-returns for `/api/.../pdf`; bumped CACHE_VERSION v2→v3
  - `MyInvoices.jsx` improved Blob error handling; added `data-testid` to download button

## 3rd-Party Integrations
- Razorpay (payments) — user API key
- Google OAuth (auth) — user API key
- AWS SES/SendGrid (email) — sandbox mode (deprioritized by user)

## Backlog / Next
- P1: User to verify WebSocket chat (real-time messages, read receipts, online presence, fallback)
- P2: Move AWS SES out of sandbox to unblock email notifications
- Feature: "Download all paid invoices for the year" button on `my-invoices` page
- Improvement: Migrate deprecated FastAPI on_event hooks to lifespan handlers
