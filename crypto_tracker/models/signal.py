"""Signal models for multi-source confirmation system."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SignalType(str, Enum):
    """Types of trading signals."""
    
    WHALE_BUY = "whale_buy"
    WHALE_SELL = "whale_sell"
    VOLUME_SPIKE = "volume_spike"
    NEW_TOKEN = "new_token"
    SOCIAL_BUZZ = "social_buzz"
    LIQUIDITY_ADD = "liquidity_add"
    PRICE_CHANGE = "price_change"
    MULTI_WHALE = "multi_whale"  # Multiple whales buying same token


class Signal(BaseModel):
    """Trading signal with multi-source confirmation."""
    
    id: str = Field(..., description="Unique signal identifier")
    signal_type: SignalType = Field(..., description="Type of signal")
    token_address: str = Field(..., description="Token contract address")
    token_symbol: Optional[str] = Field(None, description="Token symbol")
    chain: str = Field(..., description="Blockchain (eth, sol, base, etc.)")
    
    # Signal strength
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    edge_score: float = Field(..., ge=0.0, le=10.0, description="Edge score 0-10")
    
    # Data sources that contributed
    sources: list[str] = Field(
        default_factory=list,
        description="Data sources (whale_tracker, dex_scraper, sentiment, etc.)"
    )
    source_count: int = Field(..., ge=1, description="Number of confirming sources")
    
    # Market data
    market_cap: Optional[float] = Field(None, description="Market cap in USD")
    volume_24h: Optional[float] = Field(None, description="24h volume in USD")
    price: Optional[float] = Field(None, description="Current price")
    liquidity: Optional[float] = Field(None, description="Liquidity in USD")
    
    # Risk assessment
    risk_level: str = Field(..., description="Risk level: low, medium, high, extreme")
    rug_check_passed: bool = Field(False, description="Passed rug check")
    contract_verified: bool = Field(False, description="Contract verified on explorer")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    
    # Action recommendations
    recommended_action: str = Field(..., description="watch, small_buy, exit, etc.")
    position_size_pct: Optional[float] = Field(None, description="Recommended position size %")
    
    # Alert info
    alert_message: str = Field(..., description="Human-readable alert message")
    dex_link: Optional[str] = Field(None, description="DEXScreener/DEXTools link")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SignalFilter(BaseModel):
    """Filters for signal queries."""
    
    min_confidence: float = Field(0.7, ge=0.0, le=1.0)
    min_edge_score: float = Field(7.0, ge=0.0, le=10.0)
    min_sources: int = Field(3, ge=1)
    max_market_cap: Optional[float] = Field(None, description="Max market cap filter")
    chains: Optional[list[str]] = Field(None, description="Filter by chains")
    signal_types: Optional[list[SignalType]] = Field(None)
    
    def matches(self, signal: Signal) -> bool:
        """Check if signal matches filter criteria."""
        if signal.confidence < self.min_confidence:
            return False
        if signal.edge_score < self.min_edge_score:
            return False
        if signal.source_count < self.min_sources:
            return False
        if self.max_market_cap and signal.market_cap and signal.market_cap > self.max_market_cap:
            return False
        if self.chains and signal.chain not in self.chains:
            return False
        if self.signal_types and signal.signal_type not in self.signal_types:
            return False
        return True
