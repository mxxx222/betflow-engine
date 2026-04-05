"""Social sentiment tracking service."""

import asyncio
import logging
import re
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from collections import Counter

import httpx
from crypto_tracker.models.signal import Signal, SignalType


logger = logging.getLogger(__name__)


class SentimentTracker:
    """
    Social sentiment tracking service.
    
    Monitors social platforms for token mentions and sentiment:
    - Twitter/X (via API or scraping)
    - 4chan /biz/ (scraping)
    - Telegram (channel monitoring)
    
    Based on A-TIER strategy: Free social intel with proper filtering
    """
    
    def __init__(
        self,
        twitter_api_key: Optional[str] = None,
        check_interval: int = 600,  # 10 minutes
        min_mention_count: int = 10,
    ):
        """
        Initialize sentiment tracker.
        
        Args:
            twitter_api_key: Twitter API key (optional)
            check_interval: Seconds between checks
            min_mention_count: Minimum mentions to trigger signal
        """
        self.twitter_api_key = twitter_api_key
        self.check_interval = check_interval
        self.min_mention_count = min_mention_count
        
        self.mention_history: Dict[str, List[datetime]] = {}
        self._running = False
        
        # Tracked accounts (smart money on Twitter)
        self.tracked_accounts = [
            "cobie",
            "DegenSpartan", 
            "0xLouisT",
            "Route2FI",
            # Add more trusted accounts
        ]
        
        logger.info(
            f"SentimentTracker initialized: interval={check_interval}s, "
            f"tracking {len(self.tracked_accounts)} accounts"
        )
    
    async def scrape_4chan_biz(self) -> Dict[str, int]:
        """
        Scrape 4chan /biz/ for token mentions.
        
        Returns:
            Dict mapping token tickers to mention counts
        """
        token_mentions = Counter()
        
        try:
            # Fetch /biz/ catalog
            url = "https://a.4cdn.org/biz/catalog.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    catalog = response.json()
                    
                    # Extract token tickers from thread titles and posts
                    for page in catalog:
                        for thread in page.get("threads", []):
                            # Check subject and comment
                            text = f"{thread.get('sub', '')} {thread.get('com', '')}"
                            
                            # Extract potential tickers (all caps 3-5 letters with $)
                            tickers = re.findall(r'\$([A-Z]{3,5})\b', text)
                            
                            for ticker in tickers:
                                # Filter out common false positives
                                if ticker not in ["USD", "BTC", "ETH", "SOL", "LINK"]:
                                    token_mentions[ticker] += 1
            
            logger.debug(f"4chan scrape found {len(token_mentions)} token mentions")
        
        except Exception as e:
            logger.error(f"Error scraping 4chan: {e}")
        
        return dict(token_mentions)
    
    async def fetch_twitter_mentions(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch Twitter mentions for keywords.
        
        Args:
            keywords: List of keywords/tickers to search
            
        Returns:
            List of tweet data
        """
        tweets = []
        
        if not self.twitter_api_key:
            logger.warning("Twitter API key not configured")
            return tweets
        
        try:
            # In real implementation, would call Twitter API v2
            # For now, return empty list (mock)
            pass
        except Exception as e:
            logger.error(f"Error fetching Twitter mentions: {e}")
        
        return tweets
    
    async def check_smart_money_tweets(self) -> List[Dict[str, Any]]:
        """
        Check tweets from tracked smart money accounts.
        
        Returns:
            List of relevant tweets
        """
        relevant_tweets = []
        
        if not self.twitter_api_key:
            return relevant_tweets
        
        try:
            # In real implementation, would fetch recent tweets from tracked accounts
            # and parse for token mentions
            pass
        except Exception as e:
            logger.error(f"Error checking smart money tweets: {e}")
        
        return relevant_tweets
    
    def analyze_sentiment(
        self,
        token_symbol: str,
        mentions: int,
        timeframe_hours: float = 1.0
    ) -> Optional[Signal]:
        """
        Analyze sentiment data and generate signal if significant.
        
        Args:
            token_symbol: Token symbol
            mentions: Number of mentions
            timeframe_hours: Timeframe for mentions
            
        Returns:
            Signal if sentiment is significant, None otherwise
        """
        # Check if meets minimum threshold
        if mentions < self.min_mention_count:
            return None
        
        # Calculate mention velocity (mentions per hour)
        mention_velocity = mentions / timeframe_hours
        
        # Calculate confidence and edge
        confidence = min(0.9, 0.5 + (mention_velocity / 50.0))
        edge_score = min(10.0, 4.0 + (mention_velocity / 10.0))
        
        # Create signal
        signal = Signal(
            id=f"sentiment_{token_symbol}_{int(datetime.utcnow().timestamp())}",
            signal_type=SignalType.SOCIAL_BUZZ,
            token_address="",  # Will be resolved by other services
            token_symbol=token_symbol,
            chain="unknown",  # Will be determined by other services
            confidence=confidence,
            edge_score=edge_score,
            sources=["sentiment_tracker"],
            source_count=1,
            risk_level="medium",
            rug_check_passed=False,
            contract_verified=False,
            recommended_action="watch",
            alert_message=(
                f"📱 SOCIAL BUZZ: ${token_symbol}\n"
                f"Mentions: {mentions} in {timeframe_hours:.1f}h\n"
                f"Velocity: {mention_velocity:.1f}/hour"
            ),
            metadata={
                "mentions": mentions,
                "timeframe_hours": timeframe_hours,
                "mention_velocity": mention_velocity,
            }
        )
        
        return signal
    
    def track_mention(self, token_symbol: str) -> None:
        """Track a mention of a token."""
        token_symbol = token_symbol.upper()
        
        if token_symbol not in self.mention_history:
            self.mention_history[token_symbol] = []
        
        self.mention_history[token_symbol].append(datetime.utcnow())
    
    def get_mention_count(
        self, token_symbol: str, hours: float = 1.0
    ) -> int:
        """Get number of mentions in last N hours."""
        token_symbol = token_symbol.upper()
        
        if token_symbol not in self.mention_history:
            return 0
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [m for m in self.mention_history[token_symbol] if m > cutoff]
        
        return len(recent)
    
    async def start_monitoring(self, callback=None) -> None:
        """
        Start continuous sentiment monitoring.
        
        Args:
            callback: Optional callback function for new signals
        """
        self._running = True
        logger.info("Started sentiment monitoring")
        
        while self._running:
            try:
                # Scrape 4chan
                biz_mentions = await self.scrape_4chan_biz()
                
                # Track mentions
                for token, count in biz_mentions.items():
                    for _ in range(count):
                        self.track_mention(token)
                
                # Check smart money Twitter
                smart_tweets = await self.check_smart_money_tweets()
                
                # Analyze high-velocity tokens
                for token in self.mention_history.keys():
                    count_1h = self.get_mention_count(token, hours=1.0)
                    
                    if count_1h >= self.min_mention_count:
                        signal = self.analyze_sentiment(token, count_1h, 1.0)
                        
                        if signal and callback:
                            await callback(signal)
                
                # Cleanup old mentions (keep last 24h)
                cutoff = datetime.utcnow() - timedelta(hours=24)
                for token in list(self.mention_history.keys()):
                    self.mention_history[token] = [
                        m for m in self.mention_history[token] if m > cutoff
                    ]
                    if not self.mention_history[token]:
                        del self.mention_history[token]
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in sentiment monitoring loop: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self) -> None:
        """Stop sentiment monitoring."""
        self._running = False
        logger.info("Stopped sentiment monitoring")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sentiment tracker statistics."""
        total_mentions = sum(
            len(mentions) for mentions in self.mention_history.values()
        )
        
        return {
            "tracked_tokens": len(self.mention_history),
            "total_mentions_24h": total_mentions,
            "monitoring_active": self._running,
            "tracked_accounts": len(self.tracked_accounts),
        }
