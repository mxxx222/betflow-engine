#!/usr/bin/env python3
"""
Deploy BetFlow Engine MVP to Render
Automated deployment script for football OU 2.5 analytics platform
"""
import os
import subprocess
import json
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RenderDeployer:
    """Deploy BetFlow Engine to Render platform"""
    
    def __init__(self):
        self.render_token = os.getenv("RENDER_API_TOKEN")
        if not self.render_token:
            raise ValueError("RENDER_API_TOKEN environment variable required")
        
        self.project_name = "betflow-engine"
        self.services = {
            "api": {
                "name": "betflow-api",
                "type": "web",
                "env": "python",
                "plan": "starter"
            },
            "worker": {
                "name": "betflow-worker", 
                "type": "worker",
                "env": "python",
                "plan": "starter"
            },
            "web": {
                "name": "betflow-web",
                "type": "web", 
                "env": "node",
                "plan": "starter"
            }
        }
        
    def deploy(self):
        """Deploy all services to Render"""
        logger.info("Starting BetFlow Engine deployment to Render...")
        
        try:
            # 1. Create services
            self._create_services()
            
            # 2. Configure environment variables
            self._configure_environment()
            
            # 3. Deploy services
            self._deploy_services()
            
            # 4. Verify deployment
            self._verify_deployment()
            
            logger.info("✅ Deployment completed successfully!")
            self._print_service_urls()
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            raise
    
    def _create_services(self):
        """Create Render services"""
        logger.info("Creating Render services...")
        
        for service_name, config in self.services.items():
            logger.info(f"Creating {config['name']} service...")
            
            # Use Render CLI to create service
            cmd = [
                "render", "services", "create",
                "--name", config["name"],
                "--type", config["type"],
                "--env", config["env"],
                "--plan", config["plan"]
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"✅ Created {config['name']}")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to create {config['name']}: {e.stderr}")
                raise
    
    def _configure_environment(self):
        """Configure environment variables for all services"""
        logger.info("Configuring environment variables...")
        
        env_vars = {
            "DATABASE_URL": "postgresql://betflow_user:password@betflow-postgres:5432/betflow",
            "REDIS_URL": "redis://betflow-redis:6379",
            "API_RATE_LIMIT": "100",
            "JWT_SECRET": "your-jwt-secret-here",
            "ADMIN_EMAIL": "admin@betflow-engine.com",
            "PROVIDERS_ODDS_API_KEY": "YOUR_ODDS_API_KEY_HERE",
            "PROVIDERS_SPORTS_MONKS_KEY": "YOUR_SPORTS_MONKS_KEY_HERE",
            "N8N_WEBHOOK_URL": "https://betflow-worker.onrender.com/webhook",
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "INFO",
            "NEXT_PUBLIC_API_URL": "https://betflow-api.onrender.com"
        }
        
        for service_name, config in self.services.items():
            logger.info(f"Setting environment variables for {config['name']}...")
            
            for key, value in env_vars.items():
                cmd = [
                    "render", "env-vars", "set",
                    "--service", config["name"],
                    key, value
                ]
                
                try:
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to set {key} for {config['name']}: {e.stderr}")
    
    def _deploy_services(self):
        """Deploy all services"""
        logger.info("Deploying services...")
        
        for service_name, config in self.services.items():
            logger.info(f"Deploying {config['name']}...")
            
            cmd = [
                "render", "deploys", "create",
                "--service", config["name"]
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"✅ Deployed {config['name']}")
                
                # Wait for deployment to complete
                self._wait_for_deployment(config["name"])
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to deploy {config['name']}: {e.stderr}")
                raise
    
    def _wait_for_deployment(self, service_name: str, timeout: int = 300):
        """Wait for service deployment to complete"""
        logger.info(f"Waiting for {service_name} deployment...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                cmd = ["render", "services", "get", "--name", service_name]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                if "live" in result.stdout.lower():
                    logger.info(f"✅ {service_name} is live!")
                    return
                    
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(10)
        
        logger.warning(f"⚠️ {service_name} deployment timeout")
    
    def _verify_deployment(self):
        """Verify all services are running"""
        logger.info("Verifying deployment...")
        
        service_urls = {
            "api": "https://betflow-api.onrender.com/health",
            "web": "https://betflow-web.onrender.com",
            "worker": "https://betflow-worker.onrender.com"
        }
        
        for service, url in service_urls.items():
            try:
                import requests
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    logger.info(f"✅ {service} is responding")
                else:
                    logger.warning(f"⚠️ {service} returned {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ {service} verification failed: {e}")
    
    def _print_service_urls(self):
        """Print service URLs"""
        print("\n" + "="*60)
        print("🎯 BetFlow Engine MVP Deployment Complete!")
        print("="*60)
        print("\n📊 Service URLs:")
        print("• API: https://betflow-api.onrender.com")
        print("• Web Dashboard: https://betflow-web.onrender.com") 
        print("• Worker (n8n): https://betflow-worker.onrender.com")
        print("\n🔧 Next Steps:")
        print("1. Update API keys in Render dashboard")
        print("2. Run database migrations")
        print("3. Start odds collection workflows")
        print("4. Monitor signals in dashboard")
        print("\n⚽ Focus: Football Over/Under 2.5 markets")
        print("📈 Target: 2-5% monthly ROI with conservative staking")
        print("="*60)


def main():
    """Main deployment function"""
    try:
        deployer = RenderDeployer()
        deployer.deploy()
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
