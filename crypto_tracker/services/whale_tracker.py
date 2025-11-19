"""Whale wallet tracking service."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from crypto_tracker.models.whale_activity import WhaleActivity, WhaleWallet
from crypto_tracker.models.signal import Signal, SignalType


logger = logging.getLogger(__name__)


class WhaleTracker:
    """
    Whale wallet tracking service.
    
    Monitors smart money movements across chains and generates signals
    when whales make significant trades.
    
    Based on S-TIER strategy: Whale wallets don't lie - insider callers do.
    """
    
    def __init__(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        min_tx_value: float = 10000.0,
        check_interval: int = 60,
    ):
        """
        Initialize whale tracker.
        
        Args:
            api_keys: Dict of API keys (etherscan, moralis, etc.)
            min_tx_value: Minimum transaction value to track (USD)
            check_interval: Seconds between checks
        """
        self.api_keys = api_keys or {}
        self.min_tx_value = min_tx_value
        self.check_interval = check_interval
        
        self.tracked_wallets: Dict[str, WhaleWallet] = {}
        self.recent_activities: List[WhaleActivity] = []
        self._running = False
        
        logger.info(
            f"WhaleTracker initialized: min_tx=${min_tx_value:,.0f}, "
            f"interval={check_interval}s"
        )
    
    def add_wallet(self, wallet: WhaleWallet) -> None:
        """Add wallet to tracking list."""
        self.tracked_wallets[wallet.address.lower()] = wallet
        logger.info(f"Added whale wallet: {wallet.address} ({wallet.label or 'Unknown'})")
    
    def remove_wallet(self, address: str) -> None:
        """Remove wallet from tracking."""
        address = address.lower()
        if address in self.tracked_wallets:
            del self.tracked_wallets[address]
            logger.info(f"Removed whale wallet: {address}")
    
    async def fetch_wallet_transactions(
        self, wallet: WhaleWallet, since: Optional[datetime] = None
    ) -> List[WhaleActivity]:
        """
        Fetch recent transactions for a wallet.
        
        Args:
            wallet: Whale wallet to check
            since: Only fetch transactions after this time
            
        Returns:
            List of whale activities
        """
        activities = []
        
        try:
            # Determine which API to use based on chain
            if wallet.chain in ["eth", "ethereum"]:
                activities = await self._fetch_etherscan_transactions(wallet, since)
            elif wallet.chain in ["sol", "solana"]:
                activities = await self._fetch_solscan_transactions(wallet, since)
            elif wallet.chain == "base":
                activities = await self._fetch_basescan_transactions(wallet, since)
            else:
                logger.warning(f"Unsupported chain for wallet {wallet.address}: {wallet.chain}")
        
        except Exception as e:
            logger.error(f"Error fetching transactions for {wallet.address}: {e}")
        
        return activities
    
    async def _fetch_etherscan_transactions(
        self, wallet: WhaleWallet, since: Optional[datetime]
    ) -> List[WhaleActivity]:
        """Fetch Ethereum transactions via Etherscan API."""
        api_key = self.api_keys.get("etherscan")
        if not api_key:
            logger.warning("Etherscan API key not configured")
            return []
        
        # In real implementation, would call Etherscan API
        # For now, return empty list (mock)
        logger.debug(f"Fetching ETH transactions for {wallet.address}")
        return []
    
    async def _fetch_solscan_transactions(
        self, wallet: WhaleWallet, since: Optional[datetime]
    ) -> List[WhaleActivity]:
        """Fetch Solana transactions via Solscan API."""
        # Mock implementation
        logger.debug(f"Fetching SOL transactions for {wallet.address}")
        return []
    
    async def _fetch_basescan_transactions(
        self, wallet: WhaleWallet, since: Optional[datetime]
    ) -> List[WhaleActivity]:
        """Fetch Base transactions via Basescan API."""
        # Mock implementation
        logger.debug(f"Fetching BASE transactions for {wallet.address}")
        return []
    
    def analyze_whale_activity(self, activity: WhaleActivity) -> Optional[Signal]:
        """
        Analyze whale activity and generate signal if significant.
        
        Args:
            activity: Whale activity to analyze
            
        Returns:
            Signal if activity is significant, None otherwise
        """
        # Check if transaction meets minimum value
        if activity.amount_usd < self.min_tx_value:
            return None
        
        # Generate signal
        confidence = self._calculate_whale_confidence(activity)
        edge_score = self._calculate_whale_edge(activity)
        
        # Create signal
        signal = Signal(
            id=f"whale_{activity.id}",
            signal_type=(
                SignalType.WHALE_BUY if activity.action == "BUY"
                else SignalType.WHALE_SELL
            ),
            token_address=activity.token_address,
            token_symbol=activity.token_symbol,
            chain=activity.chain,
            confidence=confidence,
            edge_score=edge_score,
            sources=["whale_tracker"],
            source_count=1,
            risk_level="medium",  # Will be updated by multi-signal system
            rug_check_passed=False,  # Will be checked by other services
            contract_verified=False,
            recommended_action="watch" if activity.action == "BUY" else "exit",
            alert_message=(
                f"🐋 Whale {activity.action}: ${activity.amount_usd:,.0f} "
                f"{'into' if activity.action == 'BUY' else 'from'} "
                f"{activity.token_symbol or activity.token_address[:8]}"
            ),
            dex_link=activity.dex_link,
            metadata={
                "whale_address": activity.wallet_address,
                "whale_name": activity.wallet_name,
                "tx_hash": activity.tx_hash,
                "is_new_token": activity.is_new_token,
            }
        )
        
        return signal
    
    def _calculate_whale_confidence(self, activity: WhaleActivity) -> float:
        """Calculate confidence score for whale activity."""
        confidence = 0.7  # Base confidence for whale tracking
        
        # Higher confidence if whale is known/labeled
        if activity.wallet_name:
            confidence += 0.1
        
        # Higher confidence for larger transactions
        if activity.amount_usd > 100000:
            confidence += 0.15
        elif activity.amount_usd > 50000:
            confidence += 0.1
        
        # Lower confidence for sells (could be taking profit)
        if activity.action == "SELL":
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_whale_edge(self, activity: WhaleActivity) -> float:
        """Calculate edge score for whale activity."""
        edge = 6.0  # Base edge for whale tracking
        
        # Higher edge for buys of new tokens
        if activity.action == "BUY" and activity.is_new_token:
            edge += 2.0
        
        # Higher edge for very large transactions
        if activity.amount_usd > 100000:
            edge += 1.5
        elif activity.amount_usd > 50000:
            edge += 1.0
        
        # Lower edge for sells
        if activity.action == "SELL":
            edge -= 2.0
        
        return min(10.0, max(0.0, edge))
    
    async def start_monitoring(self, callback=None) -> None:
        """
        Start continuous monitoring of whale wallets.
        
        Args:
            callback: Optional callback function for new activities
        """
        self._running = True
        logger.info(f"Started whale monitoring for {len(self.tracked_wallets)} wallets")
        
        while self._running:
            try:
                # Check all tracked wallets
                since = datetime.utcnow() - timedelta(seconds=self.check_interval * 2)
                
                for wallet in self.tracked_wallets.values():
                    activities = await self.fetch_wallet_transactions(wallet, since)
                    
                    for activity in activities:
                        # Store activity
                        self.recent_activities.append(activity)
                        
                        # Generate signal
                        signal = self.analyze_whale_activity(activity)
                        
                        if signal and callback:
                            await callback(signal)
                
                # Cleanup old activities (keep last 1000)
                if len(self.recent_activities) > 1000:
                    self.recent_activities = self.recent_activities[-1000:]
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in whale monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    def stop_monitoring(self) -> None:
        """Stop whale monitoring."""
        self._running = False
        logger.info("Stopped whale monitoring")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get whale tracking statistics."""
        return {
            "tracked_wallets": len(self.tracked_wallets),
            "recent_activities": len(self.recent_activities),
            "monitoring_active": self._running,
            "min_tx_value": self.min_tx_value,
        }
