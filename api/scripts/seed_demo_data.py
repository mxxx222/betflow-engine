"""
Script to seed demo data for BetFlow Engine.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.local_csv import LocalCSVProvider
from core.database import init_db, AsyncSessionLocal
from models.events import Event
from models.odds import Odds
from models.models import Model
from models.api_keys import APIKey
from core.security import security_manager
from datetime import datetime, timedelta
import uuid

async def seed_demo_data():
    """Seed database with demo data."""
    print("Starting demo data seeding...")
    
    # Initialize database
    await init_db()
    
    # Generate CSV demo data
    provider = LocalCSVProvider("/app/data")
    provider.generate_demo_data(num_events=50)
    print("Generated CSV demo data")
    
    # Seed database
    async with AsyncSessionLocal() as db:
        try:
            # Create demo API key
            api_key, hashed_key = security_manager.create_api_key(
                client="demo_client",
                scope="read",
                expires_days=365
            )
            
            demo_api_key = APIKey(
                client="demo_client",
                hash=hashed_key,
                scope="read",
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=365),
                description="Demo API key for testing"
            )
            db.add(demo_api_key)
            
            # Create demo models
            elo_model = Model(
                name="ELO Rating System",
                version="1.0.0",
                model_type="elo",
                parameters={
                    "k_factor": 32.0,
                    "home_advantage": 50.0,
                    "initial_rating": 1500.0
                },
                performance_metrics={
                    "accuracy": 0.68,
                    "precision": 0.72,
                    "recall": 0.65
                },
                training_data_size=1000,
                accuracy=0.68,
                last_trained=datetime.utcnow(),
                status="active"
            )
            db.add(elo_model)
            
            poisson_model = Model(
                name="Poisson Goals Model",
                version="1.0.0",
                model_type="poisson",
                parameters={
                    "home_rate": 1.5,
                    "away_rate": 1.2,
                    "max_goals": 6
                },
                performance_metrics={
                    "accuracy": 0.62,
                    "precision": 0.58,
                    "recall": 0.70
                },
                training_data_size=800,
                accuracy=0.62,
                last_trained=datetime.utcnow(),
                status="active"
            )
            db.add(poisson_model)
            
            # Load events from CSV
            events_data = []
            with open("/app/data/events.csv", "r") as f:
                import csv
                reader = csv.DictReader(f)
                for row in reader:
                    event = Event(
                        id=uuid.UUID(row["id"]),
                        sport=row["sport"],
                        league=row["league"],
                        home_team=row["home_team"],
                        away_team=row["away_team"],
                        start_time=datetime.fromisoformat(row["start_time"]),
                        status=row["status"],
                        home_score=int(row["home_score"]) if row.get("home_score") else None,
                        away_score=int(row["away_score"]) if row.get("away_score") else None,
                        venue=row.get("venue"),
                        weather=row.get("weather", {})
                    )
                    events_data.append(event)
                    db.add(event)
            
            # Load odds from CSV
            with open("/app/data/odds.csv", "r") as f:
                import csv
                reader = csv.DictReader(f)
                for row in reader:
                    odds = Odds(
                        id=uuid.UUID(row["id"]),
                        event_id=uuid.UUID(row["event_id"]),
                        book=row["book"],
                        market=row["market"],
                        selection=row["selection"],
                        price=float(row["price"]),
                        line=float(row["line"]) if row.get("line") else None,
                        implied_probability=float(row["implied_probability"]) if row.get("implied_probability") else None,
                        vig=float(row["vig"]) if row.get("vig") else None,
                        metadata={}
                    )
                    db.add(odds)
            
            await db.commit()
            print(f"Seeded {len(events_data)} events and odds data")
            print(f"Demo API key: {api_key}")
            print("Demo data seeding completed successfully!")
            
        except Exception as e:
            print(f"Error seeding demo data: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
