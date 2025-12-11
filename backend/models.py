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
    provider: str = "google"  # google, facebook
    role: str = "user"  # admin, manager, user
    is_admin: bool = False  # Deprecated - use role instead
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None
    provider: str = "google"

class UserUpdate(BaseModel):
    role: str  # admin, manager, user

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
    additional_users: list = []  # List of email addresses (1-3 users)
    status: str = "confirmed"  # confirmed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AmenityBookingCreate(BaseModel):
    amenity_id: str
    amenity_name: str
    booking_date: str  # YYYY-MM-DD
    start_time: str  # HH:MM (24-hour)
    duration_minutes: int  # 30 or 60 minutes
    additional_users: Optional[list] = []  # Optional list of email addresses

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

class UserUpdate(BaseModel):
    role: str  # admin, manager, user
