"""Tests for crypto tracker services."""

import pytest
from datetime import datetime, timedelta

from crypto_tracker.models.signal import Signal, SignalType, SignalFilter
from crypto_tracker.models.whale_activity import WhaleActivity, WhaleWallet
from crypto_tracker.models.token_data import TokenData
from crypto_tracker.services.whale_tracker import WhaleTracker
from crypto_tracker.services.dex_scraper import DEXScraper
from crypto_tracker.services.sentiment_tracker import SentimentTracker
from crypto_tracker.services.alert_manager import AlertManager


class TestSignalModel:
    """Test signal data model."""
    
    def test_signal_creation(self):
        """Test creating a signal."""
        signal = Signal(
            id="test_signal_1",
            signal_type=SignalType.WHALE_BUY,
            token_address="0x1234567890abcdef",
            token_symbol="TEST",
            chain="eth",
            confidence=0.8,
            edge_score=7.5,
            sources=["whale_tracker"],
            source_count=1,
            risk_level="medium",
            recommended_action="watch",
            alert_message="Test alert"
        )
        
        assert signal.id == "test_signal_1"
        assert signal.signal_type == SignalType.WHALE_BUY
        assert signal.confidence == 0.8
        assert signal.edge_score == 7.5
        assert "whale_tracker" in signal.sources
    
    def test_signal_filter(self):
        """Test signal filtering."""
        signal = Signal(
            id="test_signal_1",
            signal_type=SignalType.WHALE_BUY,
            token_address="0x1234567890abcdef",
            token_symbol="TEST",
            chain="eth",
            confidence=0.8,
            edge_score=7.5,
            sources=["whale_tracker", "dex_scraper", "sentiment_tracker"],
            source_count=3,
            risk_level="medium",
            recommended_action="watch",
            alert_message="Test alert"
        )
        
        # Should pass filter
        filter1 = SignalFilter(min_confidence=0.7, min_edge_score=7.0, min_sources=3)
        assert filter1.matches(signal)
        
        # Should fail filter (confidence too low)
        filter2 = SignalFilter(min_confidence=0.9, min_edge_score=7.0, min_sources=3)
        assert not filter2.matches(signal)
        
        # Should fail filter (not enough sources)
        filter3 = SignalFilter(min_confidence=0.7, min_edge_score=7.0, min_sources=4)
        assert not filter3.matches(signal)


class TestWhaleActivity:
    """Test whale activity model."""
    
    def test_whale_activity_creation(self):
        """Test creating whale activity."""
        activity = WhaleActivity(
            id="activity_1",
            wallet_address="0xwhale123",
            wallet_name="Known Whale",
            tx_hash="0xtxhash123",
            chain="eth",
            action="BUY",
            token_address="0xtoken123",
            token_symbol="TOKEN",
            amount_usd=50000.0,
            is_new_token=True
        )
        
        assert activity.wallet_address == "0xwhale123"
        assert activity.action == "BUY"
        assert activity.amount_usd == 50000.0
        assert activity.is_new_token
    
    def test_whale_wallet_config(self):
        """Test whale wallet configuration."""
        wallet = WhaleWallet(
            address="0xwhale123",
            chain="eth",
            label="Test Whale",
            min_tx_value=10000.0,
            track_buys=True,
            track_sells=True
        )
        
        assert wallet.address == "0xwhale123"
        assert wallet.min_tx_value == 10000.0
        assert wallet.track_buys
        assert wallet.track_sells


class TestTokenData:
    """Test token data model."""
    
    def test_token_data_creation(self):
        """Test creating token data."""
        token = TokenData(
            address="0xtoken123",
            symbol="TEST",
            name="Test Token",
            chain="eth",
            price=0.001,
            volume_24h=100000.0,
            liquidity=50000.0,
            dex="uniswap",
            contract_verified=True,
            liquidity_locked=True
        )
        
        assert token.symbol == "TEST"
        assert token.price == 0.001
        assert token.contract_verified
        assert token.liquidity_locked
    
    def test_risk_level_calculation(self):
        """Test risk level calculation."""
        # Low risk token
        safe_token = TokenData(
            address="0xtoken123",
            symbol="SAFE",
            chain="eth",
            price=0.001,
            volume_24h=100000.0,
            liquidity=50000.0,
            dex="uniswap",
            age_hours=48.0,
            contract_verified=True,
            liquidity_locked=True,
            is_renounced=True,
            top_10_holders_pct=20.0
        )
        
        assert safe_token.calculate_risk_level() == "low"
        
        # High risk token
        risky_token = TokenData(
            address="0xtoken456",
            symbol="RISK",
            chain="eth",
            price=0.001,
            volume_24h=100000.0,
            liquidity=50000.0,
            dex="uniswap",
            age_hours=0.5,
            contract_verified=False,
            liquidity_locked=False,
            top_10_holders_pct=70.0
        )
        
        assert risky_token.calculate_risk_level() in ["high", "extreme"]
    
    def test_edge_score_calculation(self):
        """Test edge score calculation."""
        token = TokenData(
            address="0xtoken123",
            symbol="EDGE",
            chain="eth",
            price=0.001,
            volume_24h=200000.0,
            liquidity=50000.0,
            dex="uniswap",
            price_change_1h=25.0,
            contract_verified=True,
            liquidity_locked=True,
            is_renounced=True
        )
        
        edge_score = token.calculate_edge_score()
        assert edge_score > 5.0  # Should have positive edge
        
        # Honeypot should have 0 edge
        honeypot = TokenData(
            address="0xtoken789",
            symbol="SCAM",
            chain="eth",
            price=0.001,
            volume_24h=100000.0,
            liquidity=50000.0,
            dex="uniswap",
            is_honeypot=True
        )
        
        assert honeypot.calculate_edge_score() == 0.0


class TestWhaleTracker:
    """Test whale tracker service."""
    
    def test_whale_tracker_init(self):
        """Test whale tracker initialization."""
        tracker = WhaleTracker(min_tx_value=10000.0, check_interval=60)
        
        assert tracker.min_tx_value == 10000.0
        assert tracker.check_interval == 60
        assert len(tracker.tracked_wallets) == 0
    
    def test_add_remove_wallet(self):
        """Test adding and removing wallets."""
        tracker = WhaleTracker()
        
        wallet = WhaleWallet(
            address="0xwhale123",
            chain="eth",
            label="Test Whale"
        )
        
        tracker.add_wallet(wallet)
        assert "0xwhale123" in tracker.tracked_wallets
        
        tracker.remove_wallet("0xwhale123")
        assert "0xwhale123" not in tracker.tracked_wallets
    
    def test_analyze_whale_activity(self):
        """Test whale activity analysis."""
        tracker = WhaleTracker(min_tx_value=10000.0)
        
        # Activity below minimum should return None
        small_activity = WhaleActivity(
            id="activity_1",
            wallet_address="0xwhale123",
            tx_hash="0xtxhash123",
            chain="eth",
            action="BUY",
            token_address="0xtoken123",
            amount_usd=5000.0  # Below minimum
        )
        
        signal = tracker.analyze_whale_activity(small_activity)
        assert signal is None
        
        # Large activity should generate signal
        large_activity = WhaleActivity(
            id="activity_2",
            wallet_address="0xwhale123",
            wallet_name="Known Whale",
            tx_hash="0xtxhash456",
            chain="eth",
            action="BUY",
            token_address="0xtoken456",
            token_symbol="TOKEN",
            amount_usd=50000.0,
            is_new_token=True
        )
        
        signal = tracker.analyze_whale_activity(large_activity)
        assert signal is not None
        assert signal.signal_type == SignalType.WHALE_BUY
        assert signal.confidence > 0.7
        assert signal.edge_score > 6.0


class TestDEXScraper:
    """Test DEX scraper service."""
    
    def test_dex_scraper_init(self):
        """Test DEX scraper initialization."""
        scraper = DEXScraper(
            chains=["eth", "sol"],
            check_interval=300,
            min_liquidity=10000.0
        )
        
        assert "eth" in scraper.chains
        assert "sol" in scraper.chains
        assert scraper.check_interval == 300
        assert scraper.min_liquidity == 10000.0
    
    def test_analyze_token(self):
        """Test token analysis."""
        scraper = DEXScraper()
        
        # Token with low edge should not generate signal
        low_edge_token = TokenData(
            address="0xtoken123",
            symbol="LOW",
            chain="eth",
            price=0.001,
            volume_24h=10000.0,
            liquidity=50000.0,
            dex="uniswap",
            age_hours=48.0
        )
        
        signal = scraper.analyze_token(low_edge_token)
        assert signal is None
        
        # New token with good metrics should generate signal
        good_token = TokenData(
            address="0xtoken456",
            symbol="GOOD",
            chain="eth",
            price=0.001,
            volume_24h=200000.0,
            liquidity=50000.0,
            dex="uniswap",
            age_hours=0.5,
            contract_verified=True,
            liquidity_locked=True,
            price_change_1h=25.0
        )
        
        signal = scraper.analyze_token(good_token)
        assert signal is not None
        assert signal.signal_type == SignalType.NEW_TOKEN
        assert signal.edge_score > 5.0


class TestSentimentTracker:
    """Test sentiment tracker service."""
    
    def test_sentiment_tracker_init(self):
        """Test sentiment tracker initialization."""
        tracker = SentimentTracker(
            check_interval=600,
            min_mention_count=10
        )
        
        assert tracker.check_interval == 600
        assert tracker.min_mention_count == 10
        assert len(tracker.tracked_accounts) > 0
    
    def test_track_mention(self):
        """Test mention tracking."""
        tracker = SentimentTracker()
        
        # Track some mentions
        tracker.track_mention("TOKEN")
        tracker.track_mention("TOKEN")
        tracker.track_mention("TOKEN")
        
        count = tracker.get_mention_count("TOKEN", hours=1.0)
        assert count == 3
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis."""
        tracker = SentimentTracker(min_mention_count=10)
        
        # Below threshold should return None
        signal = tracker.analyze_sentiment("TOKEN", mentions=5, timeframe_hours=1.0)
        assert signal is None
        
        # Above threshold should generate signal
        signal = tracker.analyze_sentiment("TOKEN", mentions=15, timeframe_hours=1.0)
        assert signal is not None
        assert signal.signal_type == SignalType.SOCIAL_BUZZ
        assert signal.confidence > 0.5


class TestAlertManager:
    """Test alert manager service."""
    
    def test_alert_manager_init(self):
        """Test alert manager initialization."""
        manager = AlertManager(
            min_sources=3,
            confirmation_window=3600
        )
        
        assert manager.min_sources == 3
        assert manager.confirmation_window == 3600
    
    def test_multi_signal_confirmation(self):
        """Test multi-signal confirmation."""
        manager = AlertManager(min_sources=3, confirmation_window=3600)
        
        # Add signals from different sources
        signal1 = Signal(
            id="signal_1",
            signal_type=SignalType.WHALE_BUY,
            token_address="0xtoken123",
            token_symbol="TOKEN",
            chain="eth",
            confidence=0.8,
            edge_score=7.0,
            sources=["whale_tracker"],
            source_count=1,
            risk_level="medium",
            recommended_action="watch",
            alert_message="Whale buy"
        )
        
        signal2 = Signal(
            id="signal_2",
            signal_type=SignalType.VOLUME_SPIKE,
            token_address="0xtoken123",
            token_symbol="TOKEN",
            chain="eth",
            confidence=0.7,
            edge_score=6.5,
            sources=["dex_scraper"],
            source_count=1,
            risk_level="medium",
            recommended_action="watch",
            alert_message="Volume spike"
        )
        
        signal3 = Signal(
            id="signal_3",
            signal_type=SignalType.SOCIAL_BUZZ,
            token_address="0xtoken123",
            token_symbol="TOKEN",
            chain="eth",
            confidence=0.75,
            edge_score=6.8,
            sources=["sentiment_tracker"],
            source_count=1,
            risk_level="medium",
            recommended_action="watch",
            alert_message="Social buzz"
        )
        
        # First two signals should not confirm
        confirmed1 = manager.add_signal(signal1)
        assert confirmed1 is None
        
        confirmed2 = manager.add_signal(signal2)
        assert confirmed2 is None
        
        # Third signal should trigger confirmation
        confirmed3 = manager.add_signal(signal3)
        assert confirmed3 is not None
        assert confirmed3.source_count == 3
        assert "whale_tracker" in confirmed3.sources
        assert "dex_scraper" in confirmed3.sources
        assert "sentiment_tracker" in confirmed3.sources
        assert confirmed3.confidence > signal1.confidence  # Boosted
    
    def test_cleanup_old_signals(self):
        """Test cleanup of old signals."""
        manager = AlertManager(confirmation_window=3600)
        
        # Add signal
        signal = Signal(
            id="signal_1",
            signal_type=SignalType.WHALE_BUY,
            token_address="0xtoken123",
            token_symbol="TOKEN",
            chain="eth",
            confidence=0.8,
            edge_score=7.0,
            sources=["whale_tracker"],
            source_count=1,
            risk_level="medium",
            recommended_action="watch",
            alert_message="Test"
        )
        
        manager.add_signal(signal)
        assert len(manager.signals_by_token) > 0
        
        # Cleanup (signal is recent, should remain)
        manager.cleanup_old_signals()
        assert len(manager.signals_by_token) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
