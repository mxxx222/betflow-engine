"""
Poisson distribution module for BetFlow Engine.
Handles goal/point scoring predictions using Poisson models.
"""

from math import exp, factorial, pow, log

def poisson_probability(rate: Float64, k: Int) -> Float64:
    """
    Calculate Poisson probability for k events given rate.
    
    Args:
        rate: Expected rate (lambda)
        k: Number of events
        
    Returns:
        Probability of k events
    """
    if rate < 0.0:
        raise Error("Rate must be non-negative")
    
    if k < 0:
        return 0.0
    
    var k_factorial = 1.0
    for i in range(1, k + 1):
        k_factorial *= Float64(i)
    
    return (pow(rate, Float64(k)) * exp(-rate)) / k_factorial

def poisson_cumulative(rate: Float64, k: Int) -> Float64:
    """
    Calculate cumulative Poisson probability for 0 to k events.
    
    Args:
        rate: Expected rate (lambda)
        k: Maximum number of events
        
    Returns:
        Cumulative probability
    """
    var cumulative = 0.0
    for i in range(k + 1):
        cumulative += poisson_probability(rate, i)
    
    return cumulative

def match_outcome_probabilities(home_rate: Float64, away_rate: Float64, 
                               max_goals: Int = 6) -> List[List[Float64]]:
    """
    Calculate match outcome probabilities using Poisson model.
    
    Args:
        home_rate: Home team's expected goals
        away_rate: Away team's expected goals
        max_goals: Maximum goals to consider (default 6)
        
    Returns:
        2D array of probabilities [home_goals][away_goals]
    """
    var probabilities: List[List[Float64]] = []
    
    for home_goals in range(max_goals + 1):
        var row: List[Float64] = []
        for away_goals in range(max_goals + 1):
            var home_prob = poisson_probability(home_rate, home_goals)
            var away_prob = poisson_probability(away_rate, away_goals)
            row.append(home_prob * away_prob)
        probabilities.append(row)
    
    return probabilities

def over_under_probability(home_rate: Float64, away_rate: Float64, 
                          threshold: Float64) -> Float64:
    """
    Calculate probability of total goals over threshold.
    
    Args:
        home_rate: Home team's expected goals
        away_rate: Away team's expected goals
        threshold: Goals threshold (e.g., 2.5)
        
    Returns:
        Probability of over threshold
    """
    var total_rate = home_rate + away_rate
    var over_prob = 0.0
    
    # Calculate probability for each possible total
    for total_goals in range(int(threshold) + 1, 20):  # Up to 20 goals
        var prob = poisson_probability(total_rate, total_goals)
        over_prob += prob
    
    return over_prob

def both_teams_score_probability(home_rate: Float64, away_rate: Float64) -> Float64:
    """
    Calculate probability that both teams score.
    
    Args:
        home_rate: Home team's expected goals
        away_rate: Away team's expected goals
        
    Returns:
        Probability of both teams scoring
    """
    var home_scores = 1.0 - poisson_probability(home_rate, 0)
    var away_scores = 1.0 - poisson_probability(away_rate, 0)
    
    return home_scores * away_scores

def correct_score_probability(home_rate: Float64, away_rate: Float64, 
                            home_goals: Int, away_goals: Int) -> Float64:
    """
    Calculate probability of exact scoreline.
    
    Args:
        home_rate: Home team's expected goals
        away_rate: Away team's expected goals
        home_goals: Home team's actual goals
        away_goals: Away team's actual goals
        
    Returns:
        Probability of exact score
    """
    var home_prob = poisson_probability(home_rate, home_goals)
    var away_prob = poisson_probability(away_rate, away_goals)
    
    return home_prob * away_prob

def asian_handicap_probability(home_rate: Float64, away_rate: Float64, 
                             handicap: Float64) -> Float64:
    """
    Calculate probability for Asian handicap betting.
    
    Args:
        home_rate: Home team's expected goals
        away_rate: Away team's expected goals
        handicap: Handicap value (e.g., -1.5, 0.5)
        
    Returns:
        Probability of home team covering handicap
    """
    var adjusted_home_rate = home_rate + handicap
    var home_win_prob = 0.0
    
    # Calculate probability of home team winning with handicap
    for home_goals in range(20):
        for away_goals in range(20):
            if home_goals > away_goals:
                var prob = poisson_probability(adjusted_home_rate, home_goals) * \
                          poisson_probability(away_rate, away_goals)
                home_win_prob += prob
    
    return home_win_prob

def expected_goals_from_odds(odds: Float64, margin: Float64 = 0.05) -> Float64:
    """
    Convert over/under odds to expected total goals.
    
    Args:
        odds: Decimal odds for over/under market
        margin: Bookmaker margin (default 5%)
        
    Returns:
        Expected total goals
    """
    var implied_prob = 1.0 / odds
    var fair_prob = implied_prob / (1.0 + margin)
    
    # Approximate expected goals from probability
    # This is a simplified conversion - in practice, you'd use more sophisticated methods
    var expected_goals = -log(1.0 - fair_prob)
    
    return expected_goals

def team_expected_goals(home_rate: Float64, away_rate: Float64, 
                       home_advantage: Float64 = 0.0) -> Tuple[Float64, Float64]:
    """
    Calculate expected goals for both teams with home advantage.
    
    Args:
        home_rate: Base home team rate
        away_rate: Base away team rate
        home_advantage: Home advantage multiplier
        
    Returns:
        Tuple of (adjusted_home_rate, adjusted_away_rate)
    """
    var adjusted_home = home_rate * (1.0 + home_advantage)
    var adjusted_away = away_rate * (1.0 - home_advantage * 0.5)  # Slight penalty for away team
    
    return (adjusted_home, adjusted_away)
