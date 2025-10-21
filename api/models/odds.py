"""
Odds model for betting odds data.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base

class Odds(Base):
    """Betting odds model."""
    
    __tablename__ = "odds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    book = Column(String(100), nullable=False, index=True)  # bookmaker name
    market = Column(String(50), nullable=False, index=True)  # 1X2, moneyline, totals, etc.
    selection = Column(String(100), nullable=False)  # home, away, draw, over 2.5, etc.
    price = Column(Float, nullable=False)  # decimal odds
    line = Column(Float, nullable=True)  # for spreads, totals
    implied_probability = Column(Float, nullable=True)
    vig = Column(Float, nullable=True)  # overround
    metadata = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship
    event = relationship("Event", back_populates="odds")
    
    def __repr__(self):
        return f"<Odds(id={self.id}, {self.book} {self.market} {self.selection} @ {self.price})>"
