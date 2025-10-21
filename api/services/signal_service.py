"""
Signal service for analytics signal generation and management.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from ..models.signals import Signal
from ..models.events import Event
from ..models.odds import Odds
from ..models.schemas import SignalResponse, SignalQuery

logger = logging.getLogger(__name__)

class SignalService:
    """Service for analytics signal generation and management."""
    
    def __init__(self):
        self.engine_service = None  # Will be injected
    
    async def query_signals(self, query: SignalQuery, db: AsyncSession) -> List[SignalResponse]:
        """Query signals with filtering."""
        try:
            # Build query
            query_builder = select(Signal).options(selectinload(Signal.event))
            
            # Apply filters
            conditions = []
            
            if query.min_edge is not None:
                conditions.append(Signal.edge >= query.min_edge)
            
            if query.max_edge is not None:
                conditions.append(Signal.edge <= query.max_edge)
            
            if query.markets:
                conditions.append(Signal.market.in_(query.markets))
            
            if query.min_confidence is not None:
                conditions.append(Signal.confidence >= query.min_confidence)
            
            if query.status:
                conditions.append(Signal.status == query.status)
            
            if conditions:
                query_builder = query_builder.where(and_(*conditions))
            
            # Apply sports/leagues filter if needed
            if query.sports or query.leagues:
                query_builder = query_builder.join(Event)
                
                if query.sports:
                    query_builder = query_builder.where(Event.sport.in_(query.sports))
                
                if query.leagues:
                    query_builder = query_builder.where(Event.league.in_(query.leagues))
            
            # Apply ordering and pagination
            query_builder = query_builder.order_by(desc(Signal.created_at))
            query_builder = query_builder.offset(query.offset).limit(query.limit)
            
            # Execute query
            result = await db.execute(query_builder)
            signals = result.scalars().all()
            
            # Convert to response models
            signal_responses = []
            for signal in signals:
                signal_responses.append(SignalResponse(
                    id=signal.id,
                    event_id=signal.event_id,
                    market=signal.market,
                    signal_type=signal.signal_type,
                    implied_probability=signal.implied_probability,
                    fair_odds=signal.fair_odds,
                    best_book_odds=signal.best_book_odds,
                    edge=signal.edge,
                    confidence=signal.confidence,
                    risk_note=signal.risk_note,
                    explanation=signal.explanation,
                    model_version=signal.model_version,
                    status=signal.status,
                    expires_at=signal.expires_at,
                    created_at=signal.created_at
                ))
            
            return signal_responses
            
        except Exception as e:
            logger.error(f"Failed to query signals: {e}")
            raise
    
    async def get_signal(self, signal_id: str, db: AsyncSession) -> Optional[SignalResponse]:
        """Get specific signal by ID."""
        try:
            result = await db.execute(
                select(Signal).where(Signal.id == signal_id)
            )
            signal = result.scalar_one_or_none()
            
            if not signal:
                return None
            
            return SignalResponse(
                id=signal.id,
                event_id=signal.event_id,
                market=signal.market,
                signal_type=signal.signal_type,
                implied_probability=signal.implied_probability,
                fair_odds=signal.fair_odds,
                best_book_odds=signal.best_book_odds,
                edge=signal.edge,
                confidence=signal.confidence,
                risk_note=signal.risk_note,
                explanation=signal.explanation,
                model_version=signal.model_version,
                status=signal.status,
                expires_at=signal.expires_at,
                created_at=signal.created_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get signal: {e}")
            raise
    
    async def compute_signals(self, event_ids: List[str], db: AsyncSession) -> List[SignalResponse]:
        """Compute signals for given events."""
        try:
            signals = []
            
            for event_id in event_ids:
                # Get event and odds data
                event_result = await db.execute(
                    select(Event).where(Event.id == event_id)
                )
                event = event_result.scalar_one_or_none()
                
                if not event:
                    continue
                
                odds_result = await db.execute(
                    select(Odds).where(Odds.event_id == event_id)
                )
                odds_list = odds_result.scalars().all()
                
                if not odds_list:
                    continue
                
                # Group odds by market
                odds_by_market = {}
                for odds in odds_list:
                    if odds.market not in odds_by_market:
                        odds_by_market[odds.market] = []
                    odds_by_market[odds.market].append(odds)
                
                # Generate signals for each market
                for market, market_odds in odds_by_market.items():
                    signal = await self._generate_signal_for_market(
                        event, market, market_odds, db
                    )
                    if signal:
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Failed to compute signals: {e}")
            raise
    
    async def _generate_signal_for_market(self, event: Event, market: str, 
                                        odds_list: List[Odds], 
                                        db: AsyncSession) -> Optional[SignalResponse]:
        """Generate signal for specific market."""
        try:
            if not odds_list:
                return None
            
            # Find best odds for each selection
            best_odds = {}
            for odds in odds_list:
                selection = odds.selection
                if selection not in best_odds or odds.price > best_odds[selection]["price"]:
                    best_odds[selection] = {
                        "price": odds.price,
                        "book": odds.book,
                        "implied_prob": 1.0 / odds.price
                    }
            
            # Calculate fair probabilities (simplified model)
            total_implied = sum(odds["implied_prob"] for odds in best_odds.values())
            fair_probs = {}
            for selection, odds in best_odds.items():
                fair_probs[selection] = odds["implied_prob"] / total_implied
            
            # Find best value opportunity
            best_value = None
            best_edge = 0.0
            
            for selection, odds in best_odds.items():
                fair_prob = fair_probs[selection]
                edge = (fair_prob * odds["price"]) - 1.0
                
                if edge > best_edge:
                    best_edge = edge
                    best_value = {
                        "selection": selection,
                        "price": odds["price"],
                        "book": odds["book"],
                        "fair_prob": fair_prob,
                        "edge": edge
                    }
            
            if not best_value or best_edge < 0.01:  # Minimum edge threshold
                return None
            
            # Create signal
            signal = Signal(
                event_id=event.id,
                market=market,
                signal_type="edge",
                metrics={
                    "fair_probability": best_value["fair_prob"],
                    "implied_probability": 1.0 / best_value["price"],
                    "edge": best_value["edge"],
                    "book": best_value["book"]
                },
                implied_probability=1.0 / best_value["price"],
                fair_odds=1.0 / best_value["fair_prob"],
                best_book_odds=best_value["price"],
                edge=best_value["edge"],
                confidence=min(0.95, best_value["edge"] * 10),  # Simple confidence model
                risk_note="Educational analytics only",
                explanation=f"Fair probability: {best_value['fair_prob']:.3f}, Edge: {best_value['edge']:.3f}",
                model_version="1.0.0",
                status="active",
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.add(signal)
            await db.commit()
            
            return SignalResponse(
                id=signal.id,
                event_id=signal.event_id,
                market=signal.market,
                signal_type=signal.signal_type,
                implied_probability=signal.implied_probability,
                fair_odds=signal.fair_odds,
                best_book_odds=signal.best_book_odds,
                edge=signal.edge,
                confidence=signal.confidence,
                risk_note=signal.risk_note,
                explanation=signal.explanation,
                model_version=signal.model_version,
                status=signal.status,
                expires_at=signal.expires_at,
                created_at=signal.created_at
            )
            
        except Exception as e:
            logger.error(f"Failed to generate signal for market {market}: {e}")
            await db.rollback()
            return None
    
    async def expire_old_signals(self, db: AsyncSession):
        """Expire old signals."""
        try:
            result = await db.execute(
                select(Signal).where(
                    and_(
                        Signal.status == "active",
                        Signal.expires_at < datetime.utcnow()
                    )
                )
            )
            old_signals = result.scalars().all()
            
            for signal in old_signals:
                signal.status = "expired"
            
            await db.commit()
            
            logger.info(f"Expired {len(old_signals)} signals")
            
        except Exception as e:
            logger.error(f"Failed to expire old signals: {e}")
            await db.rollback()
            raise
