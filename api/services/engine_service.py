"""
Engine service for calculation core integration.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.models import Model
from ..models.schemas import ModelStatusResponse

logger = logging.getLogger(__name__)

class EngineService:
    """Service for engine calculations and model management."""

    def __init__(self):
        try:
            from engine import BetFlowEngine
            self.engine = BetFlowEngine()
            logger.info(f"BetFlowEngine initialized successfully. Mojo available: {self.engine.health_check().get('mojo_available', False)}")
        except ImportError as e:
            logger.error(f"Failed to import BetFlowEngine: {e}")
            self.engine = None
        except Exception as e:
            logger.error(f"Failed to initialize BetFlowEngine: {e}")
            self.engine = None
    
    async def get_model_status(self, db: AsyncSession) -> ModelStatusResponse:
        """Get model status and information."""
        try:
            # Get all models
            result = await db.execute(select(Model))
            models = result.scalars().all()
            
            # Get signal counts
            from ..models.signals import Signal
            total_signals_result = await db.execute(select(func.count(Signal.id)))
            total_signals = total_signals_result.scalar()
            
            active_signals_result = await db.execute(
                select(func.count(Signal.id)).where(Signal.status == "active")
            )
            active_signals = active_signals_result.scalar()
            
            # Format model data
            model_data = []
            for model in models:
                model_data.append({
                    "id": str(model.id),
                    "name": model.name,
                    "version": model.version,
                    "type": model.model_type,
                    "status": model.status,
                    "accuracy": model.accuracy,
                    "last_trained": model.last_trained.isoformat() if model.last_trained else None,
                    "created_at": model.created_at.isoformat(),
                    "updated_at": model.updated_at.isoformat()
                })
            
            return ModelStatusResponse(
                models=model_data,
                last_updated=datetime.utcnow(),
                total_signals=total_signals,
                active_signals=active_signals
            )
            
        except Exception as e:
            logger.error(f"Failed to get model status: {e}")
            raise
    
    async def calculate_ev(self, probability: float, odds: float) -> float:
        """Calculate expected value using BetFlowEngine."""
        if not self.engine:
            raise RuntimeError("BetFlowEngine not available")
        
        try:
            return self.engine.calc_ev(probability, odds)
        except Exception as e:
            logger.error(f"EV calculation failed: {e}")
            raise
    
    async def calculate_poisson_probabilities(self, home_rate: float, away_rate: float,
                                            max_goals: int = 6) -> List[List[float]]:
        """Calculate Poisson match outcome probabilities using BetFlowEngine."""
        if not self.engine:
            raise RuntimeError("BetFlowEngine not available")
        
        try:
            return self.engine.calc_poisson(home_rate, away_rate, max_goals)
        except Exception as e:
            logger.error(f"Poisson calculation failed: {e}")
            raise
    
    async def update_elo_ratings(self, match_data: Dict[str, Any]) -> Dict[str, float]:
        """Update ELO ratings based on match result using BetFlowEngine."""
        if not self.engine:
            raise RuntimeError("BetFlowEngine not available")
        
        try:
            from datetime import datetime
            from engine import MatchResult

            match = MatchResult(
                home_team=match_data["home_team"],
                away_team=match_data["away_team"],
                home_score=match_data["home_score"],
                away_score=match_data["away_score"],
                league=match_data.get("league", "unknown"),
                date=datetime.utcnow()
            )

            update = self.engine.update_elo(match)
            return {
                "home_rating": update.home_rating,
                "away_rating": update.away_rating,
                "home_change": update.home_change,
                "away_change": update.away_change
            }
        except Exception as e:
            logger.error(f"ELO calculation failed: {e}")
            raise
    
    async def predict_match_outcome(self, home_team: str, away_team: str,
                                   league: str) -> Dict[str, float]:
        """Predict match outcome probabilities using BetFlowEngine."""
        if not self.engine:
            raise RuntimeError("BetFlowEngine not available")
        
        try:
            home_win, draw, away_win = self.engine.predict_match(home_team, away_team, league)
            return {
                "home_win": home_win,
                "draw": draw,
                "away_win": away_win
            }
        except Exception as e:
            logger.error(f"Match prediction failed: {e}")
            raise
    
    def _poisson_probability(self, rate: float, k: int) -> float:
        """Calculate Poisson probability."""
        import math
        
        if rate < 0:
            return 0.0
        if k < 0:
            return 0.0
        
        return (rate ** k * math.exp(-rate)) / math.factorial(k)
    
    async def validate_model_parameters(self, model_type: str, parameters: Dict[str, Any]) -> bool:
        """Validate model parameters."""
        if model_type == "elo":
            required = ["k_factor", "home_advantage"]
            return all(param in parameters for param in required)
        elif model_type == "poisson":
            required = ["home_rate", "away_rate"]
            return all(param in parameters for param in required)
        elif model_type == "ev":
            required = ["probability", "odds"]
            return all(param in parameters for param in required)
        
        return False
