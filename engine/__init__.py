"""
BetFlow Engine - Mojo calculation core with Python bindings.
Provides high-performance sports analytics calculations.

Version: 0.9.0
"""

from typing import List, Tuple, Dict, Any
import numpy as np
from dataclasses import dataclass
from datetime import datetime

# Global flag for Mojo availability
USE_MOJO = False

# Try to import Mojo engine, fall back to Python implementation
try:
    from . import _betflow_engine as mojo_engine
    USE_MOJO = True
except ImportError:
    pass

@dataclass
class MatchResult:
    """Represents a match result for ELO calculations."""
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    league: str
    date: datetime

@dataclass
class EloUpdate:
    """ELO rating update result."""
    home_rating: float
    away_rating: float
    home_change: float
    away_change: float

@dataclass
class Signal:
    """Analytics signal output."""
    id: str
    event_id: str
    market: str
    implied_probability: float
    fair_odds: float
    best_book_odds: float
    edge: float
    risk_note: str
    explanation: str
    generated_at: datetime

class BetFlowEngine:
    """
    Main engine class providing Python interface to Mojo calculations.
    """

    def __init__(self):
        global USE_MOJO
        self.team_ratings: Dict[str, float] = {}
        self.player_ratings: Dict[str, float] = {}
        self._mojo_engine = None
        if USE_MOJO:
            try:
                self._mojo_engine = mojo_engine.BetFlowEngine()
            except Exception as e:
                print(f"Warning: Failed to initialize Mojo engine: {e}")
                USE_MOJO = False
        
    def calc_ev(self, probability: float, odds: float) -> float:
        """
        Calculate expected value.

        Args:
            probability: True probability (0.0 to 1.0)
            odds: Decimal odds (> 1.0)

        Returns:
            Expected value
        """
        # Input validation with security guards
        if not isinstance(probability, (int, float)) or not isinstance(odds, (int, float)):
            raise ValueError("Inputs must be numeric")
        if not 0.0 < probability < 1.0:
            raise ValueError("Probability must be between 0 and 1")
        if odds <= 1.0:
            raise ValueError("Odds must be greater than 1.0")
        if not (0 < odds < 1000):  # Reasonable bounds
            raise ValueError("Odds out of reasonable range")

        if USE_MOJO and self._mojo_engine:
            return float(self._mojo_engine.calc_ev(probability, odds))
        else:
            return (probability * odds) - 1.0
    
    def calc_poisson(self, home_rate: float, away_rate: float,
                    max_goals: int = 6) -> List[List[float]]:
        """
        Calculate Poisson match outcome probabilities.

        Args:
            home_rate: Home team expected goals
            away_rate: Away team expected goals
            max_goals: Maximum goals to consider

        Returns:
            2D array of probabilities

        SLO: p95 < 1ms, p99 < 5ms
        """
        # Input validation with security guards
        if not isinstance(home_rate, (int, float)) or not isinstance(away_rate, (int, float)):
            raise ValueError("Rates must be numeric")
        if not isinstance(max_goals, int):
            raise ValueError("max_goals must be integer")
        if home_rate < 0 or away_rate < 0:
            raise ValueError("Rates must be non-negative")
        if not (1 <= max_goals <= 20):  # Reasonable bounds
            raise ValueError("max_goals must be between 1 and 20")

        if USE_MOJO and self._mojo_engine:
            # Convert Mojo result to Python list
            mojo_result = self._mojo_engine.calc_poisson(home_rate, away_rate, max_goals)
            return [[float(prob) for prob in row] for row in mojo_result]
        else:
            # Fallback to Python implementation - use higher max_goals for accuracy
            probabilities = []

            for home_goals in range(max_goals + 1):
                row = []
                for away_goals in range(max_goals + 1):
                    home_prob = self._poisson_probability(home_rate, home_goals)
                    away_prob = self._poisson_probability(away_rate, away_goals)
                    row.append(home_prob * away_prob)
                probabilities.append(row)

            return probabilities
    
    def update_elo(self, match: MatchResult) -> EloUpdate:
        """
        Update ELO ratings based on match result.

        Args:
            match: Match result data

        Returns:
            ELO update information

        SLO: p95 < 1ms, p99 < 5ms
        """
        # Input validation with security guards
        if not isinstance(match.home_score, int) or not isinstance(match.away_score, int):
            raise ValueError("Scores must be integers")
        if match.home_score < 0 or match.away_score < 0:
            raise ValueError("Scores must be non-negative")
        if not match.home_team or not match.away_team:
            raise ValueError("Team names cannot be empty")
        if len(match.home_team) > 100 or len(match.away_team) > 100:
            raise ValueError("Team names too long")

        if USE_MOJO and self._mojo_engine:
            # Use Mojo implementation
            result = self._mojo_engine.update_elo(
                match.home_team, match.away_team,
                match.home_score, match.away_score, match.league
            )
            new_home, new_away, home_change, away_change = result
            return EloUpdate(
                home_rating=float(new_home),
                away_rating=float(new_away),
                home_change=float(home_change),
                away_change=float(away_change)
            )
        else:
            # Fallback to Python implementation
            home_rating = self.team_ratings.get(match.home_team, 1500.0)
            away_rating = self.team_ratings.get(match.away_team, 1500.0)

            # Calculate result
            if match.home_score > match.away_score:
                result = 1
            elif match.home_score == match.away_score:
                result = 0
            else:
                result = -1

            # Calculate home advantage
            home_advantage = self._get_home_advantage(match.league)

            # Update ratings
            new_home_rating, new_away_rating = self._calculate_elo_update(
                home_rating, away_rating, result, home_advantage
            )

            # Store updated ratings
            self.team_ratings[match.home_team] = new_home_rating
            self.team_ratings[match.away_team] = new_away_rating

            return EloUpdate(
                home_rating=new_home_rating,
                away_rating=new_away_rating,
                home_change=new_home_rating - home_rating,
                away_change=new_away_rating - away_rating
            )
    
    def predict_match(self, home_team: str, away_team: str,
                     league: str) -> Tuple[float, float, float]:
        """
        Predict match outcome probabilities.

        Args:
            home_team: Home team name
            away_team: Away team name
            league: League identifier

        Returns:
            Tuple of (home_win_prob, draw_prob, away_win_prob)

        SLO: p95 < 1ms, p99 < 5ms
        """
        # Input validation with security guards
        if not home_team or not away_team:
            raise ValueError("Team names cannot be empty")
        if len(home_team) > 100 or len(away_team) > 100:
            raise ValueError("Team names too long")
        if not league:
            raise ValueError("League cannot be empty")

        if USE_MOJO and self._mojo_engine:
            result = self._mojo_engine.predict_match(home_team, away_team, league)
            return (float(result[0]), float(result[1]), float(result[2]))
        else:
            # Fallback to Python implementation
            home_rating = self.team_ratings.get(home_team, 1500.0)
            away_rating = self.team_ratings.get(away_team, 1500.0)
            home_advantage = self._get_home_advantage(league)

            # Calculate probabilities
            home_win_prob = self._expected_score(home_rating, away_rating, home_advantage)

            # Estimate draw probability
            rating_diff = abs(home_rating - away_rating)
            draw_prob = 0.25 * np.exp(-rating_diff / 200.0)

            # Normalize
            total = home_win_prob + draw_prob + (1.0 - home_win_prob)
            home_win_prob /= total
            draw_prob /= total
            away_win_prob = 1.0 - home_win_prob - draw_prob

            return (home_win_prob, draw_prob, away_win_prob)
    
    def generate_signal(self, event_id: str, market: str,
                       probability: float, best_odds: float) -> Signal:
        """
        Generate analytics signal.

        Args:
            event_id: Event identifier
            market: Market type
            probability: Calculated probability
            best_odds: Best available odds

        Returns:
            Signal object

        SLO: p95 < 1ms, p99 < 5ms
        """
        # Input validation with security guards
        if not event_id or not market:
            raise ValueError("event_id and market cannot be empty")
        if not isinstance(probability, (int, float)) or not isinstance(best_odds, (int, float)):
            raise ValueError("probability and best_odds must be numeric")
        if not 0.0 < probability < 1.0:
            raise ValueError("Probability must be between 0 and 1")
        if best_odds <= 1.0:
            raise ValueError("Best odds must be greater than 1.0")

        if USE_MOJO and self._mojo_engine:
            result = self._mojo_engine.generate_signal(event_id, market, probability, best_odds)
            signal_id, implied_prob, fair_odds, edge, risk_note = result
            return Signal(
                id=str(signal_id),
                event_id=event_id,
                market=market,
                implied_probability=float(implied_prob),
                fair_odds=float(fair_odds),
                best_book_odds=best_odds,
                edge=float(edge),
                risk_note=str(risk_note),
                explanation=f"Probability: {probability:.3f}, Edge: {edge:.3f}",
                generated_at=datetime.utcnow()
            )
        else:
            # Fallback to Python implementation
            fair_odds = 1.0 / probability
            edge = (probability * best_odds) - 1.0

            return Signal(
                id=f"sig_{event_id}_{market}",
                event_id=event_id,
                market=market,
                implied_probability=1.0 / best_odds,
                fair_odds=fair_odds,
                best_book_odds=best_odds,
                edge=edge,
                risk_note="Educational analytics only",
                explanation=f"Probability: {probability:.3f}, Edge: {edge:.3f}",
                generated_at=datetime.utcnow()
            )
    
    def _poisson_probability(self, rate: float, k: int) -> float:
        """Calculate Poisson probability."""
        if rate < 0:
            return 0.0
        if k < 0:
            return 0.0

        import math
        return (rate ** k * math.exp(-rate)) / math.factorial(k)
    
    def _expected_score(self, rating1: float, rating2: float, 
                       advantage: float = 0.0) -> float:
        """Calculate expected score."""
        rating_diff = rating1 - rating2 + advantage
        return 1.0 / (1.0 + 10.0 ** (-rating_diff / 400.0))
    
    def _calculate_elo_update(self, home_rating: float, away_rating: float,
                            result: int, home_advantage: float) -> Tuple[float, float]:
        """Calculate ELO rating updates."""
        k_factor = 32.0
        
        home_expected = self._expected_score(home_rating, away_rating, home_advantage)
        away_expected = self._expected_score(away_rating, home_rating, -home_advantage)
        
        if result == 1:
            home_score, away_score = 1.0, 0.0
        elif result == 0:
            home_score, away_score = 0.5, 0.5
        else:
            home_score, away_score = 0.0, 1.0
            
        home_change = k_factor * (home_score - home_expected)
        away_change = k_factor * (away_score - away_expected)
        
        return (home_rating + home_change, away_rating + away_change)
    
    def _get_home_advantage(self, league: str) -> float:
        """Get home advantage for league."""
        advantages = {
            "premier_league": 50.0,
            "la_liga": 45.0,
            "bundesliga": 40.0,
            "serie_a": 35.0,
            "nba": 30.0,
            "nfl": 25.0
        }
        return advantages.get(league, 30.0)

    def health_check(self) -> Dict[str, Any]:
        """
        Health check endpoint for monitoring.

        Returns:
            Health status with Mojo availability and performance metrics
        """
        import time

        health = {
            "status": "healthy",
            "version": "0.9.0",
            "use_mojo": USE_MOJO,
            "mojo_available": self._mojo_engine is not None,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Quick performance test
        try:
            start = time.time()
            ev = self.calc_ev(0.6, 2.0)
            latency_ms = (time.time() - start) * 1000

            health["performance_test"] = {
                "ev_calculation_ms": round(latency_ms, 3),
                "result": round(ev, 6)
            }
        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)

        return health
