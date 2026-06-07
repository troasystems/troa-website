"""User Management routes"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime
import logging

from database import db
from models import User, UserCreate, UserUpdate, VALID_ROLES
from auth import require_admin, SUPER_ADMIN_EMAIL

logger = logging.getLogger(__name__)

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("", response_model=List[User])
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


@users_router.post("", response_model=User)
async def add_user_to_whitelist(user_data: UserCreate, request: Request):
    """Add user to whitelist - admin only"""
    try:
        admin = await require_admin(request)
        existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        if user_data.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
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


@users_router.patch("/{user_id}", response_model=User)
async def update_user(user_id: str, update: UserUpdate, request: Request):
    """Update user details - admin only"""
    try:
        await require_admin(request)
        user_to_update = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")
        if user_to_update.get('email') == SUPER_ADMIN_EMAIL and update.role and update.role != 'admin':
            raise HTTPException(status_code=400, detail="Cannot modify the super admin's role")

        update_data = {"updated_at": datetime.utcnow()}
        if update.role is not None:
            if update.role not in VALID_ROLES:
                raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
            update_data["role"] = update.role
            update_data["is_admin"] = update.role == 'admin'
        if update.name is not None:
            update_data["name"] = update.name
        if update.villa_number is not None:
            update_data["villa_number"] = update.villa_number.strip()
        if update.picture is not None:
            update_data["picture"] = update.picture
        if update.new_password is not None:
            if len(update.new_password) < 6:
                raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
            import bcrypt
            password_hash = bcrypt.hashpw(update.new_password.encode('utf-8'), bcrypt.gensalt())
            update_data["password_hash"] = password_hash.decode('utf-8')
        if update.email_verified is not None:
            update_data["email_verified"] = update.email_verified
            if update.email_verified:
                update_data["verified_at"] = datetime.utcnow()
                update_data["verification_token"] = None
            else:
                update_data["verified_at"] = None

        result = await db.users.find_one_and_update(
            {"id": user_id}, {"$set": update_data}, return_document=True
        )
        result.pop('_id', None)
        result.pop('password_hash', None)
        return User(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@users_router.delete("/{user_id}")
async def delete_user(user_id: str, request: Request):
    """Delete user - admin only"""
    try:
        admin = await require_admin(request)
        user_to_delete = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")
        if user_to_delete.get('email') == admin.get('email'):
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
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
