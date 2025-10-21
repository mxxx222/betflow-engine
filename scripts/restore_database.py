#!/usr/bin/env python3
"""
Database restore script for BetFlow Engine.
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
import sys
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.core.database import AsyncSessionLocal, init_db
from api.models.events import Event
from api.models.odds import Odds
from api.models.signals import Signal
from api.models.models import Model
from api.models.api_keys import APIKey
from api.models.audit_logs import AuditLog

class DatabaseRestore:
    """Database restore utility."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
    
    def find_latest_backup(self):
        """Find the latest backup directory."""
        if not self.backup_dir.exists():
            raise FileNotFoundError(f"Backup directory {self.backup_dir} not found")
        
        # Find manifest files
        manifest_files = list(self.backup_dir.glob("*_manifest.json"))
        if not manifest_files:
            raise FileNotFoundError("No backup manifests found")
        
        # Get the latest manifest
        latest_manifest = max(manifest_files, key=lambda x: x.stat().st_mtime)
        
        # Extract timestamp from filename
        timestamp = latest_manifest.stem.replace("_manifest", "")
        
        print(f"Found latest backup: {timestamp}")
        return timestamp
    
    def load_csv_data(self, filename: str, timestamp: str):
        """Load data from CSV file."""
        filepath = self.backup_dir / f"{timestamp}_{filename}"
        
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping...")
            return []
        
        data = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        print(f"Loaded {len(data)} records from {filename}")
        return data
    
    async def restore_events(self, data: list):
        """Restore events table."""
        if not data:
            return 0
        
        async with AsyncSessionLocal() as db:
            for event_data in data:
                event = Event(
                    id=uuid.UUID(event_data["id"]),
                    sport=event_data["sport"],
                    league=event_data["league"],
                    home_team=event_data["home_team"],
                    away_team=event_data["away_team"],
                    start_time=datetime.fromisoformat(event_data["start_time"]),
                    status=event_data["status"],
                    home_score=int(event_data["home_score"]) if event_data["home_score"] else None,
                    away_score=int(event_data["away_score"]) if event_data["away_score"] else None,
                    venue=event_data["venue"],
                    weather=json.loads(event_data["weather"]) if event_data["weather"] else None,
                    metadata=json.loads(event_data["metadata"]) if event_data["metadata"] else None,
                    created_at=datetime.fromisoformat(event_data["created_at"]),
                    updated_at=datetime.fromisoformat(event_data["updated_at"])
                )
                db.add(event)
            
            await db.commit()
            return len(data)
    
    async def restore_odds(self, data: list):
        """Restore odds table."""
        if not data:
            return 0
        
        async with AsyncSessionLocal() as db:
            for odds_data in data:
                odds = Odds(
                    id=uuid.UUID(odds_data["id"]),
                    event_id=uuid.UUID(odds_data["event_id"]),
                    book=odds_data["book"],
                    market=odds_data["market"],
                    selection=odds_data["selection"],
                    price=float(odds_data["price"]),
                    line=float(odds_data["line"]) if odds_data["line"] else None,
                    implied_probability=float(odds_data["implied_probability"]) if odds_data["implied_probability"] else None,
                    vig=float(odds_data["vig"]) if odds_data["vig"] else None,
                    metadata=json.loads(odds_data["metadata"]) if odds_data["metadata"] else None,
                    fetched_at=datetime.fromisoformat(odds_data["fetched_at"]),
                    created_at=datetime.fromisoformat(odds_data["created_at"])
                )
                db.add(odds)
            
            await db.commit()
            return len(data)
    
    async def restore_signals(self, data: list):
        """Restore signals table."""
        if not data:
            return 0
        
        async with AsyncSessionLocal() as db:
            for signal_data in data:
                signal = Signal(
                    id=uuid.UUID(signal_data["id"]),
                    event_id=uuid.UUID(signal_data["event_id"]),
                    market=signal_data["market"],
                    signal_type=signal_data["signal_type"],
                    metrics=json.loads(signal_data["metrics"]),
                    implied_probability=float(signal_data["implied_probability"]),
                    fair_odds=float(signal_data["fair_odds"]),
                    best_book_odds=float(signal_data["best_book_odds"]),
                    edge=float(signal_data["edge"]),
                    confidence=float(signal_data["confidence"]) if signal_data["confidence"] else None,
                    risk_note=signal_data["risk_note"],
                    explanation=signal_data["explanation"],
                    model_version=signal_data["model_version"],
                    status=signal_data["status"],
                    expires_at=datetime.fromisoformat(signal_data["expires_at"]) if signal_data["expires_at"] else None,
                    created_at=datetime.fromisoformat(signal_data["created_at"])
                )
                db.add(signal)
            
            await db.commit()
            return len(data)
    
    async def restore_models(self, data: list):
        """Restore models table."""
        if not data:
            return 0
        
        async with AsyncSessionLocal() as db:
            for model_data in data:
                model = Model(
                    id=uuid.UUID(model_data["id"]),
                    name=model_data["name"],
                    version=model_data["version"],
                    model_type=model_data["model_type"],
                    parameters=json.loads(model_data["parameters"]) if model_data["parameters"] else None,
                    performance_metrics=json.loads(model_data["performance_metrics"]) if model_data["performance_metrics"] else None,
                    training_data_size=int(model_data["training_data_size"]) if model_data["training_data_size"] else None,
                    accuracy=float(model_data["accuracy"]) if model_data["accuracy"] else None,
                    last_trained=datetime.fromisoformat(model_data["last_trained"]) if model_data["last_trained"] else None,
                    status=model_data["status"],
                    created_at=datetime.fromisoformat(model_data["created_at"]),
                    updated_at=datetime.fromisoformat(model_data["updated_at"])
                )
                db.add(model)
            
            await db.commit()
            return len(data)
    
    async def restore_api_keys(self, data: list):
        """Restore API keys table."""
        if not data:
            return 0
        
        async with AsyncSessionLocal() as db:
            for api_key_data in data:
                api_key = APIKey(
                    id=uuid.UUID(api_key_data["id"]),
                    client=api_key_data["client"],
                    hash=api_key_data["hash"],
                    scope=api_key_data["scope"],
                    is_active=api_key_data["is_active"].lower() == "true",
                    created_at=datetime.fromisoformat(api_key_data["created_at"]),
                    expires_at=datetime.fromisoformat(api_key_data["expires_at"]) if api_key_data["expires_at"] else None,
                    last_used_at=datetime.fromisoformat(api_key_data["last_used_at"]) if api_key_data["last_used_at"] else None,
                    revoked_at=datetime.fromisoformat(api_key_data["revoked_at"]) if api_key_data["revoked_at"] else None,
                    description=api_key_data["description"]
                )
                db.add(api_key)
            
            await db.commit()
            return len(data)
    
    async def restore_audit_logs(self, data: list):
        """Restore audit logs table."""
        if not data:
            return 0
        
        async with AsyncSessionLocal() as db:
            for log_data in data:
                audit_log = AuditLog(
                    id=uuid.UUID(log_data["id"]),
                    actor=log_data["actor"],
                    action=log_data["action"],
                    resource=log_data["resource"],
                    resource_id=log_data["resource_id"],
                    diff=json.loads(log_data["diff"]) if log_data["diff"] else None,
                    ip_address=log_data["ip_address"],
                    user_agent=log_data["user_agent"],
                    metadata=json.loads(log_data["metadata"]) if log_data["metadata"] else None,
                    created_at=datetime.fromisoformat(log_data["created_at"])
                )
                db.add(audit_log)
            
            await db.commit()
            return len(data)
    
    async def full_restore(self, timestamp: str = None):
        """Perform full database restore."""
        if timestamp is None:
            timestamp = self.find_latest_backup()
        
        print(f"Starting database restore from backup: {timestamp}")
        print(f"Backup directory: {self.backup_dir}")
        
        # Initialize database
        await init_db()
        
        counts = {}
        
        try:
            print("Loading backup data...")
            
            # Load all data
            events_data = self.load_csv_data("events.csv", timestamp)
            odds_data = self.load_csv_data("odds.csv", timestamp)
            signals_data = self.load_csv_data("signals.csv", timestamp)
            models_data = self.load_csv_data("models.csv", timestamp)
            api_keys_data = self.load_csv_data("api_keys.csv", timestamp)
            audit_logs_data = self.load_csv_data("audit_logs.csv", timestamp)
            
            print("Restoring data to database...")
            
            # Restore in order (respecting foreign key constraints)
            print("Restoring events...")
            counts["events"] = await self.restore_events(events_data)
            
            print("Restoring odds...")
            counts["odds"] = await self.restore_odds(odds_data)
            
            print("Restoring signals...")
            counts["signals"] = await self.restore_signals(signals_data)
            
            print("Restoring models...")
            counts["models"] = await self.restore_models(models_data)
            
            print("Restoring API keys...")
            counts["api_keys"] = await self.restore_api_keys(api_keys_data)
            
            print("Restoring audit logs...")
            counts["audit_logs"] = await self.restore_audit_logs(audit_logs_data)
            
            print(f"Restore completed successfully!")
            print(f"Total records restored: {sum(counts.values())}")
            
        except Exception as e:
            print(f"Restore failed: {e}")
            raise

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore BetFlow Engine database")
    parser.add_argument("--timestamp", help="Backup timestamp to restore")
    parser.add_argument("--backup-dir", default="backups", help="Backup directory")
    
    args = parser.parse_args()
    
    restore = DatabaseRestore(args.backup_dir)
    await restore.full_restore(args.timestamp)

if __name__ == "__main__":
    asyncio.run(main())
