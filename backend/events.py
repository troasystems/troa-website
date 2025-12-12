from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from models import Event, EventCreate, EventRegistration, EventRegistrationCreate
from auth import require_admin, require_auth

load_dotenv()

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events")

# Database connection
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')


async def get_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    return db, client


# ============ EVENT ENDPOINTS ============

@events_router.get("")
async def get_events(include_past: bool = False):
    """Get all events (optionally include past events)"""
    db, client = await get_db()
    try:
        query = {}
        if not include_past:
            today = datetime.now().strftime('%Y-%m-%d')
            query = {"event_date": {"$gte": today}, "is_active": True}
        
        events = await db.events.find(query, {"_id": 0}).sort("event_date", 1).to_list(100)
        return events
    finally:
        client.close()


@events_router.get("/{event_id}")
async def get_event(event_id: str):
    """Get a single event by ID"""
    db, client = await get_db()
    try:
        event = await db.events.find_one({"id": event_id}, {"_id": 0})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    finally:
        client.close()


@events_router.post("")
async def create_event(event_data: EventCreate, request: Request):
    """Create a new event (admin only)"""
    admin = await require_admin(request)
    
    # Validate event date is not in the past
    today = datetime.now().strftime('%Y-%m-%d')
    if event_data.event_date < today:
        raise HTTPException(status_code=400, detail="Cannot create events with dates in the past")
    
    # Validate payment type
    if event_data.payment_type not in ["per_person", "per_villa"]:
        raise HTTPException(status_code=400, detail="Payment type must be 'per_person' or 'per_villa'")
    
    db, client = await get_db()
    try:
        event = Event(
            name=event_data.name,
            description=event_data.description,
            image=event_data.image,
            event_date=event_data.event_date,
            event_time=event_data.event_time,
            amount=event_data.amount,
            payment_type=event_data.payment_type,
            preferences=event_data.preferences or [],
            max_registrations=event_data.max_registrations,
            created_by=admin['email']
        )
        
        await db.events.insert_one(event.dict())
        logger.info(f"Event created: {event.name} by {admin['email']}")
        return event.dict()
    finally:
        client.close()


@events_router.patch("/{event_id}")
async def update_event(event_id: str, event_data: dict, request: Request):
    """Update an event (admin only)"""
    await require_admin(request)
    
    db, client = await get_db()
    try:
        # Check if event exists
        existing = await db.events.find_one({"id": event_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Don't allow changing date to past
        if "event_date" in event_data:
            today = datetime.now().strftime('%Y-%m-%d')
            if event_data["event_date"] < today:
                raise HTTPException(status_code=400, detail="Cannot set event date to the past")
        
        event_data["updated_at"] = datetime.utcnow()
        await db.events.update_one({"id": event_id}, {"$set": event_data})
        
        updated = await db.events.find_one({"id": event_id}, {"_id": 0})
        return updated
    finally:
        client.close()


@events_router.delete("/{event_id}")
async def delete_event(event_id: str, request: Request):
    """Delete an event (admin only)"""
    await require_admin(request)
    
    db, client = await get_db()
    try:
        result = await db.events.delete_one({"id": event_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Also delete all registrations for this event
        await db.event_registrations.delete_many({"event_id": event_id})
        
        return {"message": "Event deleted successfully"}
    finally:
        client.close()


# ============ REGISTRATION ENDPOINTS ============

@events_router.post("/{event_id}/register")
async def register_for_event(event_id: str, registration_data: EventRegistrationCreate, request: Request):
    """Register for an event (authenticated users)"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        # Get event details
        event = await db.events.find_one({"id": event_id}, {"_id": 0})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if event is in the past
        today = datetime.now().strftime('%Y-%m-%d')
        if event["event_date"] < today:
            raise HTTPException(status_code=400, detail="Cannot register for past events")
        
        # Check if user already registered
        existing = await db.event_registrations.find_one({
            "event_id": event_id,
            "user_email": user["email"],
            "status": "registered"
        })
        if existing:
            raise HTTPException(status_code=400, detail="You are already registered for this event")
        
        # Calculate total amount
        num_registrants = len(registration_data.registrants)
        if num_registrants == 0:
            raise HTTPException(status_code=400, detail="At least one registrant is required")
        
        if event["payment_type"] == "per_person":
            total_amount = event["amount"] * num_registrants
        else:  # per_villa
            total_amount = event["amount"]
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            event_name=event["name"],
            user_email=user["email"],
            user_name=user["name"],
            registrants=registration_data.registrants,
            total_amount=total_amount,
            payment_status="pending"
        )
        
        await db.event_registrations.insert_one(registration.dict())
        logger.info(f"Event registration created: {user['email']} for {event['name']}")
        
        return registration.dict()
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/complete-payment")
async def complete_registration_payment(registration_id: str, payment_id: str, request: Request):
    """Mark registration payment as completed"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "user_email": user["email"]
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        await db.event_registrations.update_one(
            {"id": registration_id},
            {"$set": {
                "payment_status": "completed",
                "payment_id": payment_id,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {"message": "Payment completed successfully"}
    finally:
        client.close()


@events_router.get("/my/registrations")
async def get_my_registrations(request: Request):
    """Get all event registrations for the current user"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        registrations = await db.event_registrations.find(
            {"user_email": user["email"]},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        # Enrich with event details
        for reg in registrations:
            event = await db.events.find_one({"id": reg["event_id"]}, {"_id": 0})
            if event:
                reg["event"] = event
        
        return registrations
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/withdraw")
async def withdraw_from_event(registration_id: str, request: Request):
    """Withdraw from an event"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "user_email": user["email"],
            "status": "registered"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found or already withdrawn")
        
        await db.event_registrations.update_one(
            {"id": registration_id},
            {"$set": {
                "status": "withdrawn",
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {
            "message": "Successfully withdrawn from event",
            "refund_instructions": "For refund requests, please email: troa.systems@gmail.com, troa.treasurer@gmail.com, troa.secretary@gmail.com, and president.troa@gmail.com"
        }
    finally:
        client.close()


@events_router.get("/{event_id}/registrations")
async def get_event_registrations(event_id: str, request: Request):
    """Get all registrations for an event (admin only)"""
    await require_admin(request)
    
    db, client = await get_db()
    try:
        registrations = await db.event_registrations.find(
            {"event_id": event_id, "status": "registered"},
            {"_id": 0}
        ).to_list(500)
        
        return registrations
    finally:
        client.close()
