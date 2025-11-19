"""DEX scraping service for new token discovery and volume analysis."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from crypto_tracker.models.token_data import TokenData
from crypto_tracker.models.signal import Signal, SignalType


logger = logging.getLogger(__name__)


class DEXScraper:
    """
    DEX scraping service for real-time token discovery.
    
    Monitors DEXScreener, DEXTools and other DEX aggregators for:
    - New token launches (0-15min window)
    - Volume spikes (smart money moving)
    - Liquidity events
    - Price movements
    
    Based on S-TIER strategy: Public data > Private scams
    """
    
    def __init__(
        self,
        chains: Optional[List[str]] = None,
        check_interval: int = 300,  # 5 minutes
        min_liquidity: float = 10000.0,
    ):
        """
        Initialize DEX scraper.
        
        Args:
            chains: List of chains to monitor (eth, sol, base, etc.)
            check_interval: Seconds between checks
            min_liquidity: Minimum liquidity to consider (USD)
        """
        self.chains = chains or ["eth", "sol", "base"]
        self.check_interval = check_interval
        self.min_liquidity = min_liquidity
        
        self.discovered_tokens: Dict[str, TokenData] = {}
        self._running = False
        
        logger.info(
            f"DEXScraper initialized: chains={self.chains}, "
            f"interval={check_interval}s, min_liq=${min_liquidity:,.0f}"
        )
    
    async def fetch_new_pairs(self, chain: str) -> List[TokenData]:
        """
        Fetch newly created trading pairs from DEXScreener.
        
        Args:
            chain: Blockchain to check
            
        Returns:
            List of new token data
        """
        new_tokens = []
        
        try:
            # In real implementation, would call DEXScreener API
            # https://api.dexscreener.com/latest/dex/pairs/{chain}
            
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    
                    # Filter for recent pairs
                    cutoff = datetime.utcnow() - timedelta(minutes=15)
                    
                    for pair in pairs:
                        token_data = self._parse_dexscreener_pair(pair, chain)
                        
                        if token_data and token_data.age_hours and token_data.age_hours < 0.25:
                            if token_data.liquidity and token_data.liquidity >= self.min_liquidity:
                                new_tokens.append(token_data)
        
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching pairs for {chain}")
        except Exception as e:
            logger.error(f"Error fetching new pairs for {chain}: {e}")
        
        return new_tokens
    
    def _parse_dexscreener_pair(self, pair: Dict[str, Any], chain: str) -> Optional[TokenData]:
        """Parse DEXScreener pair data into TokenData model."""
        try:
            # Extract relevant fields from DEXScreener API response
            base_token = pair.get("baseToken", {})
            quote_token = pair.get("quoteToken", {})
            
            # Calculate age
            created_at = pair.get("pairCreatedAt")
            age_hours = None
            if created_at:
                created_time = datetime.fromtimestamp(created_at / 1000)
                age_hours = (datetime.utcnow() - created_time).total_seconds() / 3600
            
            token_data = TokenData(
                address=base_token.get("address", ""),
                symbol=base_token.get("symbol", "UNKNOWN"),
                name=base_token.get("name"),
                chain=chain,
                price=float(pair.get("priceUsd", 0)),
                market_cap=float(pair.get("fdv", 0)),
                liquidity=float(pair.get("liquidity", {}).get("usd", 0)),
                volume_24h=float(pair.get("volume", {}).get("h24", 0)),
                volume_1h=float(pair.get("volume", {}).get("h1", 0)),
                price_change_1h=float(pair.get("priceChange", {}).get("h1", 0)),
                price_change_6h=float(pair.get("priceChange", {}).get("h6", 0)),
                price_change_24h=float(pair.get("priceChange", {}).get("h24", 0)),
                age_hours=age_hours,
                dex=pair.get("dexId", "unknown"),
                pair_address=pair.get("pairAddress"),
                dexscreener_link=pair.get("url"),
            )
            
            return token_data
        
        except Exception as e:
            logger.error(f"Error parsing DEXScreener pair: {e}")
            return None
    
    async def check_volume_spike(self, token_address: str, chain: str) -> Optional[TokenData]:
        """
        Check if token has volume spike (300%+ increase).
        
        Args:
            token_address: Token to check
            chain: Blockchain
            
        Returns:
            Updated TokenData if spike detected, None otherwise
        """
        try:
            # In real implementation, would compare current vs historical volume
            # For now, return None (mock)
            pass
        except Exception as e:
            logger.error(f"Error checking volume spike: {e}")
        
        return None
    
    def analyze_token(self, token: TokenData) -> Optional[Signal]:
        """
        Analyze token and generate signal if meets criteria.
        
        Args:
            token: Token data to analyze
            
        Returns:
            Signal if token meets criteria, None otherwise
        """
        # Calculate risk and edge
        risk_level = token.calculate_risk_level()
        edge_score = token.calculate_edge_score()
        
        # Determine if signal should be generated
        if edge_score < 5.0:
            return None  # Not interesting enough
        
        # Determine signal type
        signal_type = SignalType.NEW_TOKEN
        if token.age_hours and token.age_hours > 6:
            # Not new, check if volume spike
            if token.volume_1h and token.volume_24h:
                vol_ratio = (token.volume_1h * 24) / token.volume_24h
                if vol_ratio > 3.0:
                    signal_type = SignalType.VOLUME_SPIKE
                else:
                    return None  # Not interesting
        
        # Calculate confidence
        confidence = self._calculate_token_confidence(token)
        
        # Determine action
        if risk_level == "extreme":
            recommended_action = "avoid"
        elif risk_level == "high":
            recommended_action = "watch"
        elif edge_score >= 8.0:
            recommended_action = "small_buy"
        else:
            recommended_action = "watch"
        
        # Create signal
        signal = Signal(
            id=f"dex_{token.chain}_{token.address}_{int(datetime.utcnow().timestamp())}",
            signal_type=signal_type,
            token_address=token.address,
            token_symbol=token.symbol,
            chain=token.chain,
            confidence=confidence,
            edge_score=edge_score,
            sources=["dex_scraper"],
            source_count=1,
            market_cap=token.market_cap,
            volume_24h=token.volume_24h,
            price=token.price,
            liquidity=token.liquidity,
            risk_level=risk_level,
            rug_check_passed=not token.is_honeypot,
            contract_verified=token.contract_verified,
            recommended_action=recommended_action,
            position_size_pct=1.0 if recommended_action == "small_buy" else None,
            alert_message=self._generate_alert_message(token, signal_type),
            dex_link=token.dexscreener_link,
            metadata={
                "dex": token.dex,
                "age_hours": token.age_hours,
                "liquidity_locked": token.liquidity_locked,
                "top_10_holders_pct": token.top_10_holders_pct,
            }
        )
        
        return signal
    
    def _calculate_token_confidence(self, token: TokenData) -> float:
        """Calculate confidence score for token."""
        confidence = 0.6  # Base confidence for DEX data
        
        # Higher confidence if contract verified
        if token.contract_verified:
            confidence += 0.1
        
        # Higher confidence if liquidity locked
        if token.liquidity_locked:
            confidence += 0.15
        
        # Lower confidence for very new tokens
        if token.age_hours and token.age_hours < 1:
            confidence -= 0.2
        
        # Lower confidence if honeypot detected
        if token.is_honeypot:
            confidence = 0.0
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_alert_message(self, token: TokenData, signal_type: SignalType) -> str:
        """Generate human-readable alert message."""
        if signal_type == SignalType.NEW_TOKEN:
            age_str = f"{token.age_hours:.1f}h old" if token.age_hours else "just launched"
            return (
                f"🚨 NEW TOKEN: ${token.symbol}\n"
                f"Age: {age_str}\n"
                f"Liquidity: ${token.liquidity:,.0f}\n"
                f"Volume 1h: ${token.volume_1h:,.0f}" if token.volume_1h else ""
            )
        elif signal_type == SignalType.VOLUME_SPIKE:
            return (
                f"📈 VOLUME SPIKE: ${token.symbol}\n"
                f"24h Vol: ${token.volume_24h:,.0f}\n"
                f"Price: ${token.price:.8f}"
            )
        else:
            return f"New signal for ${token.symbol}"
    
    async def start_monitoring(self, callback=None) -> None:
        """
        Start continuous DEX monitoring.
        
        Args:
            callback: Optional callback function for new signals
        """
        self._running = True
        logger.info(f"Started DEX monitoring for chains: {self.chains}")
        
        while self._running:
            try:
                # Check each chain
                for chain in self.chains:
                    new_tokens = await self.fetch_new_pairs(chain)
                    
                    for token in new_tokens:
                        # Store discovered token
                        key = f"{token.chain}_{token.address}"
                        self.discovered_tokens[key] = token
                        
                        # Analyze and generate signal
                        signal = self.analyze_token(token)
                        
                        if signal and callback:
                            await callback(signal)
                
                # Cleanup old tokens (keep last 24h)
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.discovered_tokens = {
                    k: v for k, v in self.discovered_tokens.items()
                    if v.first_seen > cutoff
                }
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in DEX monitoring loop: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self) -> None:
        """Stop DEX monitoring."""
        self._running = False
        logger.info("Stopped DEX monitoring")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get DEX scraper statistics."""
        return {
            "monitored_chains": len(self.chains),
            "discovered_tokens": len(self.discovered_tokens),
            "monitoring_active": self._running,
            "check_interval": self.check_interval,
        }
