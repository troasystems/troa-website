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
    'move_in': 200000,  # ₹2000
    'move_out': 200000,  # ₹2000
    'membership': 1100000  # ₹11000
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
        payment_type = order_request.payment_type
        
        if payment_type not in PAYMENT_AMOUNTS:
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

@payment_router.get("/transactions")
async def get_transactions(request: Request):
    """Get all payment transactions - admin only"""
    try:
        from auth import require_admin
        admin = await require_admin(request)
        
        transactions = await db.payment_transactions.find().sort("created_at", -1).to_list(1000)
        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")
