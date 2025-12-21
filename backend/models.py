from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
import uuid

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
    role: str = "user"  # admin, manager, user
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
    role: str = "user"  # admin, manager, user
    villa_number: str = ""

class UserUpdate(BaseModel):
    role: Optional[str] = None  # admin, manager, user
    name: Optional[str] = None
    villa_number: Optional[str] = None
    picture: Optional[str] = None
    new_password: Optional[str] = None  # For password reset by admin
    email_verified: Optional[bool] = None  # Admin can manually verify/unverify

class AmenityBooking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amenity_id: str
    amenity_name: str
    booked_by_email: str
    booked_by_name: str
    booking_date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format (24-hour)
    end_time: str  # HH:MM format (24-hour)
    duration_minutes: int  # 30 or 60
    additional_guests: list = []  # List of guest names (1-3 users)
    status: str = "confirmed"  # confirmed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AmenityBookingCreate(BaseModel):
    amenity_id: str
    amenity_name: str
    booking_date: str  # YYYY-MM-DD
    start_time: str  # HH:MM (24-hour)
    duration_minutes: int  # 30 or 60 minutes
    additional_guests: Optional[list] = []  # Optional list of guest names

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
