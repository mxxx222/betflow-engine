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
        self.engine = None  # Will be initialized with Mojo engine
    
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
        """Calculate expected value."""
        if not 0.0 < probability < 1.0:
            raise ValueError("Probability must be between 0 and 1")
        if odds <= 1.0:
            raise ValueError("Odds must be greater than 1.0")
        
        return (probability * odds) - 1.0
    
    async def calculate_poisson_probabilities(self, home_rate: float, away_rate: float, 
                                           max_goals: int = 6) -> List[List[float]]:
        """Calculate Poisson match outcome probabilities."""
        import math
        
        probabilities = []
        for home_goals in range(max_goals + 1):
            row = []
            for away_goals in range(max_goals + 1):
                home_prob = self._poisson_probability(home_rate, home_goals)
                away_prob = self._poisson_probability(away_rate, away_goals)
                row.append(home_prob * away_prob)
            probabilities.append(row)
        
        return probabilities
    
    async def update_elo_ratings(self, match_data: Dict[str, Any]) -> Dict[str, float]:
        """Update ELO ratings based on match result."""
        # This would integrate with the Mojo ELO module
        # For now, return mock data
        return {
            "home_rating": 1500.0,
            "away_rating": 1500.0,
            "home_change": 0.0,
            "away_change": 0.0
        }
    
    async def predict_match_outcome(self, home_team: str, away_team: str, 
                                  league: str) -> Dict[str, float]:
        """Predict match outcome probabilities."""
        # This would integrate with the Mojo prediction modules
        # For now, return mock data
        return {
            "home_win": 0.45,
            "draw": 0.25,
            "away_win": 0.30
        }
    
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
