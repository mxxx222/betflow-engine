"""
Football Over/Under 2.5 odds provider for MVP
Integrates with real odds APIs for production deployment
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class FootballMatch:
    """Football match data structure"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    start_time: datetime
    status: str
    over_2_5_odds: Optional[float] = None
    under_2_5_odds: Optional[float] = None
    bookmaker: str = ""
    last_updated: Optional[datetime] = None


class FootballOddsProvider:
    """Production football odds provider for Over/Under 2.5 markets"""
    
    def __init__(self, odds_api_key: str, sports_monks_key: str):
        self.odds_api_key = odds_api_key
        self.sports_monks_key = sports_monks_key
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_football_matches(self, leagues: List[str], days_ahead: int = 3) -> List[FootballMatch]:
        """Fetch football matches with Over/Under 2.5 odds"""
        matches = []
        
        # Fetch from multiple sources for redundancy
        tasks = [
            self._fetch_from_odds_api(leagues, days_ahead),
            self._fetch_from_sports_monks(leagues, days_ahead)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        all_matches = []
        for result in results:
            if isinstance(result, list):
                all_matches.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error fetching odds: {result}")
        
        # Deduplicate by match_id
        seen_matches = set()
        for match in all_matches:
            if match.match_id not in seen_matches:
                matches.append(match)
                seen_matches.add(match.match_id)
        
        return matches
    
    async def _fetch_from_odds_api(self, leagues: List[str], days_ahead: int) -> List[FootballMatch]:
        """Fetch from OddsAPI (primary source)"""
        if not self.odds_api_key:
            return []
            
        matches = []
        
        try:
            # OddsAPI uses league names like "soccer_epl", "soccer_championship"
            league_mapping = {
                "premier-league": "soccer_epl",
                "championship": "soccer_championship", 
                "bundesliga": "soccer_germany_bundesliga",
                "serie-a": "soccer_italy_serie_a",
                "la-liga": "soccer_spain_la_liga",
                "ligue-1": "soccer_france_ligue_one"
            }
            
            for league in leagues:
                if league not in league_mapping:
                    continue
                    
                odds_league = league_mapping[league]
                url = f"https://api.the-odds-api.com/v4/sports/{odds_league}/odds"
                
                params = {
                    "apiKey": self.odds_api_key,
                    "regions": "uk,eu,us",
                    "markets": "totals",
                    "oddsFormat": "decimal",
                    "dateFormat": "iso"
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches.extend(self._parse_odds_api_response(data, league))
                    else:
                        logger.warning(f"OddsAPI returned {response.status} for {league}")
                        
        except Exception as e:
            logger.error(f"Error fetching from OddsAPI: {e}")
            
        return matches
    
    async def _fetch_from_sports_monks(self, leagues: List[str], days_ahead: int) -> List[FootballMatch]:
        """Fetch from SportsMonks (backup source)"""
        if not self.sports_monks_key:
            return []
            
        matches = []
        
        try:
            # SportsMonks league IDs
            league_mapping = {
                "premier-league": 8,
                "championship": 9,
                "bundesliga": 82,
                "serie-a": 135,
                "la-liga": 564,
                "ligue-1": 301
            }
            
            for league in leagues:
                if league not in league_mapping:
                    continue
                    
                league_id = league_mapping[league]
                url = f"https://api.sportmonks.com/v3/football/fixtures/leagues/{league_id}"
                
                params = {
                    "api_token": self.sports_monks_key,
                    "include": "participants,odds",
                    "filters": "upcoming"
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches.extend(self._parse_sports_monks_response(data, league))
                    else:
                        logger.warning(f"SportsMonks returned {response.status} for {league}")
                        
        except Exception as e:
            logger.error(f"Error fetching from SportsMonks: {e}")
            
        return matches
    
    def _parse_odds_api_response(self, data: List[Dict], league: str) -> List[FootballMatch]:
        """Parse OddsAPI response for Over/Under 2.5 markets"""
        matches = []
        
        for fixture in data:
            try:
                # Extract match details
                home_team = fixture.get("home_team", "")
                away_team = fixture.get("away_team", "")
                start_time = datetime.fromisoformat(fixture.get("commence_time", "").replace("Z", "+00:00"))
                
                # Look for Over/Under 2.5 markets
                for bookmaker in fixture.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market.get("key") == "totals":
                            for outcome in market.get("outcomes", []):
                                if outcome.get("name") == "Over 2.5":
                                    over_odds = outcome.get("price")
                                elif outcome.get("name") == "Under 2.5":
                                    under_odds = outcome.get("price")
                    
                    # Create match if we found OU 2.5 odds
                    if "over_odds" in locals() and "under_odds" in locals():
                        match = FootballMatch(
                            match_id=f"odds_api_{fixture.get('id', '')}",
                            home_team=home_team,
                            away_team=away_team,
                            league=league,
                            start_time=start_time,
                            status="upcoming",
                            over_2_5_odds=over_odds,
                            under_2_5_odds=under_odds,
                            bookmaker=bookmaker.get("title", ""),
                            last_updated=datetime.utcnow()
                        )
                        matches.append(match)
                        
            except Exception as e:
                logger.error(f"Error parsing OddsAPI fixture: {e}")
                continue
                
        return matches
    
    def _parse_sports_monks_response(self, data: Dict, league: str) -> List[FootballMatch]:
        """Parse SportsMonks response for Over/Under 2.5 markets"""
        matches = []
        
        fixtures = data.get("data", [])
        
        for fixture in fixtures:
            try:
                # Extract match details
                participants = fixture.get("participants", [])
                if len(participants) < 2:
                    continue
                    
                home_team = participants[0].get("name", "")
                away_team = participants[1].get("name", "")
                start_time = datetime.fromisoformat(fixture.get("starting_at", "").replace("Z", "+00:00"))
                
                # Look for Over/Under 2.5 odds
                odds_data = fixture.get("odds", [])
                over_odds = None
                under_odds = None
                
                for odds in odds_data:
                    if odds.get("name") == "Over/Under 2.5":
                        for outcome in odds.get("outcomes", []):
                            if outcome.get("label") == "Over 2.5":
                                over_odds = outcome.get("odds")
                            elif outcome.get("label") == "Under 2.5":
                                under_odds = outcome.get("odds")
                
                # Create match if we found OU 2.5 odds
                if over_odds and under_odds:
                    match = FootballMatch(
                        match_id=f"sports_monks_{fixture.get('id', '')}",
                        home_team=home_team,
                        away_team=away_team,
                        league=league,
                        start_time=start_time,
                        status="upcoming",
                        over_2_5_odds=over_odds,
                        under_2_5_odds=under_odds,
                        bookmaker="SportsMonks",
                        last_updated=datetime.utcnow()
                    )
                    matches.append(match)
                    
            except Exception as e:
                logger.error(f"Error parsing SportsMonks fixture: {e}")
                continue
                
        return matches
    
    async def get_live_odds(self, match_id: str) -> Optional[Dict[str, float]]:
        """Get live odds for a specific match"""
        # This would be implemented for live trading (future phase)
        # For MVP, we focus on pre-match only
        return None
    
    def normalize_market_name(self, market_name: str) -> str:
        """Normalize market names to standard format"""
        normalizations = {
            "over/under 2.5": "over_under_2_5",
            "total goals 2.5": "over_under_2_5", 
            "ou 2.5": "over_under_2_5",
            "total 2.5": "over_under_2_5"
        }
        
        return normalizations.get(market_name.lower(), market_name.lower())
