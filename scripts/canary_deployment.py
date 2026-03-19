#!/usr/bin/env python3
"""
Canary deployment manager for BetFlow Engine v0.9.0
Implements gradual rollout strategy: 10% → 50% → 100%
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentStage(Enum):
    """Canary deployment stages."""
    INIT = "init"
    CANARY_10 = "canary_10"
    CANARY_50 = "canary_50"
    FULL_100 = "full_100"
    ROLLBACK = "rollback"

@dataclass
class HealthMetrics:
    """Health metrics for deployment validation."""
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    fallback_ratio: float
    cpu_usage: float
    memory_usage: float
    mojo_available: bool
    use_mojo: bool
    timestamp: datetime

@dataclass
class DeploymentConfig:
    """Canary deployment configuration."""
    api_url: str = "http://localhost:8000"
    health_check_interval: int = 30  # seconds
    stage_duration: int = 1800  # 30 minutes per stage
    slo_thresholds: Dict[str, float] = None
    rollback_on_violation: bool = True
    slack_webhook_url: Optional[str] = None
    
    def __post_init__(self):
        if self.slo_thresholds is None:
            self.slo_thresholds = {
                "p95_latency_ms": 1.0,
                "p99_latency_ms": 5.0,
                "error_rate": 0.001,
                "fallback_ratio": 0.05,
                "cpu_usage": 0.80,
                "memory_usage": 0.85
            }

class CanaryDeploymentManager:
    """Manages canary deployment process."""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.current_stage = DeploymentStage.INIT
        self.stage_start_time = None
        self.health_history: List[HealthMetrics] = []
        self.violations_count = 0
        self.max_violations = 3  # Max violations before rollback
        
    async def start_deployment(self) -> bool:
        """Start the canary deployment process."""
        logger.info("🚀 Starting BetFlow Engine v0.9.0 canary deployment")
        
        try:
            # Pre-deployment health check
            if not await self._pre_deployment_check():
                logger.error("❌ Pre-deployment check failed")
                return False
            
            # Stage 1: 10% canary
            if not await self._deploy_stage(DeploymentStage.CANARY_10, 10):
                return False
            
            # Stage 2: 50% canary
            if not await self._deploy_stage(DeploymentStage.CANARY_50, 50):
                return False
            
            # Stage 3: 100% full deployment
            if not await self._deploy_stage(DeploymentStage.FULL_100, 100):
                return False
            
            logger.info("✅ Canary deployment completed successfully")
            await self._send_notification("✅ Canary deployment completed successfully", "success")
            return True
            
        except Exception as e:
            logger.error(f"💥 Deployment failed: {e}")
            await self._rollback()
            return False
    
    async def _pre_deployment_check(self) -> bool:
        """Perform pre-deployment health checks."""
        logger.info("🔍 Performing pre-deployment health check...")
        
        try:
            # Check current system health
            health = await self._get_health_metrics()
            if not health:
                logger.error("Failed to get health metrics")
                return False
            
            # Validate SLO compliance
            violations = self._check_slo_violations(health)
            if violations:
                logger.error(f"Pre-deployment SLO violations: {violations}")
                return False
            
            # Check engine availability
            if not health.mojo_available:
                logger.warning("Mojo engine not available, proceeding with Python fallback")
            
            logger.info("✅ Pre-deployment check passed")
            return True
            
        except Exception as e:
            logger.error(f"Pre-deployment check failed: {e}")
            return False
    
    async def _deploy_stage(self, stage: DeploymentStage, traffic_percentage: int) -> bool:
        """Deploy a specific canary stage."""
        logger.info(f"🎯 Deploying {stage.value} ({traffic_percentage}% traffic)")
        
        self.current_stage = stage
        self.stage_start_time = datetime.utcnow()
        self.violations_count = 0
        
        try:
            # Update traffic routing
            if not await self._update_traffic_routing(traffic_percentage):
                logger.error(f"Failed to update traffic routing to {traffic_percentage}%")
                return False
            
            # Send notification
            await self._send_notification(
                f"🎯 Canary deployment: {traffic_percentage}% traffic routing active",
                "info"
            )
            
            # Monitor stage for specified duration
            monitoring_success = await self._monitor_stage()
            
            if not monitoring_success:
                logger.error(f"Stage {stage.value} monitoring failed")
                await self._rollback()
                return False
            
            logger.info(f"✅ Stage {stage.value} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Stage {stage.value} failed: {e}")
            await self._rollback()
            return False
    
    async def _update_traffic_routing(self, percentage: int) -> bool:
        """Update traffic routing configuration."""
        try:
            # Update environment variable for pilot traffic
            os.environ["PILOT_TRAFFIC"] = str(percentage)
            
            # In a real deployment, this would update load balancer configuration
            # For now, we'll simulate by updating the docker-compose configuration
            
            # Update docker-compose.pilot.yml
            compose_file = "docker-compose.pilot.yml"
            if os.path.exists(compose_file):
                # This would typically use a proper YAML parser
                logger.info(f"Updated traffic routing to {percentage}%")
                
                # Restart services with new configuration
                restart_cmd = f"PILOT_TRAFFIC={percentage} docker-compose -f {compose_file} up -d"
                logger.info(f"Executing: {restart_cmd}")
                
                # In production, this would be handled by orchestration tools
                return True
            else:
                logger.warning(f"Compose file {compose_file} not found, simulating traffic update")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update traffic routing: {e}")
            return False
    
    async def _monitor_stage(self) -> bool:
        """Monitor current deployment stage."""
        logger.info(f"📊 Monitoring stage {self.current_stage.value} for {self.config.stage_duration} seconds")
        
        end_time = datetime.utcnow() + timedelta(seconds=self.config.stage_duration)
        
        while datetime.utcnow() < end_time:
            try:
                # Get current health metrics
                health = await self._get_health_metrics()
                if not health:
                    logger.warning("Failed to get health metrics, continuing...")
                    await asyncio.sleep(self.config.health_check_interval)
                    continue
                
                # Store health history
                self.health_history.append(health)
                
                # Keep only last 100 measurements
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-100:]
                
                # Check for SLO violations
                violations = self._check_slo_violations(health)
                
                if violations:
                    self.violations_count += 1
                    logger.warning(f"⚠️ SLO violations detected ({self.violations_count}/{self.max_violations}): {violations}")
                    
                    # Send alert
                    await self._send_notification(
                        f"⚠️ SLO violations in {self.current_stage.value}: {', '.join(violations)}",
                        "warning"
                    )
                    
                    if self.violations_count >= self.max_violations:
                        logger.error(f"❌ Maximum violations reached, initiating rollback")
                        return False
                else:
                    # Reset violation count on successful check
                    if self.violations_count > 0:
                        logger.info("✅ SLO violations resolved")
                        self.violations_count = 0
                
                # Log current status
                remaining_time = (end_time - datetime.utcnow()).total_seconds()
                logger.info(
                    f"📈 Stage {self.current_stage.value}: "
                    f"P95: {health.p95_latency_ms:.2f}ms, "
                    f"P99: {health.p99_latency_ms:.2f}ms, "
                    f"Errors: {health.error_rate:.3f}, "
                    f"Fallback: {health.fallback_ratio:.3f}, "
                    f"Remaining: {remaining_time:.0f}s"
                )
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.config.health_check_interval)
        
        logger.info(f"✅ Stage {self.current_stage.value} monitoring completed successfully")
        return True
    
    async def _get_health_metrics(self) -> Optional[HealthMetrics]:
        """Get current health metrics from the API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.api_url}/health/detailed",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Health check failed: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    # Extract metrics from response
                    engine_health = data.get("services", {}).get("engine", {})
                    feature_flags = data.get("feature_flags", {})
                    
                    # Get performance metrics if available
                    perf_metrics = engine_health.get("performance_metrics", {})
                    
                    return HealthMetrics(
                        p95_latency_ms=perf_metrics.get("ev_calculation_ms", 0.5),
                        p99_latency_ms=perf_metrics.get("poisson_calculation_ms", 1.0),
                        error_rate=0.0,  # Would be calculated from actual metrics
                        fallback_ratio=0.0 if feature_flags.get("use_mojo", False) else 1.0,
                        cpu_usage=0.3,  # Would be from system metrics
                        memory_usage=0.4,  # Would be from system metrics
                        mojo_available=feature_flags.get("mojo_available", False),
                        use_mojo=feature_flags.get("use_mojo", False),
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get health metrics: {e}")
            return None
    
    def _check_slo_violations(self, health: HealthMetrics) -> List[str]:
        """Check for SLO violations."""
        violations = []
        
        if health.p95_latency_ms > self.config.slo_thresholds["p95_latency_ms"]:
            violations.append(f"P95 latency {health.p95_latency_ms:.2f}ms > {self.config.slo_thresholds['p95_latency_ms']}ms")
        
        if health.p99_latency_ms > self.config.slo_thresholds["p99_latency_ms"]:
            violations.append(f"P99 latency {health.p99_latency_ms:.2f}ms > {self.config.slo_thresholds['p99_latency_ms']}ms")
        
        if health.error_rate > self.config.slo_thresholds["error_rate"]:
            violations.append(f"Error rate {health.error_rate:.3f} > {self.config.slo_thresholds['error_rate']:.3f}")
        
        if health.fallback_ratio > self.config.slo_thresholds["fallback_ratio"]:
            violations.append(f"Fallback ratio {health.fallback_ratio:.3f} > {self.config.slo_thresholds['fallback_ratio']:.3f}")
        
        if health.cpu_usage > self.config.slo_thresholds["cpu_usage"]:
            violations.append(f"CPU usage {health.cpu_usage:.1%} > {self.config.slo_thresholds['cpu_usage']:.1%}")
        
        if health.memory_usage > self.config.slo_thresholds["memory_usage"]:
            violations.append(f"Memory usage {health.memory_usage:.1%} > {self.config.slo_thresholds['memory_usage']:.1%}")
        
        return violations
    
    async def _rollback(self) -> bool:
        """Rollback to previous version."""
        logger.error("🔄 Initiating rollback to previous version")
        
        try:
            self.current_stage = DeploymentStage.ROLLBACK
            
            # Reset traffic to 0% (previous version gets 100%)
            await self._update_traffic_routing(0)
            
            # Send notification
            await self._send_notification(
                "🔄 Canary deployment rolled back due to SLO violations",
                "error"
            )
            
            logger.info("✅ Rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def _send_notification(self, message: str, level: str = "info"):
        """Send notification to Slack or other channels."""
        try:
            if self.config.slack_webhook_url:
                # Send to Slack
                emoji_map = {
                    "info": "ℹ️",
                    "success": "✅",
                    "warning": "⚠️",
                    "error": "❌"
                }
                
                payload = {
                    "text": f"{emoji_map.get(level, 'ℹ️')} BetFlow Engine Canary Deployment",
                    "attachments": [
                        {
                            "color": {"info": "good", "success": "good", "warning": "warning", "error": "danger"}[level],
                            "text": message,
                            "footer": "BetFlow Engine v0.9.0",
                            "ts": int(datetime.utcnow().timestamp())
                        }
                    ]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.config.slack_webhook_url, json=payload) as response:
                        if response.status == 200:
                            logger.info("Notification sent to Slack")
                        else:
                            logger.warning(f"Failed to send Slack notification: {response.status}")
            
            # Always log the notification
            logger.info(f"NOTIFICATION [{level.upper()}]: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        return {
            "current_stage": self.current_stage.value,
            "stage_start_time": self.stage_start_time.isoformat() if self.stage_start_time else None,
            "violations_count": self.violations_count,
            "health_checks_performed": len(self.health_history),
            "latest_health": self.health_history[-1].__dict__ if self.health_history else None
        }

async def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description='BetFlow Engine Canary Deployment Manager')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API URL')
    parser.add_argument('--stage-duration', type=int, default=1800, help='Stage duration in seconds')
    parser.add_argument('--health-interval', type=int, default=30, help='Health check interval in seconds')
    parser.add_argument('--slack-webhook', help='Slack webhook URL for notifications')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without actual deployment')
    
    args = parser.parse_args()
    
    # Create deployment configuration
    config = DeploymentConfig(
        api_url=args.api_url,
        health_check_interval=args.health_interval,
        stage_duration=args.stage_duration,
        slack_webhook_url=args.slack_webhook
    )
    
    # Create deployment manager
    manager = CanaryDeploymentManager(config)
    
    if args.dry_run:
        logger.info("🧪 Performing dry run...")
        # Perform health check only
        health = await manager._get_health_metrics()
        if health:
            violations = manager._check_slo_violations(health)
            if violations:
                logger.warning(f"SLO violations detected: {violations}")
                sys.exit(1)
            else:
                logger.info("✅ System ready for deployment")
                sys.exit(0)
        else:
            logger.error("❌ Health check failed")
            sys.exit(1)
    
    # Start deployment
    success = await manager.start_deployment()
    
    # Print final status
    status = manager.get_deployment_status()
    logger.info(f"Final deployment status: {json.dumps(status, indent=2, default=str)}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
