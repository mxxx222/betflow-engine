"""
Local CSV provider for demo data.
"""

import csv
import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .base import OddsProvider
from ..models.schemas import EventResponse, OddsResponse

class LocalCSVProvider(OddsProvider):
    """Local CSV provider for demo data."""
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = data_dir
        self.events_file = os.path.join(data_dir, "events.csv")
        self.odds_file = os.path.join(data_dir, "odds.csv")
    
    @property
    def name(self) -> str:
        return "local_csv"
    
    @property
    def is_configured(self) -> bool:
        return os.path.exists(self.events_file) and os.path.exists(self.odds_file)
    
    async def health_check(self) -> bool:
        """Check if CSV files exist and are readable."""
        try:
            if not self.is_configured:
                return False
            
            # Try to read first line of each file
            with open(self.events_file, 'r') as f:
                next(csv.reader(f))
            
            with open(self.odds_file, 'r') as f:
                next(csv.reader(f))
            
            return True
        except Exception:
            return False
    
    async def fetch_events(self, sport: Optional[str] = None,
                          date_from: Optional[date] = None,
                          date_to: Optional[date] = None,
                          league: Optional[str] = None) -> List[EventResponse]:
        """Fetch events from CSV file."""
        if not self.is_configured:
            return []
        
        events = []
        
        try:
            with open(self.events_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse event data
                    event_date = datetime.fromisoformat(row['start_time'])
                    
                    # Apply filters
                    if sport and row['sport'] != sport:
                        continue
                    if league and row['league'] != league:
                        continue
                    if date_from and event_date.date() < date_from:
                        continue
                    if date_to and event_date.date() > date_to:
                        continue
                    
                    # Create event response
                    event = EventResponse(
                        id=uuid4(),
                        sport=row['sport'],
                        league=row['league'],
                        home_team=row['home_team'],
                        away_team=row['away_team'],
                        start_time=event_date,
                        status=row.get('status', 'scheduled'),
                        home_score=int(row['home_score']) if row.get('home_score') else None,
                        away_score=int(row['away_score']) if row.get('away_score') else None,
                        venue=row.get('venue'),
                        weather=row.get('weather', {})
                    )
                    events.append(event)
            
            return events
            
        except Exception as e:
            print(f"Error reading events CSV: {e}")
            return []
    
    async def fetch_odds(self, event_ids: List[str],
                        market: Optional[str] = None) -> List[OddsResponse]:
        """Fetch odds from CSV file."""
        if not self.is_configured:
            return []
        
        odds = []
        
        try:
            with open(self.odds_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check if event_id matches
                    if row['event_id'] not in event_ids:
                        continue
                    
                    # Apply market filter
                    if market and row['market'] != market:
                        continue
                    
                    # Create odds response
                    odds_response = OddsResponse(
                        id=uuid4(),
                        event_id=row['event_id'],
                        book=row['book'],
                        market=row['market'],
                        selection=row['selection'],
                        price=float(row['price']),
                        line=float(row['line']) if row.get('line') else None,
                        implied_probability=float(row['implied_probability']) if row.get('implied_probability') else None,
                        vig=float(row['vig']) if row.get('vig') else None,
                        fetched_at=datetime.fromisoformat(row['fetched_at'])
                    )
                    odds.append(odds_response)
            
            return odds
            
        except Exception as e:
            print(f"Error reading odds CSV: {e}")
            return []
    
    def generate_demo_data(self, num_events: int = 50):
        """Generate demo data for testing."""
        import random
        
        sports = ["football", "basketball", "tennis", "soccer"]
        leagues = ["premier_league", "nba", "wimbledon", "champions_league"]
        teams = [
            "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United",
            "Lakers", "Warriors", "Celtics", "Heat", "Bulls",
            "Federer", "Nadal", "Djokovic", "Murray", "Zverev",
            "Barcelona", "Real Madrid", "Bayern Munich", "PSG", "Juventus"
        ]
        books = ["bet365", "William Hill", "Paddy Power", "Betfair", "Unibet"]
        markets = ["1X2", "moneyline", "totals", "spread"]
        
        # Generate events
        events_data = []
        for i in range(num_events):
            sport = random.choice(sports)
            league = random.choice(leagues)
            home_team = random.choice(teams)
            away_team = random.choice([t for t in teams if t != home_team])
            
            start_time = datetime.now() + timedelta(days=random.randint(0, 30))
            
            event_data = {
                'id': f"evt_{i+1:03d}",
                'sport': sport,
                'league': league,
                'home_team': home_team,
                'away_team': away_team,
                'start_time': start_time.isoformat(),
                'status': 'scheduled',
                'home_score': None,
                'away_score': None,
                'venue': f"Stadium {i+1}",
                'weather': '{"temperature": 20, "condition": "clear"}'
            }
            events_data.append(event_data)
        
        # Generate odds
        odds_data = []
        for event in events_data:
            for book in books:
                for market in markets:
                    if market == "1X2":
                        selections = ["home", "draw", "away"]
                    elif market == "moneyline":
                        selections = ["home", "away"]
                    elif market == "totals":
                        selections = ["over_2.5", "under_2.5"]
                    else:  # spread
                        selections = ["home_spread", "away_spread"]
                    
                    for selection in selections:
                        # Generate realistic odds
                        base_prob = random.uniform(0.2, 0.8)
                        vig = random.uniform(0.05, 0.15)
                        price = (1.0 / base_prob) * (1.0 + vig)
                        
                        odds_data.append({
                            'id': f"odds_{len(odds_data)+1:04d}",
                            'event_id': event['id'],
                            'book': book,
                            'market': market,
                            'selection': selection,
                            'price': round(price, 2),
                            'line': round(random.uniform(-5, 5), 1) if market in ["spread", "totals"] else None,
                            'implied_probability': round(1.0 / price, 3),
                            'vig': round(vig, 3),
                            'fetched_at': datetime.now().isoformat()
                        })
        
        # Write to CSV files
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Write events
        with open(self.events_file, 'w', newline='') as f:
            if events_data:
                writer = csv.DictWriter(f, fieldnames=events_data[0].keys())
                writer.writeheader()
                writer.writerows(events_data)
        
        # Write odds
        with open(self.odds_file, 'w', newline='') as f:
            if odds_data:
                writer = csv.DictWriter(f, fieldnames=odds_data[0].keys())
                writer.writeheader()
                writer.writerows(odds_data)
        
        print(f"Generated {len(events_data)} events and {len(odds_data)} odds records")
