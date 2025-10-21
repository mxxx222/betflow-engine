"""
API key model for authentication.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base

class APIKey(Base):
    """API key model for authentication."""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client = Column(String(100), nullable=False, index=True)
    hash = Column(String(255), nullable=False, unique=True, index=True)
    scope = Column(String(50), default="read", index=True)  # read, write, admin
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    description = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, client={self.client}, scope={self.scope})>"
