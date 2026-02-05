# Test Results for Villa Management & Invoice System

## Features to Test

### 0. WebSocket Real-Time Chat (Current Session - Feb 2025)
- [ ] WebSocket connection establishes successfully when entering a chat group
- [ ] Real-time messages appear instantly without page refresh
- [ ] Typing indicators work via WebSocket
- [ ] Read receipts are sent via WebSocket
- [ ] Reactions sync in real-time
- [ ] Online users count shows in header
- [ ] HTTP polling fallback works when WebSocket fails
- [ ] WebSocket reconnection after disconnect

### 1. Bulk Upload Features (Jan 2025)
- [ ] Invoice bulk upload template download (/api/bulk/invoices/template) - Accountant, Manager, Admin
- [ ] Invoice bulk upload (/api/bulk/invoices/upload) - Multiple rows for same villa combined
- [ ] Villa bulk upload template download (/api/bulk/villas/template) - Admin only
- [ ] Villa bulk upload (/api/bulk/villas/upload) - Upsert with email merge
- [ ] Emails sent when invoices are created via bulk upload

### 2. Invoice System Fixes
- [ ] Accountant accessing Invoice Management page (view=manage)
- [ ] My Invoices page shows only personal/villa invoices (view=my)
- [ ] PDF download for maintenance invoices
- [ ] PDF access control for accountants
- [ ] Email sent when invoice is raised

### 3. Villa Management (Backend)
- [ ] GET /api/villas - List all villas (admin/manager/staff)
- [ ] POST /api/villas - Create new villa (admin/manager)
- [ ] PATCH /api/villas/{villa_number} - Update villa (admin/manager)
- [ ] DELETE /api/villas/{villa_number} - Delete villa (admin only)
- [ ] POST /api/villas/{villa_number}/emails - Add email to villa
- [ ] DELETE /api/villas/{villa_number}/emails/{email} - Remove email
- [ ] POST /api/villas/migrate-from-users - Migration utility

### 4. Role System Updates
- [ ] New "accountant" role is recognized
- [ ] Staff group (clubhouse_staff + accountant) works correctly
- [ ] Role-based access control for villas

### 5. Invoice System Updates
- [ ] Maintenance invoice creation (POST /api/invoices/maintenance)
- [ ] Invoice type filtering
- [ ] Multi-invoice payment (POST /api/invoices/pay-multiple)
- [ ] Multi-invoice verification (POST /api/invoices/verify-multi-payment)

### 6. Login Flow
- [ ] Regular users must have email in a villa
- [ ] Privileged roles (admin, manager, staff) bypass villa check

## Test Credentials
- Super Admin: troa.systems@gmail.com / Test@123 (always admin)
- Test Accountant: accountant@test.com / Test@123

## Incorporate User Feedback
- Testing WebSocket real-time chat functionality
- Testing the invoice management fixes
- Testing My Invoices page for accountant role
- Testing PDF download for maintenance invoices

## Testing Protocol
- Backend testing for API endpoints
- Frontend screenshot for UI validation
- WebSocket testing for real-time features
