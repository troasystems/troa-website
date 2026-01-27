# Test Results for Villa Management & Invoice System

## Features to Test

### 1. Villa Management (Backend)
- [ ] GET /api/villas - List all villas (admin/manager/staff)
- [ ] POST /api/villas - Create new villa (admin/manager)
- [ ] PATCH /api/villas/{villa_number} - Update villa (admin/manager)
- [ ] DELETE /api/villas/{villa_number} - Delete villa (admin only)
- [ ] POST /api/villas/{villa_number}/emails - Add email to villa
- [ ] DELETE /api/villas/{villa_number}/emails/{email} - Remove email
- [ ] POST /api/villas/migrate-from-users - Migration utility

### 2. Role System Updates
- [ ] New "accountant" role is recognized
- [ ] Staff group (clubhouse_staff + accountant) works correctly
- [ ] Role-based access control for villas

### 3. Invoice System Updates
- [ ] Maintenance invoice creation (POST /api/invoices/maintenance)
- [ ] Invoice type filtering
- [ ] Multi-invoice payment (POST /api/invoices/pay-multiple)
- [ ] Multi-invoice verification (POST /api/invoices/verify-multi-payment)

### 4. Login Flow
- [ ] Regular users must have email in a villa
- [ ] Privileged roles (admin, manager, staff) bypass villa check

## Test Credentials
- Super Admin: troa.systems@gmail.com (always admin)

## Incorporate User Feedback
- Testing the villa management system and accountant role
- Testing maintenance invoice workflow
- Testing multi-invoice payment

## Testing Protocol
- Backend testing for API endpoints
- Frontend screenshot for UI validation
