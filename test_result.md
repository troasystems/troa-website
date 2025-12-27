# Community Chat Enhancement Test Plan

## Features to Test

### 1. Emoji Reactions on Messages
- Long-press on message to open emoji picker
- Select emoji to add reaction
- Multiple users can react to same message
- Same user can add multiple different emojis
- Tap own reaction to remove it
- Reactions display below messages with count

### 2. Reply to Message (Swipe/Click)
- Swipe right on message to reply
- Click reply button to reply
- Reply preview shows above input
- Sent message shows quoted reply
- Tap quoted message to scroll to original

### 3. Group Types System
- Public groups: visible to all, anyone can join
- Private groups: visible only to members, invite only
- MC groups: visible only to managers/admins
- Group type selection on creation
- Group type badge on group list

### 4. Group Management
- Group creators can add/remove members
- Group creators can edit group settings
- All users can create public/private groups
- Only managers/admins can create MC groups

## Test Credentials
- Use existing test user or create via signup

## Test Status
- Backend testing: PENDING
- Frontend testing: PENDING

## Endpoints to Test
- POST /api/chat/groups - Create group with group_type
- POST /api/chat/messages/{id}/react - Add reaction
- DELETE /api/chat/messages/{id}/react/{emoji} - Remove reaction
- POST /api/chat/groups/{id}/messages - Send with reply_to
