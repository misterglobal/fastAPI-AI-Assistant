from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime


class CallLogBase(BaseModel):
    """Base schema for call log data"""
    agent_id: UUID4
    call_sid: str
    from_number: str
    to_number: str
    status: str
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None


class CallLogCreate(CallLogBase):
    """Schema for creating a call log"""
    organization_id: UUID4


class CallLogUpdate(BaseModel):
    """Schema for updating a call log"""
    status: Optional[str] = None
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None


class CallLogInDBBase(CallLogBase):
    """Schema for call log as stored in database"""
    id: UUID4
    organization_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CallLog(CallLogInDBBase):
    """Call log schema returned to client"""
    pass