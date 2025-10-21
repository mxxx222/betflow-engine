"""
ELO rating system implementation for BetFlow Engine.
Handles team and player ELO calculations with home advantage.
"""

from math import log10, pow

struct EloRating:
    var rating: Float64
    var games_played: Int
    var last_updated: Float64

    def __init__(inout self, initial_rating: Float64 = 1500.0):
        self.rating = initial_rating
        self.games_played = 0
        self.last_updated = 0.0

    def expected_score(self, opponent_rating: Float64, home_advantage: Float64 = 0.0) -> Float64:
        """
        Calculate expected score against opponent.
        
        Args:
            opponent_rating: Opponent's ELO rating
            home_advantage: Home advantage bonus (default 0.0)
            
        Returns:
            Expected score (0.0 to 1.0)
        """
        var rating_diff = self.rating - opponent_rating + home_advantage
        return 1.0 / (1.0 + pow(10.0, -rating_diff / 400.0))

    def update_rating(inout self, actual_score: Float64, opponent_rating: Float64, 
                     k_factor: Float64 = 32.0, home_advantage: Float64 = 0.0):
        """
        Update ELO rating based on match result.
        
        Args:
            actual_score: Actual result (1.0 for win, 0.5 for draw, 0.0 for loss)
            opponent_rating: Opponent's ELO rating
            k_factor: K-factor for rating updates
            home_advantage: Home advantage bonus
        """
        var expected = self.expected_score(opponent_rating, home_advantage)
        var rating_change = k_factor * (actual_score - expected)
        
        self.rating += rating_change
        self.games_played += 1

def calculate_k_factor(games_played: Int, rating: Float64) -> Float64:
    """
    Calculate dynamic K-factor based on experience and rating.
    
    Args:
        games_played: Number of games played
        rating: Current rating
        
    Returns:
        K-factor value
    """
    var base_k = 32.0
    
    # Reduce K-factor for experienced players
    if games_played > 30:
        base_k = 16.0
    elif games_played > 10:
        base_k = 24.0
    
    # Reduce K-factor for high-rated players
    if rating > 2400:
        base_k *= 0.5
    elif rating > 2000:
        base_k *= 0.75
    
    return base_k

def home_advantage_factor(league: String, home_team: String, away_team: String) -> Float64:
    """
    Calculate home advantage factor based on league and teams.
    
    Args:
        league: League identifier
        home_team: Home team name
        away_team: Away team name
        
    Returns:
        Home advantage bonus
    """
    # Base home advantage by league
    var base_advantage = 0.0
    
    if league == "premier_league":
        base_advantage = 50.0
    elif league == "la_liga":
        base_advantage = 45.0
    elif league == "bundesliga":
        base_advantage = 40.0
    elif league == "serie_a":
        base_advantage = 35.0
    elif league == "nba":
        base_advantage = 30.0
    elif league == "nfl":
        base_advantage = 25.0
    else:
        base_advantage = 30.0  # Default
    
    # Team-specific adjustments could be added here
    # For now, return base advantage
    return base_advantage

def calculate_team_elo(home_rating: Float64, away_rating: Float64, 
                      home_advantage: Float64, result: Int) -> Tuple[Float64, Float64]:
    """
    Calculate ELO updates for both teams after a match.
    
    Args:
        home_rating: Home team's current rating
        away_rating: Away team's current rating
        home_advantage: Home advantage bonus
        result: Match result (1 for home win, 0 for draw, -1 for away win)
        
    Returns:
        Tuple of (new_home_rating, new_away_rating)
    """
    var home_elo = EloRating(home_rating)
    var away_elo = EloRating(away_rating)
    
    # Convert result to scores
    var home_score: Float64
    var away_score: Float64
    
    if result == 1:
        home_score = 1.0
        away_score = 0.0
    elif result == 0:
        home_score = 0.5
        away_score = 0.5
    else:  # result == -1
        home_score = 0.0
        away_score = 1.0
    
    # Calculate K-factors
    var home_k = calculate_k_factor(home_elo.games_played, home_rating)
    var away_k = calculate_k_factor(away_elo.games_played, away_rating)
    
    # Update ratings
    home_elo.update_rating(home_score, away_rating, home_k, home_advantage)
    away_elo.update_rating(away_score, home_rating, away_k, -home_advantage)
    
    return (home_elo.rating, away_elo.rating)

def predict_match_probability(home_rating: Float64, away_rating: Float64, 
                            home_advantage: Float64 = 0.0) -> Tuple[Float64, Float64, Float64]:
    """
    Predict match outcome probabilities using ELO ratings.
    
    Args:
        home_rating: Home team's ELO rating
        away_rating: Away team's ELO rating
        home_advantage: Home advantage bonus
        
    Returns:
        Tuple of (home_win_prob, draw_prob, away_win_prob)
    """
    var home_elo = EloRating(home_rating)
    var home_win_prob = home_elo.expected_score(away_rating, home_advantage)
    
    # Estimate draw probability (simplified model)
    var rating_diff = abs(home_rating - away_rating)
    var draw_prob = 0.25 * exp(-rating_diff / 200.0)  # Decreases with rating difference
    
    # Normalize probabilities
    var total = home_win_prob + draw_prob + (1.0 - home_win_prob)
    home_win_prob /= total
    draw_prob /= total
    var away_win_prob = 1.0 - home_win_prob - draw_prob
    
    return (home_win_prob, draw_prob, away_win_prob)
