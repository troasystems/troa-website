# Test Credentials — TROA

## Auth notes
- Auth accepts session via cookie `session_token` OR header `X-Session-Token: Bearer <token>`.
- Sessions stored in Mongo `sessions` collection: `{token, user:{email,role,name}, expires}`.

## Known accounts (in DB)
- Admin: `troa.systems@gmail.com` (role: admin) — password NOT verified/known.
- Users: `abcd@gmail.com`, `resident@villa.com`, `jane.smith@villa.com`, `abcde@gmail.com`, etc.
  - NOTE: `abcd@gmail.com` / `Test@123` from old handoff did NOT work this fork (Invalid email or password).

## Testing without a known password (used this fork)
Inject a temporary session directly, then set localStorage `session_token` in the browser:
```python
# /app/backend, with dotenv loaded
await db.sessions.insert_one({'token': token, 'user': {'email':'troa.systems@gmail.com','role':'admin','name':'Admin'}, 'expires': datetime.utcnow()+timedelta(hours=2)})
```
Browser: `localStorage.setItem('session_token', token)` then load `/my-invoices`.
Remember to delete temp sessions (token prefix `testtok_`) after testing.

## Sample invoice IDs (for PDF download tests)
- `eee3f57b-9392-40bd-af53-994158a93928` (TROA-MAINT-202601-RHYKR, owner troa.systems@gmail.com)
