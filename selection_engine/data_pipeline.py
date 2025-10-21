"""
Selection Engine Data Pipeline
Builds comprehensive dataset for OU 2.5 selection with 70%+ hit rate targeting
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import asyncio
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MatchData:
    """Match data structure for selection engine"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    season: str
    date: datetime
    is_weekend: bool
    is_ucl: bool
    is_top5: bool
    
    # Labels
    goals_total: int
    over_2_5: bool
    under_2_5: bool
    
    # Features
    home_xg: float
    away_xg: float
    home_xga: float
    away_xga: float
    home_form_5: float
    away_form_5: float
    home_form_10: float
    away_form_10: float
    home_rest_days: int
    away_rest_days: int
    home_travel_distance: float
    away_travel_distance: float
    home_injuries: int
    away_injuries: int
    home_suspensions: int
    away_suspensions: int
    home_pace: float
    away_pace: float
    referee: str
    weather_temp: float
    weather_condition: str
    lineup_confirmed: bool
    market_drift_24h: float
    market_drift_1h: float
    
    # Market data
    opening_over_odds: float
    opening_under_odds: float
    closing_over_odds: float
    closing_under_odds: float
    implied_over_prob: float
    implied_under_prob: float
    vig_corrected_over_prob: float
    vig_corrected_under_prob: float


class SelectionEngineDataPipeline:
    """Data pipeline for OU 2.5 selection engine"""
    
    def __init__(self):
        self.seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
        self.top5_leagues = ["premier-league", "la-liga", "bundesliga", "serie-a", "ligue-1"]
        self.ucl_phases = ["group-stage", "round-of-16", "quarter-final", "semi-final", "final"]
        
    async def build_dataset(self) -> pd.DataFrame:
        """Build comprehensive dataset for selection engine"""
        logger.info("Building selection engine dataset...")
        
        all_matches = []
        
        # Collect data for each season
        for season in self.seasons:
            logger.info(f"Processing season {season}")
            
            # Top 5 leagues
            for league in self.top5_leagues:
                matches = await self._collect_league_data(league, season)
                all_matches.extend(matches)
            
            # UCL data
            ucl_matches = await self._collect_ucl_data(season)
            all_matches.extend(ucl_matches)
        
        # Convert to DataFrame
        df = pd.DataFrame([match.__dict__ for match in all_matches])
        
        # Add derived features
        df = self._add_derived_features(df)
        
        # Add profile tags
        df = self._add_profile_tags(df)
        
        logger.info(f"Dataset built: {len(df)} matches")
        return df
    
    async def _collect_league_data(self, league: str, season: str) -> List[MatchData]:
        """Collect data for a specific league and season"""
        matches = []
        
        # Simulate realistic data collection
        # In production, this would fetch from multiple APIs
        
        # Generate matches for the season
        num_matches = np.random.randint(300, 400)  # Typical league size
        
        for i in range(num_matches):
            # Generate realistic match data
            match = await self._generate_match_data(league, season, is_ucl=False)
            matches.append(match)
        
        return matches
    
    async def _collect_ucl_data(self, season: str) -> List[MatchData]:
        """Collect UCL data for a season"""
        matches = []
        
        # UCL has fewer matches but higher quality
        num_matches = np.random.randint(100, 150)
        
        for i in range(num_matches):
            match = await self._generate_match_data("ucl", season, is_ucl=True)
            matches.append(match)
        
        return matches
    
    async def _generate_match_data(self, league: str, season: str, is_ucl: bool) -> MatchData:
        """Generate realistic match data"""
        # Generate realistic date
        if season == "2024-25":
            base_date = datetime(2024, 8, 1)
        else:
            year = int(season.split("-")[0])
            base_date = datetime(year, 8, 1)
        
        match_date = base_date + timedelta(days=np.random.randint(0, 300))
        
        # Generate team names
        home_team = f"Team_{np.random.randint(1, 21)}"
        away_team = f"Team_{np.random.randint(1, 21)}"
        
        # Generate goals (realistic distribution)
        goals_total = self._generate_goals(league, is_ucl)
        
        # Generate features
        features = self._generate_features(league, is_ucl)
        
        # Generate market data
        market_data = self._generate_market_data(goals_total)
        
        return MatchData(
            match_id=f"{league}_{season}_{np.random.randint(1000, 9999)}",
            home_team=home_team,
            away_team=away_team,
            league=league,
            season=season,
            date=match_date,
            is_weekend=match_date.weekday() >= 5,
            is_ucl=is_ucl,
            is_top5=league in self.top5_leagues,
            goals_total=goals_total,
            over_2_5=goals_total > 2.5,
            under_2_5=goals_total < 2.5,
            **features,
            **market_data
        )
    
    def _generate_goals(self, league: str, is_ucl: bool) -> int:
        """Generate realistic goal totals"""
        if is_ucl:
            # UCL tends to have more goals
            mean_goals = 2.8
            std_goals = 1.2
        elif league == "premier-league":
            mean_goals = 2.7
            std_goals = 1.1
        elif league == "bundesliga":
            mean_goals = 2.9
            std_goals = 1.0
        elif league == "serie-a":
            mean_goals = 2.4
            std_goals = 1.0
        elif league == "la-liga":
            mean_goals = 2.6
            std_goals = 1.1
        else:
            mean_goals = 2.5
            std_goals = 1.2
        
        goals = max(0, int(np.random.normal(mean_goals, std_goals)))
        return min(goals, 8)  # Cap at 8 goals
    
    def _generate_features(self, league: str, is_ucl: bool) -> Dict:
        """Generate realistic features"""
        return {
            "home_xg": np.random.uniform(0.8, 2.5),
            "away_xg": np.random.uniform(0.8, 2.5),
            "home_xga": np.random.uniform(0.8, 2.2),
            "away_xga": np.random.uniform(0.8, 2.2),
            "home_form_5": np.random.uniform(0.2, 1.0),
            "away_form_5": np.random.uniform(0.2, 1.0),
            "home_form_10": np.random.uniform(0.3, 0.9),
            "away_form_10": np.random.uniform(0.3, 0.9),
            "home_rest_days": np.random.randint(3, 14),
            "away_rest_days": np.random.randint(3, 14),
            "home_travel_distance": np.random.uniform(0, 2000),
            "away_travel_distance": np.random.uniform(0, 2000),
            "home_injuries": np.random.randint(0, 5),
            "away_injuries": np.random.randint(0, 5),
            "home_suspensions": np.random.randint(0, 3),
            "away_suspensions": np.random.randint(0, 3),
            "home_pace": np.random.uniform(0.8, 1.5),
            "away_pace": np.random.uniform(0.8, 1.5),
            "referee": f"Referee_{np.random.randint(1, 20)}",
            "weather_temp": np.random.uniform(-5, 35),
            "weather_condition": np.random.choice(["sunny", "cloudy", "rainy", "snowy"]),
            "lineup_confirmed": np.random.choice([True, False], p=[0.8, 0.2]),
            "market_drift_24h": np.random.uniform(-0.1, 0.1),
            "market_drift_1h": np.random.uniform(-0.05, 0.05)
        }
    
    def _generate_market_data(self, goals_total: int) -> Dict:
        """Generate realistic market data"""
        # Base odds
        base_over_odds = np.random.uniform(1.8, 2.2)
        base_under_odds = np.random.uniform(1.8, 2.2)
        
        # Add some market movement
        opening_over_odds = base_over_odds + np.random.uniform(-0.1, 0.1)
        opening_under_odds = base_under_odds + np.random.uniform(-0.1, 0.1)
        closing_over_odds = base_over_odds + np.random.uniform(-0.2, 0.2)
        closing_under_odds = base_under_odds + np.random.uniform(-0.2, 0.2)
        
        # Calculate implied probabilities
        implied_over_prob = 1 / opening_over_odds
        implied_under_prob = 1 / opening_under_odds
        
        # Vig correction
        total_prob = implied_over_prob + implied_under_prob
        vig_corrected_over_prob = implied_over_prob / total_prob
        vig_corrected_under_prob = implied_under_prob / total_prob
        
        return {
            "opening_over_odds": opening_over_odds,
            "opening_under_odds": opening_under_odds,
            "closing_over_odds": closing_over_odds,
            "closing_under_odds": closing_under_odds,
            "implied_over_prob": implied_over_prob,
            "implied_under_prob": implied_under_prob,
            "vig_corrected_over_prob": vig_corrected_over_prob,
            "vig_corrected_under_prob": vig_corrected_under_prob
        }
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features to the dataset"""
        # Team strength features
        df['home_strength'] = df['home_xg'] - df['home_xga']
        df['away_strength'] = df['away_xg'] - df['away_xga']
        df['strength_diff'] = df['home_strength'] - df['away_strength']
        
        # Form features
        df['form_diff_5'] = df['home_form_5'] - df['away_form_5']
        df['form_diff_10'] = df['home_form_10'] - df['away_form_10']
        
        # Rest advantage
        df['rest_advantage'] = df['home_rest_days'] - df['away_rest_days']
        
        # Squad issues
        df['home_squad_issues'] = df['home_injuries'] + df['home_suspensions']
        df['away_squad_issues'] = df['away_injuries'] + df['away_suspensions']
        df['squad_issues_diff'] = df['home_squad_issues'] - df['away_squad_issues']
        
        # Pace features
        df['pace_diff'] = df['home_pace'] - df['away_pace']
        df['total_pace'] = df['home_pace'] + df['away_pace']
        
        # Market features
        df['market_drift_total'] = df['market_drift_24h'] + df['market_drift_1h']
        df['odds_volatility'] = abs(df['market_drift_24h']) + abs(df['market_drift_1h'])
        
        # Weather impact
        df['weather_impact'] = np.where(
            df['weather_condition'].isin(['rainy', 'snowy']), 1, 0
        )
        
        return df
    
    def _add_profile_tags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add profile tags for segmentation"""
        # Profile A: Weekend top-5 leagues
        df['profile_a'] = (df['is_weekend'] & df['is_top5']).astype(int)
        
        # Profile B: UCL
        df['profile_b'] = df['is_ucl'].astype(int)
        
        # Weekend round tag
        df['weekend_round'] = df['is_weekend'].astype(int)
        
        # UCL tag
        df['ucl_tag'] = df['is_ucl'].astype(int)
        
        # Top 5 leagues tag
        df['top5_leagues'] = df['is_top5'].astype(int)
        
        return df


async def main():
    """Build the selection engine dataset"""
    pipeline = SelectionEngineDataPipeline()
    df = await pipeline.build_dataset()
    
    # Save dataset
    df.to_csv('selection_engine/dataset.csv', index=False)
    logger.info(f"Dataset saved with {len(df)} matches")
    
    # Print summary
    print("\n📊 Dataset Summary:")
    print(f"Total matches: {len(df)}")
    print(f"Over 2.5 rate: {df['over_2_5'].mean():.3f}")
    print(f"Profile A (weekend top-5): {df['profile_a'].sum()}")
    print(f"Profile B (UCL): {df['profile_b'].sum()}")
    print(f"Average goals: {df['goals_total'].mean():.2f}")
    
    return df


if __name__ == "__main__":
    asyncio.run(main())
