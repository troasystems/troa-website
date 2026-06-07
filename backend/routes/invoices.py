"""Invoice routes (clubhouse + maintenance + offline + multi-payment)"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from typing import Optional
from datetime import datetime, timedelta, timezone
import os
import uuid
import random
import string
import logging

from database import db
from models import (
    Invoice, InvoiceCreate, InvoiceUpdate,
    MaintenanceInvoiceCreate,
    INVOICE_TYPE_CLUBHOUSE, INVOICE_TYPE_MAINTENANCE
)
from auth import require_auth, require_manager_or_admin, require_clubhouse_staff, require_accountant
from email_service import email_service
from push_notifications import send_notification_to_user, send_notification_to_admins
from pdf_service import generate_invoice_pdf

logger = logging.getLogger(__name__)

invoices_router = APIRouter(tags=["Invoices"])

INVOICE_RATE = 50.0  # per person per session
RESIDENT_MONTHLY_CAP = 300.0  # per amenity per month


def generate_invoice_number(year: int, month: int) -> str:
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TROA-INV-{year}{month:02d}-{random_suffix}"


def generate_maintenance_invoice_number() -> str:
    now = datetime.utcnow()
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TROA-MAINT-{now.year}{now.month:02d}-{random_suffix}"


@invoices_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, request: Request):
    """Create clubhouse subscription invoice for a user's amenity usage"""
    try:
        user = await require_clubhouse_staff(request)
        if invoice_data.month < 1 or invoice_data.month > 12:
            raise HTTPException(status_code=400, detail="Invalid month")
        existing = await db.invoices.find_one({
            "user_email": invoice_data.user_email,
            "amenity_id": invoice_data.amenity_id,
            "month": invoice_data.month,
            "year": invoice_data.year,
            "invoice_type": INVOICE_TYPE_CLUBHOUSE,
            "payment_status": {"$ne": "cancelled"}
        }, {"_id": 0})
        if existing:
            raise HTTPException(status_code=409, detail="Invoice already exists for this user/amenity/period")
        target_user = await db.users.find_one({"email": invoice_data.user_email}, {"_id": 0})
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        amenity = await db.amenities.find_one({"id": invoice_data.amenity_id}, {"_id": 0})
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found")

        start_date = f"{invoice_data.year}-{invoice_data.month:02d}-01"
        end_date = f"{invoice_data.year + 1}-01-01" if invoice_data.month == 12 else f"{invoice_data.year}-{invoice_data.month + 1:02d}-01"
        bookings = await db.bookings.find({
            "amenity_id": invoice_data.amenity_id,
            "booked_by_email": invoice_data.user_email,
            "booking_date": {"$gte": start_date, "$lt": end_date},
            "status": "confirmed"
        }, {"_id": 0}).to_list(100)
        if not bookings:
            raise HTTPException(status_code=400, detail="No bookings found for this user/amenity/period")

        line_items = []
        resident_sessions = 0
        resident_amount_raw = 0.0
        guest_amount = 0.0
        coach_amount = 0.0

        for booking in bookings:
            resident_sessions += 1
            resident_amount_raw += INVOICE_RATE
            line_items.append({
                'booking_id': booking['id'], 'booking_date': booking['booking_date'],
                'start_time': booking['start_time'], 'end_time': booking['end_time'],
                'attendee_type': 'resident', 'attendee_count': 1,
                'rate': INVOICE_RATE, 'amount': INVOICE_RATE,
                'audit_log': booking.get('audit_log', [])
            })
            for guest in booking.get('guests', []):
                guest_type = guest.get('guest_type', 'external')
                charge = INVOICE_RATE
                if guest_type == 'resident':
                    resident_sessions += 1
                    resident_amount_raw += charge
                    line_items.append({
                        'booking_id': booking['id'], 'booking_date': booking['booking_date'],
                        'start_time': booking['start_time'], 'end_time': booking['end_time'],
                        'attendee_type': 'resident', 'attendee_count': 1,
                        'rate': charge, 'amount': charge, 'audit_log': []
                    })
                elif guest_type == 'external':
                    guest_amount += charge
                    line_items.append({
                        'booking_id': booking['id'], 'booking_date': booking['booking_date'],
                        'start_time': booking['start_time'], 'end_time': booking['end_time'],
                        'attendee_type': 'external', 'attendee_count': 1,
                        'rate': charge, 'amount': charge, 'audit_log': []
                    })
                elif guest_type == 'coach':
                    coach_amount += charge
                    line_items.append({
                        'booking_id': booking['id'], 'booking_date': booking['booking_date'],
                        'start_time': booking['start_time'], 'end_time': booking['end_time'],
                        'attendee_type': 'coach', 'attendee_count': 1,
                        'rate': charge, 'amount': charge, 'audit_log': []
                    })

        resident_amount_capped = min(resident_amount_raw, RESIDENT_MONTHLY_CAP)
        subtotal = resident_amount_capped + guest_amount + coach_amount
        total_amount = subtotal
        due_date = datetime.utcnow() + timedelta(days=20)

        invoice = Invoice(
            invoice_number=generate_invoice_number(invoice_data.year, invoice_data.month),
            invoice_type=INVOICE_TYPE_CLUBHOUSE,
            villa_number=target_user.get('villa_number', ''),
            user_email=invoice_data.user_email,
            user_name=target_user.get('name', ''),
            user_villa=target_user.get('villa_number'),
            amenity_id=invoice_data.amenity_id,
            amenity_name=amenity['name'],
            month=invoice_data.month, year=invoice_data.year,
            line_items=line_items,
            resident_sessions_count=resident_sessions,
            resident_amount_raw=resident_amount_raw,
            resident_amount_capped=resident_amount_capped,
            guest_amount=guest_amount, coach_amount=coach_amount,
            subtotal=subtotal, total_amount=total_amount,
            due_date=due_date,
            created_by_email=user['email'], created_by_name=user['name']
        )
        await db.invoices.insert_one(invoice.dict())
        logger.info(f"Invoice {invoice.invoice_number} created for {invoice_data.user_email}")

        try:
            month_name = datetime(invoice_data.year, invoice_data.month, 1).strftime("%B %Y")
            await email_service.send_invoice_raised(
                recipient_email=invoice_data.user_email,
                user_name=target_user.get('name', ''),
                invoice_number=invoice.invoice_number,
                amenity_name=amenity['name'],
                month_year=month_name,
                total_amount=total_amount,
                due_date=due_date.strftime("%d %b %Y")
            )
        except Exception as email_error:
            logger.error(f"Failed to send invoice email: {email_error}")
        return invoice.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create invoice")


@invoices_router.post("/invoices/maintenance")
async def create_maintenance_invoice(invoice_data: MaintenanceInvoiceCreate, request: Request):
    """Create maintenance invoice against a villa"""
    try:
        user = await require_accountant(request)
        villa = await db.villas.find_one({"villa_number": invoice_data.villa_number}, {"_id": 0})
        if not villa:
            raise HTTPException(status_code=404, detail="Villa not found")
        if not invoice_data.line_items or len(invoice_data.line_items) == 0:
            raise HTTPException(status_code=400, detail="At least one line item is required")

        maintenance_line_items = []
        subtotal = 0.0
        for item in invoice_data.line_items:
            amount = item.quantity * item.rate
            maintenance_line_items.append({
                'id': str(uuid.uuid4()), 'description': item.description,
                'quantity': item.quantity, 'rate': item.rate, 'amount': amount
            })
            subtotal += amount

        discount_amount = 0.0
        if invoice_data.discount_type == "percentage":
            discount_amount = subtotal * (invoice_data.discount_value / 100)
        elif invoice_data.discount_type == "fixed":
            discount_amount = min(invoice_data.discount_value, subtotal)
        total_amount = max(subtotal - discount_amount, 0)
        due_date = datetime.utcnow() + timedelta(days=invoice_data.due_days)
        primary_email = villa.get('emails', [''])[0] if villa.get('emails') else ''

        invoice = Invoice(
            invoice_number=generate_maintenance_invoice_number(),
            invoice_type=INVOICE_TYPE_MAINTENANCE,
            villa_number=invoice_data.villa_number,
            user_email=primary_email, user_name='',
            maintenance_line_items=maintenance_line_items,
            subtotal=subtotal,
            discount_type=invoice_data.discount_type,
            discount_value=invoice_data.discount_value,
            discount_amount=discount_amount,
            total_amount=total_amount, due_date=due_date,
            created_by_email=user['email'], created_by_name=user.get('name', ''),
            audit_log=[{
                'action': 'created', 'timestamp': datetime.utcnow().isoformat(),
                'by_email': user['email'], 'by_name': user.get('name', ''),
                'details': f"Maintenance invoice created with {len(maintenance_line_items)} line items"
            }]
        )
        await db.invoices.insert_one(invoice.dict())
        logger.info(f"Maintenance invoice {invoice.invoice_number} created for villa {invoice_data.villa_number}")

        try:
            for email in villa.get('emails', []):
                villa_user = await db.users.find_one({"email": email}, {"_id": 0, "name": 1})
                user_name = villa_user.get('name', '') if villa_user else ''
                await email_service.send_maintenance_invoice_raised(
                    recipient_email=email, user_name=user_name,
                    invoice_number=invoice.invoice_number,
                    villa_number=invoice_data.villa_number,
                    total_amount=total_amount,
                    due_date=due_date.strftime("%d %b %Y"),
                    line_items=maintenance_line_items
                )
        except Exception as email_error:
            logger.error(f"Failed to send maintenance invoice email: {email_error}")
        return invoice.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating maintenance invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create maintenance invoice")


@invoices_router.get("/invoices")
async def get_invoices(request: Request, status: Optional[str] = None, invoice_type: Optional[str] = None, view: Optional[str] = None):
    """Get invoices - role-based access"""
    try:
        user = await require_auth(request)
        user_role = user.get('role')
        user_email = user.get('email')
        query = {}

        if view == 'my':
            user_villas = await db.villas.find(
                {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
                {"_id": 0, "villa_number": 1}
            ).to_list(100)
            villa_numbers = [v['villa_number'] for v in user_villas]
            if villa_numbers:
                query['$or'] = [{'user_email': user_email}, {'villa_number': {'$in': villa_numbers}}]
            else:
                query['user_email'] = user_email
        elif view == 'manage':
            if user_role in ['admin', 'manager']:
                pass
            elif user_role == 'accountant':
                query['invoice_type'] = INVOICE_TYPE_MAINTENANCE
            elif user_role == 'clubhouse_staff':
                query['invoice_type'] = INVOICE_TYPE_CLUBHOUSE
            else:
                return []
        else:
            if user_role in ['admin', 'manager']:
                pass
            elif user_role == 'accountant':
                query['invoice_type'] = INVOICE_TYPE_MAINTENANCE
                query['created_by_email'] = user_email
            elif user_role == 'clubhouse_staff':
                query['invoice_type'] = INVOICE_TYPE_CLUBHOUSE
            else:
                user_villas = await db.villas.find(
                    {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
                    {"_id": 0, "villa_number": 1}
                ).to_list(100)
                villa_numbers = [v['villa_number'] for v in user_villas]
                if villa_numbers:
                    query['$or'] = [{'user_email': user_email}, {'villa_number': {'$in': villa_numbers}}]
                else:
                    query['user_email'] = user_email
        if status:
            query['payment_status'] = status
        if invoice_type:
            query['invoice_type'] = invoice_type
        invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
        return invoices
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")


@invoices_router.get("/invoices/pending/count")
async def get_pending_invoice_count(request: Request):
    """Get count of pending invoices for current user"""
    try:
        user = await require_auth(request)
        user_email = user.get('email')
        user_villas = await db.villas.find(
            {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
            {"_id": 0, "villa_number": 1}
        ).to_list(100)
        villa_numbers = [v['villa_number'] for v in user_villas]
        query = {"payment_status": "pending"}
        if villa_numbers:
            query['$or'] = [{'user_email': user_email}, {'villa_number': {'$in': villa_numbers}}]
        else:
            query['user_email'] = user_email
        count = await db.invoices.count_documents(query)
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error counting pending invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to count invoices")


@invoices_router.get("/invoices/pending-approvals")
async def get_pending_invoice_approvals(request: Request):
    """Get all invoices with pending offline payment approvals - Admin/Manager only"""
    try:
        await require_manager_or_admin(request)
        pending = await db.invoices.find(
            {"offline_payment_status": "pending_approval"}, {"_id": 0}
        ).sort("offline_submitted_at", 1).to_list(100)
        return pending
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pending approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending approvals")


@invoices_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request):
    """Get invoice details"""
    try:
        user = await require_auth(request)
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        is_manager = user.get('role') in ['admin', 'manager']
        is_owner = invoice['user_email'] == user['email']
        if not is_manager and not is_owner:
            raise HTTPException(status_code=403, detail="Access denied")
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoice")


@invoices_router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, request: Request):
    """Download invoice as PDF"""
    try:
        user = await require_auth(request)
        user_email = user.get('email')
        user_role = user.get('role')
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        is_admin_or_manager = user_role in ['admin', 'manager']
        is_accountant = user_role == 'accountant'
        is_clubhouse_staff = user_role == 'clubhouse_staff'
        is_direct_owner = invoice.get('user_email') == user_email
        is_creator = invoice.get('created_by_email') == user_email
        is_villa_member = False
        if invoice.get('villa_number'):
            villa = await db.villas.find_one(
                {"villa_number": invoice['villa_number']}, {"_id": 0, "emails": 1}
            )
            if villa and villa.get('emails'):
                is_villa_member = any(
                    email.lower() == user_email.lower() for email in villa.get('emails', [])
                )
        has_access = (
            is_admin_or_manager or is_direct_owner or is_villa_member or
            (is_accountant and invoice.get('invoice_type') == INVOICE_TYPE_MAINTENANCE and is_creator) or
            (is_clubhouse_staff and invoice.get('invoice_type') == INVOICE_TYPE_CLUBHOUSE)
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        booking_ids = [item.get('booking_id') for item in invoice.get('line_items', []) if item.get('booking_id')]
        bookings = await db.bookings.find({"id": {"$in": list(set(booking_ids))}}, {"_id": 0}).to_list(100)
        pdf_bytes = await generate_invoice_pdf(invoice, bookings)
        filename = f"TROA_Invoice_{invoice['invoice_number']}.pdf"
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invoice PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


@invoices_router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate, request: Request):
    """Update invoice (override total amount) - Manager only, before payment"""
    try:
        user = await require_manager_or_admin(request)
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Cannot modify paid or cancelled invoice")
        update_fields = {"updated_at": datetime.utcnow()}
        if update.new_total_amount is not None:
            if update.new_total_amount < 0:
                raise HTTPException(status_code=400, detail="Total amount cannot be negative")
            previous_amount = invoice.get('total_amount', invoice.get('subtotal', 0))
            new_amount = update.new_total_amount
            subtotal = invoice.get('subtotal', 0)
            adjustment = new_amount - subtotal
            update_fields['total_amount'] = new_amount
            update_fields['adjustment'] = adjustment
            update_fields['adjustment_reason'] = update.adjustment_reason or ''
            audit_entry = {
                "action": "amount_modified",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "by_email": user['email'], "by_name": user['name'],
                "details": f"Amount changed from {previous_amount:.0f} to {new_amount:.0f}. Reason: {update.adjustment_reason or 'No reason provided'}",
                "previous_amount": previous_amount, "new_amount": new_amount
            }
            existing_audit_log = invoice.get('audit_log', [])
            existing_audit_log.append(audit_entry)
            update_fields['audit_log'] = existing_audit_log
        await db.invoices.update_one({"id": invoice_id}, {"$set": update_fields})
        logger.info(f"Invoice {invoice_id} updated by {user['email']}")
        return {"message": "Invoice updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to update invoice")


@invoices_router.post("/invoices/{invoice_id}/create-order")
async def create_invoice_payment_order(invoice_id: str, request: Request):
    """Create Razorpay order for invoice payment"""
    try:
        user = await require_auth(request)
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice['user_email'] != user['email']:
            raise HTTPException(status_code=403, detail="Access denied")
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Invoice is not pending payment")

        import razorpay
        razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        if not razorpay_key_id or not razorpay_key_secret:
            raise HTTPException(status_code=500, detail="Payment gateway not configured")
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        order_data = {
            'amount': int(invoice['total_amount'] * 100),
            'currency': 'INR',
            'receipt': invoice['invoice_number'],
            'notes': {'invoice_id': invoice['id'], 'user_email': user['email']}
        }
        order = client.order.create(data=order_data)
        return {
            'order_id': order['id'], 'amount': invoice['total_amount'],
            'currency': 'INR', 'key_id': razorpay_key_id,
            'invoice_number': invoice['invoice_number']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@invoices_router.post("/invoices/{invoice_id}/verify-payment")
async def verify_invoice_payment(invoice_id: str, request: Request):
    """Verify Razorpay payment for invoice"""
    try:
        user = await require_auth(request)
        body = await request.json()
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice['user_email'] != user['email']:
            raise HTTPException(status_code=403, detail="Access denied")

        import razorpay
        import hmac
        import hashlib
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        order_id = body.get('razorpay_order_id')
        payment_id = body.get('razorpay_payment_id')
        signature = body.get('razorpay_signature')
        if not all([order_id, payment_id, signature]):
            raise HTTPException(status_code=400, detail="Missing payment details")
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            razorpay_key_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        if signature != expected_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        payment_date = datetime.utcnow()
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "payment_status": "paid", "payment_method": "razorpay",
                "payment_id": payment_id, "payment_date": payment_date,
                "updated_at": payment_date
            }}
        )
        logger.info(f"Invoice {invoice_id} paid via Razorpay: {payment_id}")

        try:
            month_name = datetime(invoice['year'], invoice['month'], 1).strftime("%B %Y")
            await email_service.send_invoice_payment_receipt(
                recipient_email=user['email'], user_name=user['name'],
                invoice_number=invoice['invoice_number'],
                amenity_name=invoice['amenity_name'], month_year=month_name,
                total_amount=invoice['total_amount'], payment_id=payment_id,
                payment_date=payment_date.strftime("%d %b %Y %H:%M")
            )
        except Exception as email_error:
            logger.error(f"Failed to send payment receipt email: {email_error}")
        return {"message": "Payment verified successfully", "payment_id": payment_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")


@invoices_router.delete("/invoices/{invoice_id}")
async def cancel_invoice(invoice_id: str, request: Request):
    """Cancel invoice - Manager only, before payment"""
    try:
        user = await require_manager_or_admin(request)
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Cannot cancel paid invoice")
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"payment_status": "cancelled", "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Invoice {invoice_id} cancelled by {user['email']}")
        return {"message": "Invoice cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel invoice")


# ============ OFFLINE INVOICE PAYMENT ENDPOINTS ============

@invoices_router.post("/invoices/{invoice_id}/pay-offline")
async def submit_offline_invoice_payment(invoice_id: str, request: Request):
    """Submit offline payment for an invoice - requires admin approval"""
    try:
        user = await require_auth(request)
        body = await request.json()
        transaction_reference = body.get('transaction_reference', '')
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        user_villa_numbers = []
        if user.get('villa_number'):
            user_villa_numbers.append(user['villa_number'])
        user_villa = await db.villas.find_one({"emails": user['email']}, {"_id": 0, "villa_number": 1})
        if user_villa:
            user_villa_numbers.append(user_villa['villa_number'])
        has_access = (
            invoice.get('user_email') == user['email'] or
            invoice.get('villa_number') in user_villa_numbers
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        if invoice['payment_status'] != 'pending':
            raise HTTPException(status_code=400, detail="Invoice is not pending payment")
        if invoice.get('offline_payment_status') == 'pending_approval':
            raise HTTPException(status_code=400, detail="Offline payment already submitted and pending approval")

        audit_entry = {
            "action": "offline_payment_submitted",
            "timestamp": datetime.utcnow().isoformat(),
            "by_email": user['email'],
            "by_name": user.get('name', user['email']),
            "details": f"Offline payment submitted. Reference: {transaction_reference or 'N/A'}"
        }
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "offline_payment_status": "pending_approval",
                "offline_transaction_reference": transaction_reference,
                "offline_submitted_by_email": user['email'],
                "offline_submitted_by_name": user.get('name', user['email']),
                "offline_submitted_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }, "$push": {"audit_log": audit_entry}}
        )
        logger.info(f"Offline payment submitted for invoice {invoice_id} by {user['email']}")

        try:
            await send_notification_to_admins(
                title="Invoice Offline Payment",
                body=f"Offline payment submitted for Invoice #{invoice.get('invoice_number', invoice_id)}",
                url="/admin"
            )
        except Exception as notif_error:
            logger.error(f"Failed to send admin notification: {notif_error}")
        return {"message": "Offline payment submitted successfully. Pending admin approval.", "invoice_id": invoice_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting offline payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit offline payment")


@invoices_router.post("/invoices/{invoice_id}/approve-offline")
async def approve_offline_invoice_payment(invoice_id: str, request: Request):
    """Approve offline payment for an invoice - Admin/Manager only"""
    try:
        admin = await require_manager_or_admin(request)
        body = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        approval_note = body.get('approval_note', '')
        invoice = await db.invoices.find_one({
            "id": invoice_id, "offline_payment_status": "pending_approval"
        }, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found or not pending approval")
        payment_date = datetime.utcnow()
        audit_entry = {
            "action": "offline_payment_approved",
            "timestamp": payment_date.isoformat(),
            "by_email": admin['email'],
            "by_name": admin.get('name', admin['email']),
            "details": f"Offline payment approved. {approval_note or ''}"
        }
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "payment_status": "paid", "payment_method": "offline",
                "payment_date": payment_date,
                "offline_payment_status": "approved",
                "offline_approved_by_email": admin['email'],
                "offline_approved_by_name": admin.get('name', admin['email']),
                "offline_approval_note": approval_note,
                "offline_approved_at": payment_date,
                "updated_at": payment_date
            }, "$push": {"audit_log": audit_entry}}
        )
        logger.info(f"Offline payment approved for invoice {invoice_id} by {admin['email']}")

        try:
            if invoice.get('user_email'):
                await send_notification_to_user(
                    user_email=invoice['user_email'],
                    title="Payment Approved!",
                    body=f"Your offline payment for Invoice #{invoice.get('invoice_number', '')} has been approved.",
                    url="/my-invoices"
                )
        except Exception as notif_error:
            logger.error(f"Failed to send user notification: {notif_error}")
        try:
            if invoice.get('user_email'):
                if invoice.get('invoice_type') == INVOICE_TYPE_MAINTENANCE:
                    await email_service.send_invoice_payment_receipt(
                        recipient_email=invoice['user_email'],
                        user_name=invoice.get('user_name', ''),
                        invoice_number=invoice['invoice_number'],
                        amenity_name=f"Maintenance - Villa {invoice.get('villa_number', '')}",
                        month_year="N/A",
                        total_amount=invoice['total_amount'],
                        payment_id=f"OFFLINE-{invoice.get('offline_transaction_reference', 'N/A')}",
                        payment_date=payment_date.strftime("%d %b %Y %H:%M")
                    )
                else:
                    month_name = datetime(invoice['year'], invoice['month'], 1).strftime("%B %Y") if invoice.get('month') and invoice.get('year') else "N/A"
                    await email_service.send_invoice_payment_receipt(
                        recipient_email=invoice['user_email'],
                        user_name=invoice.get('user_name', ''),
                        invoice_number=invoice['invoice_number'],
                        amenity_name=invoice.get('amenity_name', ''),
                        month_year=month_name,
                        total_amount=invoice['total_amount'],
                        payment_id=f"OFFLINE-{invoice.get('offline_transaction_reference', 'N/A')}",
                        payment_date=payment_date.strftime("%d %b %Y %H:%M")
                    )
        except Exception as email_error:
            logger.error(f"Failed to send payment receipt email: {email_error}")
        return {"message": "Offline payment approved successfully", "invoice_id": invoice_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving offline payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve offline payment")


@invoices_router.post("/invoices/{invoice_id}/reject-offline")
async def reject_offline_invoice_payment(invoice_id: str, request: Request):
    """Reject offline payment for an invoice - Admin/Manager only"""
    try:
        admin = await require_manager_or_admin(request)
        body = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        rejection_reason = body.get('rejection_reason', '')
        invoice = await db.invoices.find_one({
            "id": invoice_id, "offline_payment_status": "pending_approval"
        }, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found or not pending approval")
        audit_entry = {
            "action": "offline_payment_rejected",
            "timestamp": datetime.utcnow().isoformat(),
            "by_email": admin['email'],
            "by_name": admin.get('name', admin['email']),
            "details": f"Offline payment rejected. Reason: {rejection_reason or 'No reason provided'}"
        }
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "offline_payment_status": "rejected",
                "offline_rejected_by_email": admin['email'],
                "offline_rejected_by_name": admin.get('name', admin['email']),
                "offline_rejection_reason": rejection_reason,
                "offline_rejected_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }, "$unset": {
                "offline_transaction_reference": "",
                "offline_submitted_by_email": "",
                "offline_submitted_by_name": "",
                "offline_submitted_at": ""
            }, "$push": {"audit_log": audit_entry}}
        )
        logger.info(f"Offline payment rejected for invoice {invoice_id} by {admin['email']}")
        try:
            if invoice.get('user_email'):
                await send_notification_to_user(
                    user_email=invoice['user_email'],
                    title="Payment Rejected",
                    body=f"Your offline payment for Invoice #{invoice.get('invoice_number', '')} was rejected. {rejection_reason}",
                    url="/my-invoices"
                )
        except Exception as notif_error:
            logger.error(f"Failed to send user notification: {notif_error}")
        return {"message": "Offline payment rejected", "invoice_id": invoice_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting offline payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject offline payment")


@invoices_router.get("/payment-qr-info")
async def get_payment_qr_info(request: Request):
    """Get QR code info for offline payments"""
    return {
        "upi_id": "teamretreatownersassociation@sbi",
        "bank_name": "State Bank of India",
        "account_name": "The Retreat Owners Association",
        "account_number": "50100XXXXXXXXX",
        "ifsc_code": "SBIN0001234",
        "qr_image_url": "https://customer-assets.emergentagent.com/job_troaresidents/artifacts/kfeb4dc1_Screenshot%202025-12-13%20at%201.15.41%E2%80%AFPM.png",
        "instructions": [
            "Scan the QR code using any UPI app (GPay, PhonePe, Paytm, etc.)",
            "Enter the exact invoice amount",
            "Add the Invoice Number in the remarks/notes",
            "Complete the payment and note down the Transaction ID",
            "Submit the payment with the Transaction ID for approval"
        ]
    }


@invoices_router.post("/invoices/pay-multiple")
async def create_multi_invoice_payment_order(request: Request):
    """Create Razorpay order for multiple invoices"""
    try:
        user = await require_auth(request)
        user_email = user.get('email')
        body = await request.json()
        invoice_ids = body.get('invoice_ids', [])
        if not invoice_ids:
            raise HTTPException(status_code=400, detail="No invoices selected")

        user_villas = await db.villas.find(
            {"emails": {"$elemMatch": {"$regex": f"^{user_email}$", "$options": "i"}}},
            {"_id": 0, "villa_number": 1}
        ).to_list(100)
        villa_numbers = [v['villa_number'] for v in user_villas]
        invoices = await db.invoices.find({"id": {"$in": invoice_ids}}, {"_id": 0}).to_list(100)
        if len(invoices) != len(invoice_ids):
            raise HTTPException(status_code=400, detail="One or more invoices not found")

        total_amount = 0
        valid_invoices = []
        for invoice in invoices:
            has_access = (
                invoice.get('user_email') == user_email or
                invoice.get('villa_number') in villa_numbers
            )
            if not has_access:
                raise HTTPException(status_code=403, detail=f"You don't have access to invoice {invoice.get('invoice_number')}")
            if invoice['payment_status'] != 'pending':
                raise HTTPException(status_code=400, detail=f"Invoice {invoice.get('invoice_number')} is already {invoice['payment_status']}")
            total_amount += invoice.get('total_amount', 0)
            valid_invoices.append(invoice)
        if total_amount <= 0:
            raise HTTPException(status_code=400, detail="Total amount must be greater than 0")
        valid_invoices.sort(key=lambda x: x.get('created_at', datetime.min))

        razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        if not razorpay_key_id or not razorpay_key_secret:
            raise HTTPException(status_code=500, detail="Payment gateway not configured")
        import razorpay
        razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        invoice_numbers = [inv.get('invoice_number') for inv in valid_invoices]
        order_data = {
            'amount': int(total_amount * 100), 'currency': 'INR',
            'notes': {
                'invoice_ids': ','.join(invoice_ids),
                'invoice_numbers': ','.join(invoice_numbers),
                'user_email': user_email, 'type': 'multi_invoice_payment'
            }
        }
        order = razorpay_client.order.create(data=order_data)

        for invoice in valid_invoices:
            await db.invoices.update_one(
                {"id": invoice['id']},
                {"$set": {"razorpay_order_id": order['id'], "updated_at": datetime.utcnow()}}
            )
        logger.info(f"Multi-invoice payment order created for user {user_email}, total: {total_amount}")
        return {
            'order_id': order['id'], 'amount': total_amount, 'currency': 'INR',
            'key_id': razorpay_key_id, 'invoice_ids': invoice_ids,
            'invoice_count': len(valid_invoices)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating multi-invoice payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@invoices_router.post("/invoices/verify-multi-payment")
async def verify_multi_invoice_payment(request: Request):
    """Verify Razorpay payment for multiple invoices"""
    try:
        user = await require_auth(request)
        body = await request.json()
        razorpay_payment_id = body.get('razorpay_payment_id')
        razorpay_order_id = body.get('razorpay_order_id')
        razorpay_signature = body.get('razorpay_signature')
        invoice_ids = body.get('invoice_ids', [])
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, invoice_ids]):
            raise HTTPException(status_code=400, detail="Missing payment verification data")

        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        import hmac
        import hashlib
        generated_signature = hmac.new(
            razorpay_key_secret.encode('utf-8'),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if generated_signature != razorpay_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        invoices = await db.invoices.find({"id": {"$in": invoice_ids}}, {"_id": 0}).to_list(100)
        invoices.sort(key=lambda x: x.get('created_at', datetime.min))
        now = datetime.utcnow()
        paid_invoices = []
        for invoice in invoices:
            audit_entry = {
                'action': 'payment_received', 'timestamp': now.isoformat(),
                'by_email': user['email'], 'by_name': user.get('name', ''),
                'details': f"Online payment received via multi-invoice payment. Payment ID: {razorpay_payment_id}"
            }
            await db.invoices.update_one(
                {"id": invoice['id']},
                {"$set": {
                    "payment_status": "paid", "payment_method": "razorpay",
                    "payment_id": razorpay_payment_id,
                    "payment_date": now, "updated_at": now
                }, "$push": {"audit_log": audit_entry}}
            )
            paid_invoices.append(invoice.get('invoice_number'))
        logger.info(f"Multi-invoice payment verified for user {user['email']}: {', '.join(paid_invoices)}")
        return {
            'success': True,
            'message': f'Payment verified for {len(paid_invoices)} invoices',
            'paid_invoices': paid_invoices
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying multi-invoice payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")
