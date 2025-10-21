#!/usr/bin/env python3
"""
Demo data seeding script for BetFlow Engine.
Generates realistic demo data for testing and development.
"""

import asyncio
import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from api.core.database import AsyncSessionLocal, init_db
from api.models.events import Event
from api.models.odds import Odds
from api.models.models import Model
from api.models.api_keys import APIKey
from api.models.signals import Signal
from api.core.security import security_manager

class DemoDataGenerator:
    """Generate realistic demo data for BetFlow Engine."""
    
    def __init__(self):
        self.sports = ["football", "basketball", "tennis", "soccer", "hockey", "baseball"]
        self.leagues = {
            "football": ["premier_league", "la_liga", "bundesliga", "serie_a", "champions_league"],
            "basketball": ["nba", "euroleague", "wnba"],
            "tennis": ["wimbledon", "us_open", "french_open", "australian_open"],
            "soccer": ["mls", "liga_mx", "brasileirao"],
            "hockey": ["nhl", "khl", "shl"],
            "baseball": ["mlb", "npb", "kbo"]
        }
        self.teams = {
            "football": ["Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United", 
                        "Barcelona", "Real Madrid", "Bayern Munich", "PSG", "Juventus"],
            "basketball": ["Lakers", "Warriors", "Celtics", "Heat", "Bulls", "Knicks", "Nets", "Spurs"],
            "tennis": ["Federer", "Nadal", "Djokovic", "Murray", "Zverev", "Medvedev", "Tsitsipas"],
            "soccer": ["LA Galaxy", "Seattle Sounders", "Atlanta United", "NYC FC", "Portland Timbers"],
            "hockey": ["Rangers", "Islanders", "Devils", "Bruins", "Maple Leafs", "Canadiens"],
            "baseball": ["Yankees", "Red Sox", "Dodgers", "Giants", "Cubs", "Cardinals"]
        }
        self.books = ["bet365", "William Hill", "Paddy Power", "Betfair", "Unibet", "DraftKings", "FanDuel"]
        self.markets = ["1X2", "moneyline", "totals", "spread", "both_teams_score", "correct_score"]
        
    async def generate_events(self, num_events: int = 100) -> list:
        """Generate demo events."""
        events = []
        start_date = datetime.now() + timedelta(days=1)
        
        for i in range(num_events):
            sport = random.choice(self.sports)
            league = random.choice(self.leagues[sport])
            home_team = random.choice(self.teams[sport])
            away_team = random.choice([t for t in self.teams[sport] if t != home_team])
            
            # Random start time in next 30 days
            start_time = start_date + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.choice([0, 15, 30, 45])
            )
            
            event = {
                "id": f"evt_{i+1:04d}",
                "sport": sport,
                "league": league,
                "home_team": home_team,
                "away_team": away_team,
                "start_time": start_time.isoformat(),
                "status": "scheduled",
                "home_score": None,
                "away_score": None,
                "venue": f"Stadium {i+1}",
                "weather": {
                    "temperature": random.randint(15, 35),
                    "condition": random.choice(["clear", "cloudy", "rainy", "snowy"]),
                    "humidity": random.randint(30, 90)
                }
            }
            events.append(event)
        
        return events
    
    async def generate_odds(self, events: list, num_odds_per_event: int = 20) -> list:
        """Generate demo odds for events."""
        odds = []
        
        for event in events:
            for _ in range(num_odds_per_event):
                book = random.choice(self.books)
                market = random.choice(self.markets)
                
                # Generate realistic odds
                if market == "1X2":
                    selections = ["home", "draw", "away"]
                elif market == "moneyline":
                    selections = ["home", "away"]
                elif market == "totals":
                    selections = ["over_2.5", "under_2.5", "over_3.5", "under_3.5"]
                elif market == "spread":
                    selections = ["home_spread", "away_spread"]
                elif market == "both_teams_score":
                    selections = ["yes", "no"]
                else:  # correct_score
                    selections = ["1-0", "2-0", "2-1", "0-1", "1-1", "0-0"]
                
                selection = random.choice(selections)
                
                # Generate realistic odds
                base_prob = random.uniform(0.2, 0.8)
                vig = random.uniform(0.05, 0.15)
                price = (1.0 / base_prob) * (1.0 + vig)
                
                odds.append({
                    "id": f"odds_{len(odds)+1:05d}",
                    "event_id": event["id"],
                    "book": book,
                    "market": market,
                    "selection": selection,
                    "price": round(price, 2),
                    "line": round(random.uniform(-5, 5), 1) if market in ["spread", "totals"] else None,
                    "implied_probability": round(1.0 / price, 3),
                    "vig": round(vig, 3),
                    "fetched_at": datetime.now().isoformat()
                })
        
        return odds
    
    async def generate_signals(self, events: list, num_signals: int = 50) -> list:
        """Generate demo signals."""
        signals = []
        
        for i in range(num_signals):
            event = random.choice(events)
            market = random.choice(self.markets)
            
            # Generate realistic signal data
            implied_prob = random.uniform(0.3, 0.7)
            fair_prob = implied_prob * random.uniform(0.8, 1.2)
            edge = (fair_prob * (1.0 / implied_prob)) - 1.0
            
            # Only include signals with positive edge
            if edge > 0.01:
                signal = {
                    "id": f"sig_{i+1:04d}",
                    "event_id": event["id"],
                    "market": market,
                    "signal_type": "edge",
                    "implied_probability": round(implied_prob, 3),
                    "fair_odds": round(1.0 / fair_prob, 2),
                    "best_book_odds": round(1.0 / implied_prob, 2),
                    "edge": round(edge, 3),
                    "confidence": round(random.uniform(0.6, 0.95), 2),
                    "risk_note": "Educational analytics only",
                    "explanation": f"Fair probability: {fair_prob:.3f}, Edge: {edge:.3f}",
                    "model_version": "1.0.0",
                    "status": "active",
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                signals.append(signal)
        
        return signals
    
    async def generate_models(self) -> list:
        """Generate demo models."""
        models = [
            {
                "id": "model_001",
                "name": "ELO Rating System",
                "version": "1.0.0",
                "model_type": "elo",
                "parameters": {
                    "k_factor": 32.0,
                    "home_advantage": 50.0,
                    "initial_rating": 1500.0
                },
                "performance_metrics": {
                    "accuracy": 0.68,
                    "precision": 0.72,
                    "recall": 0.65,
                    "f1_score": 0.68
                },
                "training_data_size": 1000,
                "accuracy": 0.68,
                "last_trained": datetime.now().isoformat(),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": "model_002",
                "name": "Poisson Goals Model",
                "version": "1.0.0",
                "model_type": "poisson",
                "parameters": {
                    "home_rate": 1.5,
                    "away_rate": 1.2,
                    "max_goals": 6
                },
                "performance_metrics": {
                    "accuracy": 0.62,
                    "precision": 0.58,
                    "recall": 0.70,
                    "f1_score": 0.63
                },
                "training_data_size": 800,
                "accuracy": 0.62,
                "last_trained": datetime.now().isoformat(),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": "model_003",
                "name": "Expected Value Calculator",
                "version": "1.0.0",
                "model_type": "ev",
                "parameters": {
                    "min_edge": 0.05,
                    "confidence_threshold": 0.70
                },
                "performance_metrics": {
                    "accuracy": 0.75,
                    "precision": 0.78,
                    "recall": 0.72,
                    "f1_score": 0.75
                },
                "training_data_size": 600,
                "accuracy": 0.75,
                "last_trained": datetime.now().isoformat(),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        return models
    
    async def generate_api_keys(self) -> list:
        """Generate demo API keys."""
        api_keys = []
        
        # Generate demo API key
        api_key, hashed_key = security_manager.create_api_key(
            client="demo_client",
            scope="read",
            expires_days=365
        )
        
        api_keys.append({
            "id": "api_key_001",
            "client": "demo_client",
            "hash": hashed_key,
            "scope": "read",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
            "description": "Demo API key for testing"
        })
        
        return api_keys, api_key
    
    async def save_to_csv(self, data: list, filename: str):
        """Save data to CSV file."""
        if not data:
            return
        
        filepath = Path("data") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Saved {len(data)} records to {filepath}")
    
    async def seed_database(self):
        """Seed database with demo data."""
        print("Starting database seeding...")
        
        # Initialize database
        await init_db()
        
        # Generate demo data
        print("Generating demo data...")
        events = await self.generate_events(100)
        odds = await self.generate_odds(events, 20)
        signals = await self.generate_signals(events, 50)
        models = await self.generate_models()
        api_keys, demo_api_key = await self.generate_api_keys()
        
        # Save to CSV files
        print("Saving CSV files...")
        await self.save_to_csv(events, "events.csv")
        await self.save_to_csv(odds, "odds.csv")
        await self.save_to_csv(signals, "signals.csv")
        await self.save_to_csv(models, "models.csv")
        await self.save_to_csv(api_keys, "api_keys.csv")
        
        # Seed database
        print("Seeding database...")
        async with AsyncSessionLocal() as db:
            try:
                # Create events
                for event_data in events:
                    event = Event(
                        id=uuid.UUID(event_data["id"]),
                        sport=event_data["sport"],
                        league=event_data["league"],
                        home_team=event_data["home_team"],
                        away_team=event_data["away_team"],
                        start_time=datetime.fromisoformat(event_data["start_time"]),
                        status=event_data["status"],
                        venue=event_data["venue"],
                        weather=event_data["weather"]
                    )
                    db.add(event)
                
                # Create odds
                for odds_data in odds:
                    odds = Odds(
                        id=uuid.UUID(odds_data["id"]),
                        event_id=uuid.UUID(odds_data["event_id"]),
                        book=odds_data["book"],
                        market=odds_data["market"],
                        selection=odds_data["selection"],
                        price=odds_data["price"],
                        line=odds_data["line"],
                        implied_probability=odds_data["implied_probability"],
                        vig=odds_data["vig"],
                        fetched_at=datetime.fromisoformat(odds_data["fetched_at"])
                    )
                    db.add(odds)
                
                # Create signals
                for signal_data in signals:
                    signal = Signal(
                        id=uuid.UUID(signal_data["id"]),
                        event_id=uuid.UUID(signal_data["event_id"]),
                        market=signal_data["market"],
                        signal_type=signal_data["signal_type"],
                        metrics={
                            "implied_probability": signal_data["implied_probability"],
                            "fair_odds": signal_data["fair_odds"],
                            "edge": signal_data["edge"]
                        },
                        implied_probability=signal_data["implied_probability"],
                        fair_odds=signal_data["fair_odds"],
                        best_book_odds=signal_data["best_book_odds"],
                        edge=signal_data["edge"],
                        confidence=signal_data["confidence"],
                        risk_note=signal_data["risk_note"],
                        explanation=signal_data["explanation"],
                        model_version=signal_data["model_version"],
                        status=signal_data["status"],
                        expires_at=datetime.fromisoformat(signal_data["expires_at"]),
                        created_at=datetime.fromisoformat(signal_data["created_at"])
                    )
                    db.add(signal)
                
                # Create models
                for model_data in models:
                    model = Model(
                        id=uuid.UUID(model_data["id"]),
                        name=model_data["name"],
                        version=model_data["version"],
                        model_type=model_data["model_type"],
                        parameters=model_data["parameters"],
                        performance_metrics=model_data["performance_metrics"],
                        training_data_size=model_data["training_data_size"],
                        accuracy=model_data["accuracy"],
                        last_trained=datetime.fromisoformat(model_data["last_trained"]),
                        status=model_data["status"],
                        created_at=datetime.fromisoformat(model_data["created_at"]),
                        updated_at=datetime.fromisoformat(model_data["updated_at"])
                    )
                    db.add(model)
                
                # Create API keys
                for api_key_data in api_keys:
                    api_key = APIKey(
                        id=uuid.UUID(api_key_data["id"]),
                        client=api_key_data["client"],
                        hash=api_key_data["hash"],
                        scope=api_key_data["scope"],
                        is_active=api_key_data["is_active"],
                        created_at=datetime.fromisoformat(api_key_data["created_at"]),
                        expires_at=datetime.fromisoformat(api_key_data["expires_at"]),
                        description=api_key_data["description"]
                    )
                    db.add(api_key)
                
                await db.commit()
                print("Database seeded successfully!")
                print(f"Demo API key: {demo_api_key}")
                
            except Exception as e:
                print(f"Error seeding database: {e}")
                await db.rollback()
                raise

async def main():
    """Main function."""
    generator = DemoDataGenerator()
    await generator.seed_database()

if __name__ == "__main__":
    asyncio.run(main())
