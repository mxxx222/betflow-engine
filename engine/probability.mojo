"""
Probability calculation module for BetFlow Engine.
Provides core probability functions for sports analytics.
"""

from math import log, exp, sqrt, erf, pi

def log_odds(probability: Float64) -> Float64:
    """
    Convert probability to log-odds.
    
    Args:
        probability: Probability value between 0 and 1
        
    Returns:
        Log-odds value
    """
    if probability <= 0.0 or probability >= 1.0:
        raise Error("Probability must be between 0 and 1")
    
    return log(probability / (1.0 - probability))

def implied_probability(odds: Float64) -> Float64:
    """
    Convert decimal odds to implied probability.
    
    Args:
        odds: Decimal odds value
        
    Returns:
        Implied probability
    """
    if odds <= 1.0:
        raise Error("Odds must be greater than 1.0")
    
    return 1.0 / odds

def vig_adjustment(probabilities: List[Float64]) -> List[Float64]:
    """
    Remove bookmaker vig (overround) from probabilities.
    
    Args:
        probabilities: List of probabilities that sum to > 1.0
        
    Returns:
        Adjusted probabilities that sum to 1.0
    """
    var total_prob = 0.0
    for prob in probabilities:
        total_prob += prob
    
    if total_prob <= 0.0:
        raise Error("Total probability must be positive")
    
    var adjusted: List[Float64] = []
    for prob in probabilities:
        adjusted.append(prob / total_prob)
    
    return adjusted

def kelly_criterion(probability: Float64, odds: Float64) -> Float64:
    """
    Calculate Kelly criterion for optimal stake sizing.
    
    Args:
        probability: True probability of outcome
        odds: Decimal odds
        
    Returns:
        Kelly fraction (0.0 to 1.0)
    """
    if probability <= 0.0 or probability >= 1.0:
        raise Error("Probability must be between 0 and 1")
    
    if odds <= 1.0:
        raise Error("Odds must be greater than 1.0")
    
    var kelly = (probability * odds - 1.0) / (odds - 1.0)
    return max(0.0, min(1.0, kelly))

def normal_cdf(x: Float64, mean: Float64 = 0.0, std: Float64 = 1.0) -> Float64:
    """
    Calculate cumulative distribution function of normal distribution.
    
    Args:
        x: Value to evaluate
        mean: Mean of distribution
        std: Standard deviation
        
    Returns:
        CDF value between 0 and 1
    """
    var z = (x - mean) / std
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def confidence_interval(probability: Float64, sample_size: Int, confidence: Float64 = 0.95) -> Tuple[Float64, Float64]:
    """
    Calculate confidence interval for probability estimate.
    
    Args:
        probability: Estimated probability
        sample_size: Sample size used for estimation
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if sample_size <= 0:
        raise Error("Sample size must be positive")
    
    var z_score = sqrt(2.0) * erf_inv(confidence)
    var margin = z_score * sqrt(probability * (1.0 - probability) / sample_size)
    
    var lower = max(0.0, probability - margin)
    var upper = min(1.0, probability + margin)
    
    return (lower, upper)

def erf_inv(x: Float64) -> Float64:
    """
    Approximate inverse error function using Newton-Raphson method.
    """
    if x <= -1.0 or x >= 1.0:
        raise Error("Input must be between -1 and 1")
    
    var a = 0.147
    var sign = 1.0 if x >= 0.0 else -1.0
    var x_abs = abs(x)
    
    var ln_term = log(1.0 - x_abs * x_abs)
    var sqrt_term = sqrt((2.0 / (pi * a)) + (ln_term / 2.0))
    var result = sign * sqrt(sqrt_term - (ln_term / 2.0))
    
    return result
