"""
Production configuration for BetFlow Engine MVP
Focused on football pre-match Over/Under 2.5 markets
"""
import os
from typing import List, Dict, Any
from pydantic import BaseSettings, Field


class ProductionConfig(BaseSettings):
    """Production configuration optimized for Render deployment"""
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # API Configuration
    api_rate_limit: int = Field(default=100, env="API_RATE_LIMIT")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    admin_email: str = Field(default="admin@betflow-engine.com", env="ADMIN_EMAIL")
    
    # Provider Configuration
    providers_odds_api_key: str = Field(default="", env="PROVIDERS_ODDS_API_KEY")
    providers_sports_monks_key: str = Field(default="", env="PROVIDERS_SPORTS_MONKS_KEY")
    
    # Worker Configuration
    n8n_webhook_url: str = Field(..., env="N8N_WEBHOOK_URL")
    
    # Environment
    environment: str = Field(default="production", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # MVP Focus: Football Over/Under 2.5
    target_sport: str = "football"
    target_markets: List[str] = ["over_under_2_5"]
    target_leagues: List[str] = [
        "premier-league",
        "championship", 
        "league-one",
        "league-two",
        "scottish-premiership",
        "bundesliga",
        "serie-a",
        "la-liga",
        "ligue-1",
        "eredivisie"
    ]
    
    # Risk Management
    max_edge_threshold: float = 0.15  # 15% max edge
    min_edge_threshold: float = 0.02  # 2% min edge
    max_stake_percentage: float = 0.02  # 2% of bankroll max
    stop_loss_percentage: float = 0.10  # 10% stop loss
    
    # Data Collection
    odds_update_interval: int = 300  # 5 minutes
    signal_compute_interval: int = 600  # 10 minutes
    backtest_days: int = 14  # 2 weeks backtest
    
    # Cache Configuration
    odds_cache_ttl: int = 300  # 5 minutes
    signals_cache_ttl: int = 600  # 10 minutes
    
    # Monitoring
    prometheus_enabled: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Football-specific market normalization
FOOTBALL_MARKET_MAPPING = {
    "over_under_2_5": {
        "normalized_name": "Over/Under 2.5 Goals",
        "selections": {
            "over": "Over 2.5",
            "under": "Under 2.5"
        },
        "bookmaker_mappings": {
            "bet365": "Over/Under 2.5 Goals",
            "william_hill": "Total Goals 2.5",
            "paddy_power": "Over/Under 2.5",
            "sky_bet": "Total Goals 2.5"
        }
    }
}

# League priority for MVP (highest liquidity first)
LEAGUE_PRIORITY = [
    "premier-league",
    "championship", 
    "bundesliga",
    "serie-a",
    "la-liga",
    "ligue-1",
    "scottish-premiership",
    "eredivisie",
    "league-one",
    "league-two"
]

# Risk limits per league
LEAGUE_RISK_LIMITS = {
    "premier-league": {"max_stake": 0.03, "min_confidence": 0.7},
    "championship": {"max_stake": 0.025, "min_confidence": 0.65},
    "bundesliga": {"max_stake": 0.025, "min_confidence": 0.65},
    "serie-a": {"max_stake": 0.025, "min_confidence": 0.65},
    "la-liga": {"max_stake": 0.025, "min_confidence": 0.65},
    "ligue-1": {"max_stake": 0.02, "min_confidence": 0.6},
    "scottish-premiership": {"max_stake": 0.015, "min_confidence": 0.55},
    "eredivisie": {"max_stake": 0.015, "min_confidence": 0.55},
    "league-one": {"max_stake": 0.01, "min_confidence": 0.5},
    "league-two": {"max_stake": 0.01, "min_confidence": 0.45}
}
