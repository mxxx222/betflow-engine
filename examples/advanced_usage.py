#!/usr/bin/env python3
"""
BetFlow Engine Advanced Usage Examples
Demonstrates performance optimization, batch processing, and integration patterns.
"""

import asyncio
import concurrent.futures
import time
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from engine import BetFlowEngine, MatchResult
from datetime import datetime, timedelta

class AdvancedAnalytics:
    """Advanced analytics using BetFlow Engine."""
    
    def __init__(self):
        self.engine = BetFlowEngine(enable_warmup=True)
        
    def batch_ev_analysis(self, opportunities: List[Tuple[float, float, str]]) -> pd.DataFrame:
        """Analyze multiple betting opportunities."""
        print("Analyzing betting opportunities...")
        
        results = []
        for prob, odds, description in opportunities:
            ev = self.engine.calc_ev(prob, odds)
            implied_prob = 1.0 / odds
            edge = prob - implied_prob
            
            results.append({
                'description': description,
                'probability': prob,
                'odds': odds,
                'implied_probability': implied_prob,
                'expected_value': ev,
                'edge': edge,
                'kelly_fraction': max(0, edge / (odds - 1)) if odds > 1 else 0
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('expected_value', ascending=False)
    
    def poisson_heatmap_analysis(self, home_rate: float, away_rate: float, max_goals: int = 6) -> Dict[str, Any]:
        """Generate detailed Poisson analysis with heatmap data."""
        print(f"Generating Poisson heatmap for rates {home_rate} vs {away_rate}...")
        
        probabilities = self.engine.calc_poisson(home_rate, away_rate, max_goals)
        
        # Create heatmap data
        heatmap_data = []
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                heatmap_data.append({
                    'home_goals': home_goals,
                    'away_goals': away_goals,
                    'probability': probabilities[home_goals][away_goals]
                })
        
        # Calculate market probabilities
        home_win = sum(probabilities[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h > a)
        draw = sum(probabilities[h][h] for h in range(max_goals + 1))
        away_win = sum(probabilities[h][a] for h in range(max_goals + 1) for a in range(max_goals + 1) if a > h)
        
        # Over/Under analysis
        over_under = {}
        for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
            over_prob = sum(probabilities[h][a] for h in range(max_goals + 1) 
                           for a in range(max_goals + 1) if (h + a) > threshold)
            over_under[f'over_{threshold}'] = over_prob
            over_under[f'under_{threshold}'] = 1.0 - over_prob
        
        return {
            'heatmap_data': heatmap_data,
            'match_outcomes': {
                'home_win': home_win,
                'draw': draw,
                'away_win': away_win
            },
            'over_under': over_under,
            'most_likely_score': max(heatmap_data, key=lambda x: x['probability'])
        }
    
    def elo_tournament_simulation(self, teams: List[str], league: str, rounds: int = 10) -> pd.DataFrame:
        """Simulate tournament with ELO updates."""
        print(f"Simulating {rounds}-round tournament with {len(teams)} teams...")
        
        results = []
        
        for round_num in range(1, rounds + 1):
            print(f"  Round {round_num}...")
            
            # Generate random matchups
            np.random.shuffle(teams)
            matches = [(teams[i], teams[i+1]) for i in range(0, len(teams)-1, 2)]
            
            for home_team, away_team in matches:
                # Predict match
                home_win, draw, away_win = self.engine.predict_match(home_team, away_team, league)
                
                # Simulate result based on probabilities
                outcome = np.random.choice(['home', 'draw', 'away'], p=[home_win, draw, away_win])
                
                if outcome == 'home':
                    home_score, away_score = 2, 1
                elif outcome == 'away':
                    home_score, away_score = 1, 2
                else:
                    home_score, away_score = 1, 1
                
                # Create match result
                match = MatchResult(
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    league=league,
                    date=datetime.utcnow()
                )
                
                # Update ELO
                elo_update = self.engine.update_elo(match)
                
                results.append({
                    'round': round_num,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'outcome': outcome,
                    'home_rating_before': elo_update.home_rating - elo_update.home_change,
                    'away_rating_before': elo_update.away_rating - elo_update.away_change,
                    'home_rating_after': elo_update.home_rating,
                    'away_rating_after': elo_update.away_rating,
                    'home_change': elo_update.home_change,
                    'away_change': elo_update.away_change
                })
        
        return pd.DataFrame(results)
    
    def concurrent_processing_demo(self, n_calculations: int = 10000) -> Dict[str, float]:
        """Demonstrate concurrent processing capabilities."""
        print(f"Running concurrent processing demo with {n_calculations} calculations...")
        
        # Generate random data
        prob_odds_pairs = [(np.random.uniform(0.1, 0.9), np.random.uniform(1.1, 5.0)) 
                          for _ in range(n_calculations)]
        
        # Sequential processing
        start = time.perf_counter()
        sequential_results = []
        for prob, odds in prob_odds_pairs:
            sequential_results.append(self.engine.calc_ev(prob, odds))
        sequential_time = time.perf_counter() - start
        
        # Concurrent processing
        def process_chunk(chunk):
            engine = BetFlowEngine()  # Each thread gets its own engine
            return [engine.calc_ev(prob, odds) for prob, odds in chunk]
        
        chunk_size = n_calculations // 4
        chunks = [prob_odds_pairs[i:i+chunk_size] for i in range(0, n_calculations, chunk_size)]
        
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
            concurrent_results = []
            for future in concurrent.futures.as_completed(futures):
                concurrent_results.extend(future.result())
        concurrent_time = time.perf_counter() - start
        
        return {
            'sequential_time': sequential_time,
            'concurrent_time': concurrent_time,
            'speedup': sequential_time / concurrent_time,
            'calculations_per_second_sequential': n_calculations / sequential_time,
            'calculations_per_second_concurrent': n_calculations / concurrent_time
        }
    
    def market_efficiency_analysis(self, market_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Analyze market efficiency using fair value calculations."""
        print("Analyzing market efficiency...")
        
        results = []
        
        for data in market_data:
            # Calculate fair probabilities using engine
            if data['market_type'] == 'match_winner':
                home_win, draw, away_win = self.engine.predict_match(
                    data['home_team'], data['away_team'], data['league']
                )
                fair_probs = {'home': home_win, 'draw': draw, 'away': away_win}
            else:
                # For other markets, use provided probability
                fair_probs = {'outcome': data.get('fair_probability', 0.5)}
            
            # Compare with market odds
            for outcome, fair_prob in fair_probs.items():
                if outcome in data['odds']:
                    market_odds = data['odds'][outcome]
                    implied_prob = 1.0 / market_odds
                    
                    ev = self.engine.calc_ev(fair_prob, market_odds)
                    
                    results.append({
                        'match': f"{data['home_team']} vs {data['away_team']}",
                        'market': data['market_type'],
                        'outcome': outcome,
                        'fair_probability': fair_prob,
                        'market_odds': market_odds,
                        'implied_probability': implied_prob,
                        'expected_value': ev,
                        'probability_difference': fair_prob - implied_prob,
                        'market_efficiency': abs(fair_prob - implied_prob),
                        'overround_contribution': implied_prob
                    })
        
        df = pd.DataFrame(results)
        
        # Calculate market overround
        match_groups = df.groupby(['match', 'market'])
        df['total_implied_prob'] = match_groups['implied_probability'].transform('sum')
        df['overround'] = df['total_implied_prob'] - 1.0
        
        return df.sort_values('expected_value', ascending=False)

async def async_processing_demo():
    """Demonstrate async processing patterns."""
    print("Running async processing demo...")
    
    engine = BetFlowEngine()
    
    async def calculate_ev_async(prob: float, odds: float) -> float:
        """Async wrapper for EV calculation."""
        # In a real scenario, this might involve I/O operations
        await asyncio.sleep(0.001)  # Simulate async I/O
        return engine.calc_ev(prob, odds)
    
    # Generate test data
    calculations = [(np.random.uniform(0.1, 0.9), np.random.uniform(1.1, 5.0)) 
                   for _ in range(100)]
    
    # Process asynchronously
    start = time.perf_counter()
    tasks = [calculate_ev_async(prob, odds) for prob, odds in calculations]
    results = await asyncio.gather(*tasks)
    async_time = time.perf_counter() - start
    
    print(f"  Processed {len(calculations)} async calculations in {async_time:.3f}s")
    print(f"  Average EV: {np.mean(results):.4f}")
    print(f"  Positive EV count: {sum(1 for ev in results if ev > 0)}")

def main():
    print("=== BetFlow Engine v0.9.0 Advanced Usage Examples ===\n")
    
    analytics = AdvancedAnalytics()
    
    # 1. Batch EV Analysis
    print("1. Batch Expected Value Analysis:")
    opportunities = [
        (0.65, 1.8, "Strong favorite with value"),
        (0.35, 3.2, "Underdog with potential"),
        (0.52, 2.1, "Slight edge on even match"),
        (0.28, 4.5, "Long shot with high payout"),
        (0.45, 2.0, "Negative EV example"),
        (0.75, 1.4, "Heavy favorite, low value"),
    ]
    
    ev_analysis = analytics.batch_ev_analysis(opportunities)
    print(ev_analysis.to_string(index=False, float_format='%.4f'))
    print()
    
    # 2. Poisson Heatmap Analysis
    print("2. Detailed Poisson Analysis:")
    poisson_analysis = analytics.poisson_heatmap_analysis(1.8, 1.2, 5)
    
    print("   Match Outcomes:")
    for outcome, prob in poisson_analysis['match_outcomes'].items():
        print(f"     {outcome}: {prob:.3f} ({prob:.1%})")
    
    print("   Over/Under Markets:")
    for market, prob in poisson_analysis['over_under'].items():
        print(f"     {market}: {prob:.3f} ({prob:.1%})")
    
    most_likely = poisson_analysis['most_likely_score']
    print(f"   Most likely score: {most_likely['home_goals']}-{most_likely['away_goals']} ({most_likely['probability']:.3f})")
    print()
    
    # 3. Tournament Simulation
    print("3. ELO Tournament Simulation:")
    teams = ["Arsenal", "Chelsea", "Liverpool", "Manchester City", "Tottenham", "Manchester United"]
    tournament_results = analytics.elo_tournament_simulation(teams, "premier_league", 5)
    
    # Show final ratings
    final_ratings = {}
    for team in teams:
        home_ratings = tournament_results[tournament_results['home_team'] == team]['home_rating_after']
        away_ratings = tournament_results[tournament_results['away_team'] == team]['away_rating_after']
        
        if not home_ratings.empty:
            final_ratings[team] = home_ratings.iloc[-1]
        elif not away_ratings.empty:
            final_ratings[team] = away_ratings.iloc[-1]
        else:
            final_ratings[team] = 1500.0  # Default rating
    
    print("   Final ELO Ratings:")
    for team, rating in sorted(final_ratings.items(), key=lambda x: x[1], reverse=True):
        print(f"     {team}: {rating:.1f}")
    print()
    
    # 4. Concurrent Processing
    print("4. Concurrent Processing Performance:")
    perf_results = analytics.concurrent_processing_demo(5000)
    
    print(f"   Sequential: {perf_results['sequential_time']:.3f}s ({perf_results['calculations_per_second_sequential']:.0f} calc/s)")
    print(f"   Concurrent: {perf_results['concurrent_time']:.3f}s ({perf_results['calculations_per_second_concurrent']:.0f} calc/s)")
    print(f"   Speedup: {perf_results['speedup']:.2f}x")
    print()
    
    # 5. Market Efficiency Analysis
    print("5. Market Efficiency Analysis:")
    market_data = [
        {
            'home_team': 'Barcelona',
            'away_team': 'Real Madrid',
            'league': 'la_liga',
            'market_type': 'match_winner',
            'odds': {'home': 2.1, 'draw': 3.4, 'away': 3.2}
        },
        {
            'home_team': 'Liverpool',
            'away_team': 'Manchester City',
            'league': 'premier_league',
            'market_type': 'match_winner',
            'odds': {'home': 2.8, 'draw': 3.1, 'away': 2.6}
        }
    ]
    
    efficiency_analysis = analytics.market_efficiency_analysis(market_data)
    
    # Show best opportunities
    best_opportunities = efficiency_analysis.head(3)
    print("   Best Value Opportunities:")
    for _, row in best_opportunities.iterrows():
        print(f"     {row['match']} - {row['outcome']}: EV={row['expected_value']:+.4f}, Odds={row['market_odds']:.2f}")
    print()
    
    # 6. Async Processing Demo
    print("6. Async Processing Demo:")
    asyncio.run(async_processing_demo())
    print()
    
    print("=== Advanced examples completed successfully ===")

if __name__ == "__main__":
    main()
