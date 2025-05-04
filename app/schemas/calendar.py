from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CalendarEventBase(BaseModel):
    """Base schema for calendar events."""
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: str = Field(..., description="Event start time in ISO format")
    end_time: str = Field(..., description="Event end time in ISO format")
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    location: Optional[str] = Field(None, description="Event location")

class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a new calendar event."""
    pass

class CalendarEventUpdate(CalendarEventBase):
    """Schema for updating an existing calendar event."""
    title: Optional[str] = Field(None, description="Event title")
    start_time: Optional[str] = Field(None, description="Event start time in ISO format")
    end_time: Optional[str] = Field(None, description="Event end time in ISO format")

class CalendarEvent(CalendarEventBase):
    """Schema for a calendar event."""
    id: str = Field(..., description="Event ID")
    user_id: str = Field(..., description="User ID")
    created_at: str = Field(..., description="Creation timestamp in ISO format")
    updated_at: str = Field(..., description="Last update timestamp in ISO format")

    class Config:
        from_attributes = True
