from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.db.base_class import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    greeting = Column(Text, nullable=False)
    goodbye = Column(Text, nullable=False)
    voice_id = Column(String, nullable=True)
    system_prompt = Column(Text, nullable=False)
    business_hours = Column(JSONB, nullable=False)
    transfer_directory = Column(JSONB, nullable=True)
    calendar_integration = Column(JSONB, nullable=True)
    phone_number = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)