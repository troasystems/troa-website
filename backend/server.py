from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from models import (
    CommitteeMember, CommitteeMemberCreate,
    Amenity, AmenityCreate,
    GalleryImage, GalleryImageCreate,
    MembershipApplication, MembershipApplicationCreate, MembershipApplicationUpdate
)
from auth import auth_router, require_admin
from instagram import instagram_router
from upload import upload_router
from payment import payment_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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
async def get_membership_applications(request: Request, admin = None):
    """Get membership applications - admin only for full access"""
    try:
        # Check if user is admin
        try:
            await require_admin(request)
        except Exception:
            # Non-admin users can't see applications
            raise HTTPException(status_code=403, detail="Admin access required")
        
        applications = await db.membership_applications.find().sort("created_at", -1).to_list(1000)
        return [MembershipApplication(**app) for app in applications]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching membership applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch membership applications")

@api_router.patch("/membership/{application_id}", response_model=MembershipApplication)
async def update_membership_application(application_id: str, update: MembershipApplicationUpdate, request: Request):
    """Update membership application status - admin only"""
    try:
        admin = await require_admin(request)
        
        from datetime import datetime
        result = await db.membership_applications.find_one_and_update(
            {"id": application_id},
            {
                "$set": {
                    "status": update.status,
                    "updated_at": datetime.utcnow(),
                    "reviewed_by": admin['email']
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
    """Delete membership application - admin only"""
    try:
        await require_admin(request)
        
        result = await db.membership_applications.delete_one({"id": application_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {"message": "Application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting membership application: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete membership application")

# Include routers in the main app
app.include_router(api_router)
app.include_router(auth_router, prefix="/api")
app.include_router(instagram_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(payment_router, prefix="/api")

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
