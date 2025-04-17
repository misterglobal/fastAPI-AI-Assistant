from pydantic import BaseModel, Field, UUID4, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
import json

class AgentConfigBase(BaseModel):
    """Base model for agent configuration."""
    name: str
    greeting: str
    goodbye: str
    voice_id: Optional[str] = None
    system_prompt: str
    business_hours: Dict[str, Any]
    transfer_directory: Optional[Dict[str, Any]] = None
    calendar_integration: Optional[Dict[str, Any]] = None
    phone_number: str
    organization_id: UUID4

class AgentConfigCreate(AgentConfigBase):
    """Model for creating a new agent configuration."""
    @validator('business_hours')
    def validate_business_hours(cls, v):
        # Ensure business_hours is a valid json format or dictionary
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("business_hours must be a valid JSON string")
        return v

class AgentConfigUpdate(BaseModel):
    """Model for updating an agent configuration."""
    name: Optional[str] = None
    greeting: Optional[str] = None
    goodbye: Optional[str] = None
    voice_id: Optional[str] = None
    system_prompt: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    transfer_directory: Optional[Dict[str, Any]] = None
    calendar_integration: Optional[Dict[str, Any]] = None
    phone_number: Optional[str] = None

class AgentConfig(AgentConfigBase):
    """Full agent configuration model."""
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True