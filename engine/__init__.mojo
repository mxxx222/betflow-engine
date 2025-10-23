"""
BetFlow Engine - Mojo calculation core with Python bindings.
Provides high-performance sports analytics calculations.
"""

from .elo import EloRating, calculate_team_elo, predict_match_probability, home_advantage_factor
from .ev import calculate_ev, calculate_edge, calculate_variance, calculate_sharpe_ratio, kelly_optimal_stake
from .poisson import match_outcome_probabilities, over_under_probability, both_teams_score_probability, correct_score_probability
from .probability import implied_probability, vig_adjustment, kelly_criterion, normal_cdf

# Python-compatible interface
@export
struct BetFlowEngine:
    """Main engine class providing Python interface to Mojo calculations."""

    var team_ratings: Dict[String, Float64]
    var player_ratings: Dict[String, Float64]

    def __init__(inout self):
        self.team_ratings = Dict[String, Float64]()
        self.player_ratings = Dict[String, Float64]()

    @export
    def calc_ev(self, probability: Float64, odds: Float64) -> Float64:
        """Calculate expected value."""
        return calculate_ev(probability, odds)

    @export
    def calc_poisson(self, home_rate: Float64, away_rate: Float64,
                    max_goals: Int = 6) -> List[List[Float64]]:
        """Calculate Poisson match outcome probabilities."""
        return match_outcome_probabilities(home_rate, away_rate, max_goals)

    @export
    def update_elo(self, home_team: String, away_team: String,
                  home_score: Int, away_score: Int, league: String) -> Tuple[Float64, Float64, Float64, Float64]:
        """Update ELO ratings based on match result."""
        home_rating = self.team_ratings.get(home_team, 1500.0)
        away_rating = self.team_ratings.get(away_team, 1500.0)

        home_advantage = home_advantage_factor(league, home_team, away_team)
        new_home, new_away = calculate_team_elo(home_rating, away_rating, home_advantage,
                                              1 if home_score > away_score else (0 if home_score == away_score else -1))

        self.team_ratings[home_team] = new_home
        self.team_ratings[away_team] = new_away

        return (new_home, new_away, new_home - home_rating, new_away - away_rating)

    @export
    def predict_match(self, home_team: String, away_team: String,
                     league: String) -> Tuple[Float64, Float64, Float64]:
        """Predict match outcome probabilities."""
        home_rating = self.team_ratings.get(home_team, 1500.0)
        away_rating = self.team_ratings.get(away_team, 1500.0)
        home_advantage = home_advantage_factor(league, home_team, away_team)

        return predict_match_probability(home_rating, away_rating, home_advantage)

    @export
    def generate_signal(self, event_id: String, market: String,
                       probability: Float64, best_odds: Float64) -> Tuple[String, Float64, Float64, Float64, String]:
        """Generate analytics signal."""
        fair_odds = 1.0 / probability
        edge = calculate_edge(probability, best_odds)

        signal_id = "sig_" + event_id + "_" + market
        risk_note = "Educational analytics only"
        explanation = "Probability: " + String(probability) + ", Edge: " + String(edge)

        return (signal_id, implied_probability(best_odds), fair_odds, edge, risk_note)