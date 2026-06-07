# TROA Website — Product Requirements & State

## Original Problem Statement (latest fork)
1. Sync codebase to latest `main` of `https://github.com/troasystems/troa-website`. (DONE prior)
2. Fix bug: invoice PDF download not working in production on `my-invoices` page. (DONE prior)
3. Implement WebSockets for real-time chat (read receipts + HTTP polling fallback). (DONE prior)
4. Four new amenity booking features + frontend bug fixes. (DONE — this fork)

## App Overview
React (CRA, PWA) + FastAPI + MongoDB (Motor). Resident community portal for "The Retreat Owners Association":
amenities booking, community chat (WebSockets), invoices (clubhouse + maintenance), Razorpay online payments,
offline/QR payments with admin approval, Google OAuth + email/password auth, push notifications.

## Architecture
- backend/server.py — main FastAPI app, invoice + payment + QR routes
- backend/auth.py — auth (cookie `session_token` OR `X-Session-Token: Bearer` header), sessions in Mongo
- backend/pdf_service.py — ReportLab invoice PDF generation (self-contained, Helvetica, no external files)
- backend/community_chat.py + websocket_manager.py — chat WS + HTTP
- backend/routes/bookings.py — amenity booking CRUD + edit + staff routes + PDF reports
- frontend/src/pages/MyInvoices.jsx — invoice list/download/pay
- frontend/src/utils/api.js — getBackendUrl() = window.location.origin in prod
- frontend/public/service-worker.js — PWA caching SW (now v4)

## Changelog

### 2026-06-07 (this fork)
- **Feature 1: Today/Tomorrow booking restriction.** Users can only book amenities for today or tomorrow. Backend validates via `_validate_booking_date()`. Frontend replaced date picker with Today/Tomorrow toggle buttons.
- **Feature 2: Consecutive day same-slot block.** Backend `_check_consecutive_day_slot()` prevents same person from booking the identical slot (amenity + time + duration) on consecutive days.
- **Feature 3: Edit bookings.** New `PUT /api/bookings/{id}` endpoint allows booking owners to change date, time, duration, and guests. Frontend shows Edit button on MyBookings page, opens BookingCalendar in edit mode (pre-fills all fields, calls PUT).
- **Feature 4: Peak hours restriction.** 6 PM – 8 PM are peak hours — only 60-min bookings allowed. Backend `_validate_peak_time()` rejects 30-min slots that overlap peak window. Frontend visually marks peak slots in amber, auto-switches to 60-min when peak time selected.
- **Bug fix: getBackendUrl() consistency.** Replaced `process.env.REACT_APP_BACKEND_URL` with `getBackendUrl()` from `../utils/api` in VillaManagement.jsx, VillaNumberModal.jsx, EmailVerificationBanner.jsx, VerifyEmail.jsx, Login.jsx.
- **Bug fix: villas.py dotenv path.** Changed `load_dotenv()` to `load_dotenv(Path(__file__).parent / '.env')` with proper import.
- **Bug fix: Service Worker cache version.** Bumped `CACHE_VERSION` from v3 to v4 to ensure browsers pick up the new frontend bundle.
- Testing: 13/13 backend tests pass (pytest). Frontend verified via screenshots.

### 2026-06-07 (code quality fixes)
- **Security: Hardcoded secrets in tests.** Replaced hardcoded credentials in test_user_whitelist.py and test_booking_features.py with `os.getenv()` calls.
- **Security: MD5 → SHA-256.** Replaced `hashlib.md5` with `hashlib.sha256` in gridfs_upload.py and migrate_to_gridfs.py for file integrity ETags.
- **Python: Undefined variable safety.** Added `subject_prefix = "REMINDER"` default initialization in email_service.py `send_invoice_reminder()` before conditional branches.
- **React: Index as key.** Replaced `key={index}` with stable keys in MyEvents.jsx (registrant `_key` field), Events.jsx (registrant `_key`, preference composite), HelpDesk.jsx (`service.title`, `contact.label`), CommunityChat.jsx (`file.name-file.size`).
- **Note on `is None` comparisons:** All 24 flagged `is`/`is not` comparisons in community_chat.py, routes/users.py, villas.py, routes/invoices.py are `is None`/`is not None` — correct Python idiom, no fix needed.
- **Note on localStorage tokens:** 72+ instances use localStorage for auth tokens — this is an architectural decision (PWA offline support). Migration to httpOnly cookies would require significant auth refactoring and is tracked as a future improvement.
- **Note on React hook dependencies:** Pre-existing ESLint warnings for `react-hooks/exhaustive-deps` across CommunityChat, VerifyEmail, MyInvoices, etc. — these are non-breaking and require careful per-case analysis. Tracked as tech debt.

### 2026-06-06 (previous fork)
- FIXED (P0): Invoice PDF download failing in production.
- WebSocket chat implementation completed.

## 3rd-Party Integrations
- Razorpay (payments) — user API key
- Google OAuth (auth) — user API key
- SendGrid (email) — configured
- Emergent LLM (chatbot) — configured

## Backlog / Next
- P2: Move AWS SES out of sandbox to unblock email notifications.
- Refactor: split server.py into routers (routes/, models/) for scalability.
- Refactor: split bookings.py into user + staff modules (~590 lines).
- Feature: "Download all paid invoices for the year" button.
- Enhancement: Edit booking cutoff window (e.g. no edits within 1 hour of start).
