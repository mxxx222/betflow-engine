"""
Audit log model for compliance tracking.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base

class AuditLog(Base):
    """Audit log model for compliance tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String(100), nullable=False, index=True)  # client, user, system
    action = Column(String(50), nullable=False, index=True)  # create, read, update, delete
    resource = Column(String(100), nullable=False, index=True)  # events, odds, signals
    resource_id = Column(String(100), nullable=True, index=True)
    diff = Column(JSON, nullable=True)  # before/after changes
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, {self.actor} {self.action} {self.resource})>"
