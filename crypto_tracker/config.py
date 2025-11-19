"""Configuration for crypto tracker."""

from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class CryptoTrackerConfig(BaseSettings):
    """Configuration for crypto tracking system."""
    
    # API Keys
    etherscan_api_key: Optional[str] = Field(None, env="ETHERSCAN_API_KEY")
    moralis_api_key: Optional[str] = Field(None, env="MORALIS_API_KEY")
    twitter_api_key: Optional[str] = Field(None, env="TWITTER_API_KEY")
    alchemy_api_key: Optional[str] = Field(None, env="ALCHEMY_API_KEY")
    
    # Alert Configuration
    discord_webhook: Optional[str] = Field(None, env="DISCORD_WEBHOOK_URL")
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")
    
    # Tracking Configuration
    tracked_chains: List[str] = Field(
        default=["eth", "sol", "base"],
        description="Blockchains to monitor"
    )
    
    # Whale Tracker Settings
    whale_min_tx_value: float = Field(
        default=10000.0,
        description="Minimum whale transaction value (USD)"
    )
    whale_check_interval: int = Field(
        default=60,
        description="Whale tracker check interval (seconds)"
    )
    
    # DEX Scraper Settings
    dex_min_liquidity: float = Field(
        default=10000.0,
        description="Minimum liquidity to track (USD)"
    )
    dex_check_interval: int = Field(
        default=300,
        description="DEX scraper check interval (seconds)"
    )
    
    # Sentiment Tracker Settings
    sentiment_min_mentions: int = Field(
        default=10,
        description="Minimum mentions to trigger signal"
    )
    sentiment_check_interval: int = Field(
        default=600,
        description="Sentiment tracker check interval (seconds)"
    )
    
    # Alert Manager Settings
    alert_min_sources: int = Field(
        default=3,
        description="Minimum sources for multi-signal confirmation"
    )
    alert_confirmation_window: int = Field(
        default=3600,
        description="Time window for signal correlation (seconds)"
    )
    
    # Risk Management
    max_position_size_pct: float = Field(
        default=2.0,
        description="Maximum position size as % of portfolio"
    )
    stop_loss_pct: float = Field(
        default=30.0,
        description="Stop loss percentage"
    )
    daily_loss_limit_pct: float = Field(
        default=5.0,
        description="Daily loss limit as % of portfolio"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


class TrackedWhaleConfig(BaseModel):
    """Configuration for a tracked whale wallet."""
    
    address: str = Field(..., description="Wallet address")
    chain: str = Field(..., description="Primary chain")
    label: Optional[str] = Field(None, description="Wallet label")
    min_tx_value: Optional[float] = Field(
        None,
        description="Override min transaction value"
    )


# Default tracked whales (examples - replace with real addresses)
DEFAULT_TRACKED_WHALES = [
    TrackedWhaleConfig(
        address="0x0000000000000000000000000000000000000001",
        chain="eth",
        label="Example Whale 1"
    ),
    TrackedWhaleConfig(
        address="0x0000000000000000000000000000000000000002",
        chain="eth",
        label="Example Whale 2"
    ),
    # Add more whales here
]
