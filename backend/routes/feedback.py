"""Feedback routes"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
import logging

from database import db
from models import Feedback, FeedbackCreate
from auth import require_admin, require_auth
from email_service import email_service, get_admin_manager_emails
from push_notifications import send_notification_to_admins

logger = logging.getLogger(__name__)

feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])


@feedback_router.post("", response_model=Feedback)
async def submit_feedback(feedback: FeedbackCreate, request: Request):
    """Submit feedback - requires authentication"""
    try:
        user = await require_auth(request)
        feedback_obj = Feedback(
            user_email=user['email'],
            user_name=user['name'],
            rating=feedback.rating,
            works_well=feedback.works_well,
            needs_improvement=feedback.needs_improvement,
            feature_suggestions=feedback.feature_suggestions
        )
        await db.feedback.insert_one(feedback_obj.dict())
        logger.info(f"Feedback submitted by {user['email']}")

        try:
            admin_emails = await get_admin_manager_emails()
            await email_service.send_feedback_notification(
                user_name=user['name'],
                user_email=user['email'],
                rating=feedback.rating,
                works_well=feedback.works_well,
                needs_improvement=feedback.needs_improvement,
                feature_suggestions=feedback.feature_suggestions,
                admin_emails=admin_emails
            )
        except Exception as email_error:
            logger.error(f"Failed to send feedback notification email: {email_error}")

        try:
            await send_notification_to_admins(
                title="New Feedback Received",
                body=f"{user['name']} submitted feedback with {feedback.rating} rating",
                url="/admin"
            )
        except Exception as push_error:
            logger.error(f"Failed to send feedback push notification: {push_error}")

        return feedback_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@feedback_router.get("", response_model=List[Feedback])
async def get_all_feedback(request: Request):
    """Get all feedback - admin only"""
    try:
        await require_admin(request)
        feedback_list = await db.feedback.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return [Feedback(**fb) for fb in feedback_list]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback")


@feedback_router.post("/{feedback_id}/vote")
async def vote_feedback(feedback_id: str, request: Request):
    """Vote/upvote feedback - admin only"""
    try:
        user = await require_admin(request)
        user_email = user['email']
        feedback = await db.feedback.find_one({"id": feedback_id}, {"_id": 0})
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        voted_by = feedback.get('voted_by', [])
        if user_email in voted_by:
            voted_by.remove(user_email)
            votes = feedback.get('votes', 0) - 1
        else:
            voted_by.append(user_email)
            votes = feedback.get('votes', 0) + 1
        await db.feedback.update_one(
            {"id": feedback_id},
            {"$set": {"votes": votes, "voted_by": voted_by}}
        )
        return {"message": "Vote updated", "votes": votes}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to vote feedback")


@feedback_router.delete("/{feedback_id}")
async def delete_feedback(feedback_id: str, request: Request):
    """Delete feedback - admin only"""
    try:
        await require_admin(request)
        result = await db.feedback.delete_one({"id": feedback_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return {"message": "Feedback deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete feedback")
