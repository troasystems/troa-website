from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from models import Villa, VillaCreate, VillaUpdate, PRIVILEGED_ROLES
from auth import require_admin, require_manager_or_admin, require_auth

load_dotenv()

logger = logging.getLogger(__name__)

villas_router = APIRouter(prefix="/villas")

# Database connection
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')


async def get_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    return db, client


async def check_email_in_villas(email: str) -> dict:
    """
    Check if an email exists in any villa's email list.
    Returns the villa if found, None otherwise.
    """
    db, client = await get_db()
    try:
        villa = await db.villas.find_one(
            {"emails": {"$elemMatch": {"$regex": f"^{email}$", "$options": "i"}}},
            {"_id": 0}
        )
        return villa
    finally:
        client.close()


async def get_villas_for_email(email: str) -> list:
    """
    Get all villas associated with an email address.
    """
    db, client = await get_db()
    try:
        villas = await db.villas.find(
            {"emails": {"$elemMatch": {"$regex": f"^{email}$", "$options": "i"}}},
            {"_id": 0}
        ).to_list(100)
        return villas
    finally:
        client.close()


# ============ VILLA CRUD ENDPOINTS ============

@villas_router.get("")
async def get_all_villas(request: Request):
    """Get all villas - admin, manager, and staff can view"""
    user = await require_auth(request)
    
    # Check if user has permission to view villas
    if user.get('role') not in ['admin', 'manager', 'clubhouse_staff', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db, client = await get_db()
    try:
        villas = await db.villas.find({}, {"_id": 0}).sort("villa_number", 1).to_list(1000)
        return villas
    finally:
        client.close()


@villas_router.get("/{villa_number}")
async def get_villa(villa_number: str, request: Request):
    """Get a single villa by villa number"""
    user = await require_auth(request)
    
    # Check if user has permission to view villas
    if user.get('role') not in ['admin', 'manager', 'clubhouse_staff', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db, client = await get_db()
    try:
        villa = await db.villas.find_one({"villa_number": villa_number}, {"_id": 0})
        if not villa:
            raise HTTPException(status_code=404, detail="Villa not found")
        return villa
    finally:
        client.close()


@villas_router.post("")
async def create_villa(villa_data: VillaCreate, request: Request):
    """Create a new villa - admin and manager only"""
    user = await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        # Check if villa already exists
        existing = await db.villas.find_one({"villa_number": villa_data.villa_number})
        if existing:
            raise HTTPException(status_code=400, detail="Villa with this number already exists")
        
        # Normalize emails to lowercase
        normalized_emails = [email.lower().strip() for email in villa_data.emails]
        
        villa = Villa(
            villa_number=villa_data.villa_number.strip(),
            square_feet=villa_data.square_feet,
            emails=normalized_emails
        )
        
        await db.villas.insert_one(villa.dict())
        logger.info(f"Villa created: {villa_data.villa_number} by {user['email']}")
        
        return villa.dict()
    finally:
        client.close()


@villas_router.patch("/{villa_number}")
async def update_villa(villa_number: str, villa_data: VillaUpdate, request: Request):
    """Update a villa - admin and manager only"""
    user = await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        # Check if villa exists
        existing = await db.villas.find_one({"villa_number": villa_number})
        if not existing:
            raise HTTPException(status_code=404, detail="Villa not found")
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if villa_data.square_feet is not None:
            update_data["square_feet"] = villa_data.square_feet
        
        if villa_data.emails is not None:
            # Normalize emails to lowercase
            update_data["emails"] = [email.lower().strip() for email in villa_data.emails]
        
        await db.villas.update_one(
            {"villa_number": villa_number},
            {"$set": update_data}
        )
        
        updated = await db.villas.find_one({"villa_number": villa_number}, {"_id": 0})
        logger.info(f"Villa updated: {villa_number} by {user['email']}")
        
        return updated
    finally:
        client.close()


@villas_router.delete("/{villa_number}")
async def delete_villa(villa_number: str, request: Request):
    """Delete a villa - admin only"""
    user = await require_admin(request)
    
    db, client = await get_db()
    try:
        result = await db.villas.delete_one({"villa_number": villa_number})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Villa not found")
        
        logger.info(f"Villa deleted: {villa_number} by {user['email']}")
        return {"message": "Villa deleted successfully"}
    finally:
        client.close()


@villas_router.post("/{villa_number}/emails")
async def add_email_to_villa(villa_number: str, request: Request):
    """Add an email to a villa - admin and manager only"""
    user = await require_manager_or_admin(request)
    
    body = await request.json()
    email = body.get("email", "").lower().strip()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    db, client = await get_db()
    try:
        villa = await db.villas.find_one({"villa_number": villa_number})
        if not villa:
            raise HTTPException(status_code=404, detail="Villa not found")
        
        # Check if email already exists in this villa
        if email in [e.lower() for e in villa.get("emails", [])]:
            raise HTTPException(status_code=400, detail="Email already associated with this villa")
        
        await db.villas.update_one(
            {"villa_number": villa_number},
            {
                "$push": {"emails": email},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        logger.info(f"Email {email} added to villa {villa_number} by {user['email']}")
        return {"message": "Email added successfully"}
    finally:
        client.close()


@villas_router.delete("/{villa_number}/emails/{email}")
async def remove_email_from_villa(villa_number: str, email: str, request: Request):
    """Remove an email from a villa - admin and manager only"""
    user = await require_manager_or_admin(request)
    
    email = email.lower().strip()
    
    db, client = await get_db()
    try:
        villa = await db.villas.find_one({"villa_number": villa_number})
        if not villa:
            raise HTTPException(status_code=404, detail="Villa not found")
        
        # Remove the email (case-insensitive)
        current_emails = villa.get("emails", [])
        new_emails = [e for e in current_emails if e.lower() != email]
        
        if len(new_emails) == len(current_emails):
            raise HTTPException(status_code=404, detail="Email not found in this villa")
        
        await db.villas.update_one(
            {"villa_number": villa_number},
            {
                "$set": {
                    "emails": new_emails,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Email {email} removed from villa {villa_number} by {user['email']}")
        return {"message": "Email removed successfully"}
    finally:
        client.close()


@villas_router.get("/lookup/by-email")
async def get_villa_by_email(email: str, request: Request):
    """Get villa(s) associated with an email - for internal use"""
    user = await require_auth(request)
    
    if user.get('role') not in ['admin', 'manager', 'clubhouse_staff', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    villas = await get_villas_for_email(email)
    return villas


# ============ MIGRATION ENDPOINT ============

@villas_router.post("/migrate-from-users")
async def migrate_villas_from_users(request: Request):
    """
    Migrate existing users' villa_number to create villa records.
    Admin only. One-time migration utility.
    """
    user = await require_admin(request)
    
    db, client = await get_db()
    try:
        # Get all users with villa_number set
        users = await db.users.find(
            {"villa_number": {"$exists": True, "$ne": ""}},
            {"_id": 0, "email": 1, "villa_number": 1}
        ).to_list(10000)
        
        created_villas = 0
        updated_villas = 0
        
        for user_doc in users:
            villa_number = user_doc.get("villa_number", "").strip()
            email = user_doc.get("email", "").lower().strip()
            
            if not villa_number or not email:
                continue
            
            # Check if villa exists
            existing = await db.villas.find_one({"villa_number": villa_number})
            
            if existing:
                # Add email to existing villa if not already present
                if email not in [e.lower() for e in existing.get("emails", [])]:
                    await db.villas.update_one(
                        {"villa_number": villa_number},
                        {
                            "$push": {"emails": email},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                    updated_villas += 1
            else:
                # Create new villa
                villa = Villa(
                    villa_number=villa_number,
                    square_feet=0.0,
                    emails=[email]
                )
                await db.villas.insert_one(villa.dict())
                created_villas += 1
        
        logger.info(f"Villa migration completed by {user['email']}: {created_villas} created, {updated_villas} updated")
        
        return {
            "message": "Migration completed",
            "villas_created": created_villas,
            "villas_updated": updated_villas,
            "total_users_processed": len(users)
        }
    finally:
        client.close()
