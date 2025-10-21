"""
Selection Engine Live Pipeline
Deployed to Render with gatekeeper logic and real-time selection
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import json
from dataclasses import dataclass
import schedule
import time
from selection_logic import SelectionEngine, SelectionCriteria, Selection
from model_training import SelectionEngineModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LiveMatch:
    """Live match data structure"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    start_time: datetime
    profile: str
    features: Dict
    market_data: Dict


class LivePipeline:
    """Live selection pipeline for production deployment"""
    
    def __init__(self, api_url: str, webhook_url: str):
        self.api_url = api_url
        self.webhook_url = webhook_url
        self.selection_engine = SelectionEngine(SelectionCriteria())
        self.models = None
        self.active_selections = {}
        self.performance_metrics = {}
        
    async def initialize(self):
        """Initialize the live pipeline"""
        logger.info("Initializing live pipeline...")
        
        # Load models
        try:
            model_trainer = SelectionEngineModel()
            model_trainer.load_models('selection_engine/models.pkl')
            self.models = model_trainer.models
            self.selection_engine.load_models(self.models)
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
        
        # Start scheduled tasks
        self._setup_scheduler()
        
        logger.info("Live pipeline initialized")
        return True
    
    def _setup_scheduler(self):
        """Setup scheduled tasks"""
        # D-1h recompute (1 hour before matches)
        schedule.every().hour.do(self._recompute_selections)
        
        # D-30min recompute (30 minutes before matches)
        schedule.every(30).minutes.do(self._recompute_selections)
        
        # Daily performance update
        schedule.every().day.at("23:00").do(self._update_performance_metrics)
        
        logger.info("Scheduler setup complete")
    
    async def _recompute_selections(self):
        """Recompute selections for upcoming matches"""
        logger.info("Recomputing selections...")
        
        try:
            # Fetch upcoming matches
            upcoming_matches = await self._fetch_upcoming_matches()
            
            if not upcoming_matches:
                logger.info("No upcoming matches found")
                return
            
            # Process each profile
            for profile in ['profile_a', 'profile_b']:
                profile_matches = [m for m in upcoming_matches if m.profile == profile]
                
                if not profile_matches:
                    continue
                
                # Convert to DataFrame for selection engine
                df = self._matches_to_dataframe(profile_matches)
                
                # Get selections
                selections = self.selection_engine.select_matches(df, profile)
                
                # Apply gatekeeper logic
                qualified_selections = self._apply_gatekeeper(selections)
                
                # Send alerts for qualified selections
                if qualified_selections:
                    await self._send_selection_alerts(qualified_selections)
                
                logger.info(f"Processed {len(profile_matches)} matches for {profile}, {len(qualified_selections)} qualified")
        
        except Exception as e:
            logger.error(f"Error in recompute_selections: {e}")
    
    async def _fetch_upcoming_matches(self) -> List[LiveMatch]:
        """Fetch upcoming matches from API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch from API
                url = f"{self.api_url}/mvp/events/football"
                params = {
                    'leagues': 'premier-league,championship,bundesliga,serie-a,la-liga,ucl',
                    'days_ahead': 2
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_matches(data)
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []
    
    def _parse_matches(self, data: List[Dict]) -> List[LiveMatch]:
        """Parse API response into LiveMatch objects"""
        matches = []
        
        for match_data in data:
            # Determine profile
            league = match_data.get('league', '')
            is_weekend = match_data.get('is_weekend', False)
            is_ucl = league == 'ucl'
            is_top5 = league in ['premier-league', 'la-liga', 'bundesliga', 'serie-a', 'ligue-1']
            
            if is_ucl:
                profile = 'profile_b'
            elif is_weekend and is_top5:
                profile = 'profile_a'
            else:
                continue  # Skip non-target matches
            
            # Create LiveMatch
            match = LiveMatch(
                match_id=match_data.get('id', ''),
                home_team=match_data.get('home_team', ''),
                away_team=match_data.get('away_team', ''),
                league=league,
                start_time=datetime.fromisoformat(match_data.get('start_time', '')),
                profile=profile,
                features=self._extract_features(match_data),
                market_data=self._extract_market_data(match_data)
            )
            
            matches.append(match)
        
        return matches
    
    def _extract_features(self, match_data: Dict) -> Dict:
        """Extract features from match data"""
        return {
            'home_xg': match_data.get('home_xg', 0),
            'away_xg': match_data.get('away_xg', 0),
            'home_xga': match_data.get('home_xga', 0),
            'away_xga': match_data.get('away_xga', 0),
            'home_form_5': match_data.get('home_form_5', 0.5),
            'away_form_5': match_data.get('away_form_5', 0.5),
            'home_rest_days': match_data.get('home_rest_days', 7),
            'away_rest_days': match_data.get('away_rest_days', 7),
            'lineup_confirmed': match_data.get('lineup_confirmed', False),
            'weather_impact': match_data.get('weather_impact', 0)
        }
    
    def _extract_market_data(self, match_data: Dict) -> Dict:
        """Extract market data from match data"""
        return {
            'opening_over_odds': match_data.get('opening_over_odds', 2.0),
            'opening_under_odds': match_data.get('opening_under_odds', 2.0),
            'closing_over_odds': match_data.get('closing_over_odds', 2.0),
            'closing_under_odds': match_data.get('closing_under_odds', 2.0),
            'market_drift_24h': match_data.get('market_drift_24h', 0),
            'market_drift_1h': match_data.get('market_drift_1h', 0)
        }
    
    def _matches_to_dataframe(self, matches: List[LiveMatch]) -> pd.DataFrame:
        """Convert LiveMatch objects to DataFrame"""
        data = []
        
        for match in matches:
            row = {
                'match_id': match.match_id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'league': match.league,
                'date': match.start_time,
                'profile_a': 1 if match.profile == 'profile_a' else 0,
                'profile_b': 1 if match.profile == 'profile_b' else 0,
                'is_weekend': match.start_time.weekday() >= 5,
                'is_ucl': match.league == 'ucl',
                'is_top5': match.league in ['premier-league', 'la-liga', 'bundesliga', 'serie-a', 'ligue-1']
            }
            
            # Add features
            row.update(match.features)
            row.update(match.market_data)
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def _apply_gatekeeper(self, selections: List[Selection]) -> List[Selection]:
        """Apply gatekeeper logic to filter selections"""
        qualified = []
        
        for selection in selections:
            # Check confidence bucket
            if selection.confidence < 0.75:  # Only 75%+ for live
                continue
            
            # Check edge requirements
            if selection.edge < 0.04:  # 4% minimum edge
                continue
            
            # Check CLV
            if selection.clv < 0.02:  # 2% minimum CLV
                continue
            
            # Check lineup confirmation for UCL
            if selection.profile == 'profile_b' and not selection.features.get('lineup_confirmed', False):
                continue
            
            # Check market stability
            if abs(selection.features.get('market_drift_1h', 0)) > 0.05:  # 5% max drift
                continue
            
            # Check limit proxy (simplified)
            if selection.odds < 1.5 or selection.odds > 3.0:  # Reasonable odds range
                continue
            
            qualified.append(selection)
        
        return qualified
    
    async def _send_selection_alerts(self, selections: List[Selection]):
        """Send alerts for qualified selections"""
        for selection in selections:
            try:
                # Create alert message
                message = self._create_alert_message(selection)
                
                # Send to webhook
                async with aiohttp.ClientSession() as session:
                    payload = {
                        'text': message,
                        'attachments': [{
                            'color': 'good',
                            'fields': [
                                {'title': 'Match', 'value': f"{selection.home_team} vs {selection.away_team}", 'short': True},
                                {'title': 'Selection', 'value': selection.selection_type.upper(), 'short': True},
                                {'title': 'Confidence', 'value': f"{selection.confidence:.1%}", 'short': True},
                                {'title': 'Edge', 'value': f"{selection.edge:.1%}", 'short': True},
                                {'title': 'CLV', 'value': f"{selection.clv:.1%}", 'short': True},
                                {'title': 'Stake', 'value': f"{selection.stake_percentage:.1%}", 'short': True},
                                {'title': 'Odds', 'value': f"{selection.odds:.2f}", 'short': True},
                                {'title': 'Cutoff', 'value': selection.cutoff_time.strftime('%H:%M'), 'short': True}
                            ]
                        }]
                    }
                    
                    async with session.post(self.webhook_url, json=payload) as response:
                        if response.status == 200:
                            logger.info(f"Alert sent for {selection.match_id}")
                        else:
                            logger.error(f"Failed to send alert: {response.status}")
            
            except Exception as e:
                logger.error(f"Error sending alert for {selection.match_id}: {e}")
    
    def _create_alert_message(self, selection: Selection) -> str:
        """Create alert message for selection"""
        bucket = "80%+" if selection.confidence >= 0.80 else "75-79%"
        
        message = f"""
🎯 **Qualified Selection - {bucket} Confidence**

**{selection.home_team} vs {selection.away_team}**
• **Selection**: {selection.selection_type.upper()}
• **Confidence**: {selection.confidence:.1%}
• **Edge**: {selection.edge:.1%}
• **CLV**: {selection.clv:.1%}
• **Stake**: {selection.stake_percentage:.1%} (${selection.stake_amount:.2f})
• **Odds**: {selection.odds:.2f}
• **Cutoff**: {selection.cutoff_time.strftime('%H:%M')}
• **League**: {selection.league.upper()}
        """.strip()
        
        return message
    
    async def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Calculate daily metrics
            metrics = self._calculate_daily_metrics()
            
            # Store metrics
            self.performance_metrics[datetime.now().date()] = metrics
            
            # Send performance report
            await self._send_performance_report(metrics)
            
            logger.info("Performance metrics updated")
        
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _calculate_daily_metrics(self) -> Dict:
        """Calculate daily performance metrics"""
        # This would calculate actual performance from results
        # For now, return simulated metrics
        
        return {
            'date': datetime.now().date(),
            'selections': len(self.active_selections),
            'qualified_today': 0,  # Would be calculated from actual data
            'hit_rate': 0.0,  # Would be calculated from actual results
            'roi': 0.0,  # Would be calculated from actual results
            'avg_confidence': 0.0,  # Would be calculated from actual data
            'avg_edge': 0.0  # Would be calculated from actual data
        }
    
    async def _send_performance_report(self, metrics: Dict):
        """Send daily performance report"""
        try:
            message = f"""
📊 **Daily Performance Report - {metrics['date']}**

• **Active Selections**: {metrics['selections']}
• **Qualified Today**: {metrics['qualified_today']}
• **Hit Rate**: {metrics['hit_rate']:.1%}
• **ROI**: {metrics['roi']:.2%}
• **Avg Confidence**: {metrics['avg_confidence']:.1%}
• **Avg Edge**: {metrics['avg_edge']:.1%}
            """.strip()
            
            async with aiohttp.ClientSession() as session:
                payload = {'text': message}
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Performance report sent")
                    else:
                        logger.error(f"Failed to send performance report: {response.status}")
        
        except Exception as e:
            logger.error(f"Error sending performance report: {e}")
    
    async def run(self):
        """Run the live pipeline"""
        logger.info("Starting live pipeline...")
        
        # Initialize
        if not await self.initialize():
            logger.error("Failed to initialize pipeline")
            return
        
        # Main loop
        while True:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
            
            except KeyboardInterrupt:
                logger.info("Pipeline stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying


async def main():
    """Main function for live pipeline"""
    # Configuration
    API_URL = "https://betflow-api.onrender.com"
    WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    
    # Initialize and run pipeline
    pipeline = LivePipeline(API_URL, WEBHOOK_URL)
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
