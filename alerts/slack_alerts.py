"""
Slack alerting system for BetFlow Engine v0.9.0
Sends alerts for SLO violations, fallback spikes, and memory leaks.
"""

import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of alerts."""
    SLO_VIOLATION = "slo_violation"
    FALLBACK_SPIKE = "fallback_spike"
    MEMORY_LEAK = "memory_leak"
    ENGINE_FAILURE = "engine_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"

@dataclass
class Alert:
    """Alert data structure."""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_slack_payload(self) -> Dict[str, Any]:
        """Convert alert to Slack webhook payload."""
        # Color coding based on severity
        color_map = {
            AlertSeverity.INFO: "#36a64f",      # Green
            AlertSeverity.WARNING: "#ff9500",   # Orange
            AlertSeverity.CRITICAL: "#ff0000"   # Red
        }
        
        # Emoji mapping
        emoji_map = {
            AlertType.SLO_VIOLATION: "🚨",
            AlertType.FALLBACK_SPIKE: "⚠️",
            AlertType.MEMORY_LEAK: "🧠",
            AlertType.ENGINE_FAILURE: "💥",
            AlertType.PERFORMANCE_DEGRADATION: "📉"
        }
        
        # Build fields for additional context
        fields = []
        for key, value in self.metadata.items():
            fields.append({
                "title": key.replace("_", " ").title(),
                "value": str(value),
                "short": True
            })
        
        return {
            "username": "BetFlow Engine Monitor",
            "icon_emoji": ":robot_face:",
            "attachments": [
                {
                    "color": color_map[self.severity],
                    "title": f"{emoji_map[self.alert_type]} {self.title}",
                    "text": self.message,
                    "fields": fields,
                    "footer": "BetFlow Engine v0.9.0",
                    "ts": int(self.timestamp.timestamp())
                }
            ]
        }

class SlackAlerter:
    """Slack alerting system."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
        self.alert_history: List[Alert] = []
        self.rate_limit_cache: Dict[str, datetime] = {}
        
        if not self.enabled:
            logger.warning("Slack webhook URL not configured, alerts will be logged only")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            # Add to history
            self.alert_history.append(alert)
            
            # Keep only last 100 alerts
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
            
            # Check rate limiting
            if self._is_rate_limited(alert):
                logger.info(f"Alert rate limited: {alert.title}")
                return False
            
            # Log alert locally
            logger.error(f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
            
            # Send to Slack if enabled
            if self.enabled:
                return await self._send_to_slack(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    async def _send_to_slack(self, alert: Alert) -> bool:
        """Send alert to Slack webhook."""
        try:
            payload = alert.to_slack_payload()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Alert sent to Slack: {alert.title}")
                        return True
                    else:
                        logger.error(f"Slack webhook failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    def _is_rate_limited(self, alert: Alert) -> bool:
        """Check if alert should be rate limited."""
        # Create rate limit key based on alert type and key metadata
        key_parts = [alert.alert_type.value]
        if "metric" in alert.metadata:
            key_parts.append(alert.metadata["metric"])
        
        rate_limit_key = "_".join(key_parts)
        
        # Check if we've sent this type of alert recently
        now = datetime.utcnow()
        if rate_limit_key in self.rate_limit_cache:
            last_sent = self.rate_limit_cache[rate_limit_key]
            
            # Rate limit based on severity
            rate_limit_minutes = {
                AlertSeverity.CRITICAL: 5,   # 5 minutes
                AlertSeverity.WARNING: 15,   # 15 minutes
                AlertSeverity.INFO: 60       # 1 hour
            }
            
            time_diff = now - last_sent
            if time_diff < timedelta(minutes=rate_limit_minutes[alert.severity]):
                return True
        
        # Update rate limit cache
        self.rate_limit_cache[rate_limit_key] = now
        return False
    
    async def send_slo_violation_alert(self, metric: str, value: float, threshold: float, 
                                     duration: str = "5m") -> bool:
        """Send SLO violation alert."""
        alert = Alert(
            alert_type=AlertType.SLO_VIOLATION,
            severity=AlertSeverity.CRITICAL,
            title=f"SLO Violation: {metric}",
            message=f"SLO violation detected for {metric}. Current value: {value:.3f}, Threshold: {threshold:.3f}",
            timestamp=datetime.utcnow(),
            metadata={
                "metric": metric,
                "current_value": value,
                "threshold": threshold,
                "duration": duration,
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
        
        return await self.send_alert(alert)
    
    async def send_fallback_spike_alert(self, fallback_ratio: float, threshold: float = 0.05) -> bool:
        """Send fallback spike alert."""
        alert = Alert(
            alert_type=AlertType.FALLBACK_SPIKE,
            severity=AlertSeverity.WARNING,
            title="Fallback Spike Detected",
            message=f"High fallback ratio detected: {fallback_ratio:.1%} (threshold: {threshold:.1%}). Mojo engine may be experiencing issues.",
            timestamp=datetime.utcnow(),
            metadata={
                "fallback_ratio": f"{fallback_ratio:.1%}",
                "threshold": f"{threshold:.1%}",
                "recommendation": "Check Mojo engine health and performance",
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
        
        return await self.send_alert(alert)
    
    async def send_memory_leak_alert(self, memory_growth_mb: float, duration: str = "1h") -> bool:
        """Send memory leak alert."""
        alert = Alert(
            alert_type=AlertType.MEMORY_LEAK,
            severity=AlertSeverity.WARNING,
            title="Memory Leak Detected",
            message=f"Potential memory leak detected. Memory growth: {memory_growth_mb:.1f}MB over {duration}",
            timestamp=datetime.utcnow(),
            metadata={
                "memory_growth_mb": memory_growth_mb,
                "duration": duration,
                "recommendation": "Monitor memory usage and consider restart if growth continues",
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
        
        return await self.send_alert(alert)
    
    async def send_engine_failure_alert(self, error: str) -> bool:
        """Send engine failure alert."""
        alert = Alert(
            alert_type=AlertType.ENGINE_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Engine Failure",
            message=f"BetFlow Engine failure detected: {error}",
            timestamp=datetime.utcnow(),
            metadata={
                "error": error,
                "recommendation": "Check engine logs and restart if necessary",
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
        
        return await self.send_alert(alert)
    
    async def send_performance_degradation_alert(self, metric: str, current: float, 
                                               baseline: float, degradation_pct: float) -> bool:
        """Send performance degradation alert."""
        alert = Alert(
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            severity=AlertSeverity.WARNING,
            title=f"Performance Degradation: {metric}",
            message=f"Performance degradation detected for {metric}. Current: {current:.3f}, Baseline: {baseline:.3f} ({degradation_pct:.1f}% degradation)",
            timestamp=datetime.utcnow(),
            metadata={
                "metric": metric,
                "current_value": current,
                "baseline_value": baseline,
                "degradation_percent": f"{degradation_pct:.1f}%",
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
        
        return await self.send_alert(alert)
    
    async def send_recovery_alert(self, alert_type: AlertType, metric: str) -> bool:
        """Send recovery alert when issue is resolved."""
        alert = Alert(
            alert_type=alert_type,
            severity=AlertSeverity.INFO,
            title=f"Recovery: {metric}",
            message=f"Issue resolved for {metric}. System is back to normal operation.",
            timestamp=datetime.utcnow(),
            metadata={
                "metric": metric,
                "status": "recovered",
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
        
        return await self.send_alert(alert)
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp > cutoff_time]
        
        # Count by type and severity
        type_counts = {}
        severity_counts = {}
        
        for alert in recent_alerts:
            type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
        
        return {
            "total_alerts": len(recent_alerts),
            "time_period_hours": hours,
            "alerts_by_type": type_counts,
            "alerts_by_severity": severity_counts,
            "most_recent": recent_alerts[-1].title if recent_alerts else None
        }

# Global alerter instance
_alerter = None

def get_alerter() -> SlackAlerter:
    """Get global alerter instance."""
    global _alerter
    if _alerter is None:
        _alerter = SlackAlerter()
    return _alerter

async def send_test_alert() -> bool:
    """Send a test alert to verify Slack integration."""
    alerter = get_alerter()
    
    test_alert = Alert(
        alert_type=AlertType.SLO_VIOLATION,
        severity=AlertSeverity.INFO,
        title="Test Alert",
        message="This is a test alert from BetFlow Engine v0.9.0 to verify Slack integration.",
        timestamp=datetime.utcnow(),
        metadata={
            "test": True,
            "version": "0.9.0",
            "environment": os.getenv("ENVIRONMENT", "test")
        }
    )
    
    return await alerter.send_alert(test_alert)

if __name__ == "__main__":
    # Test the alerting system
    async def main():
        print("Testing Slack alerting system...")
        
        # Send test alert
        success = await send_test_alert()
        print(f"Test alert sent: {success}")
        
        # Test different alert types
        alerter = get_alerter()
        
        await alerter.send_slo_violation_alert("p95_latency", 1.5, 1.0)
        await alerter.send_fallback_spike_alert(0.15, 0.05)
        await alerter.send_memory_leak_alert(25.5, "30m")
        
        # Print summary
        summary = alerter.get_alert_summary(1)
        print(f"Alert summary: {json.dumps(summary, indent=2)}")
    
    asyncio.run(main())
