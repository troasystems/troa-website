"""Membership routes"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime
import logging

from database import db
from models import MembershipApplication, MembershipApplicationCreate, MembershipApplicationUpdate
from auth import require_manager_or_admin
from email_service import email_service, get_admin_manager_emails
from push_notifications import send_notification_to_admins

logger = logging.getLogger(__name__)

membership_router = APIRouter(prefix="/membership", tags=["Membership"])


@membership_router.post("", response_model=MembershipApplication)
async def create_membership_application(application: MembershipApplicationCreate):
    try:
        app_dict = application.dict()
        app_obj = MembershipApplication(**app_dict)
        await db.membership_applications.insert_one(app_obj.dict())
        logger.info(f"New membership application from {app_obj.email}")

        try:
            admin_emails = await get_admin_manager_emails()
            await email_service.send_membership_application_notification(
                applicant_name=app_obj.name,
                applicant_email=app_obj.email,
                applicant_phone=app_obj.phone,
                villa_no=app_obj.villa_no,
                message=app_obj.message if hasattr(app_obj, 'message') else None,
                admin_emails=admin_emails
            )
        except Exception as email_error:
            logger.error(f"Failed to send membership notification email: {email_error}")

        try:
            await send_notification_to_admins(
                title="New Membership Application",
                body=f"{app_obj.name} (Villa {app_obj.villa_no}) applied for membership",
                url="/admin"
            )
        except Exception as push_error:
            logger.error(f"Failed to send membership push notification: {push_error}")

        return app_obj
    except Exception as e:
        logger.error(f"Error creating membership application: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit membership application")


@membership_router.get("", response_model=List[MembershipApplication])
async def get_membership_applications(request: Request):
    """Get membership applications - admin and manager access"""
    try:
        await require_manager_or_admin(request)
        applications = await db.membership_applications.find().sort("created_at", -1).to_list(1000)
        return [MembershipApplication(**app) for app in applications]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching membership applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch membership applications")


@membership_router.patch("/{application_id}", response_model=MembershipApplication)
async def update_membership_application(application_id: str, update: MembershipApplicationUpdate, request: Request):
    """Update membership application status - admin and manager access"""
    try:
        user = await require_manager_or_admin(request)
        result = await db.membership_applications.find_one_and_update(
            {"id": application_id},
            {
                "$set": {
                    "status": update.status,
                    "updated_at": datetime.utcnow(),
                    "reviewed_by": user['email']
                }
            },
            return_document=True
        )
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
        return MembershipApplication(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating membership application: {e}")
        raise HTTPException(status_code=500, detail="Failed to update membership application")


@membership_router.delete("/{application_id}")
async def delete_membership_application(application_id: str, request: Request):
    """Delete membership application - admin and manager access"""
    try:
        await require_manager_or_admin(request)
        result = await db.membership_applications.delete_one({"id": application_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        return {"message": "Application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting membership application: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete membership application")
