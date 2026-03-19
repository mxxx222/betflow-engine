#!/usr/bin/env python3
"""
BetFlow Engine Basic Usage Examples
Educational analytics demonstrations.
"""

from engine import BetFlowEngine, MatchResult
from datetime import datetime
import time

def main():
    print("=== BetFlow Engine v0.9.0 Basic Usage Examples ===\n")
    
    # Initialize engine
    print("1. Initializing BetFlow Engine...")
    engine = BetFlowEngine()
    
    # Check health
    health = engine.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Mojo Available: {health['mojo_available']}")
    print(f"   Warmed Up: {health['warmed_up']}")
    print()
    
    # Expected Value Calculations
    print("2. Expected Value Calculations:")
    
    bets = [
        (0.6, 2.0, "Favorite team"),
        (0.3, 4.0, "Underdog team"),
        (0.5, 2.2, "Even match"),
        (0.25, 3.8, "Long shot"),
    ]
    
    for prob, odds, description in bets:
        ev = engine.calc_ev(prob, odds)
        print(f"   {description}: P={prob}, Odds={odds} → EV={ev:+.4f}")
    print()
    
    # Poisson Distribution Analysis
    print("3. Poisson Distribution Analysis:")
    
    matches = [
        (1.5, 1.2, "Arsenal vs Chelsea"),
        (2.1, 0.8, "Manchester City vs Brighton"),
        (1.0, 1.0, "Even match"),
    ]
    
    for home_rate, away_rate, description in matches:
        print(f"   {description} (Home: {home_rate}, Away: {away_rate}):")
        
        probabilities = engine.calc_poisson(home_rate, away_rate, 4)
        
        # Calculate outcome probabilities
        home_win = sum(probabilities[h][a] for h in range(5) for a in range(5) if h > a)
        draw = sum(probabilities[h][h] for h in range(5))
        away_win = sum(probabilities[h][a] for h in range(5) for a in range(5) if a > h)
        
        print(f"     Home Win: {home_win:.3f} ({home_win:.1%})")
        print(f"     Draw: {draw:.3f} ({draw:.1%})")
        print(f"     Away Win: {away_win:.3f} ({away_win:.1%})")
        print()
    
    # ELO Rating Updates
    print("4. ELO Rating System:")
    
    matches = [
        {"home": "Arsenal", "away": "Chelsea", "home_score": 2, "away_score": 1, "league": "premier_league"},
        {"home": "Barcelona", "away": "Real Madrid", "home_score": 1, "away_score": 3, "league": "la_liga"},
        {"home": "Bayern Munich", "away": "Dortmund", "home_score": 0, "away_score": 0, "league": "bundesliga"},
    ]
    
    for match_data in matches:
        match = MatchResult(
            home_team=match_data["home"],
            away_team=match_data["away"],
            home_score=match_data["home_score"],
            away_score=match_data["away_score"],
            league=match_data["league"],
            date=datetime.utcnow()
        )
        
        elo_update = engine.update_elo(match)
        
        print(f"   {match_data['home']} {match_data['home_score']}-{match_data['away_score']} {match_data['away']}:")
        print(f"     {match_data['home']}: {elo_update.home_rating:.1f} (Δ{elo_update.home_change:+.1f})")
        print(f"     {match_data['away']}: {elo_update.away_rating:.1f} (Δ{elo_update.away_change:+.1f})")
        print()
    
    # Match Predictions
    print("5. Match Outcome Predictions:")
    
    upcoming_matches = [
        ("Manchester United", "Liverpool", "premier_league"),
        ("PSG", "Lyon", "ligue_1"),
        ("Juventus", "AC Milan", "serie_a"),
    ]
    
    for home, away, league in upcoming_matches:
        home_win, draw, away_win = engine.predict_match(home, away, league)
        
        # Convert to implied odds
        home_odds = 1.0 / home_win if home_win > 0 else float('inf')
        draw_odds = 1.0 / draw if draw > 0 else float('inf')
        away_odds = 1.0 / away_win if away_win > 0 else float('inf')
        
        print(f"   {home} vs {away} ({league}):")
        print(f"     {home}: {home_win:.1%} (odds: {home_odds:.2f})")
        print(f"     Draw: {draw:.1%} (odds: {draw_odds:.2f})")
        print(f"     {away}: {away_win:.1%} (odds: {away_odds:.2f})")
        print()
    
    # Performance Benchmark
    print("6. Performance Benchmark:")
    
    # EV calculations
    start = time.perf_counter()
    for _ in range(1000):
        engine.calc_ev(0.6, 2.0)
    ev_duration = (time.perf_counter() - start) * 1000
    
    # Poisson calculations
    start = time.perf_counter()
    for _ in range(100):
        engine.calc_poisson(1.5, 1.2, 4)
    poisson_duration = (time.perf_counter() - start) * 1000
    
    print(f"   1000 EV calculations: {ev_duration:.1f}ms ({ev_duration/1000:.3f}ms per calc)")
    print(f"   100 Poisson calculations: {poisson_duration:.1f}ms ({poisson_duration/100:.3f}ms per calc)")
    print()
    
    # Signal Generation
    print("7. Analytics Signal Generation:")
    
    signals_data = [
        ("match_001", "match_winner", 0.65, 1.8),
        ("match_002", "over_2.5_goals", 0.45, 2.4),
        ("match_003", "both_teams_score", 0.7, 1.6),
    ]
    
    for event_id, market, prob, odds in signals_data:
        signal = engine.generate_signal(event_id, market, prob, odds)
        
        print(f"   Signal {signal.id}:")
        print(f"     Market: {market}")
        print(f"     Fair odds: {signal.fair_odds:.2f}")
        print(f"     Best odds: {signal.best_book_odds:.2f}")
        print(f"     Edge: {signal.edge:+.4f}")
        print(f"     Note: {signal.risk_note}")
        print()
    
    print("=== Examples completed successfully ===")

if __name__ == "__main__":
    main()
