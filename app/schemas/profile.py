from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional
from datetime import datetime


class ProfileBase(BaseModel):
    """Base schema for user profile data"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[UUID4] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a user profile"""
    email: EmailStr
    user_id: str


class ProfileUpdate(ProfileBase):
    """Schema for updating a user profile"""
    pass


class ProfileInDBBase(ProfileBase):
    """Schema for profile as stored in database"""
    id: UUID4
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Profile(ProfileInDBBase):
    """Profile schema returned to client"""
    pass