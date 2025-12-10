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
async def create_committee_member(member: CommitteeMemberCreate):
    try:
        member_dict = member.dict()
        member_obj = CommitteeMember(**member_dict)
        await db.committee_members.insert_one(member_obj.dict())
        return member_obj
    except Exception as e:
        logger.error(f"Error creating committee member: {e}")
        raise HTTPException(status_code=500, detail="Failed to create committee member")

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
async def create_amenity(amenity: AmenityCreate):
    try:
        amenity_dict = amenity.dict()
        amenity_obj = Amenity(**amenity_dict)
        await db.amenities.insert_one(amenity_obj.dict())
        return amenity_obj
    except Exception as e:
        logger.error(f"Error creating amenity: {e}")
        raise HTTPException(status_code=500, detail="Failed to create amenity")

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
async def get_membership_applications():
    try:
        applications = await db.membership_applications.find().sort("created_at", -1).to_list(1000)
        return [MembershipApplication(**app) for app in applications]
    except Exception as e:
        logger.error(f"Error fetching membership applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch membership applications")

# Include the router in the main app
app.include_router(api_router)

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
