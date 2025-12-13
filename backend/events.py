from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from models import Event, EventCreate, EventRegistration, EventRegistrationCreate
from auth import require_admin, require_auth, require_manager_or_admin

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
    
    # Validate per_person_type and prices
    per_person_type = event_data.per_person_type or "uniform"
    if event_data.payment_type == "per_person" and per_person_type == "adult_child":
        if event_data.adult_price is None or event_data.child_price is None:
            raise HTTPException(status_code=400, detail="Adult and child prices are required for adult/child pricing")
    
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
            per_person_type=per_person_type,
            adult_price=event_data.adult_price,
            child_price=event_data.child_price,
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
        
        # Validate payment method
        payment_method = registration_data.payment_method
        if payment_method not in ["online", "offline"]:
            payment_method = "online"
        
        # Determine payment status based on method
        if payment_method == "offline":
            payment_status = "pending_approval"  # Offline payments need admin approval
        else:
            payment_status = "pending"  # Online payments start as pending until Razorpay confirms
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            event_name=event["name"],
            user_email=user["email"],
            user_name=user["name"],
            registrants=registration_data.registrants,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status=payment_status,
            admin_approved=False
        )
        
        await db.event_registrations.insert_one(registration.dict())
        logger.info(f"Event registration created: {user['email']} for {event['name']} (payment: {payment_method})")
        
        return registration.dict()
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/complete-payment")
async def complete_registration_payment(registration_id: str, payment_id: str, request: Request):
    """Mark registration payment as completed (for online Razorpay payments)"""
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
                "admin_approved": True,  # Online payments auto-approve
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
    """Get all registrations for an event (admin/manager only)"""
    await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        registrations = await db.event_registrations.find(
            {"event_id": event_id},
            {"_id": 0}
        ).to_list(500)
        
        return registrations
    finally:
        client.close()


# ============ ADMIN APPROVAL ENDPOINTS ============

@events_router.get("/admin/pending-approvals")
async def get_pending_approvals(request: Request):
    """Get all registrations pending admin approval (for offline payments and modifications)"""
    await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        # Get pending initial registrations AND pending modifications
        pending = await db.event_registrations.find(
            {
                "$or": [
                    # Initial offline registrations pending approval
                    {
                        "payment_method": "offline",
                        "payment_status": "pending_approval",
                        "status": "registered"
                    },
                    # Modifications pending approval
                    {
                        "modification_status": "pending_modification_approval",
                        "status": "registered"
                    }
                ]
            },
            {"_id": 0}
        ).sort("created_at", 1).to_list(100)
        
        # Enrich with event details
        for reg in pending:
            event = await db.events.find_one({"id": reg["event_id"]}, {"_id": 0})
            if event:
                reg["event"] = event
        
        return pending
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/approve")
async def approve_offline_payment(registration_id: str, request: Request, approval_note: str = ""):
    """Approve an offline payment registration (admin/manager only)"""
    admin = await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "payment_method": "offline",
            "payment_status": "pending_approval"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found or not pending approval")
        
        # Create audit log entry
        audit_entry = {
            "action": "initial_registration_approved",
            "timestamp": datetime.utcnow().isoformat(),
            "by_name": admin.get('name', admin['email']),
            "by_email": admin['email'],
            "details": f"Initial registration approved. Total: ₹{registration.get('total_amount', 0)}",
            "registrants_count": len(registration.get('registrants', []))
        }
        
        await db.event_registrations.update_one(
            {"id": registration_id},
            {
                "$set": {
                    "payment_status": "completed",
                    "admin_approved": True,
                    "approved_by_name": admin.get('name', admin['email']),
                    "approved_by_email": admin['email'],
                    "approval_note": approval_note or f"Approved by {admin.get('name', admin['email'])}",
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Offline payment approved: {registration_id} by {admin['email']}")
        
        return {"message": "Registration approved successfully"}
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/reject")
async def reject_offline_payment(registration_id: str, request: Request, rejection_reason: str = ""):
    """Reject an offline payment registration (admin/manager only)"""
    admin = await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "payment_method": "offline",
            "payment_status": "pending_approval"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found or not pending approval")
        
        # Create audit log entry
        audit_entry = {
            "action": "initial_registration_rejected",
            "timestamp": datetime.utcnow().isoformat(),
            "by_name": admin.get('name', admin['email']),
            "by_email": admin['email'],
            "details": rejection_reason or "No reason provided",
            "registrants_count": len(registration.get('registrants', []))
        }
        
        await db.event_registrations.update_one(
            {"id": registration_id},
            {
                "$set": {
                    "status": "withdrawn",
                    "rejected_by_name": admin.get('name', admin['email']),
                    "rejected_by_email": admin['email'],
                    "approval_note": rejection_reason or f"Rejected by {admin.get('name', admin['email'])}",
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Offline payment rejected: {registration_id} by {admin['email']}")
        
        return {"message": "Registration rejected"}
    finally:
        client.close()


# ============ PAYMENT ORDER ENDPOINT (for Razorpay) ============

@events_router.post("/{event_id}/create-payment-order")
async def create_event_payment_order(event_id: str, registration_id: str, request: Request):
    """Create a Razorpay order for event registration"""
    import razorpay
    import uuid as uuid_lib
    
    user = await require_auth(request)
    
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
    
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    
    db, client = await get_db()
    try:
        # Get registration details
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "user_email": user["email"],
            "event_id": event_id
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        if registration["payment_status"] == "completed":
            raise HTTPException(status_code=400, detail="Payment already completed")
        
        # Create Razorpay order
        amount_in_paise = int(registration["total_amount"] * 100)
        
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'event_{uuid_lib.uuid4().hex[:10]}',
            'notes': {
                'registration_id': registration_id,
                'event_id': event_id,
                'user_email': user["email"],
                'event_name': registration["event_name"]
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return {
            'order_id': order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': RAZORPAY_KEY_ID,
            'registration_id': registration_id
        }
        
    finally:
        client.close()


# ============ USER REGISTRATION STATUS & MODIFICATION ============

@events_router.get("/my/status")
async def get_my_registration_status(request: Request):
    """Get user's registration status for all events (to show 'already registered' on events page)"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        # Get all active registrations for the user
        registrations = await db.event_registrations.find(
            {"user_email": user["email"], "status": "registered"},
            {"_id": 0, "event_id": 1, "id": 1}
        ).to_list(100)
        
        # Return a dict mapping event_id to registration_id
        status = {reg["event_id"]: reg["id"] for reg in registrations}
        return status
    finally:
        client.close()


@events_router.patch("/registrations/{registration_id}/modify")
async def modify_registration(registration_id: str, request: Request):
    """Modify an existing registration (add/remove registrants)"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        # Get current registration
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "user_email": user["email"],
            "status": "registered"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        # Get event details
        event = await db.events.find_one({"id": registration["event_id"]}, {"_id": 0})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if event is in the past
        today = datetime.now().strftime('%Y-%m-%d')
        if event["event_date"] < today:
            raise HTTPException(status_code=400, detail="Cannot modify registrations for past events")
        
        # Parse request body
        body = await request.json()
        new_registrants = body.get("registrants", [])
        payment_method = body.get("payment_method", "online")
        
        if len(new_registrants) == 0:
            raise HTTPException(status_code=400, detail="At least one registrant is required")
        
        # Calculate new total and difference
        old_count = len(registration.get("registrants", []))
        new_count = len(new_registrants)
        
        if event["payment_type"] == "per_person":
            new_total = event["amount"] * new_count
            old_total = registration.get("total_amount", event["amount"] * old_count)
            difference = new_total - old_total
        else:  # per_villa - no additional payment needed
            new_total = event["amount"]
            difference = 0
        
        # If adding people (positive difference), handle payment
        if difference > 0:
            # Determine payment status for the modification
            if payment_method == "offline":
                modification_status = "pending_modification_approval"
            else:
                modification_status = "pending_modification_payment"
            
            # Store pending modification with audit log entry
            audit_entry = {
                "action": "modification_requested",
                "timestamp": datetime.utcnow().isoformat(),
                "by_name": user.get('name', user['email']),
                "by_email": user['email'],
                "details": f"Requested to add {new_count - old_count} person(s). Additional amount: ₹{difference}",
                "old_count": old_count,
                "new_count": new_count,
                "additional_amount": difference,
                "payment_method": payment_method
            }
            
            await db.event_registrations.update_one(
                {"id": registration_id},
                {
                    "$set": {
                        "pending_registrants": new_registrants,
                        "pending_total": new_total,
                        "additional_amount": difference,
                        "modification_payment_method": payment_method,
                        "modification_status": modification_status,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "audit_log": audit_entry
                    }
                }
            )
            
            return {
                "message": "Modification pending payment",
                "additional_amount": difference,
                "payment_method": payment_method,
                "registration_id": registration_id,
                "requires_payment": True
            }
        else:
            # Removing people or same count - update directly with audit log
            audit_entry = {
                "action": "modification_completed",
                "timestamp": datetime.utcnow().isoformat(),
                "by_name": user.get('name', user['email']),
                "by_email": user['email'],
                "details": f"Reduced registrants from {old_count} to {new_count}. Refund amount: ₹{abs(difference)}" if difference < 0 else f"Updated registrant details (no count change)",
                "old_count": old_count,
                "new_count": new_count,
                "refund_amount": abs(difference) if difference < 0 else 0
            }
            
            await db.event_registrations.update_one(
                {"id": registration_id},
                {
                    "$set": {
                        "registrants": new_registrants,
                        "total_amount": new_total,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "pending_registrants": "",
                        "pending_total": "",
                        "additional_amount": "",
                        "modification_payment_method": "",
                        "modification_status": ""
                    },
                    "$push": {
                        "audit_log": audit_entry
                    }
                }
            )
            
            return {
                "message": "Registration updated successfully",
                "requires_payment": False
            }
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/complete-modification-payment")
async def complete_modification_payment(registration_id: str, payment_id: str, request: Request):
    """Complete payment for registration modification (online Razorpay)"""
    user = await require_auth(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "user_email": user["email"],
            "modification_status": "pending_modification_payment"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="No pending modification found")
        
        # Create audit log entry
        old_count = len(registration.get("registrants", []))
        new_count = len(registration.get("pending_registrants", []))
        additional_amount = registration.get("additional_amount", 0)
        
        audit_entry = {
            "action": "modification_payment_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "by_name": user.get('name', user['email']),
            "by_email": user['email'],
            "details": f"Online payment completed. Added {new_count - old_count} person(s). Payment: ₹{additional_amount}",
            "old_count": old_count,
            "new_count": new_count,
            "payment_amount": additional_amount,
            "payment_id": payment_id,
            "payment_method": "online"
        }
        
        # Apply the pending modification
        await db.event_registrations.update_one(
            {"id": registration_id},
            {
                "$set": {
                    "registrants": registration["pending_registrants"],
                    "total_amount": registration["pending_total"],
                    "modification_payment_id": payment_id,
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "pending_registrants": "",
                    "pending_total": "",
                    "additional_amount": "",
                    "modification_payment_method": "",
                    "modification_status": ""
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        return {"message": "Modification payment completed successfully"}
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/create-modification-order")
async def create_modification_payment_order(registration_id: str, request: Request):
    """Create Razorpay order for registration modification"""
    import razorpay
    import uuid as uuid_lib
    
    user = await require_auth(request)
    
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
    
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "user_email": user["email"],
            "modification_status": "pending_modification_payment"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="No pending modification found")
        
        amount_in_paise = int(registration["additional_amount"] * 100)
        
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'mod_{uuid_lib.uuid4().hex[:10]}',
            'notes': {
                'registration_id': registration_id,
                'type': 'modification',
                'user_email': user["email"]
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return {
            'order_id': order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': RAZORPAY_KEY_ID,
            'registration_id': registration_id
        }
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/approve-modification")
async def approve_modification(registration_id: str, request: Request):
    """Approve offline payment for registration modification (admin/manager only)"""
    admin = await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "modification_status": "pending_modification_approval"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="No pending modification found")
        
        # Create audit log entry
        old_count = len(registration.get("registrants", []))
        new_count = len(registration.get("pending_registrants", []))
        additional_amount = registration.get("additional_amount", 0)
        
        audit_entry = {
            "action": "modification_approved",
            "timestamp": datetime.utcnow().isoformat(),
            "by_name": admin.get('name', admin['email']),
            "by_email": admin['email'],
            "details": f"Offline payment approved. Added {new_count - old_count} person(s). Amount: ₹{additional_amount}",
            "old_count": old_count,
            "new_count": new_count,
            "payment_amount": additional_amount,
            "payment_method": "offline"
        }
        
        # Apply the pending modification
        await db.event_registrations.update_one(
            {"id": registration_id},
            {
                "$set": {
                    "registrants": registration["pending_registrants"],
                    "total_amount": registration["pending_total"],
                    "approved_by_name": admin.get('name', admin['email']),
                    "approved_by_email": admin['email'],
                    "approval_note": f"Modification approved by {admin.get('name', admin['email'])}",
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "pending_registrants": "",
                    "pending_total": "",
                    "additional_amount": "",
                    "modification_payment_method": "",
                    "modification_status": ""
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Modification approved: {registration_id} by {admin['email']}")
        return {"message": "Modification approved successfully"}
    finally:
        client.close()


@events_router.post("/registrations/{registration_id}/reject-modification")
async def reject_modification(registration_id: str, request: Request, rejection_reason: str = ""):
    """Reject offline payment for registration modification (admin/manager only)"""
    admin = await require_manager_or_admin(request)
    
    db, client = await get_db()
    try:
        registration = await db.event_registrations.find_one({
            "id": registration_id,
            "modification_status": "pending_modification_approval"
        })
        
        if not registration:
            raise HTTPException(status_code=404, detail="No pending modification found")
        
        # Create audit log entry
        old_count = len(registration.get("registrants", []))
        new_count = len(registration.get("pending_registrants", []))
        additional_amount = registration.get("additional_amount", 0)
        
        audit_entry = {
            "action": "modification_rejected",
            "timestamp": datetime.utcnow().isoformat(),
            "by_name": admin.get('name', admin['email']),
            "by_email": admin['email'],
            "details": rejection_reason or f"Modification rejected. Attempted to add {new_count - old_count} person(s). Amount: ₹{additional_amount}",
            "old_count": old_count,
            "new_count": new_count,
            "rejected_amount": additional_amount
        }
        
        # Clear the pending modification without applying it
        await db.event_registrations.update_one(
            {"id": registration_id},
            {
                "$set": {
                    "updated_at": datetime.utcnow()
                },
                "$unset": {
                    "pending_registrants": "",
                    "pending_total": "",
                    "additional_amount": "",
                    "modification_payment_method": "",
                    "modification_status": ""
                },
                "$push": {
                    "audit_log": audit_entry
                }
            }
        )
        
        logger.info(f"Modification rejected: {registration_id} by {admin['email']}")
        return {"message": "Modification rejected successfully"}
    finally:
        client.close()

