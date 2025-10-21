"""
Event model for sports events.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base

class Event(Base):
    """Sports event model."""
    
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport = Column(String(50), nullable=False, index=True)
    league = Column(String(100), nullable=False, index=True)
    home_team = Column(String(200), nullable=False)
    away_team = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="scheduled", index=True)  # scheduled, live, finished, cancelled
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    venue = Column(String(200), nullable=True)
    weather = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Event(id={self.id}, {self.home_team} vs {self.away_team})>"
