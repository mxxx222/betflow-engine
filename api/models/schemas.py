"""
Pydantic schemas for API request/response models.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID

# Health check
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

# Event schemas
class EventResponse(BaseModel):
    id: UUID
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: datetime
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    weather: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Odds schemas
class OddsResponse(BaseModel):
    id: UUID
    event_id: UUID
    book: str
    market: str
    selection: str
    price: float
    line: Optional[float] = None
    implied_probability: Optional[float] = None
    vig: Optional[float] = None
    fetched_at: datetime
    
    class Config:
        from_attributes = True

# Signal schemas
class SignalResponse(BaseModel):
    id: UUID
    event_id: UUID
    market: str
    signal_type: str
    implied_probability: float
    fair_odds: float
    best_book_odds: float
    edge: float
    confidence: Optional[float] = None
    risk_note: Optional[str] = None
    explanation: Optional[str] = None
    model_version: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SignalQuery(BaseModel):
    """Signal query parameters."""
    min_edge: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum edge threshold")
    max_edge: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum edge threshold")
    markets: Optional[List[str]] = Field(None, description="Filter by market types")
    sports: Optional[List[str]] = Field(None, description="Filter by sports")
    leagues: Optional[List[str]] = Field(None, description="Filter by leagues")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")
    status: Optional[str] = Field("active", description="Signal status filter")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")
    offset: Optional[int] = Field(0, ge=0, description="Result offset")
    
    @validator('max_edge')
    def max_edge_must_be_greater_than_min(cls, v, values):
        if v is not None and 'min_edge' in values and values['min_edge'] is not None:
            if v <= values['min_edge']:
                raise ValueError('max_edge must be greater than min_edge')
        return v

# Webhook schemas
class WebhookPayload(BaseModel):
    """Webhook payload for data ingestion."""
    provider: str
    data_type: str  # events, odds, results
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "odds_api",
                "data_type": "odds",
                "payload": {
                    "event_id": "evt_123",
                    "market": "1X2",
                    "book": "bet365",
                    "odds": 1.85
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }

# Model status schemas
class ModelStatusResponse(BaseModel):
    """Model status and information."""
    models: List[Dict[str, Any]]
    last_updated: datetime
    total_signals: int
    active_signals: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "models": [
                    {
                        "name": "ELO Rating System",
                        "version": "1.2.0",
                        "status": "active",
                        "accuracy": 0.68,
                        "last_trained": "2024-01-01T10:00:00Z"
                    }
                ],
                "last_updated": "2024-01-01T12:00:00Z",
                "total_signals": 1250,
                "active_signals": 45
            }
        }

# Error schemas
class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    status_code: int
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Resource not found",
                "status_code": 404,
                "timestamp": "2024-01-01T12:00:00Z",
                "details": {"resource_id": "evt_123"}
            }
        }

# Compliance schemas
class ComplianceInfo(BaseModel):
    """Compliance information."""
    legal_mode: str = "analytics-only"
    purpose: str = "Educational analytics only"
    restrictions: List[str] = [
        "No betting facilitation",
        "No fund movement",
        "No tips or recommendations",
        "Analytics data only"
    ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "legal_mode": "analytics-only",
                "purpose": "Educational analytics only",
                "restrictions": [
                    "No betting facilitation",
                    "No fund movement", 
                    "No tips or recommendations",
                    "Analytics data only"
                ]
            }
        }
