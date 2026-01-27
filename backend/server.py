from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from models import (
    CommitteeMember, CommitteeMemberCreate,
    Amenity, AmenityCreate,
    GalleryImage, GalleryImageCreate,
    MembershipApplication, MembershipApplicationCreate, MembershipApplicationUpdate,
    User, UserCreate, UserUpdate,
    Feedback, FeedbackCreate,
    AmenityBooking, AmenityBookingCreate,
    BookingGuest, AuditLogEntry, BookingAvailedUpdate, BookingAmendment,
    Invoice, InvoiceCreate, InvoiceUpdate, InvoiceLineItem,
    MaintenanceInvoiceCreate, MaintenanceLineItem, MultiInvoicePayment,
    Villa, VillaCreate, VillaUpdate,
    VALID_ROLES, STAFF_ROLES, INVOICE_TYPE_CLUBHOUSE, INVOICE_TYPE_MAINTENANCE
)
from auth import auth_router, require_admin, require_manager_or_admin, require_auth, require_clubhouse_staff, require_accountant, require_staff
from basic_auth import basic_auth_middleware
from instagram import instagram_router
from gridfs_upload import gridfs_router  # GridFS-based upload for production
from payment import payment_router
from pdf_service import generate_booking_report_pdf, generate_invoice_pdf
from chatbot import chatbot_router
from events import events_router
from villas import villas_router
from email_service import email_service, get_admin_manager_emails
from push_notifications import send_notification_to_user, send_notification_to_admins

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
# redirect_slashes=False prevents 307 redirects when trailing slash is missing
app = FastAPI(redirect_slashes=False)

# Add cache headers middleware for static-like API responses
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers to responses based on endpoint type"""
    
    # Endpoints that can be cached (public, read-only data)
    CACHEABLE_ENDPOINTS = [
        '/api/amenities',
        '/api/committee',
        '/api/gallery',
    ]
    
    # Endpoints that should never be cached
    NO_CACHE_ENDPOINTS = [
        '/api/auth',
        '/api/bookings',
        '/api/payment',
        '/api/chat',
        '/api/feedback',
        '/api/membership',
        '/api/push',
        '/api/users',
        '/api/events',
    ]
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only add cache headers for GET requests
        if request.method != 'GET':
            return response
        
        path = request.url.path
        
        # Check if endpoint should be cached
        if any(path.startswith(ep) for ep in self.CACHEABLE_ENDPOINTS):
            # Cache for 5 minutes, allow stale for 1 hour while revalidating
            response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=3600'
            response.headers['Vary'] = 'Accept-Encoding'
        elif any(path.startswith(ep) for ep in self.NO_CACHE_ENDPOINTS):
            # Never cache sensitive endpoints
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
        else:
            # Default: short cache for other endpoints
            response.headers['Cache-Control'] = 'private, max-age=60'
        
        return response

app.add_middleware(CacheControlMiddleware)

# Health check endpoint at root level (no /api prefix) for Kubernetes
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes - no authentication required"""
    return {"status": "healthy"}

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint at /api/health for Docker
@api_router.get("/health")
async def api_health_check():
    """Health check endpoint for Docker - no authentication required"""
    return {"status": "healthy", "service": "troa-backend"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Routes
@api_router.get("/")
async def root():
    return {"message": "TROA API - The Retreat Owners Association"}

# Committee Members Routes
@api_router.get("/committee", response_model=List[CommitteeMember])
async def get_committee_members():
    try:
        members = await db.committee_members.find().to_list(100)
        result = []
        for member in members:
            # Use existing 'id' field or fallback to string of MongoDB '_id'
            if 'id' not in member or not member['id']:
                member['id'] = str(member['_id'])
            member.pop('_id', None)
            result.append(CommitteeMember(**member))
        return result
    except Exception as e:
        logger.error(f"Error fetching committee members: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch committee members")

@api_router.post("/committee", response_model=CommitteeMember)
async def create_committee_member(member: CommitteeMemberCreate, request: Request):
    try:
        # Require admin authentication
        await require_admin(request)
        
        member_dict = member.dict()
        member_obj = CommitteeMember(**member_dict)
        await db.committee_members.insert_one(member_obj.dict())
        return member_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating committee member: {e}")
        raise HTTPException(status_code=500, detail="Failed to create committee member")

@api_router.patch("/committee/{member_id}", response_model=CommitteeMember)
async def update_committee_member(member_id: str, member: CommitteeMemberCreate, request: Request):
    """Update committee member - admin only"""
    try:
        admin = await require_admin(request)
        
        # Try to find by 'id' field first, then by '_id' (for legacy documents)
        from bson import ObjectId
        query = {"id": member_id}
        existing = await db.committee_members.find_one(query)
        
        if not existing:
            # Try finding by MongoDB _id (for documents without 'id' field)
            try:
                query = {"_id": ObjectId(member_id)}
                existing = await db.committee_members.find_one(query)
            except:
                pass
        
        if not existing:
            raise HTTPException(status_code=404, detail="Committee member not found")
        
        # Update the document and ensure it has an 'id' field
        update_data = member.dict()
        update_data['id'] = member_id  # Persist the id field
        
        result = await db.committee_members.find_one_and_update(
            query,
            {"$set": update_data},
            return_document=True
        )
        
        result.pop('_id', None)
        return CommitteeMember(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating committee member: {e}")
        raise HTTPException(status_code=500, detail="Failed to update committee member")

@api_router.delete("/committee/{member_id}")
async def delete_committee_member(member_id: str, request: Request):
    """Delete committee member - admin only"""
    try:
        admin = await require_admin(request)
        
        # Try to delete by 'id' field first, then by '_id' (for legacy documents)
        from bson import ObjectId
        result = await db.committee_members.delete_one({"id": member_id})
        
        if result.deleted_count == 0:
            # Try deleting by MongoDB _id
            try:
                result = await db.committee_members.delete_one({"_id": ObjectId(member_id)})
            except:
                pass
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Committee member not found")
        
        return {"message": "Committee member deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting committee member: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete committee member")

# Amenities Routes
@api_router.get("/amenities", response_model=List[Amenity])
async def get_amenities():
    try:
        amenities = await db.amenities.find().to_list(100)
        result = []
        for amenity in amenities:
            # Use existing 'id' field or fallback to string of MongoDB '_id'
            if 'id' not in amenity or not amenity['id']:
                amenity['id'] = str(amenity['_id'])
            amenity.pop('_id', None)
            result.append(Amenity(**amenity))
        return result
    except Exception as e:
        logger.error(f"Error fetching amenities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch amenities")

@api_router.post("/amenities", response_model=Amenity)
async def create_amenity(amenity: AmenityCreate, request: Request):
    try:
        # Require admin authentication
        await require_admin(request)
        
        amenity_dict = amenity.dict()
        amenity_obj = Amenity(**amenity_dict)
        await db.amenities.insert_one(amenity_obj.dict())
        return amenity_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating amenity: {e}")
        raise HTTPException(status_code=500, detail="Failed to create amenity")

@api_router.patch("/amenities/{amenity_id}", response_model=Amenity)
async def update_amenity(amenity_id: str, amenity: AmenityCreate, request: Request):
    """Update amenity - admin only"""
    try:
        admin = await require_admin(request)
        
        # Try to find by 'id' field first, then by '_id' (for legacy documents)
        from bson import ObjectId
        query = {"id": amenity_id}
        existing = await db.amenities.find_one(query)
        
        if not existing:
            # Try finding by MongoDB _id (for documents without 'id' field)
            try:
                query = {"_id": ObjectId(amenity_id)}
                existing = await db.amenities.find_one(query)
            except:
                pass
        
        if not existing:
            raise HTTPException(status_code=404, detail="Amenity not found")
        
        # Update the document and ensure it has an 'id' field
        update_data = amenity.dict()
        update_data['id'] = amenity_id  # Persist the id field
        
        result = await db.amenities.find_one_and_update(
            query,
            {"$set": update_data},
            return_document=True
        )
        
        result.pop('_id', None)
        return Amenity(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating amenity: {e}")
        raise HTTPException(status_code=500, detail="Failed to update amenity")

@api_router.delete("/amenities/{amenity_id}")
async def delete_amenity(amenity_id: str, request: Request):
    """Delete amenity - admin only"""
    try:
        admin = await require_admin(request)
        
        # Try to delete by 'id' field first, then by '_id' (for legacy documents)
        from bson import ObjectId
        result = await db.amenities.delete_one({"id": amenity_id})
        
        if result.deleted_count == 0:
            # Try deleting by MongoDB _id
            try:
                result = await db.amenities.delete_one({"_id": ObjectId(amenity_id)})
            except:
                pass
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Amenity not found")
        
        return {"message": "Amenity deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting amenity: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete amenity")

# Gallery Routes
@api_router.get("/gallery", response_model=List[GalleryImage])
async def get_gallery_images():
    try:
        images = await db.gallery_images.find().to_list(100)
        return [GalleryImage(**image) for image in images]
    except Exception as e:
        logger.error(f"Error fetching gallery images: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")

@api_router.post("/gallery", response_model=GalleryImage)
async def create_gallery_image(image: GalleryImageCreate):
    try:
        image_dict = image.dict()
        image_obj = GalleryImage(**image_dict)
        await db.gallery_images.insert_one(image_obj.dict())
        return image_obj
    except Exception as e:
        logger.error(f"Error creating gallery image: {e}")
        raise HTTPException(status_code=500, detail="Failed to create gallery image")

# Membership Routes
@api_router.post("/membership", response_model=MembershipApplication)
async def create_membership_application(application: MembershipApplicationCreate):
    try:
        app_dict = application.dict()
        app_obj = MembershipApplication(**app_dict)
        await db.membership_applications.insert_one(app_obj.dict())
        logger.info(f"New membership application from {app_obj.email}")
        
        # Send email notification to admins
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
        
        # Send push notification to admins
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

@api_router.get("/membership", response_model=List[MembershipApplication])
async def get_membership_applications(request: Request):
    """Get membership applications - admin and manager access"""
    try:
        # Check if user is admin or manager
        await require_manager_or_admin(request)
        
        applications = await db.membership_applications.find().sort("created_at", -1).to_list(1000)
        return [MembershipApplication(**app) for app in applications]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching membership applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch membership applications")

@api_router.patch("/membership/{application_id}", response_model=MembershipApplication)
async def update_membership_application(application_id: str, update: MembershipApplicationUpdate, request: Request):
    """Update membership application status - admin and manager access"""
    try:
        user = await require_manager_or_admin(request)
        
        from datetime import datetime
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

@api_router.delete("/membership/{application_id}")
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

# User Management Routes (Admin only)
@api_router.get("/users", response_model=List[User])
async def get_all_users(request: Request):
    """Get all users - admin only"""
    try:
        await require_admin(request)
        
        users = await db.users.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return [User(**user) for user in users]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@api_router.post("/users", response_model=User)
async def add_user_to_whitelist(user_data: UserCreate, request: Request):
    """Add user to whitelist - admin only"""
    try:
        admin = await require_admin(request)
        
        # Check if user already exists
        existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Validate role
        if user_data.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
        
        # Create user with the specified role
        user_obj = User(
            email=user_data.email,
            name=user_data.name or "",
            picture=user_data.picture or "",
            provider="whitelist",
            role=user_data.role,
            is_admin=user_data.role == 'admin',
            villa_number=user_data.villa_number.strip() if user_data.villa_number else ""
        )
        
        await db.users.insert_one(user_obj.dict())
        logger.info(f"User added to whitelist by {admin['email']}: {user_data.email} with role {user_data.role}, villa: {user_data.villa_number}")
        return user_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding user to whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add user")

@api_router.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: str, update: UserUpdate, request: Request):
    """Update user details - admin only"""
    try:
        admin = await require_admin(request)
        
        # Check if trying to modify super admin's role
        from auth import SUPER_ADMIN_EMAIL
        user_to_update = await db.users.find_one({"id": user_id}, {"_id": 0})
        
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user_to_update.get('email') == SUPER_ADMIN_EMAIL and update.role and update.role != 'admin':
            raise HTTPException(status_code=400, detail="Cannot modify the super admin's role")
        
        # Build update dict with only provided fields
        update_data = {"updated_at": datetime.utcnow()}
        
        # Validate and add role if provided
        if update.role is not None:
            if update.role not in VALID_ROLES:
                raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
            update_data["role"] = update.role
            update_data["is_admin"] = update.role == 'admin'
        
        # Add name if provided
        if update.name is not None:
            update_data["name"] = update.name
        
        # Validate and add villa_number if provided (alphanumeric allowed)
        if update.villa_number is not None:
            update_data["villa_number"] = update.villa_number.strip()
        
        # Add picture if provided
        if update.picture is not None:
            update_data["picture"] = update.picture
        
        # Handle password reset if provided
        if update.new_password is not None:
            if len(update.new_password) < 6:
                raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
            import bcrypt
            password_hash = bcrypt.hashpw(update.new_password.encode('utf-8'), bcrypt.gensalt())
            update_data["password_hash"] = password_hash.decode('utf-8')
        
        # Handle email_verified toggle if provided
        if update.email_verified is not None:
            update_data["email_verified"] = update.email_verified
            if update.email_verified:
                update_data["verified_at"] = datetime.utcnow()
                update_data["verification_token"] = None  # Clear token when manually verified
            else:
                update_data["verified_at"] = None
        
        result = await db.users.find_one_and_update(
            {"id": user_id},
            {"$set": update_data},
            return_document=True
        )
        
        # Remove _id and password_hash for serialization
        result.pop('_id', None)
        result.pop('password_hash', None)
        return User(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    """Delete user - admin only"""
    try:
        admin = await require_admin(request)
        
        # Get user to delete
        user_to_delete = await db.users.find_one({"id": user_id}, {"_id": 0})
        
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deleting themselves
        if user_to_delete.get('email') == admin.get('email'):
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Prevent deleting the super admin
        from auth import SUPER_ADMIN_EMAIL
        if user_to_delete.get('email') == SUPER_ADMIN_EMAIL:
            raise HTTPException(status_code=400, detail="Cannot delete the super admin account")
        
        result = await db.users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

# Feedback Routes
@api_router.post("/feedback", response_model=Feedback)
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
        
        # Send email notification to admins
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
        
        # Send push notification to admins
        try:
            await send_notification_to_admins(
                title="New Feedback Received",
                body=f"{user['name']} submitted feedback with {feedback.rating}⭐ rating",
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

@api_router.get("/feedback", response_model=List[Feedback])
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

@api_router.post("/feedback/{feedback_id}/vote")
async def vote_feedback(feedback_id: str, request: Request):
    """Vote/upvote feedback - admin only"""
    try:
        user = await require_admin(request)
        user_email = user['email']
        
        # Get feedback
        feedback = await db.feedback.find_one({"id": feedback_id}, {"_id": 0})
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        voted_by = feedback.get('voted_by', [])
        
        # Toggle vote
        if user_email in voted_by:
            # Remove vote
            voted_by.remove(user_email)
            votes = feedback.get('votes', 0) - 1
        else:
            # Add vote
            voted_by.append(user_email)
            votes = feedback.get('votes', 0) + 1
        
        # Update feedback
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

@api_router.delete("/feedback/{feedback_id}")
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

# Amenity Booking Routes
GUEST_CHARGE = 50.0  # ₹50 per session for external guests and coaches

@api_router.post("/bookings", response_model=AmenityBooking)
async def create_booking(booking: AmenityBookingCreate, request: Request):
    """Create amenity booking - authenticated users only"""
    try:
        user = await require_auth(request)
        
        # Validate duration
        if booking.duration_minutes not in [30, 60]:
            raise HTTPException(status_code=400, detail="Duration must be 30 or 60 minutes")
        
        # Process guests with proper validation and charges
        processed_guests = []
        total_guest_charges = 0.0
        
        for guest in (booking.guests or []):
            guest_type = guest.get('guest_type', 'external')
            guest_name = guest.get('name', '').strip()
            villa_number = guest.get('villa_number', '').strip() if guest.get('villa_number') else None
            
            if not guest_name:
                continue
            
            # Validate resident guests have villa number
            if guest_type == 'resident' and not villa_number:
                raise HTTPException(status_code=400, detail=f"Villa number is required for resident guest: {guest_name}")
            
            # Calculate charges for external guests and coaches
            charge = 0.0
            if guest_type in ['external', 'coach']:
                charge = GUEST_CHARGE
                total_guest_charges += charge
            
            processed_guests.append({
                'name': guest_name,
                'guest_type': guest_type,
                'villa_number': villa_number,
                'charge': charge
            })
        
        # Validate max guests (3)
        if len(processed_guests) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 additional guests allowed")
        
        # Legacy support: convert additional_guests strings to guest objects
        legacy_guests = []
        if booking.additional_guests and not booking.guests:
            for name in booking.additional_guests[:3]:
                if name.strip():
                    legacy_guests.append({
                        'name': name.strip(),
                        'guest_type': 'external',
                        'villa_number': None,
                        'charge': GUEST_CHARGE
                    })
                    total_guest_charges += GUEST_CHARGE
            processed_guests = legacy_guests
        
        # Calculate end time
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(booking.start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=booking.duration_minutes)
        end_time = end_dt.strftime("%H:%M")
        
        # Check for conflicts
        existing_bookings = await db.bookings.find({
            "amenity_id": booking.amenity_id,
            "booking_date": booking.booking_date,
            "status": "confirmed"
        }, {"_id": 0}).to_list(100)
        
        for existing in existing_bookings:
            existing_start = datetime.strptime(existing['start_time'], "%H:%M")
            existing_end = datetime.strptime(existing['end_time'], "%H:%M")
            new_start = start_dt
            new_end = end_dt
            
            # Check for time overlap
            if (new_start < existing_end and new_end > existing_start):
                raise HTTPException(
                    status_code=409, 
                    detail=f"Time slot conflicts with existing booking ({existing['start_time']}-{existing['end_time']})"
                )
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'created',
            'by_email': user['email'],
            'by_name': user['name'],
            'by_role': user.get('role', 'user'),
            'details': f"Booking created with {len(processed_guests)} guest(s)",
            'changes': None
        }
        
        # Create booking
        booking_obj = AmenityBooking(
            amenity_id=booking.amenity_id,
            amenity_name=booking.amenity_name,
            booked_by_email=user['email'],
            booked_by_name=user['name'],
            booked_by_villa=user.get('villa_number'),
            booking_date=booking.booking_date,
            start_time=booking.start_time,
            end_time=end_time,
            duration_minutes=booking.duration_minutes,
            guests=processed_guests,
            additional_guests=[g['name'] for g in processed_guests],  # Legacy compatibility
            total_guest_charges=total_guest_charges,
            audit_log=[audit_entry]
        )
        
        await db.bookings.insert_one(booking_obj.dict())
        logger.info(f"Booking created by {user['email']} for {booking.amenity_name} with {len(processed_guests)} guests, charges: ₹{total_guest_charges}")
        
        # Send booking confirmation email to user
        try:
            await email_service.send_booking_confirmation(
                recipient_email=user['email'],
                user_name=user['name'],
                amenity_name=booking.amenity_name,
                booking_date=booking.booking_date,
                start_time=booking.start_time,
                end_time=end_time,
                booking_id=booking_obj.id,
                additional_guests=booking.additional_guests
            )
        except Exception as email_error:
            logger.error(f"Failed to send booking confirmation email: {email_error}")
        
        # Send notification to admins/managers
        try:
            admin_emails = await get_admin_manager_emails()
            await email_service.send_booking_notification_to_admins(
                action='created',
                user_name=user['name'],
                user_email=user['email'],
                amenity_name=booking.amenity_name,
                booking_date=booking.booking_date,
                start_time=booking.start_time,
                end_time=end_time,
                admin_emails=admin_emails
            )
        except Exception as email_error:
            logger.error(f"Failed to send admin booking notification: {email_error}")
        
        # Send push notification to user
        try:
            await send_notification_to_user(
                user_email=user['email'],
                title="Booking Confirmed 🎉",
                body=f"Your {booking.amenity_name} booking on {booking.booking_date} at {booking.start_time} is confirmed!",
                url="/my-bookings"
            )
        except Exception as push_error:
            logger.error(f"Failed to send booking push notification: {push_error}")
        
        # Send push notification to admins
        try:
            await send_notification_to_admins(
                title="New Booking",
                body=f"{user['name']} booked {booking.amenity_name} on {booking.booking_date}",
                url="/admin"
            )
        except Exception as push_error:
            logger.error(f"Failed to send admin push notification: {push_error}")
        
        return booking_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to create booking")

@api_router.get("/bookings", response_model=List[AmenityBooking])
async def get_bookings(request: Request, amenity_id: Optional[str] = None, date: Optional[str] = None):
    """Get bookings - authenticated users can see all bookings"""
    try:
        user = await require_auth(request)
        
        query = {"status": "confirmed"}
        if amenity_id:
            query["amenity_id"] = amenity_id
        if date:
            query["booking_date"] = date
        
        bookings = await db.bookings.find(query, {"_id": 0}).sort("booking_date", 1).to_list(1000)
        return [AmenityBooking(**booking) for booking in bookings]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")

@api_router.get("/bookings/my", response_model=List[AmenityBooking])
async def get_my_bookings(request: Request):
    """Get current user's bookings"""
    try:
        user = await require_auth(request)
        
        bookings = await db.bookings.find({
            "booked_by_email": user['email'],
            "status": "confirmed"
        }, {"_id": 0}).sort("booking_date", -1).to_list(1000)
        
        return [AmenityBooking(**booking) for booking in bookings]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user bookings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")

@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, request: Request):
    """Cancel booking - only booking owner can cancel"""
    try:
        user = await require_auth(request)
        
        # Find booking
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check if user is the booking owner
        if booking['booked_by_email'] != user['email']:
            raise HTTPException(status_code=403, detail="You can only cancel your own bookings")
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'cancelled',
            'by_email': user['email'],
            'by_name': user['name'],
            'by_role': user.get('role', 'user'),
            'details': 'Booking cancelled by user',
            'changes': {'status': {'from': 'confirmed', 'to': 'cancelled'}}
        }
        
        # Update status to cancelled
        await db.bookings.update_one(
            {"id": booking_id},
            {
                "$set": {"status": "cancelled", "updated_at": datetime.utcnow()},
                "$push": {"audit_log": audit_entry}
            }
        )
        
        # Send cancellation email to user
        try:
            await email_service.send_booking_cancellation(
                recipient_email=user['email'],
                user_name=user['name'],
                amenity_name=booking['amenity_name'],
                booking_date=booking['booking_date'],
                start_time=booking['start_time'],
                end_time=booking['end_time']
            )
        except Exception as email_error:
            logger.error(f"Failed to send cancellation email: {email_error}")
        
        # Send notification to admins/managers
        try:
            admin_emails = await get_admin_manager_emails()
            await email_service.send_booking_notification_to_admins(
                action='cancelled',
                user_name=user['name'],
                user_email=user['email'],
                amenity_name=booking['amenity_name'],
                booking_date=booking['booking_date'],
                start_time=booking['start_time'],
                end_time=booking['end_time'],
                admin_emails=admin_emails
            )
        except Exception as email_error:
            logger.error(f"Failed to send admin cancellation notification: {email_error}")
        
        # Send push notification to admins about cancellation
        try:
            await send_notification_to_admins(
                title="Booking Cancelled",
                body=f"{user['name']} cancelled {booking['amenity_name']} booking on {booking['booking_date']}",
                url="/admin"
            )
        except Exception as push_error:
            logger.error(f"Failed to send admin push notification: {push_error}")
        
        return {"message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel booking")


# ============ CLUBHOUSE STAFF ROUTES ============

@api_router.get("/staff/bookings/today")
async def get_todays_bookings_for_staff(request: Request):
    """Get today's bookings for clubhouse staff"""
    try:
        user = await require_clubhouse_staff(request)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        bookings = await db.bookings.find({
            "booking_date": today,
            "status": "confirmed"
        }, {"_id": 0}).sort("start_time", 1).to_list(100)
        
        # Enrich with amenity details
        for booking in bookings:
            amenity = await db.amenities.find_one({"id": booking['amenity_id']}, {"_id": 0, "name": 1, "image": 1})
            if amenity:
                booking['amenity_image'] = amenity.get('image')
        
        return bookings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching today's bookings for staff: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")

@api_router.get("/staff/bookings/date/{date}")
async def get_bookings_by_date_for_staff(date: str, request: Request):
    """Get bookings for a specific date for clubhouse staff"""
    try:
        user = await require_clubhouse_staff(request)
        
        bookings = await db.bookings.find({
            "booking_date": date,
            "status": "confirmed"
        }, {"_id": 0}).sort("start_time", 1).to_list(100)
        
        # Enrich with amenity details
        for booking in bookings:
            amenity = await db.amenities.find_one({"id": booking['amenity_id']}, {"_id": 0, "name": 1, "image": 1})
            if amenity:
                booking['amenity_image'] = amenity.get('image')
        
        return bookings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bookings by date for staff: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")

@api_router.put("/staff/bookings/{booking_id}/availed")
async def mark_booking_availed(booking_id: str, update: BookingAvailedUpdate, request: Request):
    """Mark a booking as availed or not availed - clubhouse staff only"""
    try:
        user = await require_clubhouse_staff(request)
        
        # Find booking
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if update.availed_status not in ['availed', 'not_availed']:
            raise HTTPException(status_code=400, detail="Invalid availed status")
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': update.availed_status,
            'by_email': user['email'],
            'by_name': user['name'],
            'by_role': user.get('role', 'clubhouse_staff'),
            'details': f"Marked as {update.availed_status}" + (f" - {update.notes}" if update.notes else ""),
            'changes': {'availed_status': {'from': booking.get('availed_status', 'pending'), 'to': update.availed_status}}
        }
        
        # Update booking
        await db.bookings.update_one(
            {"id": booking_id},
            {
                "$set": {
                    "availed_status": update.availed_status,
                    "availed_at": datetime.utcnow(),
                    "availed_by_email": user['email'],
                    "availed_by_name": user['name'],
                    "updated_at": datetime.utcnow()
                },
                "$push": {"audit_log": audit_entry}
            }
        )
        
        logger.info(f"Booking {booking_id} marked as {update.availed_status} by {user['email']}")
        
        return {"message": f"Booking marked as {update.availed_status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking booking availed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update booking")

@api_router.put("/staff/bookings/{booking_id}/amend")
async def amend_booking(booking_id: str, amendment: BookingAmendment, request: Request):
    """Add amendment to a booking - clubhouse staff only"""
    try:
        user = await require_clubhouse_staff(request)
        
        # Find booking
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Calculate expected attendees (booker + guests)
        expected_attendees = 1 + len(booking.get('guests', []))
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'amendment',
            'by_email': user['email'],
            'by_name': user['name'],
            'by_role': user.get('role', 'clubhouse_staff'),
            'details': amendment.amendment_notes,
            'changes': {
                'expected_attendees': expected_attendees,
                'actual_attendees': amendment.actual_attendees,
                'additional_charges': amendment.additional_charges,
                'difference': amendment.actual_attendees - expected_attendees
            }
        }
        
        # Calculate total charges update
        new_total_charges = booking.get('total_guest_charges', 0) + (amendment.additional_charges or 0)
        
        # Update booking
        await db.bookings.update_one(
            {"id": booking_id},
            {
                "$set": {
                    "actual_attendees": amendment.actual_attendees,
                    "amendment_notes": amendment.amendment_notes,
                    "total_guest_charges": new_total_charges,
                    "updated_at": datetime.utcnow()
                },
                "$push": {"audit_log": audit_entry}
            }
        )
        
        logger.info(f"Booking {booking_id} amended by {user['email']}: {amendment.amendment_notes}")
        
        return {"message": "Booking amended successfully", "additional_charges": amendment.additional_charges}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error amending booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to amend booking")

@api_router.get("/staff/bookings/{booking_id}/audit-log")
async def get_booking_audit_log(booking_id: str, request: Request):
    """Get audit log for a booking - staff, manager, admin, or booking owner"""
    try:
        user = await require_auth(request)
        
        # Find booking
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Check access - booking owner, staff, manager, or admin
        is_owner = booking['booked_by_email'] == user['email']
        is_staff_or_above = user.get('role') in ['admin', 'manager', 'clubhouse_staff']
        
        if not is_owner and not is_staff_or_above:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "booking_id": booking_id,
            "audit_log": booking.get('audit_log', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit log")


# ============ PDF REPORT ROUTES ============

from fastapi.responses import Response

@api_router.get("/staff/reports/bookings")
async def download_booking_report(
    request: Request,
    amenity_id: str,
    month: int,
    year: int
):
    """Download PDF report of bookings for an amenity in a month"""
    try:
        user = await require_clubhouse_staff(request)
        
        # Validate month
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Invalid month")
        
        # Get amenity
        amenity = await db.amenities.find_one({"id": amenity_id}, {"_id": 0})
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found")
        
        # Get bookings for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        bookings = await db.bookings.find({
            "amenity_id": amenity_id,
            "booking_date": {"$gte": start_date, "$lt": end_date},
            "status": "confirmed"
        }, {"_id": 0}).sort("booking_date", 1).to_list(1000)
        
        # Generate PDF
        pdf_bytes = await generate_booking_report_pdf(
            amenity_name=amenity['name'],
            month=month,
            year=year,
            bookings=bookings,
            generated_by=user['name']
        )
        
        filename = f"TROA_Booking_Report_{amenity['name'].replace(' ', '_')}_{year}_{month:02d}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating booking report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


# ============ INVOICE ROUTES ============

INVOICE_RATE = 50.0  # ₹50 per person per session
RESIDENT_MONTHLY_CAP = 300.0  # ₹300 cap per amenity per month

def generate_invoice_number(year: int, month: int) -> str:
    """Generate unique invoice number for clubhouse subscription"""
    import random
    import string
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TROA-INV-{year}{month:02d}-{random_suffix}"


def generate_maintenance_invoice_number() -> str:
    """Generate unique invoice number for maintenance"""
    import random
    import string
    now = datetime.utcnow()
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TROA-MAINT-{now.year}{now.month:02d}-{random_suffix}"


@api_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, request: Request):
    """Create clubhouse subscription invoice for a user's amenity usage - Clubhouse Staff, Manager, or Admin"""
    try:
        user = await require_clubhouse_staff(request)
        
        # Validate month
        if invoice_data.month < 1 or invoice_data.month > 12:
            raise HTTPException(status_code=400, detail="Invalid month")
        
        # Check if invoice already exists
        existing = await db.invoices.find_one({
            "user_email": invoice_data.user_email,
            "amenity_id": invoice_data.amenity_id,
            "month": invoice_data.month,
            "year": invoice_data.year,
            "invoice_type": INVOICE_TYPE_CLUBHOUSE,
            "payment_status": {"$ne": "cancelled"}
        }, {"_id": 0})
        
        if existing:
            raise HTTPException(status_code=409, detail="Invoice already exists for this user/amenity/period")
        
        # Get user details
        target_user = await db.users.find_one({"email": invoice_data.user_email}, {"_id": 0})
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get amenity
        amenity = await db.amenities.find_one({"id": invoice_data.amenity_id}, {"_id": 0})
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found")
        
        # Get bookings for the user in this month
        start_date = f"{invoice_data.year}-{invoice_data.month:02d}-01"
        if invoice_data.month == 12:
            end_date = f"{invoice_data.year + 1}-01-01"
        else:
            end_date = f"{invoice_data.year}-{invoice_data.month + 1:02d}-01"
        
        bookings = await db.bookings.find({
            "amenity_id": invoice_data.amenity_id,
            "booked_by_email": invoice_data.user_email,
            "booking_date": {"$gte": start_date, "$lt": end_date},
            "status": "confirmed"
        }, {"_id": 0}).to_list(100)
        
        if not bookings:
            raise HTTPException(status_code=400, detail="No bookings found for this user/amenity/period")
        
        # Calculate amounts
        line_items = []
        resident_sessions = 0
        resident_amount_raw = 0.0
        guest_amount = 0.0
        coach_amount = 0.0
        
        for booking in bookings:
            # Count the booker as resident
            resident_sessions += 1
            resident_amount_raw += INVOICE_RATE
            
            line_items.append({
                'booking_id': booking['id'],
                'booking_date': booking['booking_date'],
                'start_time': booking['start_time'],
                'end_time': booking['end_time'],
                'attendee_type': 'resident',
                'attendee_count': 1,
                'rate': INVOICE_RATE,
                'amount': INVOICE_RATE,
                'audit_log': booking.get('audit_log', [])
            })
            
            # Process guests
            for guest in booking.get('guests', []):
                guest_type = guest.get('guest_type', 'external')
                charge = INVOICE_RATE
                
                if guest_type == 'resident':
                    resident_sessions += 1
                    resident_amount_raw += charge
                    line_items.append({
                        'booking_id': booking['id'],
                        'booking_date': booking['booking_date'],
                        'start_time': booking['start_time'],
                        'end_time': booking['end_time'],
                        'attendee_type': 'resident',
                        'attendee_count': 1,
                        'rate': charge,
                        'amount': charge,
                        'audit_log': []
                    })
                elif guest_type == 'external':
                    guest_amount += charge
                    line_items.append({
                        'booking_id': booking['id'],
                        'booking_date': booking['booking_date'],
                        'start_time': booking['start_time'],
                        'end_time': booking['end_time'],
                        'attendee_type': 'external',
                        'attendee_count': 1,
                        'rate': charge,
                        'amount': charge,
                        'audit_log': []
                    })
                elif guest_type == 'coach':
                    coach_amount += charge
                    line_items.append({
                        'booking_id': booking['id'],
                        'booking_date': booking['booking_date'],
                        'start_time': booking['start_time'],
                        'end_time': booking['end_time'],
                        'attendee_type': 'coach',
                        'attendee_count': 1,
                        'rate': charge,
                        'amount': charge,
                        'audit_log': []
                    })
        
        # Apply resident cap
        resident_amount_capped = min(resident_amount_raw, RESIDENT_MONTHLY_CAP)
        
        # Calculate totals
        subtotal = resident_amount_capped + guest_amount + coach_amount
        total_amount = subtotal
        
        # Create invoice
        due_date = datetime.utcnow() + timedelta(days=20)
        
        invoice = Invoice(
            invoice_number=generate_invoice_number(invoice_data.year, invoice_data.month),
            invoice_type=INVOICE_TYPE_CLUBHOUSE,
            villa_number=target_user.get('villa_number', ''),
            user_email=invoice_data.user_email,
            user_name=target_user.get('name', ''),
            user_villa=target_user.get('villa_number'),
            amenity_id=invoice_data.amenity_id,
            amenity_name=amenity['name'],
            month=invoice_data.month,
            year=invoice_data.year,
            line_items=line_items,
            resident_sessions_count=resident_sessions,
            resident_amount_raw=resident_amount_raw,
            resident_amount_capped=resident_amount_capped,
            guest_amount=guest_amount,
            coach_amount=coach_amount,
            subtotal=subtotal,
            total_amount=total_amount,
            due_date=due_date,
            created_by_email=user['email'],
            created_by_name=user['name']
        )
        
        await db.invoices.insert_one(invoice.dict())
        logger.info(f"Invoice {invoice.invoice_number} created for {invoice_data.user_email}")
        
        # Send email notification
        try:
            month_name = datetime(invoice_data.year, invoice_data.month, 1).strftime("%B %Y")
            await email_service.send_invoice_raised(
                recipient_email=invoice_data.user_email,
                user_name=target_user.get('name', ''),
                invoice_number=invoice.invoice_number,
                amenity_name=amenity['name'],
                month_year=month_name,
                total_amount=total_amount,
                due_date=due_date.strftime("%d %b %Y")
            )
        except Exception as email_error:
            logger.error(f"Failed to send invoice email: {email_error}")
        
        return invoice.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create invoice")


@api_router.post("/invoices/maintenance")
async def create_maintenance_invoice(invoice_data: MaintenanceInvoiceCreate, request: Request):
    """Create maintenance invoice against a villa - Accountant, Manager, or Admin"""
    try:
        user = await require_accountant(request)
        
        # Validate villa exists
        villa = await db.villas.find_one({"villa_number": invoice_data.villa_number}, {"_id": 0})
        if not villa:
            raise HTTPException(status_code=404, detail="Villa not found")
        
        if not invoice_data.line_items or len(invoice_data.line_items) == 0:
            raise HTTPException(status_code=400, detail="At least one line item is required")
        
        # Calculate amounts
        maintenance_line_items = []
        subtotal = 0.0
        
        for item in invoice_data.line_items:
            amount = item.quantity * item.rate
            maintenance_line_items.append({
                'id': str(uuid.uuid4()),
                'description': item.description,
                'quantity': item.quantity,
                'rate': item.rate,
                'amount': amount
            })
            subtotal += amount
        
        # Calculate discount
        discount_amount = 0.0
        if invoice_data.discount_type == "percentage":
            discount_amount = subtotal * (invoice_data.discount_value / 100)
        elif invoice_data.discount_type == "fixed":
            discount_amount = min(invoice_data.discount_value, subtotal)  # Can't discount more than subtotal
        
        total_amount = max(subtotal - discount_amount, 0)
        
        # Calculate due date
        due_date = datetime.utcnow() + timedelta(days=invoice_data.due_days)
        
        # Get primary email for the villa (first in the list)
        primary_email = villa.get('emails', [''])[0] if villa.get('emails') else ''
        
        invoice = Invoice(
            invoice_number=generate_maintenance_invoice_number(),
            invoice_type=INVOICE_TYPE_MAINTENANCE,
            villa_number=invoice_data.villa_number,
            user_email=primary_email,
            user_name='',  # Maintenance invoices are against villas, not specific users
            maintenance_line_items=maintenance_line_items,
            subtotal=subtotal,
            discount_type=invoice_data.discount_type,
            discount_value=invoice_data.discount_value,
            discount_amount=discount_amount,
            total_amount=total_amount,
            due_date=due_date,
            created_by_email=user['email'],
            created_by_name=user.get('name', ''),
            audit_log=[{
                'action': 'created',
                'timestamp': datetime.utcnow().isoformat(),
                'by_email': user['email'],
                'by_name': user.get('name', ''),
                'details': f"Maintenance invoice created with {len(maintenance_line_items)} line items"
            }]
        )
        
        await db.invoices.insert_one(invoice.dict())
        logger.info(f"Maintenance invoice {invoice.invoice_number} created for villa {invoice_data.villa_number}")
        
        # Send email notifications to all villa emails
        try:
            for email in villa.get('emails', []):
                # Get user name if registered
                villa_user = await db.users.find_one({"email": email}, {"_id": 0, "name": 1})
                user_name = villa_user.get('name', '') if villa_user else ''
                
                await email_service.send_maintenance_invoice_raised(
                    recipient_email=email,
                    user_name=user_name,
                    invoice_number=invoice.invoice_number,
                    villa_number=invoice_data.villa_number,
                    total_amount=total_amount,
                    due_date=due_date.strftime("%d %b %Y"),
                    line_items=maintenance_line_items
                )
        except Exception as email_error:
            logger.error(f"Failed to send maintenance invoice email: {email_error}")
        
        return invoice.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating maintenance invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create maintenance invoice")


@api_router.get("/invoices")
async def get_invoices(request: Request, status: Optional[str] = None, invoice_type: Optional[str] = None, view: Optional[str] = None):
    """Get invoices - managers/accountants see based on role, users see their own
    
    view parameter:
    - 'my': Force personal view (only show invoices for user's villa) - used by My Invoices page
    - 'manage': Management view (based on role permissions) - used by Invoice Management
    - None/default: Auto-detect based on role (backward compatible)
    """
    try:
        user = await require_auth(request)
        user_role = user.get('role')
        user_email = user.get('email')
        
        query = {}
        
        # If view='my', always show only user's personal invoices (villa-based)
        if view == 'my':
            # Get villas associated with this user's email
            user_villas = await db.villas.find(
                {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
                {"_id": 0, "villa_number": 1}
            ).to_list(100)
            villa_numbers = [v['villa_number'] for v in user_villas]
            
            # User sees invoices where they are directly assigned OR their villa is assigned
            if villa_numbers:
                query['$or'] = [
                    {'user_email': user_email},
                    {'villa_number': {'$in': villa_numbers}}
                ]
            else:
                # No villa associated - only show invoices directly assigned to user's email
                query['user_email'] = user_email
        
        # Management view - role-based access
        elif view == 'manage':
            if user_role in ['admin', 'manager']:
                # Admin and Manager see all invoices
                pass
            elif user_role == 'accountant':
                # Accountant sees only maintenance invoices (all maintenance invoices for management view)
                query['invoice_type'] = INVOICE_TYPE_MAINTENANCE
            elif user_role == 'clubhouse_staff':
                # Clubhouse staff sees only clubhouse subscription invoices
                query['invoice_type'] = INVOICE_TYPE_CLUBHOUSE
            else:
                # Regular users shouldn't access management view, return empty
                return []
        
        # Default behavior (backward compatible) - auto-detect based on role
        else:
            if user_role in ['admin', 'manager']:
                # Admin and Manager see all invoices
                pass
            elif user_role == 'accountant':
                # Accountant sees only maintenance invoices they created (backward compatible)
                query['invoice_type'] = INVOICE_TYPE_MAINTENANCE
                query['created_by_email'] = user_email
            elif user_role == 'clubhouse_staff':
                # Clubhouse staff sees only clubhouse subscription invoices
                query['invoice_type'] = INVOICE_TYPE_CLUBHOUSE
            else:
                # Regular users see invoices where their email is in the villa's email list OR directly assigned
                user_villas = await db.villas.find(
                    {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
                    {"_id": 0, "villa_number": 1}
                ).to_list(100)
                villa_numbers = [v['villa_number'] for v in user_villas]
                
                if villa_numbers:
                    query['$or'] = [
                        {'user_email': user_email},
                        {'villa_number': {'$in': villa_numbers}}
                    ]
                else:
                    query['user_email'] = user_email
        
        # Filter by status if provided
        if status:
            query['payment_status'] = status
        
        # Filter by invoice type if provided (overrides role-based type filtering for admin/manager)
        if invoice_type:
            query['invoice_type'] = invoice_type
        
        invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
        
        return invoices
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")


@api_router.get("/invoices/pending/count")
async def get_pending_invoice_count(request: Request):
    """Get count of pending invoices for current user (including villa-based invoices)"""
    try:
        user = await require_auth(request)
        user_email = user.get('email')
        
        # Get villas associated with this user's email
        user_villas = await db.villas.find(
            {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
            {"_id": 0, "villa_number": 1}
        ).to_list(100)
        villa_numbers = [v['villa_number'] for v in user_villas]
        
        # Count invoices where user is directly assigned OR their villa is assigned
        query = {"payment_status": "pending"}
        if villa_numbers:
            query['$or'] = [
                {'user_email': user_email},
                {'villa_number': {'$in': villa_numbers}}
            ]
        else:
            query['user_email'] = user_email
        
        count = await db.invoices.count_documents(query)
        
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting pending invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to count invoices")


@api_router.get("/invoices/pending-approvals")
async def get_pending_invoice_approvals(request: Request):
    """Get all invoices with pending offline payment approvals - Admin/Manager only"""
    try:
        await require_manager_or_admin(request)
        
        pending = await db.invoices.find(
            {"offline_payment_status": "pending_approval"},
            {"_id": 0}
        ).sort("offline_submitted_at", 1).to_list(100)
        
        return pending
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pending approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending approvals")


@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request):
    """Get invoice details"""
    try:
        user = await require_auth(request)
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Check access
        is_manager = user.get('role') in ['admin', 'manager']
        is_owner = invoice['user_email'] == user['email']
        
        if not is_manager and not is_owner:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoice")


@api_router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, request: Request):
    """Download invoice as PDF"""
    try:
        user = await require_auth(request)
        user_email = user.get('email')
        user_role = user.get('role')
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Check access
        is_admin_or_manager = user_role in ['admin', 'manager']
        is_accountant = user_role == 'accountant'
        is_clubhouse_staff = user_role == 'clubhouse_staff'
        is_direct_owner = invoice.get('user_email') == user_email
        is_creator = invoice.get('created_by_email') == user_email
        
        # Check if user's email is in the villa's email list
        is_villa_member = False
        if invoice.get('villa_number'):
            villa = await db.villas.find_one(
                {"villa_number": invoice['villa_number']},
                {"_id": 0, "emails": 1}
            )
            if villa and villa.get('emails'):
                is_villa_member = any(
                    email.lower() == user_email.lower() 
                    for email in villa.get('emails', [])
                )
        
        # Access rules:
        # - Admin/Manager: Can access all
        # - Accountant: Can access maintenance invoices they created
        # - Clubhouse staff: Can access clubhouse invoices
        # - Direct owner: Can access invoices assigned to their email
        # - Villa member: Can access invoices for their villa
        has_access = (
            is_admin_or_manager or
            is_direct_owner or
            is_villa_member or
            (is_accountant and invoice.get('invoice_type') == INVOICE_TYPE_MAINTENANCE and is_creator) or
            (is_clubhouse_staff and invoice.get('invoice_type') == INVOICE_TYPE_CLUBHOUSE)
        )
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get bookings for audit log
        booking_ids = [item.get('booking_id') for item in invoice.get('line_items', []) if item.get('booking_id')]
        bookings = await db.bookings.find({"id": {"$in": list(set(booking_ids))}}, {"_id": 0}).to_list(100)
        
        pdf_bytes = await generate_invoice_pdf(invoice, bookings)
        
        filename = f"TROA_Invoice_{invoice['invoice_number']}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invoice PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


@api_router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate, request: Request):
    """Update invoice (override total amount) - Manager only, before payment"""
    try:
        user = await require_manager_or_admin(request)
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Cannot modify paid or cancelled invoice")
        
        # Apply new total amount as override
        update_fields = {"updated_at": datetime.utcnow()}
        
        if update.new_total_amount is not None:
            if update.new_total_amount < 0:
                raise HTTPException(status_code=400, detail="Total amount cannot be negative")
            
            previous_amount = invoice.get('total_amount', invoice.get('subtotal', 0))
            new_amount = update.new_total_amount
            
            # Calculate the adjustment from subtotal
            subtotal = invoice.get('subtotal', 0)
            adjustment = new_amount - subtotal
            
            update_fields['total_amount'] = new_amount
            update_fields['adjustment'] = adjustment
            update_fields['adjustment_reason'] = update.adjustment_reason or ''
            
            # Add audit log entry
            audit_entry = {
                "action": "amount_modified",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "by_email": user['email'],
                "by_name": user['name'],
                "details": f"Amount changed from ₹{previous_amount:.0f} to ₹{new_amount:.0f}. Reason: {update.adjustment_reason or 'No reason provided'}",
                "previous_amount": previous_amount,
                "new_amount": new_amount
            }
            
            # Append to existing audit log
            existing_audit_log = invoice.get('audit_log', [])
            existing_audit_log.append(audit_entry)
            update_fields['audit_log'] = existing_audit_log
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": update_fields}
        )
        
        logger.info(f"Invoice {invoice_id} updated by {user['email']}")
        
        return {"message": "Invoice updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to update invoice")


@api_router.post("/invoices/{invoice_id}/create-order")
async def create_invoice_payment_order(invoice_id: str, request: Request):
    """Create Razorpay order for invoice payment"""
    try:
        user = await require_auth(request)
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Check ownership
        if invoice['user_email'] != user['email']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Invoice is not pending payment")
        
        # Create Razorpay order
        import razorpay
        razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        if not razorpay_key_id or not razorpay_key_secret:
            raise HTTPException(status_code=500, detail="Payment gateway not configured")
        
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        order_data = {
            'amount': int(invoice['total_amount'] * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': invoice['invoice_number'],
            'notes': {
                'invoice_id': invoice['id'],
                'user_email': user['email']
            }
        }
        
        order = client.order.create(data=order_data)
        
        return {
            'order_id': order['id'],
            'amount': invoice['total_amount'],
            'currency': 'INR',
            'key_id': razorpay_key_id,
            'invoice_number': invoice['invoice_number']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@api_router.post("/invoices/{invoice_id}/verify-payment")
async def verify_invoice_payment(invoice_id: str, request: Request):
    """Verify Razorpay payment for invoice"""
    try:
        user = await require_auth(request)
        body = await request.json()
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Check ownership
        if invoice['user_email'] != user['email']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Verify payment signature
        import razorpay
        import hmac
        import hashlib
        
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        order_id = body.get('razorpay_order_id')
        payment_id = body.get('razorpay_payment_id')
        signature = body.get('razorpay_signature')
        
        if not all([order_id, payment_id, signature]):
            raise HTTPException(status_code=400, detail="Missing payment details")
        
        # Verify signature
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            razorpay_key_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Update invoice
        payment_date = datetime.utcnow()
        await db.invoices.update_one(
            {"id": invoice_id},
            {
                "$set": {
                    "payment_status": "paid",
                    "payment_method": "razorpay",
                    "payment_id": payment_id,
                    "payment_date": payment_date,
                    "updated_at": payment_date
                }
            }
        )
        
        logger.info(f"Invoice {invoice_id} paid via Razorpay: {payment_id}")
        
        # Send payment receipt email
        try:
            month_name = datetime(invoice['year'], invoice['month'], 1).strftime("%B %Y")
            await email_service.send_invoice_payment_receipt(
                recipient_email=user['email'],
                user_name=user['name'],
                invoice_number=invoice['invoice_number'],
                amenity_name=invoice['amenity_name'],
                month_year=month_name,
                total_amount=invoice['total_amount'],
                payment_id=payment_id,
                payment_date=payment_date.strftime("%d %b %Y %H:%M")
            )
        except Exception as email_error:
            logger.error(f"Failed to send payment receipt email: {email_error}")
        
        return {"message": "Payment verified successfully", "payment_id": payment_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")


@api_router.delete("/invoices/{invoice_id}")
async def cancel_invoice(invoice_id: str, request: Request):
    """Cancel invoice - Manager only, before payment"""
    try:
        user = await require_manager_or_admin(request)
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Cannot cancel paid invoice")
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"payment_status": "cancelled", "updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"Invoice {invoice_id} cancelled by {user['email']}")
        
        return {"message": "Invoice cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel invoice")


# ============ OFFLINE INVOICE PAYMENT ENDPOINTS ============

@api_router.post("/invoices/{invoice_id}/pay-offline")
async def submit_offline_invoice_payment(invoice_id: str, request: Request):
    """Submit offline payment for an invoice - requires admin approval"""
    try:
        user = await require_auth(request)
        body = await request.json()
        transaction_reference = body.get('transaction_reference', '')
        
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Check access - user must be the invoice owner or have access via villa
        user_villa_numbers = []
        if user.get('villa_number'):
            user_villa_numbers.append(user['villa_number'])
        user_villa = await db.villas.find_one(
            {"emails": user['email']},
            {"_id": 0, "villa_number": 1}
        )
        if user_villa:
            user_villa_numbers.append(user_villa['villa_number'])
        
        has_access = (
            invoice.get('user_email') == user['email'] or
            invoice.get('villa_number') in user_villa_numbers
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Invoice is not pending payment")
        
        if invoice.get('offline_payment_status') == 'pending_approval':
            raise HTTPException(status_code=400, detail="Offline payment already submitted and pending approval")
        
        # Create audit log entry
        audit_entry = {
            "action": "offline_payment_submitted",
            "timestamp": datetime.utcnow().isoformat(),
            "by_email": user['email'],
            "by_name": user.get('name', user['email']),
            "details": f"Offline payment submitted. Reference: {transaction_reference or 'N/A'}"
        }
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {
                "$set": {
                    "offline_payment_status": "pending_approval",
                    "offline_transaction_reference": transaction_reference,
                    "offline_submitted_by_email": user['email'],
                    "offline_submitted_by_name": user.get('name', user['email']),
                    "offline_submitted_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Offline payment submitted for invoice {invoice_id} by {user['email']}")
        
        # Notify admins
        try:
            await send_notification_to_admins(
                title="Invoice Offline Payment",
                body=f"Offline payment submitted for Invoice #{invoice.get('invoice_number', invoice_id)}",
                url="/admin"
            )
        except Exception as notif_error:
            logger.error(f"Failed to send admin notification: {notif_error}")
        
        return {
            "message": "Offline payment submitted successfully. Pending admin approval.",
            "invoice_id": invoice_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting offline payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit offline payment")


@api_router.post("/invoices/{invoice_id}/approve-offline")
async def approve_offline_invoice_payment(invoice_id: str, request: Request):
    """Approve offline payment for an invoice - Admin/Manager only"""
    try:
        admin = await require_manager_or_admin(request)
        body = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        approval_note = body.get('approval_note', '')
        
        invoice = await db.invoices.find_one({
            "id": invoice_id,
            "offline_payment_status": "pending_approval"
        }, {"_id": 0})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found or not pending approval")
        
        payment_date = datetime.utcnow()
        
        # Create audit log entry
        audit_entry = {
            "action": "offline_payment_approved",
            "timestamp": payment_date.isoformat(),
            "by_email": admin['email'],
            "by_name": admin.get('name', admin['email']),
            "details": f"Offline payment approved. {approval_note or ''}"
        }
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {
                "$set": {
                    "payment_status": "paid",
                    "payment_method": "offline",
                    "payment_date": payment_date,
                    "offline_payment_status": "approved",
                    "offline_approved_by_email": admin['email'],
                    "offline_approved_by_name": admin.get('name', admin['email']),
                    "offline_approval_note": approval_note,
                    "offline_approved_at": payment_date,
                    "updated_at": payment_date
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Offline payment approved for invoice {invoice_id} by {admin['email']}")
        
        # Send notification to user
        try:
            if invoice.get('user_email'):
                await send_notification_to_user(
                    user_email=invoice['user_email'],
                    title="Payment Approved! ✅",
                    body=f"Your offline payment for Invoice #{invoice.get('invoice_number', '')} has been approved.",
                    url="/my-invoices"
                )
        except Exception as notif_error:
            logger.error(f"Failed to send user notification: {notif_error}")
        
        # Send payment receipt email
        try:
            if invoice.get('user_email'):
                if invoice.get('invoice_type') == INVOICE_TYPE_MAINTENANCE:
                    # Maintenance invoice receipt
                    await email_service.send_invoice_payment_receipt(
                        recipient_email=invoice['user_email'],
                        user_name=invoice.get('user_name', ''),
                        invoice_number=invoice['invoice_number'],
                        amenity_name=f"Maintenance - Villa {invoice.get('villa_number', '')}",
                        month_year="N/A",
                        total_amount=invoice['total_amount'],
                        payment_id=f"OFFLINE-{invoice.get('offline_transaction_reference', 'N/A')}",
                        payment_date=payment_date.strftime("%d %b %Y %H:%M")
                    )
                else:
                    # Clubhouse invoice receipt
                    month_name = datetime(invoice['year'], invoice['month'], 1).strftime("%B %Y") if invoice.get('month') and invoice.get('year') else "N/A"
                    await email_service.send_invoice_payment_receipt(
                        recipient_email=invoice['user_email'],
                        user_name=invoice.get('user_name', ''),
                        invoice_number=invoice['invoice_number'],
                        amenity_name=invoice.get('amenity_name', ''),
                        month_year=month_name,
                        total_amount=invoice['total_amount'],
                        payment_id=f"OFFLINE-{invoice.get('offline_transaction_reference', 'N/A')}",
                        payment_date=payment_date.strftime("%d %b %Y %H:%M")
                    )
        except Exception as email_error:
            logger.error(f"Failed to send payment receipt email: {email_error}")
        
        return {
            "message": "Offline payment approved successfully",
            "invoice_id": invoice_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving offline payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve offline payment")


@api_router.post("/invoices/{invoice_id}/reject-offline")
async def reject_offline_invoice_payment(invoice_id: str, request: Request):
    """Reject offline payment for an invoice - Admin/Manager only"""
    try:
        admin = await require_manager_or_admin(request)
        body = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        rejection_reason = body.get('rejection_reason', '')
        
        invoice = await db.invoices.find_one({
            "id": invoice_id,
            "offline_payment_status": "pending_approval"
        }, {"_id": 0})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found or not pending approval")
        
        # Create audit log entry
        audit_entry = {
            "action": "offline_payment_rejected",
            "timestamp": datetime.utcnow().isoformat(),
            "by_email": admin['email'],
            "by_name": admin.get('name', admin['email']),
            "details": f"Offline payment rejected. Reason: {rejection_reason or 'No reason provided'}"
        }
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {
                "$set": {
                    "offline_payment_status": "rejected",
                    "offline_rejected_by_email": admin['email'],
                    "offline_rejected_by_name": admin.get('name', admin['email']),
                    "offline_rejection_reason": rejection_reason,
                    "offline_rejected_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "offline_transaction_reference": "",
                    "offline_submitted_by_email": "",
                    "offline_submitted_by_name": "",
                    "offline_submitted_at": ""
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Offline payment rejected for invoice {invoice_id} by {admin['email']}")
        
        # Send notification to user
        try:
            if invoice.get('user_email'):
                await send_notification_to_user(
                    user_email=invoice['user_email'],
                    title="Payment Rejected ❌",
                    body=f"Your offline payment for Invoice #{invoice.get('invoice_number', '')} was rejected. {rejection_reason}",
                    url="/my-invoices"
                )
        except Exception as notif_error:
            logger.error(f"Failed to send user notification: {notif_error}")
        
        return {
            "message": "Offline payment rejected",
            "invoice_id": invoice_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting offline payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject offline payment")


@api_router.get("/payment-qr-info")
async def get_payment_qr_info(request: Request):
    """Get QR code info for offline payments"""
    # This returns the UPI/bank details for offline payments
    # Using the same QR code as event offline payments
    return {
        "upi_id": "troa@upi",
        "bank_name": "HDFC Bank",
        "account_name": "The Retreat Owners Association",
        "account_number": "50100XXXXXXXXX",
        "ifsc_code": "HDFC0001234",
        "qr_image_url": "https://customer-assets.emergentagent.com/job_troaresidents/artifacts/kfeb4dc1_Screenshot%202025-12-13%20at%201.15.41%E2%80%AFPM.png",
        "instructions": [
            "Scan the QR code using any UPI app (GPay, PhonePe, Paytm, etc.)",
            "Enter the exact invoice amount",
            "Add the Invoice Number in the remarks/notes",
            "Complete the payment and note down the Transaction ID",
            "Submit the payment with the Transaction ID for approval"
        ]
    }


@api_router.post("/invoices/pay-multiple")
async def create_multi_invoice_payment_order(request: Request):
    """Create Razorpay order for multiple invoices - Pay oldest first"""
    try:
        user = await require_auth(request)
        user_email = user.get('email')
        
        body = await request.json()
        invoice_ids = body.get('invoice_ids', [])
        
        if not invoice_ids:
            raise HTTPException(status_code=400, detail="No invoices selected")
        
        # Get user's villas
        user_villas = await db.villas.find(
            {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
            {"_id": 0, "villa_number": 1}
        ).to_list(100)
        villa_numbers = [v['villa_number'] for v in user_villas]
        
        # Fetch and validate all invoices
        invoices = await db.invoices.find(
            {"id": {"$in": invoice_ids}},
            {"_id": 0}
        ).to_list(100)
        
        if len(invoices) != len(invoice_ids):
            raise HTTPException(status_code=400, detail="One or more invoices not found")
        
        total_amount = 0
        valid_invoices = []
        
        for invoice in invoices:
            # Verify user has access to this invoice
            has_access = (
                invoice.get('user_email') == user_email or
                invoice.get('villa_number') in villa_numbers
            )
            if not has_access:
                raise HTTPException(status_code=403, detail=f"You don't have access to invoice {invoice.get('invoice_number')}")
            
            if invoice['payment_status'] != 'pending':
                raise HTTPException(status_code=400, detail=f"Invoice {invoice.get('invoice_number')} is already {invoice['payment_status']}")
            
            total_amount += invoice.get('total_amount', 0)
            valid_invoices.append(invoice)
        
        if total_amount <= 0:
            raise HTTPException(status_code=400, detail="Total amount must be greater than 0")
        
        # Sort by created_at (oldest first)
        valid_invoices.sort(key=lambda x: x.get('created_at', datetime.min))
        
        # Create Razorpay order
        razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        if not razorpay_key_id or not razorpay_key_secret:
            raise HTTPException(status_code=500, detail="Payment gateway not configured")
        
        import razorpay
        razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        invoice_numbers = [inv.get('invoice_number') for inv in valid_invoices]
        
        order_data = {
            'amount': int(total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'notes': {
                'invoice_ids': ','.join(invoice_ids),
                'invoice_numbers': ','.join(invoice_numbers),
                'user_email': user_email,
                'type': 'multi_invoice_payment'
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        # Store payment order reference for each invoice
        for invoice in valid_invoices:
            await db.invoices.update_one(
                {"id": invoice['id']},
                {"$set": {
                    "razorpay_order_id": order['id'],
                    "updated_at": datetime.utcnow()
                }}
            )
        
        logger.info(f"Multi-invoice payment order created for user {user_email}, total: ₹{total_amount}")
        
        return {
            'order_id': order['id'],
            'amount': total_amount,
            'currency': 'INR',
            'key_id': razorpay_key_id,
            'invoice_ids': invoice_ids,
            'invoice_count': len(valid_invoices)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating multi-invoice payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@api_router.post("/invoices/verify-multi-payment")
async def verify_multi_invoice_payment(request: Request):
    """Verify Razorpay payment for multiple invoices - Mark oldest first as paid"""
    try:
        user = await require_auth(request)
        
        body = await request.json()
        razorpay_payment_id = body.get('razorpay_payment_id')
        razorpay_order_id = body.get('razorpay_order_id')
        razorpay_signature = body.get('razorpay_signature')
        invoice_ids = body.get('invoice_ids', [])
        
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, invoice_ids]):
            raise HTTPException(status_code=400, detail="Missing payment verification data")
        
        # Verify signature
        razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        
        import razorpay
        import hmac
        import hashlib
        
        razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        # Verify signature
        generated_signature = hmac.new(
            razorpay_key_secret.encode('utf-8'),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
        
        # Fetch invoices and sort by created_at (oldest first)
        invoices = await db.invoices.find(
            {"id": {"$in": invoice_ids}},
            {"_id": 0}
        ).to_list(100)
        
        invoices.sort(key=lambda x: x.get('created_at', datetime.min))
        
        # Mark each invoice as paid (oldest first)
        now = datetime.utcnow()
        paid_invoices = []
        
        for invoice in invoices:
            audit_entry = {
                'action': 'payment_received',
                'timestamp': now.isoformat(),
                'by_email': user['email'],
                'by_name': user.get('name', ''),
                'details': f"Online payment received via multi-invoice payment. Payment ID: {razorpay_payment_id}"
            }
            
            await db.invoices.update_one(
                {"id": invoice['id']},
                {
                    "$set": {
                        "payment_status": "paid",
                        "payment_method": "razorpay",
                        "payment_id": razorpay_payment_id,
                        "payment_date": now,
                        "updated_at": now
                    },
                    "$push": {"audit_log": audit_entry}
                }
            )
            paid_invoices.append(invoice.get('invoice_number'))
        
        logger.info(f"Multi-invoice payment verified for user {user['email']}: {', '.join(paid_invoices)}")
        
        return {
            'success': True,
            'message': f'Payment verified for {len(paid_invoices)} invoices',
            'paid_invoices': paid_invoices
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying multi-invoice payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")


# Include routers in the main app
app.include_router(api_router)
app.include_router(auth_router, prefix="/api")
app.include_router(instagram_router, prefix="/api")
# Use GridFS-based upload for production (persists across pod restarts)
app.include_router(gridfs_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(villas_router, prefix="/api")

# Push notifications router for PWA
from push_notifications import push_router
app.include_router(push_router, prefix="/api")

# Community Chat router
from community_chat import chat_router, init_mc_group
app.include_router(chat_router, prefix="/api")

# Bulk upload router
from bulk_upload import bulk_router
app.include_router(bulk_router, prefix="/api")

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
)

# CORS configuration - read from environment variable or use defaults
# Set CORS_ORIGINS env var as comma-separated list: "https://troa.in,http://localhost:3000"
default_cors_origins = [
    "https://troa.in",
    "http://troa.in",
    "https://emailbuzz.preview.emergentagent.com",
    "https://tenant-assist-6.emergent.host",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Parse CORS_ORIGINS from environment variable if set
cors_origins_env = os.environ.get('CORS_ORIGINS', '')
if cors_origins_env:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
else:
    CORS_ORIGINS = default_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Background task for invoice reminders
async def send_invoice_reminders():
    """Background task to send invoice payment reminders.
    
    Reminder schedule:
    - Before due date: Every 5 days
    - After due date (overdue): Every day
    """
    logger.info("Starting invoice reminder background task")
    
    while True:
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Find all pending invoices
            pending_invoices = await db.invoices.find(
                {"payment_status": "pending"},
                {"_id": 0}
            ).to_list(1000)
            
            for invoice in pending_invoices:
                try:
                    due_date = invoice.get('due_date')
                    if not due_date:
                        continue
                    
                    # Parse due date if it's a string
                    if isinstance(due_date, str):
                        due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    
                    due_date_normalized = due_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                    days_until_due = (due_date_normalized - today).days
                    is_overdue = days_until_due < 0
                    
                    # Determine if we should send a reminder
                    last_reminder = invoice.get('last_reminder_sent')
                    should_send = False
                    
                    if last_reminder:
                        if isinstance(last_reminder, str):
                            last_reminder = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                        last_reminder_normalized = last_reminder.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                        days_since_last_reminder = (today - last_reminder_normalized).days
                        
                        if is_overdue:
                            # Overdue: send reminder daily
                            should_send = days_since_last_reminder >= 1
                        else:
                            # Before due date: send reminder every 5 days
                            should_send = days_since_last_reminder >= 5
                    else:
                        # No reminder sent yet - send if invoice is at least 1 day old
                        created_at = invoice.get('created_at')
                        if created_at:
                            if isinstance(created_at, str):
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at_normalized = created_at.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                            days_since_creation = (today - created_at_normalized).days
                            
                            if is_overdue:
                                should_send = days_since_creation >= 1
                            else:
                                # Send first reminder 5 days after creation (initial email was sent on creation)
                                should_send = days_since_creation >= 5
                    
                    if should_send:
                        villa_number = invoice.get('villa_number', '')
                        invoice_number = invoice.get('invoice_number', '')
                        total_amount = invoice.get('total_amount', 0)
                        due_date_str = due_date.strftime("%d %b %Y") if due_date else ''
                        
                        # Get all emails to notify
                        emails_to_notify = []
                        
                        # Add user_email if present
                        if invoice.get('user_email'):
                            emails_to_notify.append(invoice['user_email'])
                        
                        # Add villa emails if villa_number is present
                        if villa_number:
                            villa = await db.villas.find_one(
                                {"villa_number": villa_number},
                                {"_id": 0, "emails": 1}
                            )
                            if villa and villa.get('emails'):
                                for email in villa['emails']:
                                    if email and email not in emails_to_notify:
                                        emails_to_notify.append(email)
                        
                        # Send reminders to all relevant emails
                        for email in emails_to_notify:
                            try:
                                # Get user name if available
                                user = await db.users.find_one({"email": email}, {"_id": 0, "name": 1})
                                user_name = user.get('name', '') if user else ''
                                
                                await email_service.send_invoice_reminder(
                                    recipient_email=email,
                                    user_name=user_name,
                                    invoice_number=invoice_number,
                                    villa_number=villa_number,
                                    total_amount=total_amount,
                                    due_date=due_date_str,
                                    days_until_due=days_until_due,
                                    is_overdue=is_overdue
                                )
                                logger.info(f"Sent invoice reminder for {invoice_number} to {email}")
                            except Exception as email_error:
                                logger.error(f"Failed to send reminder to {email}: {email_error}")
                        
                        # Update last_reminder_sent timestamp
                        await db.invoices.update_one(
                            {"id": invoice['id']},
                            {"$set": {"last_reminder_sent": datetime.utcnow()}}
                        )
                        
                except Exception as invoice_error:
                    logger.error(f"Error processing reminder for invoice {invoice.get('invoice_number', 'unknown')}: {invoice_error}")
            
        except Exception as e:
            logger.error(f"Error in invoice reminder task: {e}")
        
        # Run every hour (check hourly, but actual sending is based on day calculations)
        await asyncio.sleep(3600)  # 1 hour


@app.on_event("startup")
async def startup_event():
    # Initialize MC Group
    try:
        await init_mc_group()
    except Exception as e:
        logging.error(f"Error initializing MC Group: {e}")
    
    # Start invoice reminder background task
    asyncio.create_task(send_invoice_reminders())
