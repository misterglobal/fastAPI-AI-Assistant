from pydantic import BaseModel, Field, UUID4, EmailStr
from typing import Optional
from datetime import datetime

class GoogleIntegrationBase(BaseModel):
    """Base model for Google integration."""
    email: EmailStr
    access_token: str
    refresh_token: str
    scopes: str
    calendar_id: Optional[str] = None
    availability_days: Optional[str] = None
    availability_start: Optional[str] = None
    availability_end: Optional[str] = None

class GoogleIntegrationCreate(GoogleIntegrationBase):
    """Model for creating a new Google integration."""
    user_id: str

class GoogleIntegrationUpdate(BaseModel):
    """Model for updating a Google integration."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    scopes: Optional[str] = None
    calendar_id: Optional[str] = None
    availability_days: Optional[str] = None
    availability_start: Optional[str] = None
    availability_end: Optional[str] = None

class GoogleIntegration(GoogleIntegrationBase):
    """Full Google integration model."""
    id: UUID4
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True