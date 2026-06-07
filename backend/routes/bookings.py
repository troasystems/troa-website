"""Amenity Bookings + Clubhouse Staff routes + PDF Reports"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from typing import List, Optional
from datetime import datetime, timedelta
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


# ============ BOOKING ROUTES ============

@bookings_router.post("/bookings", response_model=AmenityBooking)
async def create_booking(booking: AmenityBookingCreate, request: Request):
    """Create amenity booking - authenticated users only"""
    try:
        user = await require_auth(request)
        if booking.duration_minutes not in [30, 60]:
            raise HTTPException(status_code=400, detail="Duration must be 30 or 60 minutes")

        processed_guests = []
        total_guest_charges = 0.0
        for guest in (booking.guests or []):
            guest_type = guest.get('guest_type', 'external')
            guest_name = guest.get('name', '').strip()
            villa_number = guest.get('villa_number', '').strip() if guest.get('villa_number') else None
            if not guest_name:
                continue
            if guest_type == 'resident' and not villa_number:
                raise HTTPException(status_code=400, detail=f"Villa number is required for resident guest: {guest_name}")
            charge = GUEST_CHARGE if guest_type in ['external', 'coach'] else 0.0
            if charge:
                total_guest_charges += charge
            processed_guests.append({
                'name': guest_name, 'guest_type': guest_type,
                'villa_number': villa_number, 'charge': charge
            })
        if len(processed_guests) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 additional guests allowed")

        legacy_guests = []
        if booking.additional_guests and not booking.guests:
            for name in booking.additional_guests[:3]:
                if name.strip():
                    legacy_guests.append({
                        'name': name.strip(), 'guest_type': 'external',
                        'villa_number': None, 'charge': GUEST_CHARGE
                    })
                    total_guest_charges += GUEST_CHARGE
            processed_guests = legacy_guests

        start_dt = datetime.strptime(booking.start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=booking.duration_minutes)
        end_time = end_dt.strftime("%H:%M")

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
