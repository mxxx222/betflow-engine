"""Alert management and multi-signal confirmation system."""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict

import httpx
from crypto_tracker.models.signal import Signal, SignalType, SignalFilter


logger = logging.getLogger(__name__)


class AlertManager:
    """
    Alert management and multi-signal confirmation system.
    
    Combines signals from multiple sources (whale tracker, DEX scraper, sentiment)
    and generates alerts only when multiple signals confirm the same opportunity.
    
    Based on critical rule: Multi-Signal Confirmation (need 3+ signals).
    """
    
    def __init__(
        self,
        discord_webhook: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        min_sources: int = 3,
        confirmation_window: int = 3600,  # 1 hour
    ):
        """
        Initialize alert manager.
        
        Args:
            discord_webhook: Discord webhook URL
            telegram_bot_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
            min_sources: Minimum number of sources for alert
            confirmation_window: Time window for signal correlation (seconds)
        """
        self.discord_webhook = discord_webhook
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.min_sources = min_sources
        self.confirmation_window = confirmation_window
        
        # Signal storage by token
        self.signals_by_token: Dict[str, List[Signal]] = defaultdict(list)
        self.alert_history: List[Dict[str, Any]] = []
        
        logger.info(
            f"AlertManager initialized: min_sources={min_sources}, "
            f"window={confirmation_window}s"
        )
    
    def add_signal(self, signal: Signal) -> Optional[Signal]:
        """
        Add signal and check for multi-source confirmation.
        
        Args:
            signal: New signal to add
            
        Returns:
            Confirmed signal if meets criteria, None otherwise
        """
        # Create token key
        token_key = self._get_token_key(signal)
        
        # Add signal
        self.signals_by_token[token_key].append(signal)
        
        # Check for confirmation
        confirmed = self._check_confirmation(token_key)
        
        if confirmed:
            logger.info(
                f"Multi-signal confirmation: {signal.token_symbol} "
                f"({confirmed.source_count} sources, edge={confirmed.edge_score:.1f})"
            )
        
        return confirmed
    
    def _get_token_key(self, signal: Signal) -> str:
        """Generate unique key for token."""
        # Use symbol if available, otherwise use address
        if signal.token_symbol:
            return f"{signal.chain}_{signal.token_symbol}".lower()
        else:
            return f"{signal.chain}_{signal.token_address}".lower()
    
    def _check_confirmation(self, token_key: str) -> Optional[Signal]:
        """
        Check if token has enough signals for confirmation.
        
        Args:
            token_key: Token identifier
            
        Returns:
            Confirmed signal if meets criteria, None otherwise
        """
        signals = self.signals_by_token[token_key]
        
        if not signals:
            return None
        
        # Filter recent signals (within confirmation window)
        cutoff = datetime.utcnow() - timedelta(seconds=self.confirmation_window)
        recent_signals = [s for s in signals if s.timestamp > cutoff]
        
        if len(recent_signals) < self.min_sources:
            return None
        
        # Get unique sources
        unique_sources = set()
        for signal in recent_signals:
            unique_sources.update(signal.sources)
        
        if len(unique_sources) < self.min_sources:
            return None
        
        # Combine signals into confirmed signal
        return self._combine_signals(recent_signals)
    
    def _combine_signals(self, signals: List[Signal]) -> Signal:
        """
        Combine multiple signals into single confirmed signal.
        
        Args:
            signals: List of signals to combine
            
        Returns:
            Combined signal with averaged metrics
        """
        # Use most recent signal as base
        base_signal = signals[-1]
        
        # Combine sources
        all_sources = set()
        for signal in signals:
            all_sources.update(signal.sources)
        
        # Average confidence and edge
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        avg_edge = sum(s.edge_score for s in signals) / len(signals)
        
        # Boost confidence for multi-source confirmation
        confirmed_confidence = min(1.0, avg_confidence + 0.1 * len(all_sources))
        
        # Determine risk level (use highest risk)
        risk_levels = ["low", "medium", "high", "extreme"]
        max_risk = max(
            signals,
            key=lambda s: risk_levels.index(s.risk_level)
        ).risk_level
        
        # Determine recommended action
        if max_risk == "extreme":
            action = "avoid"
        elif avg_edge >= 8.0 and confirmed_confidence >= 0.8:
            action = "small_buy"
        elif avg_edge >= 7.0:
            action = "watch"
        else:
            action = "wait"
        
        # Create confirmed signal
        confirmed = Signal(
            id=f"confirmed_{base_signal.id}",
            signal_type=SignalType.MULTI_WHALE,  # Mark as multi-source
            token_address=base_signal.token_address,
            token_symbol=base_signal.token_symbol,
            chain=base_signal.chain,
            confidence=confirmed_confidence,
            edge_score=avg_edge,
            sources=list(all_sources),
            source_count=len(all_sources),
            market_cap=base_signal.market_cap,
            volume_24h=base_signal.volume_24h,
            price=base_signal.price,
            liquidity=base_signal.liquidity,
            risk_level=max_risk,
            rug_check_passed=any(s.rug_check_passed for s in signals),
            contract_verified=any(s.contract_verified for s in signals),
            recommended_action=action,
            position_size_pct=1.0 if action == "small_buy" else None,
            alert_message=self._generate_combined_alert(signals),
            dex_link=base_signal.dex_link,
            metadata={
                "signal_count": len(signals),
                "signal_types": [s.signal_type.value for s in signals],
            }
        )
        
        return confirmed
    
    def _generate_combined_alert(self, signals: List[Signal]) -> str:
        """Generate combined alert message."""
        signal = signals[-1]  # Most recent
        
        signal_types = [s.signal_type.value for s in signals]
        sources = set()
        for s in signals:
            sources.update(s.sources)
        
        message = (
            f"🚨 MULTI-SIGNAL CONFIRMATION 🚨\n"
            f"Token: ${signal.token_symbol or signal.token_address[:8]}\n"
            f"Chain: {signal.chain.upper()}\n"
            f"Sources: {len(sources)} ({', '.join(sources)})\n"
            f"Confidence: {signal.confidence:.1%}\n"
            f"Edge Score: {signal.edge_score:.1f}/10\n"
            f"Risk: {signal.risk_level.upper()}\n"
            f"Action: {signal.recommended_action.upper()}"
        )
        
        if signal.market_cap:
            message += f"\nMCap: ${signal.market_cap:,.0f}"
        if signal.volume_24h:
            message += f"\n24h Vol: ${signal.volume_24h:,.0f}"
        
        return message
    
    async def send_discord_alert(self, signal: Signal) -> bool:
        """
        Send alert to Discord webhook.
        
        Args:
            signal: Signal to alert
            
        Returns:
            True if sent successfully
        """
        if not self.discord_webhook:
            return False
        
        try:
            # Format message for Discord
            embed = {
                "title": f"🚨 {signal.recommended_action.upper()}: ${signal.token_symbol}",
                "description": signal.alert_message,
                "color": self._get_alert_color(signal),
                "fields": [
                    {
                        "name": "Confidence",
                        "value": f"{signal.confidence:.1%}",
                        "inline": True
                    },
                    {
                        "name": "Edge Score",
                        "value": f"{signal.edge_score:.1f}/10",
                        "inline": True
                    },
                    {
                        "name": "Risk",
                        "value": signal.risk_level.upper(),
                        "inline": True
                    },
                ],
                "timestamp": signal.timestamp.isoformat(),
            }
            
            if signal.dex_link:
                embed["url"] = signal.dex_link
            
            payload = {"embeds": [embed]}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_webhook,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"Discord alert sent: {signal.token_symbol}")
                    return True
                else:
                    logger.warning(
                        f"Discord alert failed: {response.status_code}"
                    )
                    return False
        
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            return False
    
    def _get_alert_color(self, signal: Signal) -> int:
        """Get Discord embed color based on signal."""
        if signal.recommended_action == "small_buy":
            return 0x00FF00  # Green
        elif signal.recommended_action == "watch":
            return 0xFFFF00  # Yellow
        elif signal.recommended_action == "exit":
            return 0xFF0000  # Red
        else:
            return 0x808080  # Gray
    
    async def send_telegram_alert(self, signal: Signal) -> bool:
        """
        Send alert to Telegram.
        
        Args:
            signal: Signal to alert
            
        Returns:
            True if sent successfully
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            # Format message for Telegram
            message = signal.alert_message
            
            if signal.dex_link:
                message += f"\n\n🔗 {signal.dex_link}"
            
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                
                if response.status_code == 200:
                    logger.info(f"Telegram alert sent: {signal.token_symbol}")
                    return True
                else:
                    logger.warning(
                        f"Telegram alert failed: {response.status_code}"
                    )
                    return False
        
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    async def send_alert(self, signal: Signal) -> None:
        """Send alert through all configured channels."""
        # Record in history
        self.alert_history.append({
            "signal": signal,
            "timestamp": datetime.utcnow(),
        })
        
        # Send to Discord
        if self.discord_webhook:
            await self.send_discord_alert(signal)
        
        # Send to Telegram
        if self.telegram_bot_token:
            await self.send_telegram_alert(signal)
    
    def cleanup_old_signals(self) -> None:
        """Remove old signals beyond confirmation window."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.confirmation_window * 2)
        
        for token_key in list(self.signals_by_token.keys()):
            signals = self.signals_by_token[token_key]
            recent = [s for s in signals if s.timestamp > cutoff]
            
            if recent:
                self.signals_by_token[token_key] = recent
            else:
                del self.signals_by_token[token_key]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert manager statistics."""
        return {
            "tracked_tokens": len(self.signals_by_token),
            "total_signals": sum(
                len(signals) for signals in self.signals_by_token.values()
            ),
            "alerts_sent_24h": len([
                a for a in self.alert_history
                if a["timestamp"] > datetime.utcnow() - timedelta(hours=24)
            ]),
            "min_sources": self.min_sources,
        }
