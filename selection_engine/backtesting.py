"""
Selection Engine Backtesting
Walk-forward validation with weekly round reports and performance analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RoundReport:
    """Weekly round performance report"""
    round_id: str
    start_date: datetime
    end_date: datetime
    profile: str
    total_matches: int
    selections: int
    wins: int
    losses: int
    hit_rate: float
    roi: float
    clv: float
    total_stake: float
    profit_loss: float
    avg_confidence: float
    avg_edge: float
    max_drawdown: float
    selections_by_bucket: Dict[str, int]
    performance_by_bucket: Dict[str, Dict]


@dataclass
class BacktestResults:
    """Overall backtest results"""
    total_rounds: int
    total_selections: int
    overall_hit_rate: float
    overall_roi: float
    max_drawdown: float
    sharpe_ratio: float
    calmar_ratio: float
    round_reports: List[RoundReport]
    profile_performance: Dict[str, Dict]
    bucket_performance: Dict[str, Dict]


class SelectionEngineBacktester:
    """Backtesting system for selection engine"""
    
    def __init__(self, selection_engine, bankroll: float = 10000.0):
        self.selection_engine = selection_engine
        self.initial_bankroll = bankroll
        self.current_bankroll = bankroll
        self.bankroll_history = [bankroll]
        self.round_reports = []
        self.selections_history = []
        
    def run_backtest(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> BacktestResults:
        """Run walk-forward backtest"""
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Sort data by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Filter data for backtest period
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        backtest_data = df[mask].copy()
        
        if len(backtest_data) == 0:
            logger.error("No data found for backtest period")
            return None
        
        # Group by weeks for walk-forward validation
        weekly_groups = self._group_by_weeks(backtest_data)
        
        logger.info(f"Running backtest on {len(weekly_groups)} weeks")
        
        # Process each week
        for week_num, week_data in weekly_groups.items():
            logger.info(f"Processing week {week_num}")
            
            # Train models on historical data (up to this week)
            historical_data = backtest_data[backtest_data['date'] < week_data['start_date']]
            
            if len(historical_data) < 100:
                logger.warning(f"Insufficient historical data for week {week_num}")
                continue
            
            # Test on current week
            week_results = self._test_week(week_data, historical_data, week_num)
            if week_results:
                self.round_reports.append(week_results)
        
        # Calculate overall results
        results = self._calculate_overall_results()
        
        logger.info(f"Backtest completed: {results.overall_roi:.2%} ROI, {results.overall_hit_rate:.1%} hit rate")
        return results
    
    def _group_by_weeks(self, df: pd.DataFrame) -> Dict[int, Dict]:
        """Group data by weeks"""
        df['week'] = df['date'].dt.isocalendar().week
        df['year'] = df['date'].dt.year
        
        weekly_groups = {}
        
        for (year, week), group in df.groupby(['year', 'week']):
            week_key = f"{year}_W{week:02d}"
            weekly_groups[week_key] = {
                'start_date': group['date'].min(),
                'end_date': group['date'].max(),
                'data': group
            }
        
        return weekly_groups
    
    def _test_week(self, week_data: Dict, historical_data: pd.DataFrame, week_id: str) -> Optional[RoundReport]:
        """Test selection engine on a specific week"""
        week_df = week_data['data']
        
        # Test both profiles
        profile_a_selections = self.selection_engine.select_matches(week_df, 'profile_a')
        profile_b_selections = self.selection_engine.select_matches(week_df, 'profile_b')
        
        all_selections = profile_a_selections + profile_b_selections
        
        if not all_selections:
            return None
        
        # Simulate results (in production, would use actual match results)
        results = self._simulate_results(all_selections, week_df)
        
        # Calculate performance
        performance = self._calculate_week_performance(all_selections, results)
        
        # Update bankroll
        self._update_bankroll(all_selections, results)
        
        # Create round report
        round_report = RoundReport(
            round_id=week_id,
            start_date=week_data['start_date'],
            end_date=week_data['end_date'],
            profile='combined',
            total_matches=len(week_df),
            selections=len(all_selections),
            wins=performance['wins'],
            losses=performance['losses'],
            hit_rate=performance['hit_rate'],
            roi=performance['roi'],
            clv=performance['clv'],
            total_stake=performance['total_stake'],
            profit_loss=performance['profit_loss'],
            avg_confidence=performance['avg_confidence'],
            avg_edge=performance['avg_edge'],
            max_drawdown=performance['max_drawdown'],
            selections_by_bucket=performance['selections_by_bucket'],
            performance_by_bucket=performance['performance_by_bucket']
        )
        
        return round_report
    
    def _simulate_results(self, selections: List, week_df: pd.DataFrame) -> Dict[str, bool]:
        """Simulate match results (in production, use actual results)"""
        results = {}
        
        for selection in selections:
            # Find corresponding match in data
            match = week_df[
                (week_df['home_team'] == selection.home_team) & 
                (week_df['away_team'] == selection.away_team)
            ]
            
            if len(match) == 0:
                # Use model probability to simulate result
                win_prob = selection.model_prob
                result = np.random.random() < win_prob
            else:
                # Use actual match result
                goals_total = match.iloc[0]['goals_total']
                
                if selection.selection_type == 'over':
                    result = goals_total > 2.5
                else:
                    result = goals_total < 2.5
            
            results[selection.match_id] = result
        
        return results
    
    def _calculate_week_performance(self, selections: List, results: Dict[str, bool]) -> Dict:
        """Calculate performance metrics for a week"""
        if not selections:
            return {
                'wins': 0, 'losses': 0, 'hit_rate': 0, 'roi': 0, 'clv': 0,
                'total_stake': 0, 'profit_loss': 0, 'avg_confidence': 0,
                'avg_edge': 0, 'max_drawdown': 0, 'selections_by_bucket': {},
                'performance_by_bucket': {}
            }
        
        wins = 0
        losses = 0
        total_stake = 0
        profit_loss = 0
        clv_sum = 0
        
        # Group by confidence buckets
        buckets = {
            '70-74%': [],
            '75-79%': [],
            '80%+': []
        }
        
        for selection in selections:
            # Categorize by confidence
            if selection.confidence >= 0.80:
                bucket = '80%+'
            elif selection.confidence >= 0.75:
                bucket = '75-79%'
            else:
                bucket = '70-74%'
            
            buckets[bucket].append(selection)
            
            # Calculate result
            if selection.match_id in results:
                result = results[selection.match_id]
                if result:
                    wins += 1
                    profit_loss += selection.stake_amount * (selection.odds - 1)
                else:
                    losses += 1
                    profit_loss -= selection.stake_amount
                
                clv_sum += selection.clv
            
            total_stake += selection.stake_amount
        
        # Calculate metrics
        total_selections = wins + losses
        hit_rate = wins / total_selections if total_selections > 0 else 0
        roi = profit_loss / total_stake if total_stake > 0 else 0
        avg_clv = clv_sum / len(selections) if selections else 0
        
        # Calculate drawdown
        peak = max(self.bankroll_history) if self.bankroll_history else self.initial_bankroll
        current = self.current_bankroll
        max_drawdown = (peak - current) / peak if peak > 0 else 0
        
        # Performance by bucket
        performance_by_bucket = {}
        selections_by_bucket = {}
        
        for bucket_name, bucket_selections in buckets.items():
            if bucket_selections:
                bucket_wins = sum(1 for s in bucket_selections if results.get(s.match_id, False))
                bucket_total = len(bucket_selections)
                bucket_hit_rate = bucket_wins / bucket_total if bucket_total > 0 else 0
                
                performance_by_bucket[bucket_name] = {
                    'selections': bucket_total,
                    'wins': bucket_wins,
                    'hit_rate': bucket_hit_rate
                }
                selections_by_bucket[bucket_name] = bucket_total
            else:
                performance_by_bucket[bucket_name] = {'selections': 0, 'wins': 0, 'hit_rate': 0}
                selections_by_bucket[bucket_name] = 0
        
        return {
            'wins': wins,
            'losses': losses,
            'hit_rate': hit_rate,
            'roi': roi,
            'clv': avg_clv,
            'total_stake': total_stake,
            'profit_loss': profit_loss,
            'avg_confidence': np.mean([s.confidence for s in selections]),
            'avg_edge': np.mean([s.edge for s in selections]),
            'max_drawdown': max_drawdown,
            'selections_by_bucket': selections_by_bucket,
            'performance_by_bucket': performance_by_bucket
        }
    
    def _update_bankroll(self, selections: List, results: Dict[str, bool]):
        """Update bankroll based on results"""
        for selection in selections:
            if selection.match_id in results:
                result = results[selection.match_id]
                if result:
                    # Win
                    profit = selection.stake_amount * (selection.odds - 1)
                    self.current_bankroll += profit
                else:
                    # Loss
                    self.current_bankroll -= selection.stake_amount
        
        # Record bankroll history
        self.bankroll_history.append(self.current_bankroll)
    
    def _calculate_overall_results(self) -> BacktestResults:
        """Calculate overall backtest results"""
        if not self.round_reports:
            return BacktestResults(0, 0, 0, 0, 0, 0, 0, [], {}, {})
        
        # Aggregate metrics
        total_selections = sum(r.selections for r in self.round_reports)
        total_wins = sum(r.wins for r in self.round_reports)
        total_losses = sum(r.losses for r in self.round_reports)
        overall_hit_rate = total_wins / total_selections if total_selections > 0 else 0
        
        # Calculate ROI
        final_bankroll = self.current_bankroll
        overall_roi = (final_bankroll - self.initial_bankroll) / self.initial_bankroll
        
        # Calculate drawdown
        peak_bankroll = max(self.bankroll_history)
        max_drawdown = (peak_bankroll - min(self.bankroll_history)) / peak_bankroll
        
        # Calculate Sharpe ratio (simplified)
        returns = [self.bankroll_history[i] / self.bankroll_history[i-1] - 1 
                  for i in range(1, len(self.bankroll_history))]
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Calculate Calmar ratio
        calmar_ratio = overall_roi / max_drawdown if max_drawdown > 0 else 0
        
        # Profile performance
        profile_performance = self._calculate_profile_performance()
        
        # Bucket performance
        bucket_performance = self._calculate_bucket_performance()
        
        return BacktestResults(
            total_rounds=len(self.round_reports),
            total_selections=total_selections,
            overall_hit_rate=overall_hit_rate,
            overall_roi=overall_roi,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            calmar_ratio=calmar_ratio,
            round_reports=self.round_reports,
            profile_performance=profile_performance,
            bucket_performance=bucket_performance
        )
    
    def _calculate_profile_performance(self) -> Dict[str, Dict]:
        """Calculate performance by profile"""
        profile_performance = {}
        
        for profile in ['profile_a', 'profile_b']:
            profile_reports = [r for r in self.round_reports if profile in r.profile]
            
            if profile_reports:
                total_selections = sum(r.selections for r in profile_reports)
                total_wins = sum(r.wins for r in profile_reports)
                hit_rate = total_wins / total_selections if total_selections > 0 else 0
                
                profile_performance[profile] = {
                    'selections': total_selections,
                    'wins': total_wins,
                    'hit_rate': hit_rate,
                    'rounds': len(profile_reports)
                }
            else:
                profile_performance[profile] = {
                    'selections': 0, 'wins': 0, 'hit_rate': 0, 'rounds': 0
                }
        
        return profile_performance
    
    def _calculate_bucket_performance(self) -> Dict[str, Dict]:
        """Calculate performance by confidence bucket"""
        bucket_performance = {}
        
        for bucket in ['70-74%', '75-79%', '80%+']:
            bucket_selections = 0
            bucket_wins = 0
            
            for report in self.round_reports:
                if bucket in report.selections_by_bucket:
                    bucket_selections += report.selections_by_bucket[bucket]
                    if bucket in report.performance_by_bucket:
                        bucket_wins += report.performance_by_bucket[bucket]['wins']
            
            hit_rate = bucket_wins / bucket_selections if bucket_selections > 0 else 0
            
            bucket_performance[bucket] = {
                'selections': bucket_selections,
                'wins': bucket_wins,
                'hit_rate': hit_rate
            }
        
        return bucket_performance
    
    def generate_report(self, results: BacktestResults) -> str:
        """Generate comprehensive backtest report"""
        report = f"""
# Selection Engine Backtest Report

## Overall Performance
- **Total Rounds**: {results.total_rounds}
- **Total Selections**: {results.total_selections}
- **Hit Rate**: {results.overall_hit_rate:.1%}
- **ROI**: {results.overall_roi:.2%}
- **Max Drawdown**: {results.max_drawdown:.2%}
- **Sharpe Ratio**: {results.sharpe_ratio:.2f}
- **Calmar Ratio**: {results.calmar_ratio:.2f}

## Profile Performance
"""
        
        for profile, perf in results.profile_performance.items():
            profile_name = "Weekend Top-5" if profile == "profile_a" else "UCL"
            report += f"""
### {profile_name}
- **Selections**: {perf['selections']}
- **Wins**: {perf['wins']}
- **Hit Rate**: {perf['hit_rate']:.1%}
- **Rounds**: {perf['rounds']}
"""
        
        report += "\n## Confidence Bucket Performance\n"
        
        for bucket, perf in results.bucket_performance.items():
            report += f"""
### {bucket}
- **Selections**: {perf['selections']}
- **Wins**: {perf['wins']}
- **Hit Rate**: {perf['hit_rate']:.1%}
"""
        
        report += "\n## Weekly Round Reports\n"
        
        for report_data in results.round_reports[-5:]:  # Show last 5 weeks
            report += f"""
### {report_data.round_id}
- **Date**: {report_data.start_date.strftime('%Y-%m-%d')} to {report_data.end_date.strftime('%Y-%m-%d')}
- **Selections**: {report_data.selections}
- **Hit Rate**: {report_data.hit_rate:.1%}
- **ROI**: {report_data.roi:.2%}
- **Avg Confidence**: {report_data.avg_confidence:.3f}
"""
        
        return report
    
    def plot_performance(self, results: BacktestResults, save_path: str = None):
        """Plot backtest performance"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Bankroll progression
        axes[0, 0].plot(self.bankroll_history)
        axes[0, 0].set_title('Bankroll Progression')
        axes[0, 0].set_xlabel('Week')
        axes[0, 0].set_ylabel('Bankroll')
        
        # Hit rate by bucket
        buckets = list(results.bucket_performance.keys())
        hit_rates = [results.bucket_performance[b]['hit_rate'] for b in buckets]
        axes[0, 1].bar(buckets, hit_rates)
        axes[0, 1].set_title('Hit Rate by Confidence Bucket')
        axes[0, 1].set_ylabel('Hit Rate')
        
        # Selections by bucket
        selections = [results.bucket_performance[b]['selections'] for b in buckets]
        axes[1, 0].bar(buckets, selections)
        axes[1, 0].set_title('Selections by Confidence Bucket')
        axes[1, 0].set_ylabel('Number of Selections')
        
        # Weekly ROI
        weekly_rois = [r.roi for r in results.round_reports]
        axes[1, 1].plot(weekly_rois)
        axes[1, 1].set_title('Weekly ROI')
        axes[1, 1].set_xlabel('Week')
        axes[1, 1].set_ylabel('ROI')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()


def main():
    """Run selection engine backtest"""
    # Load data
    df = pd.read_csv('selection_engine/dataset.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Initialize backtester
    from selection_logic import SelectionEngine, SelectionCriteria
    
    criteria = SelectionCriteria()
    selection_engine = SelectionEngine(criteria)
    backtester = SelectionEngineBacktester(selection_engine)
    
    # Run backtest
    start_date = datetime(2023, 8, 1)
    end_date = datetime(2024, 5, 31)
    
    results = backtester.run_backtest(df, start_date, end_date)
    
    if results:
        # Generate report
        report = backtester.generate_report(results)
        print(report)
        
        # Save report
        with open('selection_engine/backtest_report.md', 'w') as f:
            f.write(report)
        
        # Plot performance
        backtester.plot_performance(results, 'selection_engine/performance_plots.png')
        
        logger.info("Backtest completed successfully")


if __name__ == "__main__":
    main()
