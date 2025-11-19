"""
Crypto Tracker - Whale Tracking & DEX Scraping System

Advanced crypto trading intelligence platform for tracking smart money,
DEX activity, and social sentiment analysis.

Based on veteran trader insights for edge detection in 2025 crypto markets.
"""

__version__ = "1.0.0"
__author__ = "BetFlow Engine Team"

from crypto_tracker.services.whale_tracker import WhaleTracker
from crypto_tracker.services.dex_scraper import DEXScraper
from crypto_tracker.services.sentiment_tracker import SentimentTracker
from crypto_tracker.services.alert_manager import AlertManager
from crypto_tracker.models.signal import Signal, SignalType
from crypto_tracker.models.whale_activity import WhaleActivity
from crypto_tracker.models.token_data import TokenData

__all__ = [
    "WhaleTracker",
    "DEXScraper",
    "SentimentTracker",
    "AlertManager",
    "Signal",
    "SignalType",
    "WhaleActivity",
    "TokenData",
]
