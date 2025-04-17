from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base_class import Base


class GoogleIntegration(Base):
    __tablename__ = "google_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    scopes = Column(Text, nullable=False)
    calendar_id = Column(String, nullable=True)
    availability_days = Column(String, nullable=True)  # JSON string representation
    availability_start = Column(String, nullable=True)  # Time in HH:MM format
    availability_end = Column(String, nullable=True)  # Time in HH:MM format
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)