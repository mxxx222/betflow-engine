"""
Provider service for data ingestion and normalization.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.events import Event
from ..models.odds import Odds
from ..models.schemas import EventResponse, OddsResponse
from ..providers.base import OddsProvider

logger = logging.getLogger(__name__)

class ProviderService:
    """Service for data provider management and ingestion."""
    
    def __init__(self, providers: Dict[str, OddsProvider]):
        self.providers = providers
    
    async def get_events(self, sport: Optional[str] = None, 
                   date_from: Optional[date] = None,
                   date_to: Optional[date] = None,
                   league: Optional[str] = None) -> List[EventResponse]:
        """Get events from providers."""
        try:
            events = []
            
            # Try local CSV first (demo data)
            if "local_csv" in self.providers:
                local_events = await self.providers["local_csv"].fetch_events(
                    sport=sport,
                    date_from=date_from,
                    date_to=date_to,
                    league=league
                )
                events.extend(local_events)
            
            # Try external providers if configured
            for provider_name, provider in self.providers.items():
                if provider_name == "local_csv":
                    continue
                
                try:
                    provider_events = await provider.fetch_events(
                        sport=sport,
                        date_from=date_from,
                        date_to=date_to,
                        league=league
                    )
                    events.extend(provider_events)
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            raise
    
    async def get_odds(self, event_id: str, market: Optional[str] = None) -> List[OddsResponse]:
        """Get odds for specific event."""
        try:
            odds = []
            
            # Try local CSV first
            if "local_csv" in self.providers:
                local_odds = await self.providers["local_csv"].fetch_odds(
                    event_ids=[event_id],
                    market=market
                )
                odds.extend(local_odds)
            
            # Try external providers
            for provider_name, provider in self.providers.items():
                if provider_name == "local_csv":
                    continue
                
                try:
                    provider_odds = await provider.fetch_odds(
                        event_ids=[event_id],
                        market=market
                    )
                    odds.extend(provider_odds)
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed: {e}")
                    continue
            
            return odds
            
        except Exception as e:
            logger.error(f"Failed to get odds: {e}")
            raise
    
    async def process_webhook(self, payload: Dict[str, Any], db: AsyncSession):
        """Process webhook payload from external providers."""
        try:
            provider_name = payload.get("provider")
            data_type = payload.get("data_type")
            data = payload.get("payload", {})
            
            if provider_name not in self.providers:
                logger.error(f"Unknown provider: {provider_name}")
                return
            
            provider = self.providers[provider_name]
            
            if data_type == "events":
                await self._process_events_webhook(data, db)
            elif data_type == "odds":
                await self._process_odds_webhook(data, db)
            elif data_type == "results":
                await self._process_results_webhook(data, db)
            else:
                logger.warning(f"Unknown data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            raise
    
    async def _process_events_webhook(self, data: Dict[str, Any], db: AsyncSession):
        """Process events webhook data."""
        try:
            # Create or update event
            event = Event(
                sport=data.get("sport"),
                league=data.get("league"),
                home_team=data.get("home_team"),
                away_team=data.get("away_team"),
                start_time=datetime.fromisoformat(data.get("start_time")),
                status=data.get("status", "scheduled"),
                venue=data.get("venue"),
                metadata=data.get("metadata")
            )
            
            db.add(event)
            await db.commit()
            
            logger.info(f"Processed event webhook: {event.id}")
            
        except Exception as e:
            logger.error(f"Failed to process events webhook: {e}")
            await db.rollback()
            raise
    
    async def _process_odds_webhook(self, data: Dict[str, Any], db: AsyncSession):
        """Process odds webhook data."""
        try:
            # Create odds record
            odds = Odds(
                event_id=data.get("event_id"),
                book=data.get("book"),
                market=data.get("market"),
                selection=data.get("selection"),
                price=data.get("price"),
                line=data.get("line"),
                implied_probability=data.get("implied_probability"),
                vig=data.get("vig"),
                metadata=data.get("metadata")
            )
            
            db.add(odds)
            await db.commit()
            
            logger.info(f"Processed odds webhook: {odds.id}")
            
        except Exception as e:
            logger.error(f"Failed to process odds webhook: {e}")
            await db.rollback()
            raise
    
    async def _process_results_webhook(self, data: Dict[str, Any], db: AsyncSession):
        """Process results webhook data."""
        try:
            # Update event with results
            result = await db.execute(
                select(Event).where(Event.id == data.get("event_id"))
            )
            event = result.scalar_one_or_none()
            
            if event:
                event.home_score = data.get("home_score")
                event.away_score = data.get("away_score")
                event.status = "finished"
                event.updated_at = datetime.utcnow()
                
                await db.commit()
                
                logger.info(f"Processed results webhook: {event.id}")
            else:
                logger.warning(f"Event not found for results: {data.get('event_id')}")
                
        except Exception as e:
            logger.error(f"Failed to process results webhook: {e}")
            await db.rollback()
            raise
    
    async def sync_provider_data(self, provider_name: str, db: AsyncSession):
        """Sync data from specific provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        try:
            # Fetch events
            events = await provider.fetch_events()
            for event_data in events:
                # Store or update event
                pass
            
            # Fetch odds for events
            event_ids = [event.id for event in events]
            odds = await provider.fetch_odds(event_ids)
            for odds_data in odds:
                # Store odds
                pass
            
            logger.info(f"Synced data from {provider_name}")
            
        except Exception as e:
            logger.error(f"Failed to sync from {provider_name}: {e}")
            raise
