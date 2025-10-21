"""
OddsAPI provider for external odds data.
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

class OddsAPIProvider(OddsProvider):
    """OddsAPI provider for external odds data."""
    
    def __init__(self):
        self.api_key = settings.ODDS_API_KEY
        self.base_url = "https://api.the-odds-api.com/v4"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def name(self) -> str:
        return "odds_api"
    
    @property
    def is_configured(self) -> bool:
        return self.api_key is not None and self.api_key != "your-odds-api-key"
    
    async def health_check(self) -> bool:
        """Check if OddsAPI is accessible."""
        if not self.is_configured:
            return False
        
        try:
            response = await self.client.get(
                f"{self.base_url}/sports",
                params={"apiKey": self.api_key}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OddsAPI health check failed: {e}")
            return False
    
    async def fetch_events(self, sport: Optional[str] = None,
                          date_from: Optional[date] = None,
                          date_to: Optional[date] = None,
                          league: Optional[str] = None) -> List[EventResponse]:
        """Fetch events from OddsAPI."""
        if not self.is_configured:
            logger.warning("OddsAPI not configured")
            return []
        
        try:
            # Get available sports first
            sports_response = await self.client.get(
                f"{self.base_url}/sports",
                params={"apiKey": self.api_key}
            )
            sports_response.raise_for_status()
            available_sports = sports_response.json()
            
            # Filter by sport if specified
            if sport:
                sport_key = next(
                    (s["key"] for s in available_sports if s["title"].lower() == sport.lower()),
                    None
                )
                if not sport_key:
                    logger.warning(f"Sport '{sport}' not found in OddsAPI")
                    return []
            else:
                sport_key = "soccer_epl"  # Default to Premier League
            
            # Fetch events
            events_response = await self.client.get(
                f"{self.base_url}/sports/{sport_key}/events",
                params={
                    "apiKey": self.api_key,
                    "commenceTimeFrom": date_from.isoformat() if date_from else None,
                    "commenceTimeTo": date_to.isoformat() if date_to else None,
                }
            )
            events_response.raise_for_status()
            events_data = events_response.json()
            
            # Convert to EventResponse objects
            events = []
            for event_data in events_data:
                # Parse start time
                start_time = datetime.fromisoformat(
                    event_data["commence_time"].replace("Z", "+00:00")
                )
                
                # Apply additional filters
                if league and event_data.get("sport_title", "").lower() != league.lower():
                    continue
                
                event = EventResponse(
                    id=uuid4(),
                    sport=event_data.get("sport_title", "").lower(),
                    league=event_data.get("sport_title", ""),
                    home_team=event_data["home_team"],
                    away_team=event_data["away_team"],
                    start_time=start_time,
                    status="scheduled",
                    venue=None,
                    weather=None
                )
                events.append(event)
            
            logger.info(f"Fetched {len(events)} events from OddsAPI")
            return events
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching events from OddsAPI: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching events from OddsAPI: {e}")
            return []
    
    async def fetch_odds(self, event_ids: List[str],
                        market: Optional[str] = None) -> List[OddsResponse]:
        """Fetch odds from OddsAPI."""
        if not self.is_configured:
            logger.warning("OddsAPI not configured")
            return []
        
        try:
            # Get available sports
            sports_response = await self.client.get(
                f"{self.base_url}/sports",
                params={"apiKey": self.api_key}
            )
            sports_response.raise_for_status()
            available_sports = sports_response.json()
            
            odds = []
            
            # Fetch odds for each sport
            for sport_data in available_sports:
                sport_key = sport_data["key"]
                
                try:
                    odds_response = await self.client.get(
                        f"{self.base_url}/sports/{sport_key}/odds",
                        params={
                            "apiKey": self.api_key,
                            "regions": "us,uk",
                            "markets": market or "h2h,spreads,totals",
                            "oddsFormat": "decimal",
                            "dateFormat": "iso"
                        }
                    )
                    odds_response.raise_for_status()
                    odds_data = odds_response.json()
                    
                    # Process odds data
                    for event_odds in odds_data:
                        event_id = event_odds.get("id")
                        if event_id not in event_ids:
                            continue
                        
                        # Process different markets
                        for bookmaker in event_odds.get("bookmakers", []):
                            book_name = bookmaker["title"]
                            
                            for market_data in bookmaker.get("markets", []):
                                market_name = market_data["key"]
                                
                                for outcome in market_data.get("outcomes", []):
                                    odds_response = OddsResponse(
                                        id=uuid4(),
                                        event_id=event_id,
                                        book=book_name,
                                        market=market_name,
                                        selection=outcome["name"],
                                        price=outcome["price"],
                                        line=outcome.get("point"),
                                        implied_probability=1.0 / outcome["price"],
                                        vig=None,  # Would need to calculate
                                        fetched_at=datetime.utcnow()
                                    )
                                    odds.append(odds_response)
                
                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch odds for {sport_key}: {e}")
                    continue
            
            logger.info(f"Fetched {len(odds)} odds from OddsAPI")
            return odds
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching odds from OddsAPI: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching odds from OddsAPI: {e}")
            return []
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
