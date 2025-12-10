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
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MembershipApplicationCreate(BaseModel):
    firstName: str
    lastName: Optional[str] = None
    email: EmailStr
    phone: str
    villaNo: str
    message: Optional[str] = None
