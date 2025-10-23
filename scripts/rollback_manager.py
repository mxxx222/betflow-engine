#!/usr/bin/env python3
"""
Rollback Manager for Production Pilot
Handles rollback to previous version and canary deployment management
"""
import subprocess
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RollbackConfig:
    """Rollback configuration"""
    current_branch: str = "main"
    previous_branch: str = "previous-version"
    rollback_timeout: int = 300  # 5 minutes
    health_check_interval: int = 30  # 30 seconds
    max_health_checks: int = 10  # 5 minutes of health checks


class RollbackManager:
    """Manages rollback and canary deployment"""
    
    def __init__(self, config: RollbackConfig = None):
        self.config = config or RollbackConfig()
        self.rollback_history = []
        
    def prepare_rollback_path(self) -> bool:
        """Prepare rollback path by testing previous version"""
        logger.info("🔄 Preparing rollback path...")
        
        try:
            # Check current branch
            current_branch = self._get_current_branch()
            logger.info(f"📍 Current branch: {current_branch}")
            
            # Check if previous version exists
            if not self._branch_exists(self.config.previous_branch):
                logger.warning(f"⚠️ Previous version branch '{self.config.previous_branch}' not found")
                logger.info("💡 Creating previous version branch from current HEAD")
                self._create_previous_version_branch()
            
            # Test previous version (dry run)
            logger.info("🧪 Testing previous version (dry run)...")
            success = self._test_previous_version()
            
            if success:
                logger.info("✅ Rollback path prepared successfully")
                return True
            else:
                logger.error("❌ Rollback path preparation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error preparing rollback path: {e}")
            return False
    
    def execute_rollback(self) -> bool:
        """Execute rollback to previous version"""
        logger.info("🚨 Executing rollback to previous version...")
        
        try:
            # Record rollback start
            rollback_start = datetime.now()
            
            # Switch to previous version
            logger.info(f"🔄 Switching to {self.config.previous_branch}...")
            result = subprocess.run(
                ["git", "checkout", self.config.previous_branch],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to checkout {self.config.previous_branch}: {result.stderr}")
                return False
            
            # Build previous version
            logger.info("🔨 Building previous version...")
            build_success = self._build_previous_version()
            
            if not build_success:
                logger.error("❌ Failed to build previous version")
                return False
            
            # Start previous version
            logger.info("🚀 Starting previous version...")
            start_success = self._start_previous_version()
            
            if not start_success:
                logger.error("❌ Failed to start previous version")
                return False
            
            # Wait for health check
            logger.info("🏥 Waiting for health check...")
            health_success = self._wait_for_health()
            
            if not health_success:
                logger.error("❌ Health check failed after rollback")
                return False
            
            # Record successful rollback
            rollback_duration = (datetime.now() - rollback_start).total_seconds()
            
            rollback_record = {
                "timestamp": rollback_start.isoformat(),
                "duration_seconds": rollback_duration,
                "previous_branch": self.config.previous_branch,
                "success": True
            }
            
            self.rollback_history.append(rollback_record)
            
            logger.info(f"✅ Rollback completed successfully in {rollback_duration:.1f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            
            # Record failed rollback
            rollback_record = {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": 0,
                "previous_branch": self.config.previous_branch,
                "success": False,
                "error": str(e)
            }
            
            self.rollback_history.append(rollback_record)
            return False
    
    def return_to_current(self) -> bool:
        """Return to current version after rollback"""
        logger.info("🔄 Returning to current version...")
        
        try:
            # Switch back to current branch
            result = subprocess.run(
                ["git", "checkout", self.config.current_branch],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to checkout {self.config.current_branch}: {result.stderr}")
                return False
            
            logger.info(f"✅ Returned to {self.config.current_branch}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to return to current version: {e}")
            return False
    
    def _get_current_branch(self) -> str:
        """Get current git branch"""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to get current branch: {result.stderr}")
        
        return result.stdout.strip()
    
    def _branch_exists(self, branch: str) -> bool:
        """Check if branch exists"""
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return False
        
        return branch in result.stdout
    
    def _create_previous_version_branch(self) -> bool:
        """Create previous version branch from current HEAD"""
        try:
            # Create branch from current HEAD
            result = subprocess.run(
                ["git", "checkout", "-b", self.config.previous_branch],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Failed to create {self.config.previous_branch}: {result.stderr}")
                return False
            
            logger.info(f"✅ Created {self.config.previous_branch} branch")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating previous version branch: {e}")
            return False
    
    def _test_previous_version(self) -> bool:
        """Test previous version without swapping"""
        try:
            # Build previous version
            logger.info("🔨 Building previous version (test)...")
            build_result = subprocess.run(
                ["make", "build"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode != 0:
                logger.error(f"❌ Build failed: {build_result.stderr}")
                return False
            
            logger.info("✅ Previous version build successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing previous version: {e}")
            return False
    
    def _build_previous_version(self) -> bool:
        """Build previous version"""
        try:
            result = subprocess.run(
                ["make", "build"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Build failed: {result.stderr}")
                return False
            
            logger.info("✅ Build successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Build error: {e}")
            return False
    
    def _start_previous_version(self) -> bool:
        """Start previous version"""
        try:
            # Start services
            result = subprocess.run(
                ["make", "up"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Start failed: {result.stderr}")
                return False
            
            logger.info("✅ Services started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Start error: {e}")
            return False
    
    def _wait_for_health(self) -> bool:
        """Wait for health check to pass"""
        logger.info("🏥 Waiting for health check...")
        
        for attempt in range(self.config.max_health_checks):
            try:
                # Check health
                result = subprocess.run(
                    ["make", "health"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("✅ Health check passed")
                    return True
                
                logger.info(f"⏳ Health check attempt {attempt + 1}/{self.config.max_health_checks}")
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.warning(f"⚠️ Health check error: {e}")
                time.sleep(self.config.health_check_interval)
        
        logger.error("❌ Health check timeout")
        return False
    
    def get_rollback_status(self) -> Dict:
        """Get current rollback status"""
        current_branch = self._get_current_branch()
        previous_exists = self._branch_exists(self.config.previous_branch)
        
        return {
            "current_branch": current_branch,
            "previous_branch": self.config.previous_branch,
            "previous_exists": previous_exists,
            "rollback_history": self.rollback_history,
            "ready_for_rollback": previous_exists
        }
    
    def save_rollback_config(self, filepath: str):
        """Save rollback configuration"""
        config_data = {
            "config": self.config,
            "rollback_history": self.rollback_history,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"💾 Rollback config saved to {filepath}")


def main():
    """Main rollback manager function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rollback Manager for Production Pilot')
    parser.add_argument('--action', choices=['prepare', 'rollback', 'return', 'status'], 
                       default='prepare', help='Action to perform')
    parser.add_argument('--previous-branch', default='previous-version', 
                       help='Previous version branch name')
    parser.add_argument('--current-branch', default='main', 
                       help='Current branch name')
    
    args = parser.parse_args()
    
    # Create rollback manager
    config = RollbackConfig(
        current_branch=args.current_branch,
        previous_branch=args.previous_branch
    )
    
    manager = RollbackManager(config)
    
    if args.action == 'prepare':
        success = manager.prepare_rollback_path()
        if success:
            print("✅ Rollback path prepared successfully")
            sys.exit(0)
        else:
            print("❌ Rollback path preparation failed")
            sys.exit(1)
    
    elif args.action == 'rollback':
        success = manager.execute_rollback()
        if success:
            print("✅ Rollback executed successfully")
            sys.exit(0)
        else:
            print("❌ Rollback failed")
            sys.exit(1)
    
    elif args.action == 'return':
        success = manager.return_to_current()
        if success:
            print("✅ Returned to current version")
            sys.exit(0)
        else:
            print("❌ Failed to return to current version")
            sys.exit(1)
    
    elif args.action == 'status':
        status = manager.get_rollback_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
