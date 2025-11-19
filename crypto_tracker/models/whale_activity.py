"""Whale activity tracking models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WhaleActivity(BaseModel):
    """Whale wallet transaction activity."""
    
    id: str = Field(..., description="Unique activity ID")
    wallet_address: str = Field(..., description="Whale wallet address")
    wallet_name: Optional[str] = Field(None, description="Known whale name/label")
    
    # Transaction details
    tx_hash: str = Field(..., description="Transaction hash")
    chain: str = Field(..., description="Blockchain")
    action: str = Field(..., description="BUY or SELL")
    
    # Token details
    token_address: str = Field(..., description="Token contract address")
    token_symbol: Optional[str] = Field(None, description="Token symbol")
    
    # Transaction amounts
    amount_usd: float = Field(..., description="Transaction value in USD")
    amount_tokens: Optional[float] = Field(None, description="Number of tokens")
    
    # Context
    is_new_token: bool = Field(False, description="First time buying this token")
    whale_portfolio_pct: Optional[float] = Field(None, description="% of whale's portfolio")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    token_age_hours: Optional[float] = Field(None, description="How old is the token")
    
    # DEX info
    dex: Optional[str] = Field(None, description="DEX used (Uniswap, Raydium, etc.)")
    dex_link: Optional[str] = Field(None, description="Transaction explorer link")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WhaleWallet(BaseModel):
    """Tracked whale wallet configuration."""
    
    address: str = Field(..., description="Wallet address")
    chain: str = Field(..., description="Primary chain")
    label: Optional[str] = Field(None, description="Wallet label/name")
    
    # Tracking config
    min_tx_value: float = Field(10000.0, description="Minimum transaction value to alert (USD)")
    track_buys: bool = Field(True, description="Alert on buys")
    track_sells: bool = Field(True, description="Alert on sells")
    
    # Stats
    win_rate: Optional[float] = Field(None, description="Historical win rate %")
    avg_return: Optional[float] = Field(None, description="Average return %")
    total_trades: Optional[int] = Field(None, description="Total tracked trades")
    
    # Metadata
    added_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = Field(None, description="Last transaction time")
    notes: Optional[str] = Field(None, description="Notes about this whale")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
