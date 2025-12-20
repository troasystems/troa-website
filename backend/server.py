from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from models import (
    CommitteeMember, CommitteeMemberCreate,
    Amenity, AmenityCreate,
    GalleryImage, GalleryImageCreate,
    MembershipApplication, MembershipApplicationCreate, MembershipApplicationUpdate,
    User, UserCreate, UserUpdate,
    Feedback, FeedbackCreate,
    AmenityBooking, AmenityBookingCreate
)
from auth import auth_router, require_admin, require_manager_or_admin, require_auth
from basic_auth import basic_auth_middleware
from instagram import instagram_router
from gridfs_upload import gridfs_router  # GridFS-based upload for production
from payment import payment_router
from chatbot import chatbot_router
from events import events_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
# redirect_slashes=False prevents 307 redirects when trailing slash is missing
app = FastAPI(redirect_slashes=False)

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
        members = await db.committee_members.find({}, {"_id": 0}).to_list(100)
        return [CommitteeMember(**member) for member in members]
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
        
        result = await db.committee_members.find_one_and_update(
            {"id": member_id},
            {"$set": member.dict()},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Committee member not found")
        
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
        
        result = await db.committee_members.delete_one({"id": member_id})
        
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
        return [Amenity(**amenity) for amenity in amenities]
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
        
        result = await db.amenities.find_one_and_update(
            {"id": amenity_id},
            {"$set": amenity.dict()},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Amenity not found")
        
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
        
        result = await db.amenities.delete_one({"id": amenity_id})
        
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
        if user_data.role not in ['admin', 'manager', 'user']:
            raise HTTPException(status_code=400, detail="Invalid role. Must be: admin, manager, or user")
        
        # Create user with the specified role
        user_obj = User(
            email=user_data.email,
            name=user_data.name or "",
            picture=user_data.picture or "",
            provider="whitelist",
            role=user_data.role,
            is_admin=user_data.role == 'admin'
        )
        
        await db.users.insert_one(user_obj.dict())
        logger.info(f"User added to whitelist by {admin['email']}: {user_data.email} with role {user_data.role}")
        return user_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding user to whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add user")

@api_router.patch("/users/{user_id}", response_model=User)
async def update_user_role(user_id: str, update: UserUpdate, request: Request):
    """Update user role - admin only"""
    try:
        admin = await require_admin(request)
        
        # Validate role
        if update.role not in ['admin', 'manager', 'user']:
            raise HTTPException(status_code=400, detail="Invalid role. Must be: admin, manager, or user")
        
        # Check if trying to modify super admin
        from auth import SUPER_ADMIN_EMAIL
        user_to_update = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user_to_update and user_to_update.get('email') == SUPER_ADMIN_EMAIL:
            raise HTTPException(status_code=400, detail="Cannot modify the super admin's role")
        
        from datetime import datetime
        result = await db.users.find_one_and_update(
            {"id": user_id},
            {
                "$set": {
                    "role": update.role,
                    "is_admin": update.role == 'admin',
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove _id for serialization
        result.pop('_id', None)
        return User(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user role")

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
@api_router.post("/bookings", response_model=AmenityBooking)
async def create_booking(booking: AmenityBookingCreate, request: Request):
    """Create amenity booking - authenticated users only"""
    try:
        user = await require_auth(request)
        
        # Validate duration
        if booking.duration_minutes not in [30, 60]:
            raise HTTPException(status_code=400, detail="Duration must be 30 or 60 minutes")
        
        # Validate additional guests count
        if len(booking.additional_guests) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 additional guests allowed")
        
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
        
        # Create booking
        booking_obj = AmenityBooking(
            amenity_id=booking.amenity_id,
            amenity_name=booking.amenity_name,
            booked_by_email=user['email'],
            booked_by_name=user['name'],
            booking_date=booking.booking_date,
            start_time=booking.start_time,
            end_time=end_time,
            duration_minutes=booking.duration_minutes,
            additional_guests=booking.additional_guests or []
        )
        
        await db.bookings.insert_one(booking_obj.dict())
        logger.info(f"Booking created by {user['email']} for {booking.amenity_name}")
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
        
        # Update status to cancelled
        await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel booking")

# Include routers in the main app
app.include_router(api_router)
app.include_router(auth_router, prefix="/api")
app.include_router(instagram_router, prefix="/api")
# Use GridFS-based upload for production (persists across pod restarts)
app.include_router(gridfs_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(events_router, prefix="/api")

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
    "https://troa-residence.preview.emergentagent.com",
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
