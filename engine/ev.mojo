"""
Expected Value (EV) calculation module for BetFlow Engine.
Handles EV calculations, variance, and risk metrics.
"""

from math import sqrt, log, exp
from probability import implied_probability, log_odds

def calculate_ev(probability: Float64, odds: Float64) -> Float64:
    """
    Calculate expected value of a bet.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        
    Returns:
        Expected value (positive = profitable)
    """
    if probability <= 0.0 or probability >= 1.0:
        raise Error("Probability must be between 0 and 1")
    
    if odds <= 1.0:
        raise Error("Odds must be greater than 1.0")
    
    return (probability * odds) - 1.0

def calculate_edge(probability: Float64, odds: Float64) -> Float64:
    """
    Calculate edge percentage.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        
    Returns:
        Edge as percentage (0.0 to 1.0)
    """
    var ev = calculate_ev(probability, odds)
    return ev / odds

def calculate_variance(probability: Float64, odds: Float64, stake: Float64 = 1.0) -> Float64:
    """
    Calculate variance of bet outcome.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        stake: Stake amount (default 1.0)
        
    Returns:
        Variance of return
    """
    var win_return = (odds - 1.0) * stake
    var loss_return = -stake
    
    var expected_return = probability * win_return + (1.0 - probability) * loss_return
    var win_variance = probability * pow(win_return - expected_return, 2.0)
    var loss_variance = (1.0 - probability) * pow(loss_return - expected_return, 2.0)
    
    return win_variance + loss_variance

def calculate_standard_deviation(probability: Float64, odds: Float64, stake: Float64 = 1.0) -> Float64:
    """
    Calculate standard deviation of bet outcome.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        stake: Stake amount (default 1.0)
        
    Returns:
        Standard deviation of return
    """
    return sqrt(calculate_variance(probability, odds, stake))

def calculate_sharpe_ratio(probability: Float64, odds: Float64, 
                          risk_free_rate: Float64 = 0.0) -> Float64:
    """
    Calculate Sharpe ratio for bet evaluation.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        risk_free_rate: Risk-free rate (default 0.0)
        
    Returns:
        Sharpe ratio
    """
    var ev = calculate_ev(probability, odds)
    var std_dev = calculate_standard_deviation(probability, odds)
    
    if std_dev == 0.0:
        return 0.0
    
    return (ev - risk_free_rate) / std_dev

def calculate_value_at_risk(probability: Float64, odds: Float64, stake: Float64, 
                          confidence: Float64 = 0.95) -> Float64:
    """
    Calculate Value at Risk (VaR) for bet.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        stake: Stake amount
        confidence: Confidence level (default 0.95)
        
    Returns:
        VaR (maximum expected loss)
    """
    var loss_return = -stake
    var win_return = (odds - 1.0) * stake
    
    # For binary outcomes, VaR is simply the loss amount
    if probability < (1.0 - confidence):
        return abs(loss_return)
    else:
        return 0.0

def calculate_expected_shortfall(probability: Float64, odds: Float64, stake: Float64, 
                               confidence: Float64 = 0.95) -> Float64:
    """
    Calculate Expected Shortfall (Conditional VaR).
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        stake: Stake amount
        confidence: Confidence level (default 0.95)
        
    Returns:
        Expected Shortfall
    """
    var loss_return = -stake
    
    if probability < (1.0 - confidence):
        return abs(loss_return)
    else:
        return 0.0

def portfolio_ev(probabilities: List[Float64], odds: List[Float64], 
                stakes: List[Float64]) -> Float64:
    """
    Calculate expected value of bet portfolio.
    
    Args:
        probabilities: List of true probabilities
        odds: List of decimal odds
        stakes: List of stake amounts
        
    Returns:
        Total expected value
    """
    if len(probabilities) != len(odds) or len(odds) != len(stakes):
        raise Error("All lists must have same length")
    
    var total_ev = 0.0
    for i in range(len(probabilities)):
        total_ev += calculate_ev(probabilities[i], odds[i]) * stakes[i]
    
    return total_ev

def portfolio_variance(probabilities: List[Float64], odds: List[Float64], 
                      stakes: List[Float64], correlations: List[List[Float64]] = []) -> Float64:
    """
    Calculate variance of bet portfolio.
    
    Args:
        probabilities: List of true probabilities
        odds: List of decimal odds
        stakes: List of stake amounts
        correlations: Correlation matrix (optional)
        
    Returns:
        Portfolio variance
    """
    if len(probabilities) != len(odds) or len(odds) != len(stakes):
        raise Error("All lists must have same length")
    
    var n = len(probabilities)
    var total_variance = 0.0
    
    # Individual variances
    for i in range(n):
        var individual_var = calculate_variance(probabilities[i], odds[i], stakes[i])
        total_variance += individual_var
    
    # Correlation terms (if provided)
    if len(correlations) > 0:
        for i in range(n):
            for j in range(i + 1, n):
                var std_i = calculate_standard_deviation(probabilities[i], odds[i], stakes[i])
                var std_j = calculate_standard_deviation(probabilities[j], odds[j], stakes[j])
                var correlation = correlations[i][j] if i < len(correlations) and j < len(correlations[i]) else 0.0
                total_variance += 2.0 * correlation * std_i * std_j
    
    return total_variance

def kelly_optimal_stake(probability: Float64, odds: Float64, 
                       bankroll: Float64, kelly_fraction: Float64 = 1.0) -> Float64:
    """
    Calculate optimal stake using Kelly criterion.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        bankroll: Total bankroll
        kelly_fraction: Kelly fraction (0.0 to 1.0, default 1.0)
        
    Returns:
        Optimal stake amount
    """
    var kelly = (probability * odds - 1.0) / (odds - 1.0)
    var optimal_fraction = max(0.0, min(1.0, kelly * kelly_fraction))
    
    return bankroll * optimal_fraction

def risk_adjusted_return(probability: Float64, odds: Float64, 
                        risk_tolerance: Float64 = 1.0) -> Float64:
    """
    Calculate risk-adjusted return metric.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        risk_tolerance: Risk tolerance factor (default 1.0)
        
    Returns:
        Risk-adjusted return
    """
    var ev = calculate_ev(probability, odds)
    var variance = calculate_variance(probability, odds)
    
    return ev - (risk_tolerance * variance / 2.0)

def confidence_interval_ev(probability: Float64, odds: Float64, stake: Float64,
                         confidence: Float64 = 0.95, n_simulations: Int = 10000) -> Tuple[Float64, Float64]:
    """
    Calculate confidence interval for EV using Monte Carlo simulation.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        stake: Stake amount
        confidence: Confidence level (default 0.95)
        n_simulations: Number of simulations (default 10000)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    # This is a simplified version - full implementation would use random sampling
    var ev = calculate_ev(probability, odds) * stake
    var std_dev = calculate_standard_deviation(probability, odds, stake)
    
    # Approximate confidence interval using normal approximation
    var z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
    var margin = z_score * std_dev
    
    return (ev - margin, ev + margin)
