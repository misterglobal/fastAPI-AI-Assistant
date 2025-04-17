from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime

class OrganizationBase(BaseModel):
    """Base model for organization."""
    name: str
    settings: Optional[Dict[str, Any]] = None

class OrganizationCreate(OrganizationBase):
    """Model for creating a new organization."""
    owner_id: Optional[str] = None  # Will be set from the authenticated user

class OrganizationUpdate(BaseModel):
    """Model for updating an organization."""
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class Organization(OrganizationBase):
    """Full organization model."""
    id: UUID4
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True