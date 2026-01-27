from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

# ============ ROLE CONSTANTS ============
# Staff roles group
STAFF_ROLES = ['clubhouse_staff', 'accountant']
# All valid roles
VALID_ROLES = ['admin', 'manager', 'clubhouse_staff', 'accountant', 'user']
# Roles that bypass villa email check on login
PRIVILEGED_ROLES = ['admin', 'manager', 'clubhouse_staff', 'accountant']


# ============ VILLA MODELS ============

class Villa(BaseModel):
    villa_number: str  # Primary key - alphanumeric (e.g., "A-101", "205")
    square_feet: float = 0.0
    emails: List[str] = []  # List of email addresses associated with this villa
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VillaCreate(BaseModel):
    villa_number: str
    square_feet: float = 0.0
    emails: List[str] = []

class VillaUpdate(BaseModel):
    square_feet: Optional[float] = None
    emails: Optional[List[str]] = None


class CommitteeMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    position: str
    image: str
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommitteeMemberCreate(BaseModel):
    name: str
    position: str
    image: str
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None

class Amenity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AmenityCreate(BaseModel):
    name: str
    description: str
    image: str

class GalleryImage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    category: str
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GalleryImageCreate(BaseModel):
    title: str
    category: str
    url: str

class MembershipApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    firstName: str
    lastName: Optional[str] = None
    email: EmailStr
    phone: str
    villaNo: str
    message: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

class MembershipApplicationCreate(BaseModel):
    firstName: str
    lastName: Optional[str] = None
    email: EmailStr
    phone: str
    villaNo: str
    message: Optional[str] = None

class MembershipApplicationUpdate(BaseModel):
    status: str  # approved, rejected

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    picture: Optional[str] = None
    provider: str = "google"  # google, facebook, email
    role: str = "user"  # admin, manager, clubhouse_staff, accountant, user
    is_admin: bool = False  # Deprecated - use role instead
    villa_number: str = ""  # Villa/Unit number - required for email signups
    email_verified: bool = False  # Email verification status
    verification_token: Optional[str] = None  # One-time verification token
    verification_expires_at: Optional[datetime] = None  # Token expiry (2 weeks)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    name: str = ""
    picture: Optional[str] = None
    provider: str = "whitelist"
    role: str = "user"  # admin, manager, clubhouse_staff, accountant, user
    villa_number: str = ""

class UserUpdate(BaseModel):
    role: Optional[str] = None  # admin, manager, clubhouse_staff, accountant, user
    name: Optional[str] = None
    villa_number: Optional[str] = None
    picture: Optional[str] = None
    new_password: Optional[str] = None  # For password reset by admin
    email_verified: Optional[bool] = None  # Admin can manually verify/unverify

# Guest type for amenity bookings
class BookingGuest(BaseModel):
    name: str
    guest_type: str  # "resident", "external", "coach"
    villa_number: Optional[str] = None  # Required for resident guests
    charge: float = 0.0  # ₹50 for external guests and coaches

class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str  # "created", "modified", "availed", "not_availed", "amendment"
    by_email: str
    by_name: str
    by_role: str
    details: str
    changes: Optional[dict] = None  # For amendments, store what changed

class AmenityBooking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amenity_id: str
    amenity_name: str
    booked_by_email: str
    booked_by_name: str
    booked_by_villa: Optional[str] = None  # Booker's villa number
    booking_date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format (24-hour)
    end_time: str  # HH:MM format (24-hour)
    duration_minutes: int  # 30 or 60
    # Enhanced guest tracking
    guests: list = []  # List of BookingGuest objects
    additional_guests: list = []  # Legacy: List of guest names (kept for backward compatibility)
    total_guest_charges: float = 0.0  # Total charges for external guests/coaches
    # Availed status (for clubhouse staff)
    availed_status: str = "pending"  # "pending", "availed", "not_availed"
    availed_at: Optional[datetime] = None
    availed_by_email: Optional[str] = None
    availed_by_name: Optional[str] = None
    # Actual attendance (for amendments)
    actual_attendees: Optional[int] = None  # Actual number who showed up
    amendment_notes: Optional[str] = None
    # Audit log
    audit_log: list = []  # List of AuditLogEntry objects
    status: str = "confirmed"  # confirmed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AmenityBookingCreate(BaseModel):
    amenity_id: str
    amenity_name: str
    booking_date: str  # YYYY-MM-DD
    start_time: str  # HH:MM (24-hour)
    duration_minutes: int  # 30 or 60 minutes
    guests: Optional[list] = []  # List of BookingGuest objects
    additional_guests: Optional[list] = []  # Legacy: Optional list of guest names

# Staff operations models
class BookingAvailedUpdate(BaseModel):
    availed_status: str  # "availed" or "not_availed"
    notes: Optional[str] = None

class BookingAmendment(BaseModel):
    actual_attendees: int
    amendment_notes: str
    additional_charges: Optional[float] = 0.0  # For extra guests

class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    user_name: str
    rating: int  # 1-5 stars
    works_well: Optional[str] = None
    needs_improvement: Optional[str] = None
    feature_suggestions: Optional[str] = None
    votes: int = 0  # Number of upvotes from managers/admins
    voted_by: list = []  # List of emails who voted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, reviewed, implemented

class FeedbackCreate(BaseModel):
    rating: int
    works_well: Optional[str] = None
    needs_improvement: Optional[str] = None
    feature_suggestions: Optional[str] = None

# Event Models
class EventPreference(BaseModel):
    name: str  # e.g., "Food Preference"
    options: list  # e.g., ["Vegetarian", "Non-Vegetarian"]

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image: str
    event_date: str  # YYYY-MM-DD format
    event_time: str  # HH:MM format
    amount: float  # Used for per_villa or per_person (uniform) pricing
    payment_type: str  # "per_villa" or "per_person"
    per_person_type: str = "uniform"  # "uniform" (single price) or "adult_child" (separate prices)
    adult_price: Optional[float] = None  # Price per adult when per_person_type is "adult_child"
    child_price: Optional[float] = None  # Price per child when per_person_type is "adult_child"
    preferences: list = []  # List of EventPreference dicts
    max_registrations: Optional[int] = None  # Optional limit
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EventCreate(BaseModel):
    name: str
    description: str
    image: str
    event_date: str  # YYYY-MM-DD
    event_time: str  # HH:MM
    amount: float  # Used for per_villa or per_person (uniform) pricing
    payment_type: str  # "per_villa" or "per_person"
    per_person_type: str = "uniform"  # "uniform" or "adult_child"
    adult_price: Optional[float] = None  # For adult_child pricing
    child_price: Optional[float] = None  # For adult_child pricing
    preferences: Optional[list] = []  # List of preference objects
    max_registrations: Optional[int] = None

class EventRegistrant(BaseModel):
    name: str
    registrant_type: str = "adult"  # "adult" or "child"
    preferences: dict = {}  # e.g., {"Food Preference": "Vegetarian"}

class EventRegistration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    event_name: str
    user_email: str
    user_name: str
    registrants: list = []  # List of EventRegistrant dicts
    total_amount: float
    payment_method: str = "online"  # "online" (Razorpay) or "offline" (cash/bank transfer)
    payment_status: str = "pending"  # pending, completed, pending_approval
    payment_id: Optional[str] = None
    admin_approved: bool = False  # For offline payments, admin must approve
    approval_note: Optional[str] = None  # Admin can add a note when approving
    status: str = "registered"  # registered, withdrawn
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EventRegistrationCreate(BaseModel):
    event_id: str
    registrants: list  # List of registrant objects with name and preferences
    payment_method: str = "online"  # "online" or "offline"


# ============ INVOICE MODELS ============

# Invoice types
INVOICE_TYPE_CLUBHOUSE = "clubhouse_subscription"
INVOICE_TYPE_MAINTENANCE = "maintenance"

class InvoiceLineItem(BaseModel):
    """Line item for clubhouse subscription invoices (booking-based)"""
    booking_id: str
    booking_date: str
    start_time: str
    end_time: str
    attendee_type: str  # "resident", "external", "coach"
    attendee_count: int
    rate: float  # ₹50 per person per session
    amount: float
    audit_log: list = []  # Copy of booking audit log for proof

class MaintenanceLineItem(BaseModel):
    """Line item for maintenance invoices"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    quantity: float = 1.0
    rate: float = 0.0
    amount: float = 0.0  # quantity * rate

class MaintenanceLineItemCreate(BaseModel):
    description: str
    quantity: float = 1.0
    rate: float = 0.0

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str  # Format: TROA-INV-YYYYMM-XXXXX or TROA-MAINT-YYYYMM-XXXXX
    invoice_type: str = INVOICE_TYPE_CLUBHOUSE  # "clubhouse_subscription" or "maintenance"
    
    # Villa details (primary association)
    villa_number: str = ""  # Villa this invoice is raised against
    
    # User details (for display and payment tracking)
    user_email: str = ""  # Primary contact email (may be empty for villa-based invoices)
    user_name: str = ""
    user_villa: Optional[str] = None  # Deprecated - use villa_number instead
    
    # Amenity details (for clubhouse_subscription type)
    amenity_id: str = ""
    amenity_name: str = ""
    
    # Period (for clubhouse_subscription type)
    month: int = 0  # 1-12
    year: int = 0
    
    # Line items for clubhouse subscription invoices
    line_items: list = []  # List of InvoiceLineItem dicts
    resident_sessions_count: int = 0
    resident_amount_raw: float = 0.0  # Before cap
    resident_amount_capped: float = 0.0  # After ₹300 cap per amenity
    guest_amount: float = 0.0
    coach_amount: float = 0.0
    
    # Line items for maintenance invoices
    maintenance_line_items: list = []  # List of MaintenanceLineItem dicts
    
    # Amounts
    subtotal: float = 0.0  # Sum of all line items
    discount_type: str = "none"  # "none", "percentage", "fixed"
    discount_value: float = 0.0  # Percentage (0-100) or fixed amount
    discount_amount: float = 0.0  # Calculated discount amount
    adjustment: float = 0.0  # Manual adjustment by manager (can be negative)
    adjustment_reason: Optional[str] = None
    total_amount: float = 0.0  # subtotal - discount_amount + adjustment
    
    # Payment
    payment_status: str = "pending"  # pending, paid, cancelled
    payment_method: Optional[str] = None  # razorpay, offline
    payment_id: Optional[str] = None
    payment_date: Optional[datetime] = None
    
    # Dates
    due_date: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=20))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Created by
    created_by_email: str = ""
    created_by_name: str = ""
    
    # Audit log
    audit_log: list = []  # List of InvoiceAuditEntry dicts

class InvoiceCreate(BaseModel):
    """Create clubhouse subscription invoice"""
    user_email: str
    amenity_id: str
    month: int  # 1-12
    year: int

class MaintenanceInvoiceCreate(BaseModel):
    """Create maintenance invoice"""
    villa_number: str
    line_items: List[MaintenanceLineItemCreate]
    discount_type: str = "none"  # "none", "percentage", "fixed"
    discount_value: float = 0.0
    due_days: int = 20  # Number of days until due (configurable)
    notes: Optional[str] = None

class InvoiceUpdate(BaseModel):
    new_total_amount: Optional[float] = None  # Override total amount
    adjustment_reason: Optional[str] = None

class InvoiceAuditEntry(BaseModel):
    action: str  # "created", "amount_modified", "payment_received", "cancelled"
    timestamp: str
    by_email: str
    by_name: str
    details: str
    previous_amount: Optional[float] = None
    new_amount: Optional[float] = None

class MultiInvoicePayment(BaseModel):
    """Pay multiple invoices at once"""
    invoice_ids: List[str]
    payment_method: str = "online"  # "online" or "offline"
