"""Main orchestrator for crypto tracking system."""

import asyncio
import logging
from typing import Optional, List

from crypto_tracker.config import CryptoTrackerConfig, DEFAULT_TRACKED_WHALES
from crypto_tracker.services.whale_tracker import WhaleTracker
from crypto_tracker.services.dex_scraper import DEXScraper
from crypto_tracker.services.sentiment_tracker import SentimentTracker
from crypto_tracker.services.alert_manager import AlertManager
from crypto_tracker.models.signal import Signal
from crypto_tracker.models.whale_activity import WhaleWallet


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoTracker:
    """
    Main crypto tracking orchestrator.
    
    Coordinates whale tracking, DEX scraping, sentiment analysis,
    and multi-signal confirmation for crypto trading intelligence.
    
    Based on veteran OG trader strategy:
    - S-TIER: Whale tracking + DEX automation + Free social intel
    - Multi-signal confirmation (3+ sources)
    - Risk management built-in
    - No full-auto trading (semi-auto alerts only)
    """
    
    def __init__(self, config: Optional[CryptoTrackerConfig] = None):
        """
        Initialize crypto tracker.
        
        Args:
            config: Configuration (loads from .env if not provided)
        """
        self.config = config or CryptoTrackerConfig()
        
        # Initialize services
        self.whale_tracker = WhaleTracker(
            api_keys={
                "etherscan": self.config.etherscan_api_key,
                "moralis": self.config.moralis_api_key,
            },
            min_tx_value=self.config.whale_min_tx_value,
            check_interval=self.config.whale_check_interval,
        )
        
        self.dex_scraper = DEXScraper(
            chains=self.config.tracked_chains,
            check_interval=self.config.dex_check_interval,
            min_liquidity=self.config.dex_min_liquidity,
        )
        
        self.sentiment_tracker = SentimentTracker(
            twitter_api_key=self.config.twitter_api_key,
            check_interval=self.config.sentiment_check_interval,
            min_mention_count=self.config.sentiment_min_mentions,
        )
        
        self.alert_manager = AlertManager(
            discord_webhook=self.config.discord_webhook,
            telegram_bot_token=self.config.telegram_bot_token,
            telegram_chat_id=self.config.telegram_chat_id,
            min_sources=self.config.alert_min_sources,
            confirmation_window=self.config.alert_confirmation_window,
        )
        
        # Add default tracked whales
        for whale_config in DEFAULT_TRACKED_WHALES:
            whale = WhaleWallet(
                address=whale_config.address,
                chain=whale_config.chain,
                label=whale_config.label,
                min_tx_value=whale_config.min_tx_value or self.config.whale_min_tx_value,
            )
            self.whale_tracker.add_wallet(whale)
        
        logger.info("CryptoTracker initialized successfully")
    
    async def handle_signal(self, signal: Signal) -> None:
        """
        Handle incoming signal from any service.
        
        Args:
            signal: Signal to process
        """
        logger.info(
            f"Received signal: {signal.signal_type.value} for "
            f"{signal.token_symbol or signal.token_address[:8]} "
            f"(confidence={signal.confidence:.2f}, edge={signal.edge_score:.1f})"
        )
        
        # Add to alert manager for multi-signal confirmation
        confirmed_signal = self.alert_manager.add_signal(signal)
        
        if confirmed_signal:
            logger.info(
                f"🚨 CONFIRMED SIGNAL: {confirmed_signal.token_symbol} "
                f"({confirmed_signal.source_count} sources, "
                f"edge={confirmed_signal.edge_score:.1f})"
            )
            
            # Send alert through configured channels
            await self.alert_manager.send_alert(confirmed_signal)
    
    async def start(self) -> None:
        """Start all tracking services."""
        logger.info("Starting crypto tracker services...")
        
        # Start all services concurrently
        tasks = [
            self.whale_tracker.start_monitoring(callback=self.handle_signal),
            self.dex_scraper.start_monitoring(callback=self.handle_signal),
            self.sentiment_tracker.start_monitoring(callback=self.handle_signal),
        ]
        
        # Add periodic cleanup task
        async def cleanup_loop():
            while True:
                await asyncio.sleep(3600)  # Every hour
                self.alert_manager.cleanup_old_signals()
                logger.debug("Cleaned up old signals")
        
        tasks.append(cleanup_loop())
        
        logger.info("✅ All crypto tracker services started")
        
        # Run all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def stop(self) -> None:
        """Stop all tracking services."""
        logger.info("Stopping crypto tracker services...")
        self.whale_tracker.stop_monitoring()
        self.dex_scraper.stop_monitoring()
        self.sentiment_tracker.stop_monitoring()
        logger.info("✅ All services stopped")
    
    def get_status(self) -> dict:
        """Get current tracker status and statistics."""
        return {
            "whale_tracker": self.whale_tracker.get_statistics(),
            "dex_scraper": self.dex_scraper.get_statistics(),
            "sentiment_tracker": self.sentiment_tracker.get_statistics(),
            "alert_manager": self.alert_manager.get_statistics(),
            "config": {
                "tracked_chains": self.config.tracked_chains,
                "min_sources": self.config.alert_min_sources,
                "alerts_configured": bool(
                    self.config.discord_webhook or self.config.telegram_bot_token
                ),
            }
        }


async def main():
    """Main entry point for running crypto tracker."""
    logger.info("🚀 Starting BetFlow Crypto Tracker")
    logger.info("=" * 60)
    logger.info("Based on veteran OG trader strategy:")
    logger.info("- Whale wallet tracking (smart money)")
    logger.info("- DEX scraping (new tokens 0-15min)")
    logger.info("- Social sentiment (Twitter, 4chan, Telegram)")
    logger.info("- Multi-signal confirmation (3+ sources)")
    logger.info("=" * 60)
    
    tracker = CryptoTracker()
    
    # Display status
    status = tracker.get_status()
    logger.info(f"Tracking {status['whale_tracker']['tracked_wallets']} whale wallets")
    logger.info(f"Monitoring {status['dex_scraper']['monitored_chains']} chains")
    logger.info(f"Tracking {status['sentiment_tracker']['tracked_accounts']} Twitter accounts")
    
    if not status['config']['alerts_configured']:
        logger.warning("⚠️  No alert channels configured (Discord/Telegram)")
        logger.warning("   Set DISCORD_WEBHOOK_URL or TELEGRAM_BOT_TOKEN in .env")
    
    try:
        await tracker.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        tracker.stop()
        logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
