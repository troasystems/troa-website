"""Committee Members routes"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
from bson import ObjectId
import logging

from database import db
from models import CommitteeMember, CommitteeMemberCreate
from auth import require_admin

logger = logging.getLogger(__name__)

committee_router = APIRouter(prefix="/committee", tags=["Committee"])


@committee_router.get("", response_model=List[CommitteeMember])
async def get_committee_members():
    try:
        members = await db.committee_members.find().to_list(100)
        result = []
        for member in members:
            if 'id' not in member or not member['id']:
                member['id'] = str(member['_id'])
            member.pop('_id', None)
            result.append(CommitteeMember(**member))
        return result
    except Exception as e:
        logger.error(f"Error fetching committee members: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch committee members")


@committee_router.post("", response_model=CommitteeMember)
async def create_committee_member(member: CommitteeMemberCreate, request: Request):
    try:
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


@committee_router.patch("/{member_id}", response_model=CommitteeMember)
async def update_committee_member(member_id: str, member: CommitteeMemberCreate, request: Request):
    """Update committee member - admin only"""
    try:
        await require_admin(request)
        query = {"id": member_id}
        existing = await db.committee_members.find_one(query)
        if not existing:
            try:
                query = {"_id": ObjectId(member_id)}
                existing = await db.committee_members.find_one(query)
            except Exception:
                pass
        if not existing:
            raise HTTPException(status_code=404, detail="Committee member not found")
        update_data = member.dict()
        update_data['id'] = member_id
        result = await db.committee_members.find_one_and_update(
            query, {"$set": update_data}, return_document=True
        )
        result.pop('_id', None)
        return CommitteeMember(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating committee member: {e}")
        raise HTTPException(status_code=500, detail="Failed to update committee member")


@committee_router.delete("/{member_id}")
async def delete_committee_member(member_id: str, request: Request):
    """Delete committee member - admin only"""
    try:
        await require_admin(request)
        result = await db.committee_members.delete_one({"id": member_id})
        if result.deleted_count == 0:
            try:
                result = await db.committee_members.delete_one({"_id": ObjectId(member_id)})
            except Exception:
                pass
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Committee member not found")
        return {"message": "Committee member deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting committee member: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete committee member")
