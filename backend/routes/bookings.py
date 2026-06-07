"""Amenity Bookings + Clubhouse Staff routes + PDF Reports"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date as date_type
import logging

from database import db
from models import AmenityBooking, AmenityBookingCreate, BookingAvailedUpdate, BookingAmendment
from auth import require_auth, require_clubhouse_staff
from email_service import email_service, get_admin_manager_emails
from push_notifications import send_notification_to_user, send_notification_to_admins
from pdf_service import generate_booking_report_pdf

logger = logging.getLogger(__name__)

bookings_router = APIRouter(tags=["Bookings"])

GUEST_CHARGE = 50.0  # per session for external guests and coaches

# Peak hours: 6 PM (18:00) to 8 PM (20:00) — no 30-min slots allowed
PEAK_START_HOUR = 18
PEAK_END_HOUR = 20


def _validate_booking_date(booking_date: str):
    """Validate booking date is today or tomorrow only"""
    today = date_type.today()
    tomorrow = today + timedelta(days=1)
    try:
        bd = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    if bd < today:
        raise HTTPException(status_code=400, detail="Cannot book in the past")
    if bd > tomorrow:
        raise HTTPException(status_code=400, detail="Bookings can only be made for today or tomorrow")


def _validate_peak_time(start_time: str, duration_minutes: int):
    """Peak hours 18:00-20:00: only 60-min slots allowed"""
    h, m = map(int, start_time.split(':'))
    slot_start = h * 60 + m
    slot_end = slot_start + duration_minutes
    peak_start = PEAK_START_HOUR * 60
    peak_end = PEAK_END_HOUR * 60
    # If the slot overlaps with peak window at all, enforce 60 min
    if slot_start < peak_end and slot_end > peak_start and duration_minutes != 60:
        raise HTTPException(
            status_code=400,
            detail="Peak hours (6 PM – 8 PM): only 1-hour bookings are allowed"
        )


async def _check_consecutive_day_slot(user_email: str, amenity_id: str, booking_date: str, start_time: str, duration_minutes: int, exclude_booking_id: str = None):
    """Same person cannot book the same slot 2 days in a row"""
    bd = datetime.strptime(booking_date, "%Y-%m-%d").date()
    prev_day = (bd - timedelta(days=1)).strftime("%Y-%m-%d")
    next_day = (bd + timedelta(days=1)).strftime("%Y-%m-%d")

    query = {
        "booked_by_email": user_email,
        "amenity_id": amenity_id,
        "status": "confirmed",
        "booking_date": {"$in": [prev_day, next_day]},
        "start_time": start_time,
        "duration_minutes": duration_minutes,
    }
    if exclude_booking_id:
        query["id"] = {"$ne": exclude_booking_id}

    conflict = await db.bookings.find_one(query, {"_id": 0})
    if conflict:
        raise HTTPException(
            status_code=400,
            detail=f"You already have this same slot booked on {conflict['booking_date']}. The same slot cannot be booked on consecutive days."
        )


def _process_guests(raw_guests, legacy_guests_list=None):
    """Process and validate guest list, return (processed_guests, total_charges)"""
    processed = []
    total_charges = 0.0
    for guest in (raw_guests or []):
        guest_type = guest.get('guest_type', 'external')
        guest_name = guest.get('name', '').strip()
        villa_number = guest.get('villa_number', '').strip() if guest.get('villa_number') else None
        if not guest_name:
            continue
        if guest_type == 'resident' and not villa_number:
            raise HTTPException(status_code=400, detail=f"Villa number is required for resident guest: {guest_name}")
        charge = GUEST_CHARGE if guest_type in ['external', 'coach'] else 0.0
        if charge:
            total_charges += charge
        processed.append({
            'name': guest_name, 'guest_type': guest_type,
            'villa_number': villa_number, 'charge': charge
        })
    if len(processed) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 additional guests allowed")

    if not processed and legacy_guests_list:
        for name in legacy_guests_list[:3]:
            if name.strip():
                processed.append({
                    'name': name.strip(), 'guest_type': 'external',
                    'villa_number': None, 'charge': GUEST_CHARGE
                })
                total_charges += GUEST_CHARGE
    return processed, total_charges


# ============ BOOKING ROUTES ============

@bookings_router.post("/bookings", response_model=AmenityBooking)
async def create_booking(booking: AmenityBookingCreate, request: Request):
    """Create amenity booking - authenticated users only"""
    try:
        user = await require_auth(request)
        if booking.duration_minutes not in [30, 60]:
            raise HTTPException(status_code=400, detail="Duration must be 30 or 60 minutes")

        # Feature 1: only today/tomorrow
        _validate_booking_date(booking.booking_date)

        # Feature 4: peak time restriction
        _validate_peak_time(booking.start_time, booking.duration_minutes)

        processed_guests, total_guest_charges = _process_guests(
            booking.guests, booking.additional_guests if not booking.guests else None
        )

        start_dt = datetime.strptime(booking.start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=booking.duration_minutes)
        end_time = end_dt.strftime("%H:%M")

        # Overlap check
        existing_bookings = await db.bookings.find({
            "amenity_id": booking.amenity_id,
            "booking_date": booking.booking_date,
            "status": "confirmed"
        }, {"_id": 0}).to_list(100)
        for existing in existing_bookings:
            existing_start = datetime.strptime(existing['start_time'], "%H:%M")
            existing_end = datetime.strptime(existing['end_time'], "%H:%M")
            if start_dt < existing_end and end_dt > existing_start:
                raise HTTPException(
                    status_code=409,
                    detail=f"Time slot conflicts with existing booking ({existing['start_time']}-{existing['end_time']})"
                )

        # Feature 2: no consecutive day same slot
        await _check_consecutive_day_slot(user['email'], booking.amenity_id, booking.booking_date, booking.start_time, booking.duration_minutes)

        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(), 'action': 'created',
            'by_email': user['email'], 'by_name': user['name'],
            'by_role': user.get('role', 'user'),
            'details': f"Booking created with {len(processed_guests)} guest(s)",
            'changes': None
        }
        booking_obj = AmenityBooking(
            amenity_id=booking.amenity_id, amenity_name=booking.amenity_name,
            booked_by_email=user['email'], booked_by_name=user['name'],
            booked_by_villa=user.get('villa_number'),
            booking_date=booking.booking_date, start_time=booking.start_time,
            end_time=end_time, duration_minutes=booking.duration_minutes,
            guests=processed_guests,
            additional_guests=[g['name'] for g in processed_guests],
            total_guest_charges=total_guest_charges, audit_log=[audit_entry]
        )
        await db.bookings.insert_one(booking_obj.dict())
        logger.info(f"Booking created by {user['email']} for {booking.amenity_name} with {len(processed_guests)} guests, charges: {total_guest_charges}")

        try:
            await email_service.send_booking_confirmation(
                recipient_email=user['email'], user_name=user['name'],
                amenity_name=booking.amenity_name, booking_date=booking.booking_date,
                start_time=booking.start_time, end_time=end_time,
                booking_id=booking_obj.id, additional_guests=booking.additional_guests
            )
        except Exception as email_error:
            logger.error(f"Failed to send booking confirmation email: {email_error}")
        try:
            admin_emails = await get_admin_manager_emails()
            await email_service.send_booking_notification_to_admins(
                action='created', user_name=user['name'], user_email=user['email'],
                amenity_name=booking.amenity_name, booking_date=booking.booking_date,
                start_time=booking.start_time, end_time=end_time, admin_emails=admin_emails
            )
        except Exception as email_error:
            logger.error(f"Failed to send admin booking notification: {email_error}")
        try:
            await send_notification_to_user(
                user_email=user['email'], title="Booking Confirmed",
                body=f"Your {booking.amenity_name} booking on {booking.booking_date} at {booking.start_time} is confirmed!",
                url="/my-bookings"
            )
        except Exception as push_error:
            logger.error(f"Failed to send booking push notification: {push_error}")
        try:
            await send_notification_to_admins(
                title="New Booking",
                body=f"{user['name']} booked {booking.amenity_name} on {booking.booking_date}",
                url="/admin"
            )
        except Exception as push_error:
            logger.error(f"Failed to send admin push notification: {push_error}")

        return booking_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to create booking")


@bookings_router.get("/bookings", response_model=List[AmenityBooking])
async def get_bookings(request: Request, amenity_id: Optional[str] = None, date: Optional[str] = None):
    """Get bookings - authenticated users can see all bookings"""
    try:
        await require_auth(request)
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


@bookings_router.get("/bookings/my", response_model=List[AmenityBooking])
async def get_my_bookings(request: Request):
    """Get current user's bookings"""
    try:
        user = await require_auth(request)
        bookings = await db.bookings.find({
            "booked_by_email": user['email'], "status": "confirmed"
        }, {"_id": 0}).sort("booking_date", -1).to_list(1000)
        return [AmenityBooking(**booking) for booking in bookings]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user bookings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")


@bookings_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, request: Request):
    """Cancel booking - only booking owner can cancel"""
    try:
        user = await require_auth(request)
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking['booked_by_email'] != user['email']:
            raise HTTPException(status_code=403, detail="You can only cancel your own bookings")

        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(), 'action': 'cancelled',
            'by_email': user['email'], 'by_name': user['name'],
            'by_role': user.get('role', 'user'),
            'details': 'Booking cancelled by user',
            'changes': {'status': {'from': 'confirmed', 'to': 'cancelled'}}
        }
        await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()},
             "$push": {"audit_log": audit_entry}}
        )

        try:
            await email_service.send_booking_cancellation(
                recipient_email=user['email'], user_name=user['name'],
                amenity_name=booking['amenity_name'], booking_date=booking['booking_date'],
                start_time=booking['start_time'], end_time=booking['end_time']
            )
        except Exception as email_error:
            logger.error(f"Failed to send cancellation email: {email_error}")
        try:
            admin_emails = await get_admin_manager_emails()
            await email_service.send_booking_notification_to_admins(
                action='cancelled', user_name=user['name'], user_email=user['email'],
                amenity_name=booking['amenity_name'], booking_date=booking['booking_date'],
                start_time=booking['start_time'], end_time=booking['end_time'],
                admin_emails=admin_emails
            )
        except Exception as email_error:
            logger.error(f"Failed to send admin cancellation notification: {email_error}")
        try:
            await send_notification_to_admins(
                title="Booking Cancelled",
                body=f"{user['name']} cancelled {booking['amenity_name']} booking on {booking['booking_date']}",
                url="/admin"
            )
        except Exception as push_error:
            logger.error(f"Failed to send admin push notification: {push_error}")

        return {"message": "Booking cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel booking")


# ============ EDIT BOOKING ============

class BookingEditRequest(BaseModel):
    booking_date: str
    start_time: str
    duration_minutes: int
    guests: Optional[list] = []

@bookings_router.put("/bookings/{booking_id}")
async def edit_booking(booking_id: str, edit_data: BookingEditRequest, request: Request):
    """Edit an existing booking — only the owner, before the booking time"""
    try:
        user = await require_auth(request)
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking['booked_by_email'] != user['email']:
            raise HTTPException(status_code=403, detail="You can only edit your own bookings")

        # Can't edit past bookings
        now = datetime.now()
        bdate = datetime.strptime(booking['booking_date'], "%Y-%m-%d")
        btime = datetime.strptime(booking['start_time'], "%H:%M")
        booking_dt = bdate.replace(hour=btime.hour, minute=btime.minute)
        if booking_dt < now:
            raise HTTPException(status_code=400, detail="Cannot edit a past booking")

        if edit_data.duration_minutes not in [30, 60]:
            raise HTTPException(status_code=400, detail="Duration must be 30 or 60 minutes")

        # Feature 1: only today/tomorrow
        _validate_booking_date(edit_data.booking_date)
        # Feature 4: peak time restriction
        _validate_peak_time(edit_data.start_time, edit_data.duration_minutes)

        start_dt = datetime.strptime(edit_data.start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=edit_data.duration_minutes)
        end_time = end_dt.strftime("%H:%M")

        # Overlap check (excluding this booking)
        existing_bookings = await db.bookings.find({
            "amenity_id": booking['amenity_id'],
            "booking_date": edit_data.booking_date,
            "status": "confirmed",
            "id": {"$ne": booking_id}
        }, {"_id": 0}).to_list(100)
        for existing in existing_bookings:
            es = datetime.strptime(existing['start_time'], "%H:%M")
            ee = datetime.strptime(existing['end_time'], "%H:%M")
            if start_dt < ee and end_dt > es:
                raise HTTPException(
                    status_code=409,
                    detail=f"Time slot conflicts with existing booking ({existing['start_time']}-{existing['end_time']})"
                )

        # Feature 2: consecutive day check (excluding self)
        await _check_consecutive_day_slot(
            user['email'], booking['amenity_id'],
            edit_data.booking_date, edit_data.start_time, edit_data.duration_minutes,
            exclude_booking_id=booking_id
        )

        processed_guests, total_guest_charges = _process_guests(edit_data.guests)

        changes = {}
        if booking['booking_date'] != edit_data.booking_date:
            changes['booking_date'] = {'from': booking['booking_date'], 'to': edit_data.booking_date}
        if booking['start_time'] != edit_data.start_time:
            changes['start_time'] = {'from': booking['start_time'], 'to': edit_data.start_time}
        if booking['duration_minutes'] != edit_data.duration_minutes:
            changes['duration_minutes'] = {'from': booking['duration_minutes'], 'to': edit_data.duration_minutes}

        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(), 'action': 'edited',
            'by_email': user['email'], 'by_name': user['name'],
            'by_role': user.get('role', 'user'),
            'details': f"Booking edited: {edit_data.booking_date} {edit_data.start_time}-{end_time}",
            'changes': changes if changes else None
        }

        await db.bookings.update_one(
            {"id": booking_id},
            {
                "$set": {
                    "booking_date": edit_data.booking_date,
                    "start_time": edit_data.start_time,
                    "end_time": end_time,
                    "duration_minutes": edit_data.duration_minutes,
                    "guests": processed_guests,
                    "additional_guests": [g['name'] for g in processed_guests],
                    "total_guest_charges": total_guest_charges,
                    "updated_at": datetime.utcnow(),
                },
                "$push": {"audit_log": audit_entry}
            }
        )
        logger.info(f"Booking {booking_id} edited by {user['email']}")
        updated = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        return AmenityBooking(**updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to edit booking")


# ============ CLUBHOUSE STAFF ROUTES ============

@bookings_router.get("/staff/bookings/today")
async def get_todays_bookings_for_staff(request: Request):
    """Get today's bookings for clubhouse staff"""
    try:
        await require_clubhouse_staff(request)
        today = datetime.now().strftime("%Y-%m-%d")
        bookings = await db.bookings.find({
            "booking_date": today, "status": "confirmed"
        }, {"_id": 0}).sort("start_time", 1).to_list(100)
        for booking in bookings:
            amenity = await db.amenities.find_one({"id": booking['amenity_id']}, {"_id": 0, "name": 1, "image": 1})
            if amenity:
                booking['amenity_image'] = amenity.get('image')
        return bookings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching today's bookings for staff: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")


@bookings_router.get("/staff/bookings/date/{date}")
async def get_bookings_by_date_for_staff(date: str, request: Request):
    """Get bookings for a specific date for clubhouse staff"""
    try:
        await require_clubhouse_staff(request)
        bookings = await db.bookings.find({
            "booking_date": date, "status": "confirmed"
        }, {"_id": 0}).sort("start_time", 1).to_list(100)
        for booking in bookings:
            amenity = await db.amenities.find_one({"id": booking['amenity_id']}, {"_id": 0, "name": 1, "image": 1})
            if amenity:
                booking['amenity_image'] = amenity.get('image')
        return bookings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bookings by date for staff: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bookings")


@bookings_router.put("/staff/bookings/{booking_id}/availed")
async def mark_booking_availed(booking_id: str, update: BookingAvailedUpdate, request: Request):
    """Mark a booking as availed or not availed - clubhouse staff only"""
    try:
        user = await require_clubhouse_staff(request)
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if update.availed_status not in ['availed', 'not_availed']:
            raise HTTPException(status_code=400, detail="Invalid availed status")
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(), 'action': update.availed_status,
            'by_email': user['email'], 'by_name': user['name'],
            'by_role': user.get('role', 'clubhouse_staff'),
            'details': f"Marked as {update.availed_status}" + (f" - {update.notes}" if update.notes else ""),
            'changes': {'availed_status': {'from': booking.get('availed_status', 'pending'), 'to': update.availed_status}}
        }
        await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {
                "availed_status": update.availed_status,
                "availed_at": datetime.utcnow(), "availed_by_email": user['email'],
                "availed_by_name": user['name'], "updated_at": datetime.utcnow()
            }, "$push": {"audit_log": audit_entry}}
        )
        logger.info(f"Booking {booking_id} marked as {update.availed_status} by {user['email']}")
        return {"message": f"Booking marked as {update.availed_status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking booking availed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update booking")


@bookings_router.put("/staff/bookings/{booking_id}/amend")
async def amend_booking(booking_id: str, amendment: BookingAmendment, request: Request):
    """Add amendment to a booking - clubhouse staff only"""
    try:
        user = await require_clubhouse_staff(request)
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        expected_attendees = 1 + len(booking.get('guests', []))
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(), 'action': 'amendment',
            'by_email': user['email'], 'by_name': user['name'],
            'by_role': user.get('role', 'clubhouse_staff'),
            'details': amendment.amendment_notes,
            'changes': {
                'expected_attendees': expected_attendees,
                'actual_attendees': amendment.actual_attendees,
                'additional_charges': amendment.additional_charges,
                'difference': amendment.actual_attendees - expected_attendees
            }
        }
        new_total_charges = booking.get('total_guest_charges', 0) + (amendment.additional_charges or 0)
        await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {
                "actual_attendees": amendment.actual_attendees,
                "amendment_notes": amendment.amendment_notes,
                "total_guest_charges": new_total_charges,
                "updated_at": datetime.utcnow()
            }, "$push": {"audit_log": audit_entry}}
        )
        logger.info(f"Booking {booking_id} amended by {user['email']}: {amendment.amendment_notes}")
        return {"message": "Booking amended successfully", "additional_charges": amendment.additional_charges}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error amending booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to amend booking")


@bookings_router.get("/staff/bookings/{booking_id}/audit-log")
async def get_booking_audit_log(booking_id: str, request: Request):
    """Get audit log for a booking - staff, manager, admin, or booking owner"""
    try:
        user = await require_auth(request)
        booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        is_owner = booking['booked_by_email'] == user['email']
        is_staff_or_above = user.get('role') in ['admin', 'manager', 'clubhouse_staff']
        if not is_owner and not is_staff_or_above:
            raise HTTPException(status_code=403, detail="Access denied")
        return {"booking_id": booking_id, "audit_log": booking.get('audit_log', [])}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit log")


# ============ PDF REPORT ROUTES ============

@bookings_router.get("/staff/reports/bookings")
async def download_booking_report(request: Request, amenity_id: str, month: int, year: int):
    """Download PDF report of bookings for an amenity in a month"""
    try:
        user = await require_clubhouse_staff(request)
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Invalid month")
        amenity = await db.amenities.find_one({"id": amenity_id}, {"_id": 0})
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found")
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        bookings = await db.bookings.find({
            "amenity_id": amenity_id,
            "booking_date": {"$gte": start_date, "$lt": end_date},
            "status": "confirmed"
        }, {"_id": 0}).sort("booking_date", 1).to_list(1000)
        pdf_bytes = await generate_booking_report_pdf(
            amenity_name=amenity['name'], month=month, year=year,
            bookings=bookings, generated_by=user['name']
        )
        filename = f"TROA_Booking_Report_{amenity['name'].replace(' ', '_')}_{year}_{month:02d}.pdf"
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating booking report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")
