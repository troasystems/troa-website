"""Gallery routes"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from database import db
from models import GalleryImage, GalleryImageCreate

logger = logging.getLogger(__name__)

gallery_router = APIRouter(prefix="/gallery", tags=["Gallery"])


@gallery_router.get("", response_model=List[GalleryImage])
async def get_gallery_images():
    try:
        images = await db.gallery_images.find().to_list(100)
        return [GalleryImage(**image) for image in images]
    except Exception as e:
        logger.error(f"Error fetching gallery images: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch gallery images")


@gallery_router.post("", response_model=GalleryImage)
async def create_gallery_image(image: GalleryImageCreate):
    try:
        image_dict = image.dict()
        image_obj = GalleryImage(**image_dict)
        await db.gallery_images.insert_one(image_obj.dict())
        return image_obj
    except Exception as e:
        logger.error(f"Error creating gallery image: {e}")
        raise HTTPException(status_code=500, detail="Failed to create gallery image")
