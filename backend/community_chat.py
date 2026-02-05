"""
Community Chat Service for TROA
WhatsApp-like group chat functionality with file upload support
Now with WebSocket support for real-time messaging
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import os
import logging
import base64
import mimetypes
import json

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["Community Chat"])

# Import push notification helper
from push_notifications import send_notification_to_group_members

# Import WebSocket manager
from websocket_manager import chat_manager, WSMessageType

# File upload constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_DOC_TYPES = ['application/pdf', 'application/msword', 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'application/vnd.ms-excel',
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     'text/plain']
ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOC_TYPES

# Extension to MIME type mapping for fallback
EXTENSION_TO_MIME = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.txt': 'text/plain',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp'
}

def get_content_type(file: UploadFile) -> str:
    """Get content type from file, using extension as fallback"""
    content_type = file.content_type
    
    # If content_type is missing or generic, try to determine from extension
    if not content_type or content_type == 'application/octet-stream':
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            content_type = EXTENSION_TO_MIME.get(ext, content_type)
            if not content_type:
                # Use mimetypes as last resort
                guessed_type, _ = mimetypes.guess_type(file.filename)
                content_type = guessed_type or 'application/octet-stream'
    
    return content_type

# Pydantic Models

# Group types: public (anyone can see/join), private (invite only), mc_only (managers/admins only)
class GroupType:
    PUBLIC = "public"
    PRIVATE = "private"
    MC_ONLY = "mc_only"

class ChatGroupCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    group_type: str = "public"  # "public", "private", "mc_only"
    is_mc_only: bool = False  # Deprecated - kept for backward compatibility
    initial_members: Optional[List[str]] = []  # Emails of initial members to add
    icon: Optional[str] = None  # Base64 encoded group icon

class ChatGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None  # Base64 encoded group icon
    group_type: Optional[str] = None  # "public", "private", "mc_only"

class ReplyTo(BaseModel):
    message_id: str
    sender_name: str
    content_preview: str  # First ~100 chars of the original message

class ChatMessage(BaseModel):
    content: str
    group_id: str
    reply_to: Optional[ReplyTo] = None  # For replying to a specific message

class Reaction(BaseModel):
    emoji: str
    user_email: str
    user_name: str
    created_at: Optional[str] = None

class AddReactionRequest(BaseModel):
    emoji: str

class FileAttachment(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    is_image: bool
    data: Optional[str] = None  # Base64 data for images

class ChatGroup(BaseModel):
    id: str
    name: str
    description: str
    created_by: str
    created_by_name: str
    created_at: datetime
    group_type: str = "public"  # "public", "private", "mc_only"
    is_mc_only: bool = False  # Deprecated - kept for backward compatibility
    members: List[str] = []
    member_count: int = 0
    icon: Optional[str] = None  # Base64 encoded group icon

class Message(BaseModel):
    id: str
    group_id: str
    sender_email: str
    sender_name: str
    sender_picture: Optional[str] = None
    content: str
    created_at: datetime
    attachments: Optional[List[dict]] = []
    status: str = "sent"  # "sending", "sent", "delivered", "read"
    read_by: Optional[List[str]] = []  # List of emails who have read this message
    is_deleted: bool = False  # Soft delete flag
    deleted_at: Optional[str] = None  # When the message was deleted
    reactions: Optional[List[dict]] = []  # List of reactions on this message
    reply_to: Optional[dict] = None  # Reference to message being replied to

class AddMemberRequest(BaseModel):
    email: str

class RemoveMemberRequest(BaseModel):
    email: str

class MarkMessagesReadRequest(BaseModel):
    message_ids: List[str]


# Helper to get DB
async def get_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    return client[os.environ['DB_NAME']]


@chat_router.get("/groups", response_model=List[ChatGroup])
async def get_chat_groups(request: Request):
    """Get all chat groups the user can access"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get user's role
        user_role = user.get('role', 'user')
        is_admin_or_manager = user_role in ['admin', 'manager']
        user_email = user.get('email')
        
        # Build query based on group visibility rules:
        # - Public groups: visible to all
        # - Private groups: visible only to members (creator + added members)
        # - MC-only groups: visible only to managers/admins
        
        if is_admin_or_manager:
            # Admins/managers can see all groups
            query = {}
        else:
            # Regular users can see:
            # 1. Public groups
            # 2. Private groups they are a member of
            query = {
                '$or': [
                    {'group_type': 'public'},
                    {'group_type': {'$exists': False}},  # Legacy groups without group_type
                    {'group_type': 'private', 'members': user_email}
                ],
                # Exclude MC-only groups for non-managers (backward compatibility)
                'is_mc_only': {'$ne': True}
            }
        
        # Get groups based on user role
        groups = await db.chat_groups.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        result = []
        for group in groups:
            group['member_count'] = len(group.get('members', []))
            # Ensure group_type exists (backward compatibility)
            if 'group_type' not in group:
                group['group_type'] = 'mc_only' if group.get('is_mc_only') else 'public'
            result.append(ChatGroup(**group))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat groups")


@chat_router.post("/groups", response_model=ChatGroup)
async def create_chat_group(group_data: ChatGroupCreate, request: Request):
    """Create a new chat group - managers and admins can create any type, regular users can create public/private"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get user's role
        user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
        user_role = user_data.get('role', 'user') if user_data else 'user'
        is_admin_or_manager = user_role in ['admin', 'manager']
        
        # Determine group type (prioritize explicit group_type over is_mc_only)
        group_type = group_data.group_type
        if group_data.is_mc_only and group_type == "public":
            group_type = "mc_only"  # Backward compatibility
        
        # Only admins/managers can create MC-only groups
        if group_type == "mc_only" and not is_admin_or_manager:
            raise HTTPException(status_code=403, detail="Only managers and admins can create MC groups")
        
        # Check if MC Group already exists if trying to create one
        if group_type == "mc_only":
            existing_mc = await db.chat_groups.find_one(
                {"$or": [{"is_mc_only": True}, {"group_type": "mc_only"}]}, 
                {"_id": 0}
            )
            if existing_mc:
                raise HTTPException(status_code=400, detail="MC Group already exists")
        
        # Start with creator as member
        members = [user['email']]
        
        # Add initial members if provided
        if group_data.initial_members:
            for email in group_data.initial_members:
                if email and email not in members:
                    # Verify user exists
                    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
                    if existing_user:
                        members.append(email)
        
        group = {
            "id": str(uuid4()),
            "name": group_data.name,
            "description": group_data.description or "",
            "created_by": user['email'],
            "created_by_name": user['name'],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "group_type": group_type,
            "is_mc_only": group_type == "mc_only",  # Backward compatibility
            "members": members,
            "icon": group_data.icon
        }
        
        await db.chat_groups.insert_one(group)
        group['member_count'] = len(members)
        
        logger.info(f"Chat group '{group_data.name}' ({group_type}) created by {user['email']} with {len(members)} members")
        return ChatGroup(**group)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat group")


@chat_router.post("/groups/{group_id}/join")
async def join_chat_group(group_id: str, request: Request):
    """Join a chat group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        group_type = group.get('group_type', 'public')
        
        # Check group type restrictions
        if group.get('is_mc_only') or group_type == 'mc_only':
            # Only managers/admins can join MC group
            user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
            if not user_data or user_data.get('role') not in ['admin', 'manager']:
                raise HTTPException(status_code=403, detail="Only managers can join the MC Group")
        elif group_type == 'private':
            # Private groups - users cannot self-join, must be added by creator/admin
            raise HTTPException(status_code=403, detail="This is a private group. You must be invited to join.")
        
        # Check if already a member
        if user['email'] in group.get('members', []):
            return {"message": "Already a member of this group"}
        
        # Add user to members
        await db.chat_groups.update_one(
            {"id": group_id},
            {"$addToSet": {"members": user['email']}}
        )
        
        logger.info(f"User {user['email']} joined group {group['name']}")
        return {"message": f"Successfully joined {group['name']}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to join chat group")


@chat_router.post("/groups/{group_id}/leave")
async def leave_chat_group(group_id: str, request: Request):
    """Leave a chat group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if member
        if user['email'] not in group.get('members', []):
            return {"message": "Not a member of this group"}
        
        # Remove user from members
        await db.chat_groups.update_one(
            {"id": group_id},
            {"$pull": {"members": user['email']}}
        )
        
        logger.info(f"User {user['email']} left group {group['name']}")
        return {"message": f"Successfully left {group['name']}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to leave chat group")


@chat_router.post("/groups/{group_id}/add-member")
async def add_member_to_group(group_id: str, member_data: AddMemberRequest, request: Request):
    """Add a member to a chat group - permissions depend on group type"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        group_type = group.get('group_type', 'public')
        user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
        user_role = user_data.get('role', 'user') if user_data else 'user'
        is_admin_or_manager = user_role in ['admin', 'manager']
        is_creator = group.get('created_by') == user['email']
        
        # Permission check based on group type
        if group.get('is_mc_only') or group_type == 'mc_only':
            # MC-only groups - only managers/admins can add
            if not is_admin_or_manager:
                raise HTTPException(status_code=403, detail="Only managers can add members to the MC Group")
        elif group_type == 'private':
            # Private groups - only creator or admins can add
            if not is_creator and not is_admin_or_manager:
                raise HTTPException(status_code=403, detail="Only the group creator can add members to this private group")
        else:
            # Public groups - any member can add others
            if user['email'] not in group.get('members', []):
                raise HTTPException(status_code=403, detail="You must be a member to add others")
        
        # Verify the user to add exists
        user_to_add = await db.users.find_one({"email": member_data.email}, {"_id": 0})
        if not user_to_add:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already a member
        if member_data.email in group.get('members', []):
            return {"message": "User is already a member of this group"}
        
        # Add user to members
        await db.chat_groups.update_one(
            {"id": group_id},
            {"$addToSet": {"members": member_data.email}}
        )
        
        logger.info(f"User {member_data.email} added to group {group['name']} by {user['email']}")
        return {"message": f"Successfully added {user_to_add.get('name', member_data.email)} to the group"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding member to chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to add member to chat group")


@chat_router.post("/groups/{group_id}/remove-member")
async def remove_member_from_group(group_id: str, member_data: RemoveMemberRequest, request: Request):
    """Remove a member from a chat group - creator or admins/managers can remove"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check permissions - creator or admin/manager can remove members
        user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
        user_role = user_data.get('role', 'user') if user_data else 'user'
        is_admin_or_manager = user_role in ['admin', 'manager']
        is_creator = group.get('created_by') == user['email']
        
        if not is_creator and not is_admin_or_manager:
            raise HTTPException(status_code=403, detail="Only the group creator or admins can remove members")
        
        # Check if the user to remove is a member
        if member_data.email not in group.get('members', []):
            return {"message": "User is not a member of this group"}
        
        # Remove user from members
        await db.chat_groups.update_one(
            {"id": group_id},
            {"$pull": {"members": member_data.email}}
        )
        
        logger.info(f"User {member_data.email} removed from group {group['name']} by {user['email']}")
        return {"message": "Successfully removed member from the group"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member from chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove member from chat group")


@chat_router.put("/groups/{group_id}")
async def update_chat_group(group_id: str, group_data: ChatGroupUpdate, request: Request):
    """Update a chat group settings - creator or managers/admins can update"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check permissions - creator or admin/manager can update
        user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
        user_role = user_data.get('role', 'user') if user_data else 'user'
        is_admin_or_manager = user_role in ['admin', 'manager']
        is_creator = group.get('created_by') == user['email']
        
        if not is_creator and not is_admin_or_manager:
            raise HTTPException(status_code=403, detail="Only the group creator or admins can update group settings")
        
        # Build update dict
        update_data = {}
        if group_data.name is not None:
            update_data["name"] = group_data.name
        if group_data.description is not None:
            update_data["description"] = group_data.description
        if group_data.icon is not None:
            update_data["icon"] = group_data.icon
        if group_data.group_type is not None:
            # Only admins/managers can change to/from mc_only
            if group_data.group_type == "mc_only" or group.get('group_type') == "mc_only":
                if not is_admin_or_manager:
                    raise HTTPException(status_code=403, detail="Only admins can change MC group settings")
            update_data["group_type"] = group_data.group_type
            update_data["is_mc_only"] = group_data.group_type == "mc_only"
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Update the group
        await db.chat_groups.update_one(
            {"id": group_id},
            {"$set": update_data}
        )
        
        # Get updated group
        updated_group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        updated_group['member_count'] = len(updated_group.get('members', []))
        if 'group_type' not in updated_group:
            updated_group['group_type'] = 'mc_only' if updated_group.get('is_mc_only') else 'public'
        
        logger.info(f"Chat group {group_id} updated by {user['email']}")
        return ChatGroup(**updated_group)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to update chat group")


@chat_router.delete("/groups/{group_id}")
async def delete_chat_group(group_id: str, request: Request):
    """Delete a chat group - creator or managers/admins can delete"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the group first to check permissions
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check permissions - creator or admin/manager can delete
        user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
        user_role = user_data.get('role', 'user') if user_data else 'user'
        is_admin_or_manager = user_role in ['admin', 'manager']
        is_creator = group.get('created_by') == user['email']
        
        if not is_creator and not is_admin_or_manager:
            raise HTTPException(status_code=403, detail="Only the group creator or admins can delete this group")
        
        # Delete the group
        await db.chat_groups.delete_one({"id": group_id})
        
        # Delete all messages in the group
        await db.chat_messages.delete_many({"group_id": group_id})
        
        # Delete all file attachments for this group
        await db.chat_attachments.delete_many({"group_id": group_id})
        
        logger.info(f"Chat group {group_id} deleted by {user['email']}")
        return {"message": "Group deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat group")


@chat_router.get("/groups/{group_id}/messages", response_model=List[Message])
async def get_group_messages(group_id: str, request: Request, limit: int = 10, before: Optional[str] = None):
    """Get messages from a chat group with pagination (reverse chronological)"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Check if group exists and user is a member
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        if user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must join this group to view messages")
        
        # Build query
        query = {"group_id": group_id}
        if before:
            query["created_at"] = {"$lt": before}
        
        # Get messages (newest first, then reverse for display)
        messages = await db.chat_messages.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        messages.reverse()  # Oldest first for chat display
        
        # Get user pictures for all senders
        sender_emails = list(set(msg.get('sender_email') for msg in messages))
        users_data = await db.users.find(
            {"email": {"$in": sender_emails}},
            {"_id": 0, "email": 1, "picture": 1}
        ).to_list(100)
        user_pictures = {u['email']: u.get('picture') for u in users_data}
        
        # Add sender pictures and ensure status/read_by/is_deleted/reactions/reply_to fields
        for msg in messages:
            msg['sender_picture'] = user_pictures.get(msg.get('sender_email'))
            if 'status' not in msg:
                msg['status'] = 'delivered'  # Default for old messages
            if 'read_by' not in msg:
                msg['read_by'] = []
            if 'is_deleted' not in msg:
                msg['is_deleted'] = False
            if 'deleted_at' not in msg:
                msg['deleted_at'] = None
            if 'reactions' not in msg:
                msg['reactions'] = []
            if 'reply_to' not in msg:
                msg['reply_to'] = None
            # Mark as read if current user hasn't read it yet
            if user['email'] not in msg['read_by'] and msg['sender_email'] != user['email']:
                await db.chat_messages.update_one(
                    {"id": msg['id']},
                    {"$addToSet": {"read_by": user['email']}}
                )
                msg['read_by'].append(user['email'])
        
        return [Message(**msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")


@chat_router.post("/groups/{group_id}/messages", response_model=Message)
async def send_message(group_id: str, message_data: ChatMessage, request: Request):
    """Send a text message to a chat group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Check if group exists
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if user is a member
        if user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must join this group to send messages")
        
        # Check if MC-only group - only managers can send
        if group.get('is_mc_only') or group.get('group_type') == 'mc_only':
            user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
            if not user_data or user_data.get('role') not in ['admin', 'manager']:
                raise HTTPException(status_code=403, detail="Only managers can send messages in the MC Group")
        
        # Get sender's picture
        sender_data = await db.users.find_one({"email": user['email']}, {"_id": 0, "picture": 1})
        sender_picture = sender_data.get('picture') if sender_data else None
        
        # Handle reply_to if provided
        reply_to_data = None
        if message_data.reply_to:
            reply_to_data = {
                "message_id": message_data.reply_to.message_id,
                "sender_name": message_data.reply_to.sender_name,
                "content_preview": message_data.reply_to.content_preview[:100] if message_data.reply_to.content_preview else ""
            }
        
        # Create message
        message = {
            "id": str(uuid4()),
            "group_id": group_id,
            "sender_email": user['email'],
            "sender_name": user['name'],
            "sender_picture": sender_picture,
            "content": message_data.content,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "attachments": [],
            "status": "sent",
            "read_by": [],
            "reactions": [],
            "reply_to": reply_to_data
        }
        
        await db.chat_messages.insert_one(message)
        
        # Send push notification to group members (except sender)
        try:
            # Truncate message for notification
            preview = message_data.content[:50] + "..." if len(message_data.content) > 50 else message_data.content
            await send_notification_to_group_members(
                group_id=group_id,
                title=f"{user['name']} in {group['name']}",
                body=preview,
                exclude_email=user['email'],
                url=f"/chat?group={group_id}"
            )
        except Exception as push_error:
            logger.error(f"Failed to send chat push notifications: {push_error}")
        
        return Message(**message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@chat_router.post("/groups/{group_id}/messages/upload")
async def send_message_with_files(
    group_id: str,
    request: Request,
    content: str = Form(default=""),
    files: List[UploadFile] = File(default=[]),
    reply_to_message_id: Optional[str] = Form(default=None),
    reply_to_sender_name: Optional[str] = Form(default=None),
    reply_to_content_preview: Optional[str] = Form(default=None)
):
    """Send a message with file attachments to a chat group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Check if group exists
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if user is a member
        if user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must join this group to send messages")
        
        # Check if MC-only group - only managers can send
        if group.get('is_mc_only') or group.get('group_type') == 'mc_only':
            user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
            if not user_data or user_data.get('role') not in ['admin', 'manager']:
                raise HTTPException(status_code=403, detail="Only managers can send messages in the MC Group")
        
        # Must have either content or files
        if not content.strip() and not files:
            raise HTTPException(status_code=400, detail="Message must have content or attachments")
        
        # Process file attachments
        attachments = []
        for file in files:
            # Check file size
            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} exceeds maximum size of 5MB"
                )
            
            # Get content type with fallback to extension-based detection
            content_type = get_content_type(file)
            logger.info(f"File upload: {file.filename}, detected content_type: {content_type}, original: {file.content_type}")
            
            # Check file type
            if content_type not in ALLOWED_FILE_TYPES:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {content_type} is not allowed. Allowed types: images (jpeg, png, gif, webp) and documents (pdf, doc, docx, xls, xlsx, txt)"
                )
            
            is_image = content_type in ALLOWED_IMAGE_TYPES
            
            attachment = {
                "id": str(uuid4()),
                "filename": file.filename,
                "content_type": content_type,
                "size": len(file_content),
                "is_image": is_image,
                "group_id": group_id,
                "uploaded_by": user['email'],
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store file data as base64
            attachment["data"] = base64.b64encode(file_content).decode('utf-8')
            
            # Store attachment in separate collection
            await db.chat_attachments.insert_one(attachment)
            
            # Add to message attachments (without the full data for message storage)
            attachments.append({
                "id": attachment["id"],
                "filename": attachment["filename"],
                "content_type": attachment["content_type"],
                "size": attachment["size"],
                "is_image": attachment["is_image"]
            })
        
        # Get sender's picture
        sender_data = await db.users.find_one({"email": user['email']}, {"_id": 0, "picture": 1})
        sender_picture = sender_data.get('picture') if sender_data else None
        
        # Create message
        # Handle reply_to if provided
        reply_to_data = None
        if reply_to_message_id:
            reply_to_data = {
                "message_id": reply_to_message_id,
                "sender_name": reply_to_sender_name or "",
                "content_preview": (reply_to_content_preview or "")[:100]
            }
        
        message = {
            "id": str(uuid4()),
            "group_id": group_id,
            "sender_email": user['email'],
            "sender_name": user['name'],
            "sender_picture": sender_picture,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "attachments": attachments,
            "status": "sent",
            "read_by": [],
            "reactions": [],
            "reply_to": reply_to_data
        }
        
        await db.chat_messages.insert_one(message)
        
        # Send push notification
        try:
            notification_text = content[:50] if content else f"Sent {len(attachments)} file(s)"
            if len(content) > 50:
                notification_text += "..."
            await send_notification_to_group_members(
                group_id=group_id,
                title=f"{user['name']} in {group['name']}",
                body=notification_text,
                exclude_email=user['email'],
                url=f"/chat?group={group_id}"
            )
        except Exception as push_error:
            logger.error(f"Failed to send chat push notifications: {push_error}")
        
        return Message(**message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message with files: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@chat_router.get("/attachments/{attachment_id}")
async def get_attachment(attachment_id: str, request: Request):
    """Get a file attachment by ID"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the attachment
        attachment = await db.chat_attachments.find_one({"id": attachment_id}, {"_id": 0})
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        # Check if user is a member of the group
        group = await db.chat_groups.find_one({"id": attachment["group_id"]}, {"_id": 0})
        if not group or user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You don't have access to this attachment")
        
        return {
            "id": attachment["id"],
            "filename": attachment["filename"],
            "content_type": attachment["content_type"],
            "size": attachment["size"],
            "is_image": attachment["is_image"],
            "data": attachment.get("data")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attachment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attachment")


@chat_router.delete("/messages/{message_id}")
async def delete_message(message_id: str, request: Request):
    """Soft delete a message - only the sender can delete their own messages"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the message
        message = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check if user is the sender
        if message['sender_email'] != user['email']:
            raise HTTPException(status_code=403, detail="You can only delete your own messages")
        
        # Soft delete - mark as deleted but keep the record
        await db.chat_messages.update_one(
            {"id": message_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                    "content": "",  # Clear content
                    "attachments": []  # Clear attachments
                }
            }
        )
        
        # Delete associated attachments from storage
        if message.get('attachments'):
            attachment_ids = [att['id'] for att in message['attachments']]
            await db.chat_attachments.delete_many({"id": {"$in": attachment_ids}})
        
        logger.info(f"Message {message_id} deleted by {user['email']}")
        return {"message": "Message deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete message")


@chat_router.get("/groups/{group_id}/members")
async def get_group_members(group_id: str, request: Request):
    """Get members of a chat group"""
    try:
        from auth import require_auth
        await require_auth(request)  # Verify user is authenticated
        db = await get_db()
        
        # Get the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Get member details
        member_emails = group.get('members', [])
        members = await db.users.find(
            {"email": {"$in": member_emails}},
            {"_id": 0, "email": 1, "name": 1, "picture": 1, "role": 1}
        ).to_list(100)
        
        return {
            "group_id": group_id,
            "group_name": group['name'],
            "member_count": len(members),
            "members": members
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching group members: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch group members")


@chat_router.get("/users/search")
@chat_router.get("/users/search")
async def search_users(request: Request, q: str = ""):
    """Search users by name or email for adding to groups"""
    try:
        from auth import require_auth
        await require_auth(request)  # Verify user is authenticated
        db = await get_db()
        
        if not q or len(q) < 2:
            return []
        
        # Search users by name or email (case-insensitive)
        users = await db.users.find(
            {
                "$or": [
                    {"name": {"$regex": q, "$options": "i"}},
                    {"email": {"$regex": q, "$options": "i"}}
                ]
            },
            {"_id": 0, "email": 1, "name": 1, "picture": 1, "role": 1}
        ).limit(10).to_list(10)
        
        return users
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to search users")


@chat_router.post("/messages/{message_id}/react")
async def add_reaction_to_message(message_id: str, reaction_data: AddReactionRequest, request: Request):
    """Add or update a reaction to a message. Each user can only have one emoji per message."""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the message
        message = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check if user is a member of the group
        group = await db.chat_groups.find_one({"id": message["group_id"]}, {"_id": 0})
        if not group or user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must be a group member to react to messages")
        
        # Get existing reactions
        reactions = message.get('reactions', [])
        
        # Find user's existing reaction (if any)
        existing_reaction = None
        existing_reaction_idx = None
        for idx, r in enumerate(reactions):
            if r.get('user_email') == user['email']:
                existing_reaction = r
                existing_reaction_idx = idx
                break
        
        if existing_reaction is not None:
            if existing_reaction.get('emoji') == reaction_data.emoji:
                # Same emoji - toggle off (remove reaction)
                reactions.pop(existing_reaction_idx)
                action = "removed"
            else:
                # Different emoji - update to new emoji
                reactions[existing_reaction_idx] = {
                    "emoji": reaction_data.emoji,
                    "user_email": user['email'],
                    "user_name": user['name'],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                action = "updated"
        else:
            # No existing reaction - add new one
            new_reaction = {
                "emoji": reaction_data.emoji,
                "user_email": user['email'],
                "user_name": user['name'],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            reactions.append(new_reaction)
            action = "added"
        
        # Update the message
        await db.chat_messages.update_one(
            {"id": message_id},
            {"$set": {"reactions": reactions}}
        )
        
        logger.info(f"User {user['email']} {action} reaction {reaction_data.emoji} to message {message_id}")
        return {"message": f"Reaction {action}", "reactions": reactions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reaction")


@chat_router.delete("/messages/{message_id}/react/{emoji}")
async def remove_reaction_from_message(message_id: str, emoji: str, request: Request):
    """Remove a specific reaction from a message"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the message
        message = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Get existing reactions and remove user's reaction with this emoji
        reactions = message.get('reactions', [])
        reactions = [r for r in reactions if not (r.get('user_email') == user['email'] and r.get('emoji') == emoji)]
        
        # Update the message
        await db.chat_messages.update_one(
            {"id": message_id},
            {"$set": {"reactions": reactions}}
        )
        
        logger.info(f"User {user['email']} removed reaction {emoji} from message {message_id}")
        return {"message": "Reaction removed", "reactions": reactions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove reaction")


@chat_router.get("/messages/{message_id}/reactions")
async def get_message_reactions(message_id: str, request: Request):
    """Get all reactions for a message"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Get the message
        message = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check if user is a member of the group
        group = await db.chat_groups.find_one({"id": message["group_id"]}, {"_id": 0})
        if not group or user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must be a group member to view reactions")
        
        return {"reactions": message.get('reactions', [])}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reactions")


# ============ TYPING INDICATOR ENDPOINTS ============

# In-memory typing status (clears automatically after 5 seconds)
# Format: {group_id: {user_email: {name, timestamp}}}
typing_status = {}

TYPING_TIMEOUT_SECONDS = 5

class TypingStatus(BaseModel):
    is_typing: bool

@chat_router.post("/groups/{group_id}/typing")
async def update_typing_status(group_id: str, status: TypingStatus, request: Request):
    """Update typing status for current user in a group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Verify user is member of the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group or user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must be a group member")
        
        if status.is_typing:
            # Set typing status
            if group_id not in typing_status:
                typing_status[group_id] = {}
            typing_status[group_id][user['email']] = {
                'name': user['name'],
                'timestamp': datetime.now(timezone.utc)
            }
        else:
            # Clear typing status
            if group_id in typing_status and user['email'] in typing_status[group_id]:
                del typing_status[group_id][user['email']]
        
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating typing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update typing status")


@chat_router.get("/groups/{group_id}/typing")
async def get_typing_users(group_id: str, request: Request):
    """Get list of users currently typing in a group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Verify user is member of the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group or user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must be a group member")
        
        now = datetime.now(timezone.utc)
        typing_users = []
        
        if group_id in typing_status:
            # Clean up expired entries and collect active ones
            expired = []
            for email, data in typing_status[group_id].items():
                # Skip current user
                if email == user['email']:
                    continue
                # Check if expired
                if (now - data['timestamp']).total_seconds() > TYPING_TIMEOUT_SECONDS:
                    expired.append(email)
                else:
                    typing_users.append({'email': email, 'name': data['name']})
            
            # Clean up expired
            for email in expired:
                del typing_status[group_id][email]
        
        return {"typing_users": typing_users}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting typing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get typing status")


# ============ UNREAD COUNT ENDPOINTS ============

@chat_router.post("/groups/{group_id}/mark-read")
async def mark_group_as_read(group_id: str, request: Request):
    """Mark all messages in a group as read for the current user"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        # Verify user is member of the group
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
        if not group or user['email'] not in group.get('members', []):
            raise HTTPException(status_code=403, detail="You must be a group member")
        
        # Update user's last read timestamp for this group
        await db.chat_user_reads.update_one(
            {"user_email": user['email'], "group_id": group_id},
            {
                "$set": {
                    "user_email": user['email'],
                    "group_id": group_id,
                    "last_read_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking group as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark as read")


@chat_router.get("/groups/unread-counts")
async def get_unread_counts(request: Request):
    """Get unread message counts for all groups the user is a member of"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        db = await get_db()
        
        user_email = user['email']
        
        # Get all groups user is a member of
        groups = await db.chat_groups.find(
            {"members": user_email},
            {"_id": 0, "id": 1}
        ).to_list(100)
        
        group_ids = [g['id'] for g in groups]
        
        # Get user's last read timestamps for each group
        user_reads = await db.chat_user_reads.find(
            {"user_email": user_email, "group_id": {"$in": group_ids}},
            {"_id": 0}
        ).to_list(100)
        
        last_read_map = {r['group_id']: r['last_read_at'] for r in user_reads}
        
        # Calculate unread counts and get latest message time for each group
        unread_counts = {}
        latest_message_times = {}
        
        for group_id in group_ids:
            last_read = last_read_map.get(group_id)
            
            # Get unread count (messages after last_read, excluding user's own messages)
            query = {
                "group_id": group_id,
                "sender_email": {"$ne": user_email},
                "is_deleted": {"$ne": True}
            }
            if last_read:
                query["created_at"] = {"$gt": last_read}
            
            count = await db.chat_messages.count_documents(query)
            unread_counts[group_id] = count
            
            # Get latest message time for sorting
            latest_msg = await db.chat_messages.find_one(
                {"group_id": group_id, "is_deleted": {"$ne": True}},
                {"_id": 0, "created_at": 1},
                sort=[("created_at", -1)]
            )
            if latest_msg:
                latest_message_times[group_id] = latest_msg['created_at']
            else:
                latest_message_times[group_id] = None
        
        return {
            "unread_counts": unread_counts,
            "latest_message_times": latest_message_times
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread counts")


# ============ WEBSOCKET ENDPOINT ============

async def verify_websocket_token(token: str) -> Optional[dict]:
    """Verify session token and return user data"""
    try:
        db = await get_db()
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Find session
        session = await db.sessions.find_one({"token": token}, {"_id": 0})
        if not session:
            return None
        
        # Check if expired
        expires_at = session.get('expires_at')
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if expires_at < datetime.now(timezone.utc):
                return None
        
        # Get user data
        user = await db.users.find_one({"email": session['user_email']}, {"_id": 0})
        if not user:
            return None
        
        return {
            "email": user['email'],
            "name": user.get('name', 'Unknown'),
            "picture": user.get('picture'),
            "role": user.get('role', 'user')
        }
    except Exception as e:
        logger.error(f"WebSocket token verification error: {e}")
        return None


@chat_router.websocket("/ws/{group_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    group_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time chat
    
    Connect with: ws://host/api/chat/ws/{group_id}?token={session_token}
    
    Message types from client:
    - {"type": "send_message", "content": "...", "reply_to": {...}}
    - {"type": "start_typing"}
    - {"type": "stop_typing"}
    - {"type": "mark_read", "message_ids": [...]}
    - {"type": "add_reaction", "message_id": "...", "emoji": "..."}
    - {"type": "get_online_users"}
    
    Message types from server:
    - {"type": "new_message", "message": {...}}
    - {"type": "typing_start", "user_email": "...", "user_name": "..."}
    - {"type": "typing_stop", "user_email": "..."}
    - {"type": "read_receipt", "user_email": "...", "message_ids": [...]}
    - {"type": "reaction_added", "message_id": "...", "reactions": [...]}
    - {"type": "online_users", "users": [...]}
    - {"type": "user_joined", "user_email": "...", "user_name": "..."}
    - {"type": "user_left", "user_email": "..."}
    """
    db = await get_db()
    
    # Verify token
    user = await verify_websocket_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    user_email = user['email']
    user_name = user['name']
    user_picture = user.get('picture')
    user_role = user.get('role', 'user')
    
    # Check if group exists and user is a member
    group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        await websocket.close(code=4004, reason="Group not found")
        return
    
    if user_email not in group.get('members', []):
        await websocket.close(code=4003, reason="Not a member of this group")
        return
    
    # Check MC-only restrictions
    is_mc_only = group.get('is_mc_only') or group.get('group_type') == 'mc_only'
    is_admin_or_manager = user_role in ['admin', 'manager']
    
    # Connect to WebSocket
    await chat_manager.connect(websocket, group_id, user_email, user_name, user_picture)
    
    # Send current online users to the new connection
    online_users = chat_manager.get_online_users(group_id)
    await websocket.send_text(json.dumps({
        "type": WSMessageType.ONLINE_USERS,
        "users": online_users
    }))
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            msg_type = message_data.get("type")
            
            if msg_type == WSMessageType.SEND_MESSAGE:
                # Check if user can send messages in MC-only groups
                if is_mc_only and not is_admin_or_manager:
                    await websocket.send_text(json.dumps({
                        "type": WSMessageType.ERROR,
                        "error": "Only managers can send messages in this group"
                    }))
                    continue
                
                content = message_data.get("content", "").strip()
                reply_to = message_data.get("reply_to")
                
                if not content:
                    continue
                
                # Create message
                message = {
                    "id": str(uuid4()),
                    "group_id": group_id,
                    "sender_email": user_email,
                    "sender_name": user_name,
                    "sender_picture": user_picture,
                    "content": content,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "attachments": [],
                    "status": "sent",
                    "read_by": [],
                    "reactions": [],
                    "reply_to": reply_to
                }
                
                await db.chat_messages.insert_one(message)
                
                # Broadcast to all users in group (including sender for confirmation)
                await chat_manager.broadcast_to_group(group_id, {
                    "type": WSMessageType.NEW_MESSAGE,
                    "message": message
                })
                
                # Send push notification to offline members
                try:
                    preview = content[:50] + "..." if len(content) > 50 else content
                    await send_notification_to_group_members(
                        group_id=group_id,
                        title=f"{user_name} in {group['name']}",
                        body=preview,
                        exclude_email=user_email,
                        url=f"/chat?group={group_id}"
                    )
                except Exception as push_error:
                    logger.error(f"Failed to send push notification: {push_error}")
            
            elif msg_type == WSMessageType.START_TYPING:
                # Broadcast typing start to others
                await chat_manager.broadcast_to_group(group_id, {
                    "type": WSMessageType.TYPING_START,
                    "user_email": user_email,
                    "user_name": user_name
                }, exclude_user=user_email)
            
            elif msg_type == WSMessageType.STOP_TYPING:
                # Broadcast typing stop to others
                await chat_manager.broadcast_to_group(group_id, {
                    "type": WSMessageType.TYPING_STOP,
                    "user_email": user_email
                }, exclude_user=user_email)
            
            elif msg_type == WSMessageType.MARK_READ:
                message_ids = message_data.get("message_ids", [])
                if message_ids:
                    # Update messages in database
                    await db.chat_messages.update_many(
                        {"id": {"$in": message_ids}, "sender_email": {"$ne": user_email}},
                        {"$addToSet": {"read_by": user_email}}
                    )
                    
                    # Also update user's last read timestamp
                    await db.chat_user_reads.update_one(
                        {"user_email": user_email, "group_id": group_id},
                        {
                            "$set": {
                                "user_email": user_email,
                                "group_id": group_id,
                                "last_read_at": datetime.now(timezone.utc).isoformat()
                            }
                        },
                        upsert=True
                    )
                    
                    # Broadcast read receipt to message senders
                    await chat_manager.broadcast_to_group(group_id, {
                        "type": WSMessageType.READ_RECEIPT,
                        "user_email": user_email,
                        "user_name": user_name,
                        "message_ids": message_ids
                    }, exclude_user=user_email)
            
            elif msg_type == WSMessageType.ADD_REACTION:
                message_id = message_data.get("message_id")
                emoji = message_data.get("emoji")
                
                if not message_id or not emoji:
                    continue
                
                # Get the message
                msg = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
                if not msg:
                    continue
                
                reactions = msg.get('reactions', [])
                
                # Find existing reaction from this user
                existing_idx = None
                for idx, r in enumerate(reactions):
                    if r.get('user_email') == user_email:
                        existing_idx = idx
                        break
                
                if existing_idx is not None:
                    if reactions[existing_idx].get('emoji') == emoji:
                        # Same emoji - remove it
                        reactions.pop(existing_idx)
                    else:
                        # Different emoji - update
                        reactions[existing_idx] = {
                            "emoji": emoji,
                            "user_email": user_email,
                            "user_name": user_name,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                else:
                    # Add new reaction
                    reactions.append({
                        "emoji": emoji,
                        "user_email": user_email,
                        "user_name": user_name,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                
                # Update database
                await db.chat_messages.update_one(
                    {"id": message_id},
                    {"$set": {"reactions": reactions}}
                )
                
                # Broadcast reaction update
                await chat_manager.broadcast_to_group(group_id, {
                    "type": WSMessageType.REACTION_ADDED,
                    "message_id": message_id,
                    "reactions": reactions
                })
            
            elif msg_type == WSMessageType.DELETE_MESSAGE:
                message_id = message_data.get("message_id")
                if not message_id:
                    continue
                
                # Verify ownership
                msg = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
                if not msg or msg.get('sender_email') != user_email:
                    await websocket.send_text(json.dumps({
                        "type": WSMessageType.ERROR,
                        "error": "Cannot delete this message"
                    }))
                    continue
                
                # Soft delete
                await db.chat_messages.update_one(
                    {"id": message_id},
                    {
                        "$set": {
                            "is_deleted": True,
                            "deleted_at": datetime.now(timezone.utc).isoformat(),
                            "content": "",
                            "attachments": []
                        }
                    }
                )
                
                # Broadcast deletion
                await chat_manager.broadcast_to_group(group_id, {
                    "type": WSMessageType.MESSAGE_DELETED,
                    "message_id": message_id
                })
            
            elif msg_type == WSMessageType.GET_ONLINE_USERS:
                online_users = chat_manager.get_online_users(group_id)
                await websocket.send_text(json.dumps({
                    "type": WSMessageType.ONLINE_USERS,
                    "users": online_users
                }))
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_email} from group {group_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_email} in group {group_id}: {e}")
    finally:
        await chat_manager.disconnect(group_id, user_email)


# Helper function to broadcast message via WebSocket (for HTTP endpoints)
async def broadcast_new_message(group_id: str, message: dict):
    """Broadcast a new message to all WebSocket connections in a group"""
    await chat_manager.broadcast_to_group(group_id, {
        "type": WSMessageType.NEW_MESSAGE,
        "message": message
    })


async def broadcast_message_deleted(group_id: str, message_id: str):
    """Broadcast message deletion to all WebSocket connections in a group"""
    await chat_manager.broadcast_to_group(group_id, {
        "type": WSMessageType.MESSAGE_DELETED,
        "message_id": message_id
    })


async def broadcast_reaction_update(group_id: str, message_id: str, reactions: list):
    """Broadcast reaction update to all WebSocket connections in a group"""
    await chat_manager.broadcast_to_group(group_id, {
        "type": WSMessageType.REACTION_ADDED,
        "message_id": message_id,
        "reactions": reactions
    })


# Initialize MC Group on startup
async def init_mc_group():
    """Create MC Group if it doesn't exist"""
    try:
        db = await get_db()
        existing = await db.chat_groups.find_one({"is_mc_only": True}, {"_id": 0})
        if not existing:
            mc_group = {
                "id": str(uuid4()),
                "name": "MC Group",
                "description": "Management Committee - Only managers can send messages",
                "created_by": "system",
                "created_by_name": "System",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_mc_only": True,
                "members": []
            }
            await db.chat_groups.insert_one(mc_group)
            logger.info("MC Group created")
    except Exception as e:
        logger.error(f"Error initializing MC Group: {e}")
