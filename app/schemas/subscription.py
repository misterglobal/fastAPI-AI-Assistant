from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime

class SubscriptionBase(BaseModel):
    """Base model for subscription."""
    plan_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    organization_id: UUID4

class SubscriptionCreate(SubscriptionBase):
    """Model for creating a new subscription."""
    user_id: str

class SubscriptionUpdate(BaseModel):
    """Model for updating a subscription."""
    plan_id: Optional[str] = None
    status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

class Subscription(SubscriptionBase):
    """Full subscription model."""
    id: UUID4
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True