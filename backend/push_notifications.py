"""
Push Notifications Service for PWA
Handles web push notifications using py-vapid and pywebpush
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
import json

logger = logging.getLogger(__name__)

push_router = APIRouter(prefix="/push", tags=["Push Notifications"])

# Store subscriptions in memory (in production, use database)
# This will be migrated to MongoDB
push_subscriptions = {}

class PushSubscription(BaseModel):
    subscription: dict
    user_email: str

class UnsubscribeRequest(BaseModel):
    user_email: str

class PushNotificationPayload(BaseModel):
    title: str
    body: str
    icon: Optional[str] = "/icons/icon-192x192.png"
    badge: Optional[str] = "/icons/icon-72x72.png"
    url: Optional[str] = "/"
    tag: Optional[str] = "troa-notification"
    user_emails: Optional[List[str]] = None  # If None, send to all


@push_router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for push notification subscription"""
    vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    if not vapid_public_key:
        raise HTTPException(status_code=500, detail="VAPID keys not configured")
    return {"publicKey": vapid_public_key}


@push_router.post("/subscribe")
async def subscribe_to_push(data: PushSubscription, request: Request):
    """Subscribe a user to push notifications"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        
        # Store subscription
        push_subscriptions[data.user_email] = data.subscription
        
        logger.info(f"Push subscription added for {data.user_email}")
        
        # In production, save to MongoDB
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        await db.push_subscriptions.update_one(
            {"user_email": data.user_email},
            {
                "$set": {
                    "user_email": data.user_email,
                    "subscription": data.subscription,
                    "active": True
                }
            },
            upsert=True
        )
        
        return {"message": "Successfully subscribed to push notifications"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to push: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe to push notifications")

@push_router.post("/unsubscribe")
async def unsubscribe_from_push(data: UnsubscribeRequest, request: Request):
    """Unsubscribe a user from push notifications"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        
        # Remove from memory
        if data.user_email in push_subscriptions:
            del push_subscriptions[data.user_email]
        
        # Remove from MongoDB
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        await db.push_subscriptions.update_one(
            {"user_email": data.user_email},
            {"$set": {"active": False}}
        )
        
        logger.info(f"Push subscription removed for {data.user_email}")
        return {"message": "Successfully unsubscribed from push notifications"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from push: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe from push notifications")

@push_router.post("/send")
async def send_push_notification(payload: PushNotificationPayload, request: Request):
    """Send push notification to users (admin only)"""
    try:
        from auth import require_admin
        await require_admin(request)
        
        # Get VAPID keys from environment
        vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY', '').replace('\\n', '\n')
        vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY')
        vapid_email = os.environ.get('VAPID_EMAIL', 'mailto:troa.systems@gmail.com')
        
        if not vapid_private_key or not vapid_public_key:
            logger.warning("VAPID keys not configured, push notifications disabled")
            return {"message": "Push notifications not configured", "sent": 0}
        
        # Get subscriptions from MongoDB
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        query = {"active": True}
        if payload.user_emails:
            query["user_email"] = {"$in": payload.user_emails}
        
        subscriptions = await db.push_subscriptions.find(query, {"_id": 0}).to_list(1000)
        
        if not subscriptions:
            return {"message": "No active subscriptions found", "sent": 0}
        
        # Send notifications using pywebpush
        try:
            from pywebpush import webpush, WebPushException
            
            notification_payload = json.dumps({
                "title": payload.title,
                "body": payload.body,
                "icon": payload.icon,
                "badge": payload.badge,
                "data": {"url": payload.url},
                "tag": payload.tag
            })
            
            sent_count = 0
            failed_count = 0
            
            for sub in subscriptions:
                try:
                    webpush(
                        subscription_info=sub['subscription'],
                        data=notification_payload,
                        vapid_private_key=vapid_private_key,
                        vapid_claims={
                            "sub": vapid_email
                        }
                    )
                    sent_count += 1
                except WebPushException as e:
                    logger.error(f"Failed to send push to {sub['user_email']}: {e}")
                    # If subscription is invalid, mark as inactive
                    if e.response and e.response.status_code in [404, 410]:
                        await db.push_subscriptions.update_one(
                            {"user_email": sub['user_email']},
                            {"$set": {"active": False}}
                        )
                    failed_count += 1
            
            return {
                "message": f"Push notifications sent",
                "sent": sent_count,
                "failed": failed_count
            }
        except ImportError:
            logger.warning("pywebpush not installed, skipping push notifications")
            return {"message": "pywebpush not installed", "sent": 0}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send push notification")

@push_router.get("/status")
async def get_push_status(request: Request):
    """Get push notification status for current user"""
    try:
        from auth import require_auth
        user = await require_auth(request)
        
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        subscription = await db.push_subscriptions.find_one(
            {"user_email": user['email'], "active": True},
            {"_id": 0}
        )
        
        return {
            "subscribed": subscription is not None,
            "vapid_configured": bool(os.environ.get('VAPID_PUBLIC_KEY'))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting push status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get push status")


# Helper function to send push notification from other services
async def send_notification_to_user(user_email: str, title: str, body: str, url: str = "/"):
    """Helper function to send push notification to a specific user"""
    try:
        vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY', '').replace('\\n', '\n')
        vapid_public_key = os.environ.get('VAPID_PUBLIC_KEY')
        vapid_email = os.environ.get('VAPID_EMAIL', 'mailto:troa.systems@gmail.com')
        
        if not vapid_private_key or not vapid_public_key:
            logger.debug("VAPID keys not configured")
            return False
        
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        subscription = await db.push_subscriptions.find_one(
            {"user_email": user_email, "active": True},
            {"_id": 0}
        )
        
        if not subscription:
            return False
        
        try:
            from pywebpush import webpush, WebPushException
            
            notification_payload = json.dumps({
                "title": title,
                "body": body,
                "icon": "/icons/icon-192x192.png",
                "badge": "/icons/icon-72x72.png",
                "data": {"url": url},
                "tag": "troa-notification"
            })
            
            webpush(
                subscription_info=subscription['subscription'],
                data=notification_payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": vapid_email}
            )
            return True
        except ImportError:
            logger.debug("pywebpush not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False
    except Exception as e:
        logger.error(f"Error in send_notification_to_user: {e}")
        return False


async def send_notification_to_admins(title: str, body: str, url: str = "/admin"):
    """Helper function to send push notification to all admins (admin role only, not managers)"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        # Get admin emails only (not managers)
        admins = await db.users.find(
            {"role": "admin"},
            {"email": 1, "_id": 0}
        ).to_list(100)
        
        admin_emails = [admin['email'] for admin in admins]
        
        for email in admin_emails:
            await send_notification_to_user(email, title, body, url)
    except Exception as e:
        logger.error(f"Error sending notifications to admins: {e}")


async def send_notification_to_group_members(group_id: str, title: str, body: str, exclude_email: str = None, url: str = "/chat"):
    """Helper function to send push notification to all members of a chat group"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        # Get group members
        group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0, "members": 1})
        if not group:
            return
        
        member_emails = group.get('members', [])
        
        for email in member_emails:
            # Skip the sender
            if email == exclude_email:
                continue
            await send_notification_to_user(email, title, body, url)
    except Exception as e:
        logger.error(f"Error sending notifications to group members: {e}")
