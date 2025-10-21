"""
Signal model for analytics signals.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base

class Signal(Base):
    """Analytics signal model."""
    
    __tablename__ = "signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    market = Column(String(50), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)  # edge, value, arbitrage
    metrics = Column(JSON, nullable=False)  # calculated metrics
    implied_probability = Column(Float, nullable=False)
    fair_odds = Column(Float, nullable=False)
    best_book_odds = Column(Float, nullable=False)
    edge = Column(Float, nullable=False, index=True)
    confidence = Column(Float, nullable=True)
    risk_note = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    model_version = Column(String(20), nullable=True)
    status = Column(String(20), default="active", index=True)  # active, expired, invalidated
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationship
    event = relationship("Event", back_populates="signals")
    
    def __repr__(self):
        return f"<Signal(id={self.id}, {self.market} edge={self.edge:.3f})>"
