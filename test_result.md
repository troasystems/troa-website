# Chat Features Test Plan

## Features to Test

### 1. Image Thumbnail Preview with Popup
- Images in messages should show as small thumbnails (max 150px)
- Clicking thumbnail opens medium-sized popup (max 600x600px)
- Popup has download button
- Popup closes when clicking outside or X button

### 2. Message Deletion (Soft Delete)
- Users can delete their own messages
- Delete button appears on hover
- Confirmation dialog before deletion
- Deleted messages show "This message was deleted" to all users
- Sender name still visible, content replaced

### 3. File Uploads (PDF Fix)
- PDFs should upload successfully
- Other document types (doc, docx, xls, xlsx, txt) should work
- MIME type detection uses extension as fallback

### 4. Reverse Pagination
- Initially loads last 10 messages
- Scrolling to top loads previous 10 messages
- Loading indicator shows when fetching older messages
- "Beginning of conversation" shown when no more messages

## Test Credentials
- Use Google OAuth login (no password auth)
- Test user: troa.systems@gmail.com

## API Endpoints to Test
- GET /api/chat/groups/{group_id}/messages?limit=10&before={timestamp}
- DELETE /api/chat/messages/{message_id}
- POST /api/chat/groups/{group_id}/messages/upload (with PDF)

## Test Status
- Backend testing: PENDING
- Frontend testing: PENDING
