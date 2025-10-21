"""
SportsMonks provider for sports data.
"""

import httpx
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .base import OddsProvider
from ..models.schemas import EventResponse, OddsResponse
from ...core.config import settings

logger = logging.getLogger(__name__)

class SportsMonksProvider(OddsProvider):
    """SportsMonks provider for sports data."""
    
    def __init__(self):
        self.api_key = settings.SPORTS_MONKS_KEY
        self.base_url = "https://api.sportmonks.com/v3/football"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def name(self) -> str:
        return "sports_monks"
    
    @property
    def is_configured(self) -> bool:
        return self.api_key is not None and self.api_key != "your-sports-monks-key"
    
    async def health_check(self) -> bool:
        """Check if SportsMonks API is accessible."""
        if not self.is_configured:
            return False
        
        try:
            response = await self.client.get(
                f"{self.base_url}/countries",
                params={"api_token": self.api_key}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SportsMonks health check failed: {e}")
            return False
    
    async def fetch_events(self, sport: Optional[str] = None,
                          date_from: Optional[date] = None,
                          date_to: Optional[date] = None,
                          league: Optional[str] = None) -> List[EventResponse]:
        """Fetch events from SportsMonks."""
        if not self.is_configured:
            logger.warning("SportsMonks not configured")
            return []
        
        try:
            # Build date filter
            date_filter = {}
            if date_from:
                date_filter["from"] = date_from.isoformat()
            if date_to:
                date_filter["to"] = date_to.isoformat()
            
            # Fetch fixtures
            response = await self.client.get(
                f"{self.base_url}/fixtures",
                params={
                    "api_token": self.api_key,
                    "include": "participants,league",
                    **date_filter
                }
            )
            response.raise_for_status()
            fixtures_data = response.json()
            
            events = []
            for fixture in fixtures_data.get("data", []):
                # Parse fixture data
                participants = fixture.get("participants", [])
                if len(participants) < 2:
                    continue
                
                home_team = participants[0]["name"]
                away_team = participants[1]["name"]
                
                # Parse start time
                start_time = datetime.fromisoformat(
                    fixture["starting_at"].replace("Z", "+00:00")
                )
                
                # Get league info
                league_info = fixture.get("league", {})
                league_name = league_info.get("name", "Unknown")
                
                # Apply filters
                if sport and sport.lower() != "football":
                    continue
                if league and league_name.lower() != league.lower():
                    continue
                
                event = EventResponse(
                    id=uuid4(),
                    sport="football",
                    league=league_name,
                    home_team=home_team,
                    away_team=away_team,
                    start_time=start_time,
                    status=fixture.get("state", "scheduled"),
                    home_score=fixture.get("scores", {}).get("home"),
                    away_score=fixture.get("scores", {}).get("away"),
                    venue=fixture.get("venue", {}).get("name"),
                    weather=None
                )
                events.append(event)
            
            logger.info(f"Fetched {len(events)} events from SportsMonks")
            return events
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching events from SportsMonks: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching events from SportsMonks: {e}")
            return []
    
    async def fetch_odds(self, event_ids: List[str],
                        market: Optional[str] = None) -> List[OddsResponse]:
        """Fetch odds from SportsMonks."""
        if not self.is_configured:
            logger.warning("SportsMonks not configured")
            return []
        
        try:
            odds = []
            
            # SportsMonks doesn't provide odds directly
            # This would need to be implemented based on their odds API
            # For now, return empty list
            logger.info("SportsMonks odds fetching not implemented")
            return odds
            
        except Exception as e:
            logger.error(f"Error fetching odds from SportsMonks: {e}")
            return []
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
