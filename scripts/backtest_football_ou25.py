#!/usr/bin/env python3
"""
Football Over/Under 2.5 backtesting system for MVP validation
Runs 2-week backtest with risk management and ROI reporting
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.core.production_config import ProductionConfig, LEAGUE_PRIORITY, LEAGUE_RISK_LIMITS
from api.providers.football_odds_provider import FootballOddsProvider, FootballMatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest result for a single match"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    predicted_over: float
    predicted_under: float
    bookmaker_over: float
    bookmaker_under: float
    edge_over: float
    edge_under: float
    stake_over: float
    stake_under: float
    actual_goals: int
    result_over: float
    result_under: float
    profit_loss: float
    confidence: float


@dataclass
class BacktestSummary:
    """Overall backtest summary"""
    total_matches: int
    profitable_matches: int
    total_profit: float
    total_stake: float
    roi_percentage: float
    max_drawdown: float
    win_rate: float
    avg_edge: float
    league_breakdown: Dict[str, Dict[str, float]]


class FootballOU25Backtester:
    """Backtesting system for football Over/Under 2.5 markets"""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.bankroll = 10000.0  # Starting bankroll
        self.current_bankroll = self.bankroll
        self.max_stake_percentage = 0.02  # 2% max stake
        self.stop_loss_percentage = 0.10  # 10% stop loss
        
        # Track results
        self.results: List[BacktestResult] = []
        self.bankroll_history: List[float] = [self.bankroll]
        self.drawdown_history: List[float] = [0.0]
        
    async def run_backtest(self, days: int = 14) -> BacktestSummary:
        """Run backtest for specified number of days"""
        logger.info(f"Starting {days}-day backtest for football OU 2.5")
        
        # Generate historical data (in production, this would come from real APIs)
        historical_matches = await self._generate_historical_data(days)
        
        # Process each match
        for match in historical_matches:
            await self._process_match(match)
            
        # Calculate summary
        summary = self._calculate_summary()
        
        logger.info(f"Backtest completed: {summary.roi_percentage:.2f}% ROI")
        return summary
    
    async def _generate_historical_data(self, days: int) -> List[FootballMatch]:
        """Generate historical match data for backtesting"""
        # In production, this would fetch real historical data
        # For MVP, we'll simulate realistic data
        
        matches = []
        start_date = datetime.now() - timedelta(days=days)
        
        # Simulate matches for each league
        for league in LEAGUE_PRIORITY[:5]:  # Top 5 leagues for MVP
            league_risk = LEAGUE_RISK_LIMITS.get(league, {"max_stake": 0.01, "min_confidence": 0.5})
            
            # Generate 2-3 matches per day per league
            for day_offset in range(days):
                match_date = start_date + timedelta(days=day_offset)
                
                # Skip weekends for some leagues
                if league in ["premier-league", "championship"] and match_date.weekday() not in [5, 6]:
                    continue
                    
                # Generate 1-3 matches per day
                num_matches = np.random.randint(1, 4)
                
                for match_num in range(num_matches):
                    # Simulate realistic odds
                    over_odds = np.random.uniform(1.8, 2.2)
                    under_odds = np.random.uniform(1.8, 2.2)
                    
                    # Simulate actual goals (realistic distribution)
                    actual_goals = self._simulate_goals(league)
                    
                    match = FootballMatch(
                        match_id=f"backtest_{league}_{day_offset}_{match_num}",
                        home_team=f"Home Team {match_num}",
                        away_team=f"Away Team {match_num}",
                        league=league,
                        start_time=match_date,
                        status="completed",
                        over_2_5_odds=over_odds,
                        under_2_5_odds=under_odds,
                        bookmaker="Simulated",
                        last_updated=datetime.utcnow()
                    )
                    
                    # Add actual goals for backtesting
                    match.actual_goals = actual_goals
                    matches.append(match)
        
        return matches
    
    def _simulate_goals(self, league: str) -> int:
        """Simulate realistic goal counts based on league"""
        # League-specific goal distributions
        league_params = {
            "premier-league": {"mean": 2.7, "std": 1.2},
            "championship": {"mean": 2.5, "std": 1.3},
            "bundesliga": {"mean": 2.8, "std": 1.1},
            "serie-a": {"mean": 2.4, "std": 1.0},
            "la-liga": {"mean": 2.6, "std": 1.2}
        }
        
        params = league_params.get(league, {"mean": 2.5, "std": 1.2})
        goals = max(0, int(np.random.normal(params["mean"], params["std"])))
        return min(goals, 8)  # Cap at 8 goals
    
    async def _process_match(self, match: FootballMatch):
        """Process a single match for backtesting"""
        # Calculate model predictions (simplified for MVP)
        over_prob, under_prob = self._calculate_model_predictions(match)
        
        # Calculate edges
        over_edge = (over_prob * match.over_2_5_odds) - 1
        under_edge = (under_prob * match.under_2_5_odds) - 1
        
        # Determine if we should bet
        max_edge = max(over_edge, under_edge)
        min_edge = min(over_edge, under_edge)
        
        if max_edge < self.config.min_edge_threshold:
            return  # No bet if edge too low
            
        # Calculate stakes using Kelly Criterion (simplified)
        if over_edge > under_edge:
            stake_over = self._calculate_stake(over_edge, match.over_2_5_odds)
            stake_under = 0
            predicted_over = over_prob
            predicted_under = under_prob
        else:
            stake_over = 0
            stake_under = self._calculate_stake(under_edge, match.under_2_5_odds)
            predicted_over = over_prob
            predicted_under = under_prob
        
        # Calculate results
        actual_goals = getattr(match, 'actual_goals', 0)
        result_over = 1 if actual_goals > 2.5 else 0
        result_under = 1 if actual_goals < 2.5 else 0
        
        # Calculate profit/loss
        profit_loss = 0
        if stake_over > 0:
            profit_loss += (result_over * match.over_2_5_odds - 1) * stake_over
        if stake_under > 0:
            profit_loss += (result_under * match.under_2_5_odds - 1) * stake_under
        
        # Update bankroll
        self.current_bankroll += profit_loss
        self.bankroll_history.append(self.current_bankroll)
        
        # Calculate drawdown
        peak = max(self.bankroll_history)
        drawdown = (peak - self.current_bankroll) / peak
        self.drawdown_history.append(drawdown)
        
        # Store result
        result = BacktestResult(
            match_id=match.match_id,
            home_team=match.home_team,
            away_team=match.away_team,
            league=match.league,
            predicted_over=predicted_over,
            predicted_under=predicted_under,
            bookmaker_over=match.over_2_5_odds,
            bookmaker_under=match.under_2_5_odds,
            edge_over=over_edge,
            edge_under=under_edge,
            stake_over=stake_over,
            stake_under=stake_under,
            actual_goals=actual_goals,
            result_over=result_over,
            result_under=result_under,
            profit_loss=profit_loss,
            confidence=max_edge
        )
        
        self.results.append(result)
        
        # Check stop loss
        if drawdown > self.stop_loss_percentage:
            logger.warning(f"Stop loss triggered at {drawdown:.2%} drawdown")
            return
    
    def _calculate_model_predictions(self, match: FootballMatch) -> Tuple[float, float]:
        """Calculate model predictions for Over/Under 2.5"""
        # Simplified model for MVP - in production this would use the Mojo engine
        
        # Base probabilities (league-specific)
        league_base = {
            "premier-league": 0.52,
            "championship": 0.48,
            "bundesliga": 0.54,
            "serie-a": 0.46,
            "la-liga": 0.50
        }
        
        base_over_prob = league_base.get(match.league, 0.50)
        
        # Add some randomness for realistic simulation
        over_prob = base_over_prob + np.random.normal(0, 0.05)
        over_prob = max(0.1, min(0.9, over_prob))  # Clamp to realistic range
        under_prob = 1 - over_prob
        
        return over_prob, under_prob
    
    def _calculate_stake(self, edge: float, odds: float) -> float:
        """Calculate stake using Kelly Criterion"""
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = win probability, q = loss probability
        
        win_prob = 1 / odds
        kelly_fraction = (odds * win_prob - 1) / (odds - 1)
        
        # Apply conservative Kelly (25% of full Kelly)
        kelly_fraction *= 0.25
        
        # Apply bankroll percentage limit
        max_stake = self.current_bankroll * self.max_stake_percentage
        kelly_stake = self.current_bankroll * kelly_fraction
        
        return min(kelly_stake, max_stake)
    
    def _calculate_summary(self) -> BacktestSummary:
        """Calculate backtest summary statistics"""
        if not self.results:
            return BacktestSummary(0, 0, 0, 0, 0, 0, 0, 0, {})
        
        total_matches = len(self.results)
        profitable_matches = sum(1 for r in self.results if r.profit_loss > 0)
        total_profit = sum(r.profit_loss for r in self.results)
        total_stake = sum(r.stake_over + r.stake_under for r in self.results)
        
        roi_percentage = (total_profit / self.bankroll) * 100 if self.bankroll > 0 else 0
        max_drawdown = max(self.drawdown_history) if self.drawdown_history else 0
        win_rate = profitable_matches / total_matches if total_matches > 0 else 0
        avg_edge = np.mean([max(r.edge_over, r.edge_under) for r in self.results])
        
        # League breakdown
        league_breakdown = {}
        for league in set(r.league for r in self.results):
            league_results = [r for r in self.results if r.league == league]
            league_profit = sum(r.profit_loss for r in league_results)
            league_stake = sum(r.stake_over + r.stake_under for r in league_results)
            league_roi = (league_profit / league_stake * 100) if league_stake > 0 else 0
            
            league_breakdown[league] = {
                "matches": len(league_results),
                "profit": league_profit,
                "roi": league_roi
            }
        
        return BacktestSummary(
            total_matches=total_matches,
            profitable_matches=profitable_matches,
            total_profit=total_profit,
            total_stake=total_stake,
            roi_percentage=roi_percentage,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            avg_edge=avg_edge,
            league_breakdown=league_breakdown
        )
    
    def generate_report(self, summary: BacktestSummary) -> str:
        """Generate detailed backtest report"""
        report = f"""
# Football Over/Under 2.5 Backtest Report

## Summary Statistics
- **Total Matches**: {summary.total_matches}
- **Profitable Matches**: {summary.profitable_matches} ({summary.win_rate:.1%})
- **Total Profit**: £{summary.total_profit:.2f}
- **Total Stake**: £{summary.total_stake:.2f}
- **ROI**: {summary.roi_percentage:.2f}%
- **Max Drawdown**: {summary.max_drawdown:.2%}
- **Average Edge**: {summary.avg_edge:.3f}

## League Breakdown
"""
        
        for league, stats in summary.league_breakdown.items():
            report += f"""
### {league.replace('-', ' ').title()}
- **Matches**: {stats['matches']}
- **Profit**: £{stats['profit']:.2f}
- **ROI**: {stats['roi']:.2f}%
"""
        
        report += f"""
## Risk Management
- **Max Stake**: {self.max_stake_percentage:.1%} of bankroll
- **Stop Loss**: {self.stop_loss_percentage:.1%} drawdown
- **Starting Bankroll**: £{self.bankroll:,.2f}
- **Final Bankroll**: £{self.current_bankroll:,.2f}

## Recommendations
"""
        
        if summary.roi_percentage > 5:
            report += "✅ **Strong Performance**: Continue with current strategy\n"
        elif summary.roi_percentage > 2:
            report += "🟡 **Moderate Performance**: Consider strategy adjustments\n"
        else:
            report += "❌ **Poor Performance**: Strategy needs revision\n"
        
        if summary.max_drawdown > 0.15:
            report += "⚠️ **High Drawdown**: Consider reducing stake sizes\n"
        
        return report


async def main():
    """Run the backtest"""
    config = ProductionConfig()
    backtester = FootballOU25Backtester(config)
    
    logger.info("Starting 2-week football OU 2.5 backtest...")
    summary = await backtester.run_backtest(days=14)
    
    # Generate and save report
    report = backtester.generate_report(summary)
    
    with open("backtest_report.md", "w") as f:
        f.write(report)
    
    print(report)
    logger.info("Backtest completed. Report saved to backtest_report.md")


if __name__ == "__main__":
    asyncio.run(main())
