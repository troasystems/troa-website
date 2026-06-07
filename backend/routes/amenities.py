"""Amenities routes"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
from bson import ObjectId
import logging

from database import db
from models import Amenity, AmenityCreate
from auth import require_admin

logger = logging.getLogger(__name__)

amenities_router = APIRouter(prefix="/amenities", tags=["Amenities"])


@amenities_router.get("", response_model=List[Amenity])
async def get_amenities():
    try:
        amenities = await db.amenities.find().to_list(100)
        result = []
        for amenity in amenities:
            if 'id' not in amenity or not amenity['id']:
                amenity['id'] = str(amenity['_id'])
            amenity.pop('_id', None)
            result.append(Amenity(**amenity))
        return result
    except Exception as e:
        logger.error(f"Error fetching amenities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch amenities")


@amenities_router.post("", response_model=Amenity)
async def create_amenity(amenity: AmenityCreate, request: Request):
    try:
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


@amenities_router.patch("/{amenity_id}", response_model=Amenity)
async def update_amenity(amenity_id: str, amenity: AmenityCreate, request: Request):
    """Update amenity - admin only"""
    try:
        await require_admin(request)
        query = {"id": amenity_id}
        existing = await db.amenities.find_one(query)
        if not existing:
            try:
                query = {"_id": ObjectId(amenity_id)}
                existing = await db.amenities.find_one(query)
            except Exception:
                pass
        if not existing:
            raise HTTPException(status_code=404, detail="Amenity not found")
        update_data = amenity.dict()
        update_data['id'] = amenity_id
        result = await db.amenities.find_one_and_update(
            query, {"$set": update_data}, return_document=True
        )
        result.pop('_id', None)
        return Amenity(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating amenity: {e}")
        raise HTTPException(status_code=500, detail="Failed to update amenity")


@amenities_router.delete("/{amenity_id}")
async def delete_amenity(amenity_id: str, request: Request):
    """Delete amenity - admin only"""
    try:
        await require_admin(request)
        result = await db.amenities.delete_one({"id": amenity_id})
        if result.deleted_count == 0:
            try:
                result = await db.amenities.delete_one({"_id": ObjectId(amenity_id)})
            except Exception:
                pass
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Amenity not found")
        return {"message": "Amenity deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting amenity: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete amenity")
