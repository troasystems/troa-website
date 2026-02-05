"""
WebSocket Manager for TROA Community Chat
Handles real-time messaging, typing indicators, and read receipts
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
import json
import logging
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for chat groups"""
    
    def __init__(self):
        # Structure: {group_id: {user_email: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Track user info for each connection
        self.user_info: Dict[str, Dict[str, dict]] = {}  # {group_id: {user_email: {name, picture}}}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, group_id: str, user_email: str, user_name: str, user_picture: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        async with self._lock:
            if group_id not in self.active_connections:
                self.active_connections[group_id] = {}
                self.user_info[group_id] = {}
            
            # Close existing connection for same user in same group (if any)
            if user_email in self.active_connections[group_id]:
                try:
                    await self.active_connections[group_id][user_email].close()
                except:
                    pass
            
            self.active_connections[group_id][user_email] = websocket
            self.user_info[group_id][user_email] = {
                "name": user_name,
                "picture": user_picture
            }
        
        logger.info(f"WebSocket connected: {user_email} to group {group_id}")
        
        # Notify others that user joined
        await self.broadcast_to_group(group_id, {
            "type": "user_joined",
            "user_email": user_email,
            "user_name": user_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, exclude_user=user_email)
    
    async def disconnect(self, group_id: str, user_email: str):
        """Remove a WebSocket connection"""
        async with self._lock:
            if group_id in self.active_connections:
                if user_email in self.active_connections[group_id]:
                    del self.active_connections[group_id][user_email]
                    
                if user_email in self.user_info.get(group_id, {}):
                    del self.user_info[group_id][user_email]
                
                # Clean up empty groups
                if not self.active_connections[group_id]:
                    del self.active_connections[group_id]
                    if group_id in self.user_info:
                        del self.user_info[group_id]
        
        logger.info(f"WebSocket disconnected: {user_email} from group {group_id}")
        
        # Notify others that user left
        await self.broadcast_to_group(group_id, {
            "type": "user_left",
            "user_email": user_email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def broadcast_to_group(self, group_id: str, message: dict, exclude_user: Optional[str] = None):
        """Broadcast a message to all users in a group"""
        if group_id not in self.active_connections:
            return
        
        disconnected = []
        message_json = json.dumps(message)
        
        for user_email, websocket in self.active_connections[group_id].items():
            if exclude_user and user_email == exclude_user:
                continue
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to {user_email}: {e}")
                disconnected.append(user_email)
        
        # Clean up disconnected users
        for user_email in disconnected:
            await self.disconnect(group_id, user_email)
    
    async def send_to_user(self, group_id: str, user_email: str, message: dict):
        """Send a message to a specific user in a group"""
        if group_id not in self.active_connections:
            return False
        if user_email not in self.active_connections[group_id]:
            return False
        
        try:
            await self.active_connections[group_id][user_email].send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending to {user_email}: {e}")
            await self.disconnect(group_id, user_email)
            return False
    
    def get_online_users(self, group_id: str) -> List[dict]:
        """Get list of online users in a group"""
        if group_id not in self.active_connections:
            return []
        
        online_users = []
        for user_email in self.active_connections[group_id].keys():
            user_data = self.user_info.get(group_id, {}).get(user_email, {})
            online_users.append({
                "email": user_email,
                "name": user_data.get("name", "Unknown"),
                "picture": user_data.get("picture")
            })
        return online_users
    
    def is_user_online(self, group_id: str, user_email: str) -> bool:
        """Check if a user is online in a group"""
        return (group_id in self.active_connections and 
                user_email in self.active_connections[group_id])
    
    def get_connection_count(self, group_id: str) -> int:
        """Get number of connections in a group"""
        if group_id not in self.active_connections:
            return 0
        return len(self.active_connections[group_id])


# Global WebSocket manager instance
chat_manager = ConnectionManager()


# Message types for WebSocket communication
class WSMessageType:
    # Outgoing (server -> client)
    NEW_MESSAGE = "new_message"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_UPDATED = "message_updated"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    READ_RECEIPT = "read_receipt"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ONLINE_USERS = "online_users"
    ERROR = "error"
    
    # Incoming (client -> server)
    SEND_MESSAGE = "send_message"
    DELETE_MESSAGE = "delete_message"
    START_TYPING = "start_typing"
    STOP_TYPING = "stop_typing"
    MARK_READ = "mark_read"
    ADD_REACTION = "add_reaction"
    REMOVE_REACTION = "remove_reaction"
    GET_ONLINE_USERS = "get_online_users"
