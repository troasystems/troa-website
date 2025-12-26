"""
Community Chat Service for TROA
WhatsApp-like group chat functionality
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import os
import logging

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["Community Chat"])

# Import push notification helper
from push_notifications import send_notification_to_group_members

# Pydantic Models
class ChatGroupCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    is_mc_only: bool = False  # If true, only managers can send messages

class ChatGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ChatMessage(BaseModel):
    content: str
    group_id: str

class ChatGroup(BaseModel):
    id: str
    name: str
    description: str
    created_by: str
    created_by_name: str
    created_at: datetime
    is_mc_only: bool = False
    members: List[str] = []
    member_count: int = 0

class Message(BaseModel):
    id: str
    group_id: str
    sender_email: str
    sender_name: str
    content: str
    created_at: datetime


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
        
        # Build query - filter out MC-only groups for normal users
        query = {}
        if not is_admin_or_manager:
            query['is_mc_only'] = {'$ne': True}
        
        # Get groups based on user role
        groups = await db.chat_groups.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        result = []
        for group in groups:
            group['member_count'] = len(group.get('members', []))
            result.append(ChatGroup(**group))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat groups")


@chat_router.post("/groups", response_model=ChatGroup)
async def create_chat_group(group_data: ChatGroupCreate, request: Request):
    """Create a new chat group - managers and admins only"""
    try:
        from auth import require_manager_or_admin
        user = await require_manager_or_admin(request)
        db = await get_db()
        
        # Check if MC Group already exists if trying to create one
        if group_data.is_mc_only:
            existing_mc = await db.chat_groups.find_one({"is_mc_only": True}, {"_id": 0})
            if existing_mc:
                raise HTTPException(status_code=400, detail="MC Group already exists")
        
        group = {
            "id": str(uuid4()),
            "name": group_data.name,
            "description": group_data.description or "",
            "created_by": user['email'],
            "created_by_name": user['name'],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_mc_only": group_data.is_mc_only,
            "members": [user['email']]  # Creator auto-joins
        }
        
        await db.chat_groups.insert_one(group)
        group['member_count'] = 1
        
        logger.info(f"Chat group '{group_data.name}' created by {user['email']}")
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
        
        # Check if MC-only group
        if group.get('is_mc_only'):
            # Only managers/admins can join MC group
            user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
            if not user_data or user_data.get('role') not in ['admin', 'manager']:
                raise HTTPException(status_code=403, detail="Only managers can join the MC Group")
        
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


@chat_router.delete("/groups/{group_id}")
async def delete_chat_group(group_id: str, request: Request):
    """Delete a chat group - managers and admins only"""
    try:
        from auth import require_manager_or_admin
        user = await require_manager_or_admin(request)
        db = await get_db()
        
        # Delete the group
        result = await db.chat_groups.delete_one({"id": group_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Delete all messages in the group
        await db.chat_messages.delete_many({"group_id": group_id})
        
        logger.info(f"Chat group {group_id} deleted by {user['email']}")
        return {"message": "Group deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat group")


@chat_router.get("/groups/{group_id}/messages", response_model=List[Message])
async def get_group_messages(group_id: str, request: Request, limit: int = 50, before: Optional[str] = None):
    """Get messages from a chat group"""
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
        
        return [Message(**msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")


@chat_router.post("/groups/{group_id}/messages", response_model=Message)
async def send_message(group_id: str, message_data: ChatMessage, request: Request):
    """Send a message to a chat group"""
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
        if group.get('is_mc_only'):
            user_data = await db.users.find_one({"email": user['email']}, {"_id": 0})
            if not user_data or user_data.get('role') not in ['admin', 'manager']:
                raise HTTPException(status_code=403, detail="Only managers can send messages in the MC Group")
        
        # Create message
        message = {
            "id": str(uuid4()),
            "group_id": group_id,
            "sender_email": user['email'],
            "sender_name": user['name'],
            "content": message_data.content,
            "created_at": datetime.now(timezone.utc).isoformat()
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


@chat_router.get("/groups/{group_id}/members")
async def get_group_members(group_id: str, request: Request):
    """Get members of a chat group"""
    try:
        from auth import require_auth
        user = await require_auth(request)
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
