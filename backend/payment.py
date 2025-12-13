from fastapi import APIRouter, HTTPException, Request
import razorpay
import os
import logging
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

payment_router = APIRouter(prefix="/payment")

# Razorpay credentials
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Payment amounts (in paise - 1 INR = 100 paise)
PAYMENT_AMOUNTS = {
    'move_in': 236000,  # ₹2360 (₹2000 + 18% GST)
    'move_out': 236000,  # ₹2360 (₹2000 + 18% GST)
    'membership': 1180000  # ₹11800 (₹10000 + 18% GST)
}

class PaymentOrderRequest(BaseModel):
    payment_type: str  # move_in, move_out, membership
    name: str
    email: str
    phone: str

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    payment_type: str
    user_details: dict

@payment_router.post("/create-order")
async def create_payment_order(order_request: PaymentOrderRequest):
    """Create a Razorpay order"""
    try:
        logger.info(f"Creating payment order for type: {order_request.payment_type}")
        payment_type = order_request.payment_type
        
        if payment_type not in PAYMENT_AMOUNTS:
            logger.error(f"Invalid payment type: {payment_type}")
            raise HTTPException(status_code=400, detail="Invalid payment type")
        
        amount = PAYMENT_AMOUNTS[payment_type]
        
        # Create Razorpay order
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'{payment_type}_{uuid.uuid4().hex[:10]}',
            'notes': {
                'payment_type': payment_type,
                'name': order_request.name,
                'email': order_request.email,
                'phone': order_request.phone
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        logger.info(f"Payment order created: {order['id']}")
        
        return {
            'order_id': order['id'],
            'amount': amount,
            'currency': 'INR',
            'key_id': RAZORPAY_KEY_ID
        }
        
    except Exception as e:
        logger.error(f"Error creating payment order: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

@payment_router.post("/verify")
async def verify_payment(verification: PaymentVerification):
    """Verify payment signature and store transaction"""
    try:
        # Verify signature
        params_dict = {
            'razorpay_order_id': verification.razorpay_order_id,
            'razorpay_payment_id': verification.razorpay_payment_id,
            'razorpay_signature': verification.razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Fetch payment details
        payment = razorpay_client.payment.fetch(verification.razorpay_payment_id)
        
        # Store transaction in database
        transaction = {
            'id': str(uuid.uuid4()),
            'order_id': verification.razorpay_order_id,
            'payment_id': verification.razorpay_payment_id,
            'payment_type': verification.payment_type,
            'amount': payment['amount'] / 100,  # Convert paise to rupees
            'currency': payment['currency'],
            'status': payment['status'],
            'method': payment.get('method'),
            'user_details': verification.user_details,
            'created_at': datetime.utcnow()
        }
        
        await db.payment_transactions.insert_one(transaction)
        
        logger.info(f"Payment verified and stored: {verification.razorpay_payment_id}")
        
        return {
            'success': True,
            'message': 'Payment successful',
            'payment_id': verification.razorpay_payment_id,
            'amount': payment['amount'] / 100
        }
        
    except razorpay.errors.SignatureVerificationError:
        logger.error("Payment signature verification failed")
        raise HTTPException(status_code=400, detail="Payment verification failed")
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify payment")


class OfflinePaymentRequest(BaseModel):
    payment_type: str  # move_in, move_out, membership
    payment_method: str  # qr_code, cash_transfer
    name: str
    email: str
    phone: str
    villa_no: str = None
    notes: str = None


@payment_router.post("/offline-payment")
async def create_offline_payment(payment_request: OfflinePaymentRequest):
    """Create an offline payment request that requires admin approval"""
    try:
        from datetime import timezone
        
        if payment_request.payment_type not in PAYMENT_AMOUNTS:
            raise HTTPException(status_code=400, detail="Invalid payment type")
        
        amount = PAYMENT_AMOUNTS[payment_request.payment_type] / 100  # Convert paise to rupees
        
        # Create offline payment record
        payment_record = {
            'id': str(uuid.uuid4()),
            'payment_type': payment_request.payment_type,
            'payment_method': payment_request.payment_method,
            'amount': amount,
            'currency': 'INR',
            'status': 'pending_approval',
            'user_details': {
                'name': payment_request.name,
                'email': payment_request.email,
                'phone': payment_request.phone,
                'villa_no': payment_request.villa_no
            },
            'notes': payment_request.notes,
            'admin_approved': False,
            'approved_by': None,
            'approved_at': None,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db.offline_payments.insert_one(payment_record)
        
        logger.info(f"Offline payment request created: {payment_record['id']}")
        
        return {
            'success': True,
            'message': 'Offline payment request submitted. Awaiting admin approval.',
            'payment_id': payment_record['id'],
            'amount': amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating offline payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create offline payment request")


@payment_router.get("/offline-payments")
async def get_offline_payments(request: Request):
    """Get all offline payment requests - manager and admin access"""
    try:
        from auth import require_manager_or_admin
        await require_manager_or_admin(request)
        
        payments = await db.offline_payments.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return payments
    except HTTPException:
        raise  # Re-raise HTTP exceptions (like 401, 403) without modification
    except Exception as e:
        logger.error(f"Error fetching offline payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch offline payments")


class ApproveOfflinePayment(BaseModel):
    payment_id: str
    action: str  # approve, reject


@payment_router.post("/offline-payments/approve")
async def approve_offline_payment(request: Request, approval: ApproveOfflinePayment):
    """Approve or reject an offline payment - manager and admin access"""
    try:
        from auth import require_manager_or_admin
        from datetime import timezone
        
        admin = await require_manager_or_admin(request)
        
        payment = await db.offline_payments.find_one({"id": approval.payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if approval.action == 'approve':
            update = {
                'status': 'completed',
                'admin_approved': True,
                'approved_by': admin.get('name', admin.get('email')),
                'approved_at': datetime.now(timezone.utc)
            }
        elif approval.action == 'reject':
            update = {
                'status': 'rejected',
                'admin_approved': False,
                'approved_by': admin.get('name', admin.get('email')),
                'approved_at': datetime.now(timezone.utc)
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        await db.offline_payments.update_one(
            {"id": approval.payment_id},
            {"$set": update}
        )
        
        logger.info(f"Offline payment {approval.action}d: {approval.payment_id}")
        
        return {
            'success': True,
            'message': f'Payment {approval.action}d successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving offline payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process payment approval")


@payment_router.get("/transactions")
async def get_transactions(request: Request):
    """Get all payment transactions - admin only"""
    try:
        from auth import require_admin
        await require_admin(request)
        
        transactions = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")
