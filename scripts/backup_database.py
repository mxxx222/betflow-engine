#!/usr/bin/env python3
"""
Database backup script for BetFlow Engine.
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.core.database import AsyncSessionLocal
from api.models.events import Event
from api.models.odds import Odds
from api.models.signals import Signal
from api.models.models import Model
from api.models.api_keys import APIKey
from api.models.audit_logs import AuditLog
from sqlalchemy import select

class DatabaseBackup:
    """Database backup utility."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async def backup_events(self):
        """Backup events table."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Event))
            events = result.scalars().all()
            
            data = []
            for event in events:
                data.append({
                    "id": str(event.id),
                    "sport": event.sport,
                    "league": event.league,
                    "home_team": event.home_team,
                    "away_team": event.away_team,
                    "start_time": event.start_time.isoformat(),
                    "status": event.status,
                    "home_score": event.home_score,
                    "away_score": event.away_score,
                    "venue": event.venue,
                    "weather": json.dumps(event.weather) if event.weather else None,
                    "metadata": json.dumps(event.metadata) if event.metadata else None,
                    "created_at": event.created_at.isoformat(),
                    "updated_at": event.updated_at.isoformat()
                })
            
            await self.save_to_csv(data, "events.csv")
            return len(data)
    
    async def backup_odds(self):
        """Backup odds table."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Odds))
            odds = result.scalars().all()
            
            data = []
            for odd in odds:
                data.append({
                    "id": str(odd.id),
                    "event_id": str(odd.event_id),
                    "book": odd.book,
                    "market": odd.market,
                    "selection": odd.selection,
                    "price": odd.price,
                    "line": odd.line,
                    "implied_probability": odd.implied_probability,
                    "vig": odd.vig,
                    "metadata": json.dumps(odd.metadata) if odd.metadata else None,
                    "fetched_at": odd.fetched_at.isoformat(),
                    "created_at": odd.created_at.isoformat()
                })
            
            await self.save_to_csv(data, "odds.csv")
            return len(data)
    
    async def backup_signals(self):
        """Backup signals table."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Signal))
            signals = result.scalars().all()
            
            data = []
            for signal in signals:
                data.append({
                    "id": str(signal.id),
                    "event_id": str(signal.event_id),
                    "market": signal.market,
                    "signal_type": signal.signal_type,
                    "metrics": json.dumps(signal.metrics),
                    "implied_probability": signal.implied_probability,
                    "fair_odds": signal.fair_odds,
                    "best_book_odds": signal.best_book_odds,
                    "edge": signal.edge,
                    "confidence": signal.confidence,
                    "risk_note": signal.risk_note,
                    "explanation": signal.explanation,
                    "model_version": signal.model_version,
                    "status": signal.status,
                    "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,
                    "created_at": signal.created_at.isoformat()
                })
            
            await self.save_to_csv(data, "signals.csv")
            return len(data)
    
    async def backup_models(self):
        """Backup models table."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Model))
            models = result.scalars().all()
            
            data = []
            for model in models:
                data.append({
                    "id": str(model.id),
                    "name": model.name,
                    "version": model.version,
                    "model_type": model.model_type,
                    "parameters": json.dumps(model.parameters) if model.parameters else None,
                    "performance_metrics": json.dumps(model.performance_metrics) if model.performance_metrics else None,
                    "training_data_size": model.training_data_size,
                    "accuracy": model.accuracy,
                    "last_trained": model.last_trained.isoformat() if model.last_trained else None,
                    "status": model.status,
                    "created_at": model.created_at.isoformat(),
                    "updated_at": model.updated_at.isoformat()
                })
            
            await self.save_to_csv(data, "models.csv")
            return len(data)
    
    async def backup_api_keys(self):
        """Backup API keys table."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(APIKey))
            api_keys = result.scalars().all()
            
            data = []
            for api_key in api_keys:
                data.append({
                    "id": str(api_key.id),
                    "client": api_key.client,
                    "hash": api_key.hash,
                    "scope": api_key.scope,
                    "is_active": api_key.is_active,
                    "created_at": api_key.created_at.isoformat(),
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    "revoked_at": api_key.revoked_at.isoformat() if api_key.revoked_at else None,
                    "description": api_key.description
                })
            
            await self.save_to_csv(data, "api_keys.csv")
            return len(data)
    
    async def backup_audit_logs(self):
        """Backup audit logs table."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AuditLog))
            audit_logs = result.scalars().all()
            
            data = []
            for log in audit_logs:
                data.append({
                    "id": str(log.id),
                    "actor": log.actor,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "diff": json.dumps(log.diff) if log.diff else None,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "metadata": json.dumps(log.metadata) if log.metadata else None,
                    "created_at": log.created_at.isoformat()
                })
            
            await self.save_to_csv(data, "audit_logs.csv")
            return len(data)
    
    async def save_to_csv(self, data: list, filename: str):
        """Save data to CSV file."""
        if not data:
            return
        
        filepath = self.backup_dir / f"{self.timestamp}_{filename}"
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Backed up {len(data)} records to {filepath}")
    
    async def create_backup_manifest(self, counts: dict):
        """Create backup manifest."""
        manifest = {
            "timestamp": self.timestamp,
            "backup_date": datetime.now().isoformat(),
            "tables": counts,
            "total_records": sum(counts.values())
        }
        
        manifest_path = self.backup_dir / f"{self.timestamp}_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Backup manifest saved to {manifest_path}")
    
    async def full_backup(self):
        """Perform full database backup."""
        print(f"Starting database backup at {datetime.now()}")
        print(f"Backup directory: {self.backup_dir}")
        
        counts = {}
        
        try:
            print("Backing up events...")
            counts["events"] = await self.backup_events()
            
            print("Backing up odds...")
            counts["odds"] = await self.backup_odds()
            
            print("Backing up signals...")
            counts["signals"] = await self.backup_signals()
            
            print("Backing up models...")
            counts["models"] = await self.backup_models()
            
            print("Backing up API keys...")
            counts["api_keys"] = await self.backup_api_keys()
            
            print("Backing up audit logs...")
            counts["audit_logs"] = await self.backup_audit_logs()
            
            await self.create_backup_manifest(counts)
            
            print(f"Backup completed successfully!")
            print(f"Total records backed up: {sum(counts.values())}")
            
        except Exception as e:
            print(f"Backup failed: {e}")
            raise

async def main():
    """Main function."""
    backup = DatabaseBackup()
    await backup.full_backup()

if __name__ == "__main__":
    asyncio.run(main())
