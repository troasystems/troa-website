from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (used by background tasks in this file)
from database import db, client

# Create the main app
app = FastAPI(redirect_slashes=False)


# ============ MIDDLEWARE ============

class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers to responses based on endpoint type"""
    CACHEABLE_ENDPOINTS = [
        '/api/amenities',
        '/api/committee',
        '/api/gallery',
    ]
    NO_CACHE_ENDPOINTS = [
        '/api/auth',
        '/api/bookings',
        '/api/payment',
        '/api/chat',
        '/api/feedback',
        '/api/membership',
        '/api/push',
        '/api/users',
        '/api/events',
    ]

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method != 'GET':
            return response
        path = request.url.path
        if any(path.startswith(ep) for ep in self.CACHEABLE_ENDPOINTS):
            response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=3600'
            response.headers['Vary'] = 'Accept-Encoding'
        elif any(path.startswith(ep) for ep in self.NO_CACHE_ENDPOINTS):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
        else:
            response.headers['Cache-Control'] = 'private, max-age=60'
        return response

app.add_middleware(CacheControlMiddleware)


# ============ HEALTH & ROOT ============

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy"}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
async def api_health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "troa-backend"}


@api_router.get("/")
async def root():
    return {"message": "TROA API - The Retreat Owners Association"}


# ============ INCLUDE ROUTE MODULES ============

from routes.committee import committee_router
from routes.amenities import amenities_router
from routes.gallery import gallery_router
from routes.membership import membership_router
from routes.users import users_router
from routes.feedback import feedback_router
from routes.bookings import bookings_router
from routes.invoices import invoices_router

# Include route modules under /api prefix via api_router
api_router.include_router(committee_router)
api_router.include_router(amenities_router)
api_router.include_router(gallery_router)
api_router.include_router(membership_router)
api_router.include_router(users_router)
api_router.include_router(feedback_router)
api_router.include_router(bookings_router)
api_router.include_router(invoices_router)

# Include api_router in app
app.include_router(api_router)

# Include existing external routers
from auth import auth_router
from basic_auth import basic_auth_middleware
from instagram import instagram_router
from gridfs_upload import gridfs_router
from payment import payment_router
from chatbot import chatbot_router
from events import events_router
from villas import villas_router

app.include_router(auth_router, prefix="/api")
app.include_router(instagram_router, prefix="/api")
app.include_router(gridfs_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(villas_router, prefix="/api")

# Push notifications router for PWA
from push_notifications import push_router
app.include_router(push_router, prefix="/api")

# Community Chat router
from community_chat import chat_router, init_mc_group
app.include_router(chat_router, prefix="/api")

# Bulk upload router
from bulk_upload import bulk_router
app.include_router(bulk_router, prefix="/api")


# ============ SESSION & CORS MIDDLEWARE ============

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
)

default_cors_origins = [
    "https://troa.in",
    "http://troa.in",
    "https://websocket-app-3.preview.emergentagent.com",
    "https://tenant-assist-6.emergent.host",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

cors_origins_env = os.environ.get('CORS_ORIGINS', '')
if cors_origins_env:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
else:
    CORS_ORIGINS = default_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ LIFECYCLE EVENTS ============

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Background task for invoice reminders
from email_service import email_service

async def send_invoice_reminders():
    """Background task to send invoice payment reminders."""
    logger.info("Starting invoice reminder background task")
    while True:
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            pending_invoices = await db.invoices.find(
                {"payment_status": "pending"}, {"_id": 0}
            ).to_list(1000)

            for invoice in pending_invoices:
                try:
                    due_date = invoice.get('due_date')
                    if not due_date:
                        continue
                    if isinstance(due_date, str):
                        due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    due_date_normalized = due_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                    days_until_due = (due_date_normalized - today).days
                    is_overdue = days_until_due < 0

                    last_reminder = invoice.get('last_reminder_sent')
                    should_send = False
                    if last_reminder:
                        if isinstance(last_reminder, str):
                            last_reminder = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                        last_reminder_normalized = last_reminder.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                        days_since_last_reminder = (today - last_reminder_normalized).days
                        if is_overdue:
                            should_send = days_since_last_reminder >= 1
                        else:
                            should_send = days_since_last_reminder >= 5
                    else:
                        created_at = invoice.get('created_at')
                        if created_at:
                            if isinstance(created_at, str):
                                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at_normalized = created_at.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                            days_since_creation = (today - created_at_normalized).days
                            if is_overdue:
                                should_send = days_since_creation >= 1
                            else:
                                should_send = days_since_creation >= 5

                    if should_send:
                        villa_number = invoice.get('villa_number', '')
                        invoice_number = invoice.get('invoice_number', '')
                        total_amount = invoice.get('total_amount', 0)
                        due_date_str = due_date.strftime("%d %b %Y") if due_date else ''
                        emails_to_notify = []
                        if invoice.get('user_email'):
                            emails_to_notify.append(invoice['user_email'])
                        if villa_number:
                            villa = await db.villas.find_one(
                                {"villa_number": villa_number}, {"_id": 0, "emails": 1}
                            )
                            if villa and villa.get('emails'):
                                for email in villa['emails']:
                                    if email and email not in emails_to_notify:
                                        emails_to_notify.append(email)
                        for email in emails_to_notify:
                            try:
                                user = await db.users.find_one({"email": email}, {"_id": 0, "name": 1})
                                user_name = user.get('name', '') if user else ''
                                await email_service.send_invoice_reminder(
                                    recipient_email=email, user_name=user_name,
                                    invoice_number=invoice_number, villa_number=villa_number,
                                    total_amount=total_amount, due_date=due_date_str,
                                    days_until_due=days_until_due, is_overdue=is_overdue
                                )
                                logger.info(f"Sent invoice reminder for {invoice_number} to {email}")
                            except Exception as email_error:
                                logger.error(f"Failed to send reminder to {email}: {email_error}")
                        await db.invoices.update_one(
                            {"id": invoice['id']},
                            {"$set": {"last_reminder_sent": datetime.utcnow()}}
                        )
                except Exception as invoice_error:
                    logger.error(f"Error processing reminder for invoice {invoice.get('invoice_number', 'unknown')}: {invoice_error}")
        except Exception as e:
            logger.error(f"Error in invoice reminder task: {e}")
        await asyncio.sleep(3600)


@app.on_event("startup")
async def startup_event():
    try:
        await init_mc_group()
    except Exception as e:
        logging.error(f"Error initializing MC Group: {e}")
    asyncio.create_task(send_invoice_reminders())
