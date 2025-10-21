"""
Model tracking for analytics models.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base

class Model(Base):
    """Analytics model tracking."""
    
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)  # elo, poisson, ev, etc.
    parameters = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    training_data_size = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=True)
    last_trained = Column(DateTime, nullable=True)
    status = Column(String(20), default="active", index=True)  # active, training, inactive
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Model(id={self.id}, {self.name} v{self.version})>"
