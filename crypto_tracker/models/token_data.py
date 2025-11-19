"""Token data models for DEX tracking."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """Comprehensive token data from DEX."""
    
    # Identifiers
    address: str = Field(..., description="Token contract address")
    symbol: str = Field(..., description="Token symbol")
    name: Optional[str] = Field(None, description="Token name")
    chain: str = Field(..., description="Blockchain")
    
    # Market data
    price: float = Field(..., description="Current price in USD")
    market_cap: Optional[float] = Field(None, description="Market cap in USD")
    liquidity: Optional[float] = Field(None, description="Total liquidity in USD")
    volume_24h: float = Field(..., description="24h trading volume in USD")
    volume_1h: Optional[float] = Field(None, description="1h trading volume in USD")
    
    # Price changes
    price_change_1h: Optional[float] = Field(None, description="1h price change %")
    price_change_6h: Optional[float] = Field(None, description="6h price change %")
    price_change_24h: Optional[float] = Field(None, description="24h price change %")
    
    # Token metrics
    age_hours: Optional[float] = Field(None, description="Token age in hours")
    holder_count: Optional[int] = Field(None, description="Number of holders")
    top_10_holders_pct: Optional[float] = Field(None, description="% held by top 10")
    
    # Liquidity info
    liquidity_locked: bool = Field(False, description="Is liquidity locked")
    liquidity_lock_duration: Optional[str] = Field(None, description="Lock duration")
    
    # Contract safety
    contract_verified: bool = Field(False, description="Contract verified on explorer")
    is_honeypot: bool = Field(False, description="Detected as honeypot")
    has_hidden_mint: bool = Field(False, description="Has hidden mint function")
    has_proxy: bool = Field(False, description="Is proxy contract")
    is_renounced: bool = Field(False, description="Ownership renounced")
    
    # DEX info
    dex: str = Field(..., description="Primary DEX")
    pair_address: Optional[str] = Field(None, description="Pair contract address")
    
    # Social
    telegram_size: Optional[int] = Field(None, description="Telegram member count")
    twitter_exists: bool = Field(False, description="Has Twitter account")
    
    # Links
    dexscreener_link: Optional[str] = Field(None, description="DEXScreener URL")
    dextools_link: Optional[str] = Field(None, description="DEXTools URL")
    explorer_link: Optional[str] = Field(None, description="Blockchain explorer URL")
    
    # Metadata
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def calculate_risk_level(self) -> str:
        """Calculate risk level based on token properties."""
        risk_score = 0
        
        # Age risk
        if self.age_hours and self.age_hours < 1:
            risk_score += 3  # Ultra early = extreme risk
        elif self.age_hours and self.age_hours < 6:
            risk_score += 2  # Very early = high risk
        elif self.age_hours and self.age_hours < 24:
            risk_score += 1  # Early = medium risk
        
        # Holder concentration risk
        if self.top_10_holders_pct and self.top_10_holders_pct > 60:
            risk_score += 3
        elif self.top_10_holders_pct and self.top_10_holders_pct > 40:
            risk_score += 2
        
        # Contract safety risk
        if self.is_honeypot:
            risk_score += 5
        if self.has_hidden_mint:
            risk_score += 4
        if not self.contract_verified:
            risk_score += 2
        if not self.liquidity_locked:
            risk_score += 3
        if not self.is_renounced:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 10:
            return "extreme"
        elif risk_score >= 7:
            return "high"
        elif risk_score >= 4:
            return "medium"
        else:
            return "low"
    
    def calculate_edge_score(self) -> float:
        """Calculate edge score 0-10 based on token metrics."""
        score = 5.0  # Start neutral
        
        # Volume/liquidity ratio (good hype indicator)
        if self.liquidity and self.volume_24h:
            vol_liq_ratio = self.volume_24h / self.liquidity
            if vol_liq_ratio > 2.0:
                score += 2.0
            elif vol_liq_ratio > 1.0:
                score += 1.0
            elif vol_liq_ratio < 0.5:
                score -= 1.0
        
        # Price momentum
        if self.price_change_1h and self.price_change_1h > 20:
            score += 1.5
        elif self.price_change_1h and self.price_change_1h > 10:
            score += 1.0
        
        # Safety factors
        if self.liquidity_locked:
            score += 1.0
        if self.is_renounced:
            score += 0.5
        if self.contract_verified:
            score += 0.5
        
        # Negative factors
        if self.is_honeypot:
            score = 0.0  # Automatic zero
        if self.has_hidden_mint:
            score -= 3.0
        if self.top_10_holders_pct and self.top_10_holders_pct > 50:
            score -= 2.0
        
        return max(0.0, min(10.0, score))
