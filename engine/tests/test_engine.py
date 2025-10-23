"""
Test suite for BetFlow Engine calculations.
Tests Mojo functions against known reference calculations.
"""

import pytest
import numpy as np
from datetime import datetime
from engine import BetFlowEngine, MatchResult, Signal

class TestBetFlowEngine:
    """Test cases for BetFlow Engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = BetFlowEngine()
    
    def test_calc_ev_positive(self):
        """Test EV calculation with positive expected value."""
        probability = 0.6
        odds = 2.0
        ev = self.engine.calc_ev(probability, odds)
        expected_ev = (0.6 * 2.0) - 1.0  # 0.2
        assert abs(ev - expected_ev) < 1e-10
    
    def test_calc_ev_negative(self):
        """Test EV calculation with negative expected value."""
        probability = 0.4
        odds = 2.0
        ev = self.engine.calc_ev(probability, odds)
        expected_ev = (0.4 * 2.0) - 1.0  # -0.2
        assert abs(ev - expected_ev) < 1e-10
    
    def test_calc_ev_edge_cases(self):
        """Test EV calculation edge cases."""
        # Break-even
        ev = self.engine.calc_ev(0.5, 2.0)
        assert abs(ev) < 1e-10
        
        # Invalid inputs
        with pytest.raises(ValueError):
            self.engine.calc_ev(0.0, 2.0)
        with pytest.raises(ValueError):
            self.engine.calc_ev(1.0, 2.0)
        with pytest.raises(ValueError):
            self.engine.calc_ev(0.5, 1.0)
    
    def test_calc_poisson_basic(self):
        """Test Poisson probability calculations."""
        home_rate = 1.5
        away_rate = 1.2
        probabilities = self.engine.calc_poisson(home_rate, away_rate, max_goals=3)

        # Check dimensions
        assert len(probabilities) == 4  # 0-3 goals
        assert len(probabilities[0]) == 4

        # Check probabilities sum to approximately 1 (allowing for truncation with low max_goals)
        total_prob = sum(sum(row) for row in probabilities)
        assert abs(total_prob - 1.0) < 0.15  # More lenient for truncated distributions
    
    def test_calc_poisson_reference_values(self):
        """Test Poisson against known reference values."""
        # Test 0-0 score probability
        probabilities = self.engine.calc_poisson(1.0, 1.0, max_goals=0)
        prob_0_0 = probabilities[0][0]
        
        # P(0,0) = P(0|λ₁) * P(0|λ₂) = e^(-1) * e^(-1) = e^(-2)
        expected = np.exp(-2.0)
        assert abs(prob_0_0 - expected) < 1e-10
    
    def test_elo_update_home_win(self):
        """Test ELO update for home team win."""
        match = MatchResult(
            home_team="Team A",
            away_team="Team B", 
            home_score=2,
            away_score=1,
            league="premier_league",
            date=datetime.now()
        )
        
        # Set initial ratings
        self.engine.team_ratings["Team A"] = 1500.0
        self.engine.team_ratings["Team B"] = 1500.0
        
        update = self.engine.update_elo(match)
        
        # Home team should gain rating, away team should lose
        assert update.home_rating > 1500.0
        assert update.away_rating < 1500.0
        assert update.home_change > 0
        assert update.away_change < 0
    
    def test_elo_update_draw(self):
        """Test ELO update for draw."""
        match = MatchResult(
            home_team="Team A",
            away_team="Team B",
            home_score=1,
            away_score=1,
            league="premier_league", 
            date=datetime.now()
        )
        
        self.engine.team_ratings["Team A"] = 1500.0
        self.engine.team_ratings["Team B"] = 1500.0
        
        update = self.engine.update_elo(match)
        
        # Both teams should have minimal change for draw
        assert abs(update.home_change) < 5.0
        assert abs(update.away_change) < 5.0
    
    def test_elo_update_away_win(self):
        """Test ELO update for away team win."""
        match = MatchResult(
            home_team="Team A",
            away_team="Team B",
            home_score=0,
            away_score=2,
            league="premier_league",
            date=datetime.now()
        )
        
        self.engine.team_ratings["Team A"] = 1500.0
        self.engine.team_ratings["Team B"] = 1500.0
        
        update = self.engine.update_elo(match)
        
        # Away team should gain rating, home team should lose
        assert update.away_rating > 1500.0
        assert update.home_rating < 1500.0
        assert update.away_change > 0
        assert update.home_change < 0
    
    def test_predict_match_equal_teams(self):
        """Test match prediction for equal teams."""
        self.engine.team_ratings["Team A"] = 1500.0
        self.engine.team_ratings["Team B"] = 1500.0
        
        home_prob, draw_prob, away_prob = self.engine.predict_match(
            "Team A", "Team B", "premier_league"
        )
        
        # Probabilities should sum to 1
        assert abs(home_prob + draw_prob + away_prob - 1.0) < 1e-10
        
        # Home team should have slight advantage due to home field
        assert home_prob > away_prob
    
    def test_predict_match_unequal_teams(self):
        """Test match prediction for unequal teams."""
        self.engine.team_ratings["Strong Team"] = 1800.0
        self.engine.team_ratings["Weak Team"] = 1200.0
        
        home_prob, draw_prob, away_prob = self.engine.predict_match(
            "Strong Team", "Weak Team", "premier_league"
        )
        
        # Strong team should be heavily favored
        assert home_prob > 0.7
        assert away_prob < 0.2
    
    def test_generate_signal(self):
        """Test signal generation."""
        signal = self.engine.generate_signal(
            event_id="evt_123",
            market="1X2",
            probability=0.6,
            best_odds=1.8
        )
        
        assert signal.event_id == "evt_123"
        assert signal.market == "1X2"
        assert signal.implied_probability == 1.0 / 1.8
        assert signal.fair_odds == 1.0 / 0.6
        assert signal.edge == (0.6 * 1.8) - 1.0
        assert "Educational analytics only" in signal.risk_note
    
    def test_poisson_probability_edge_cases(self):
        """Test Poisson probability edge cases."""
        # Rate = 0
        prob = self.engine._poisson_probability(0.0, 0)
        assert prob == 1.0
        
        prob = self.engine._poisson_probability(0.0, 1)
        assert prob == 0.0
        
        # Negative k
        prob = self.engine._poisson_probability(1.0, -1)
        assert prob == 0.0
    
    def test_expected_score_calculation(self):
        """Test expected score calculation."""
        # Equal ratings
        score = self.engine._expected_score(1500.0, 1500.0)
        assert abs(score - 0.5) < 1e-10
        
        # Higher rating should have higher expected score
        score1 = self.engine._expected_score(1600.0, 1500.0)
        score2 = self.engine._expected_score(1500.0, 1600.0)
        assert score1 > score2
        assert score1 > 0.5
        assert score2 < 0.5
    
    def test_home_advantage_by_league(self):
        """Test home advantage calculation by league."""
        advantages = {
            "premier_league": 50.0,
            "la_liga": 45.0,
            "bundesliga": 40.0,
            "serie_a": 35.0,
            "nba": 30.0,
            "nfl": 25.0,
            "unknown_league": 30.0
        }
        
        for league, expected_advantage in advantages.items():
            advantage = self.engine._get_home_advantage(league)
            assert advantage == expected_advantage

if __name__ == "__main__":
    pytest.main([__file__])
