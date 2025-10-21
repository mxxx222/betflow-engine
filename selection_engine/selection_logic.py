"""
Selection Engine Logic
Implements 70%+ confidence targeting with edge requirements and risk management
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfidenceBucket(Enum):
    """Confidence buckets for selection"""
    BUCKET_70_74 = (0.70, 0.74)
    BUCKET_75_79 = (0.75, 0.79)
    BUCKET_80_PLUS = (0.80, 1.00)


@dataclass
class SelectionCriteria:
    """Selection criteria configuration"""
    min_confidence: float = 0.70
    edge_min_bucket_70_74: float = 0.03  # 3 percentage points
    edge_min_bucket_75_79: float = 0.04  # 4 percentage points
    edge_min_bucket_80_plus: float = 0.05  # 5 percentage points
    clv_min: float = 0.02  # Minimum closing line value
    max_selections_per_round: int = 5
    max_selections_per_profile: int = 3
    kelly_fraction: float = 0.25  # 25% of full Kelly
    max_stake_percentage: float = 0.02  # 2% max stake
    stop_loss_percentage: float = 0.10  # 10% stop loss


@dataclass
class Selection:
    """Individual selection result"""
    match_id: str
    home_team: str
    away_team: str
    league: str
    profile: str
    selection_type: str  # 'over' or 'under'
    confidence: float
    edge: float
    clv: float
    stake_percentage: float
    stake_amount: float
    odds: float
    implied_prob: float
    model_prob: float
    selection_time: datetime
    cutoff_time: datetime
    features: Dict


class SelectionEngine:
    """Main selection engine with 70%+ confidence targeting"""
    
    def __init__(self, criteria: SelectionCriteria = None):
        self.criteria = criteria or SelectionCriteria()
        self.models = None
        self.bankroll = 10000.0
        self.current_bankroll = self.bankroll
        self.selections_history = []
        self.performance_metrics = {}
        
    def load_models(self, models):
        """Load trained models"""
        self.models = models
        logger.info("Models loaded for selection engine")
    
    def select_matches(self, df: pd.DataFrame, profile: str) -> List[Selection]:
        """Select matches for a specific profile"""
        if not self.models:
            logger.error("No models loaded")
            return []
        
        logger.info(f"Selecting matches for {profile}")
        
        # Filter data for profile
        profile_data = df[df[profile] == 1].copy()
        
        if len(profile_data) == 0:
            logger.warning(f"No data found for profile {profile}")
            return []
        
        selections = []
        
        # Process each match
        for _, match in profile_data.iterrows():
            try:
                # Get model predictions
                over_pred = self._get_model_prediction(match, profile, 'over_2_5')
                under_pred = self._get_model_prediction(match, profile, 'under_2_5')
                
                # Check selection criteria
                over_selection = self._evaluate_selection(
                    match, profile, 'over', over_pred, under_pred
                )
                under_selection = self._evaluate_selection(
                    match, profile, 'under', over_pred, under_pred
                )
                
                # Add valid selections
                if over_selection:
                    selections.append(over_selection)
                if under_selection:
                    selections.append(under_selection)
                
            except Exception as e:
                logger.error(f"Error processing match {match.get('match_id', 'unknown')}: {e}")
                continue
        
        # Apply limits and sort by confidence
        selections = self._apply_selection_limits(selections, profile)
        
        logger.info(f"Selected {len(selections)} matches for {profile}")
        return selections
    
    def _get_model_prediction(self, match: pd.Series, profile: str, target: str) -> Dict:
        """Get model prediction for a match"""
        if not self.models:
            return {'over_prob': 0.5, 'under_prob': 0.5}
        
        model_key = f"{profile}_{target}"
        
        if model_key not in self.models:
            logger.warning(f"No model found for {model_key}")
            return {'over_prob': 0.5, 'under_prob': 0.5}
        
        # Prepare features for prediction
        features = self._prepare_features(match)
        
        # Get ensemble prediction
        models = self.models[model_key]
        predictions = []
        
        for model_name, model in models.items():
            try:
                prob = model.predict_proba([features])[0][1]
                predictions.append(prob)
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
                continue
        
        if predictions:
            ensemble_prob = np.mean(predictions)
        else:
            ensemble_prob = 0.5
        
        # Return probabilities
        if target == 'over_2_5':
            return {
                'over_prob': ensemble_prob,
                'under_prob': 1 - ensemble_prob
            }
        else:
            return {
                'over_prob': 1 - ensemble_prob,
                'under_prob': ensemble_prob
            }
    
    def _prepare_features(self, match: pd.Series) -> List[float]:
        """Prepare features for model prediction"""
        # Core features that should be available
        features = []
        
        # Team stats
        features.extend([
            match.get('home_xg', 0),
            match.get('away_xg', 0),
            match.get('home_xga', 0),
            match.get('away_xga', 0),
            match.get('home_strength', 0),
            match.get('away_strength', 0),
            match.get('strength_diff', 0)
        ])
        
        # Form
        features.extend([
            match.get('home_form_5', 0.5),
            match.get('away_form_5', 0.5),
            match.get('home_form_10', 0.5),
            match.get('away_form_10', 0.5),
            match.get('form_diff_5', 0),
            match.get('form_diff_10', 0)
        ])
        
        # Context
        features.extend([
            match.get('home_rest_days', 7),
            match.get('away_rest_days', 7),
            match.get('rest_advantage', 0),
            match.get('home_travel_distance', 0),
            match.get('away_travel_distance', 0)
        ])
        
        # Market
        features.extend([
            match.get('market_drift_24h', 0),
            match.get('market_drift_1h', 0),
            match.get('implied_over_prob', 0.5),
            match.get('implied_under_prob', 0.5)
        ])
        
        # Fill any NaN values
        features = [f if not pd.isna(f) else 0 for f in features]
        
        return features
    
    def _evaluate_selection(self, match: pd.Series, profile: str, 
                          selection_type: str, over_pred: Dict, under_pred: Dict) -> Optional[Selection]:
        """Evaluate if a match meets selection criteria"""
        
        # Get relevant prediction
        if selection_type == 'over':
            model_prob = over_pred['over_prob']
            implied_prob = match.get('implied_over_prob', 0.5)
            odds = match.get('opening_over_odds', 2.0)
        else:
            model_prob = under_pred['under_prob']
            implied_prob = match.get('implied_under_prob', 0.5)
            odds = match.get('opening_under_odds', 2.0)
        
        # Calculate confidence and edge
        confidence = model_prob
        edge = model_prob - implied_prob
        
        # Check confidence threshold
        if confidence < self.criteria.min_confidence:
            return None
        
        # Check edge requirements by confidence bucket
        edge_required = self._get_required_edge(confidence)
        if edge < edge_required:
            return None
        
        # Calculate CLV (Closing Line Value)
        closing_odds = match.get('closing_over_odds' if selection_type == 'over' else 'closing_under_odds', odds)
        clv = (1 / closing_odds) - (1 / odds)
        
        if clv < self.criteria.clv_min:
            return None
        
        # Calculate stake using Kelly Criterion
        stake_percentage = self._calculate_kelly_stake(model_prob, odds)
        stake_amount = self.current_bankroll * stake_percentage
        
        # Check stake limits
        if stake_amount > self.current_bankroll * self.criteria.max_stake_percentage:
            stake_amount = self.current_bankroll * self.criteria.max_stake_percentage
            stake_percentage = self.criteria.max_stake_percentage
        
        # Create selection
        selection = Selection(
            match_id=match.get('match_id', 'unknown'),
            home_team=match.get('home_team', ''),
            away_team=match.get('away_team', ''),
            league=match.get('league', ''),
            profile=profile,
            selection_type=selection_type,
            confidence=confidence,
            edge=edge,
            clv=clv,
            stake_percentage=stake_percentage,
            stake_amount=stake_amount,
            odds=odds,
            implied_prob=implied_prob,
            model_prob=model_prob,
            selection_time=datetime.now(),
            cutoff_time=datetime.now() + timedelta(hours=1),  # 1 hour before match
            features=self._extract_key_features(match)
        )
        
        return selection
    
    def _get_required_edge(self, confidence: float) -> float:
        """Get required edge based on confidence bucket"""
        if confidence >= 0.80:
            return self.criteria.edge_min_bucket_80_plus
        elif confidence >= 0.75:
            return self.criteria.edge_min_bucket_75_79
        else:
            return self.criteria.edge_min_bucket_70_74
    
    def _calculate_kelly_stake(self, model_prob: float, odds: float) -> float:
        """Calculate stake using Kelly Criterion"""
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = win probability, q = loss probability
        
        win_prob = model_prob
        loss_prob = 1 - win_prob
        b = odds - 1
        
        if b <= 0:
            return 0
        
        kelly_fraction = (b * win_prob - loss_prob) / b
        
        # Apply conservative Kelly (25% of full Kelly)
        kelly_fraction *= self.criteria.kelly_fraction
        
        # Ensure non-negative
        return max(0, kelly_fraction)
    
    def _extract_key_features(self, match: pd.Series) -> Dict:
        """Extract key features for analysis"""
        return {
            'home_strength': match.get('home_strength', 0),
            'away_strength': match.get('away_strength', 0),
            'form_diff_5': match.get('form_diff_5', 0),
            'rest_advantage': match.get('rest_advantage', 0),
            'market_drift_24h': match.get('market_drift_24h', 0),
            'lineup_confirmed': match.get('lineup_confirmed', False),
            'weather_impact': match.get('weather_impact', 0)
        }
    
    def _apply_selection_limits(self, selections: List[Selection], profile: str) -> List[Selection]:
        """Apply selection limits and sort by confidence"""
        # Sort by confidence (descending)
        selections.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply profile limit
        profile_selections = [s for s in selections if s.profile == profile]
        if len(profile_selections) > self.criteria.max_selections_per_profile:
            profile_selections = profile_selections[:self.criteria.max_selections_per_profile]
        
        # Apply total limit
        if len(selections) > self.criteria.max_selections_per_round:
            selections = selections[:self.criteria.max_selections_per_round]
        
        return selections
    
    def update_performance(self, results: Dict[str, bool]):
        """Update performance metrics with results"""
        for selection in self.selections_history:
            if selection.match_id in results:
                # Update bankroll based on result
                if results[selection.match_id]:
                    # Win
                    profit = selection.stake_amount * (selection.odds - 1)
                    self.current_bankroll += profit
                else:
                    # Loss
                    self.current_bankroll -= selection.stake_amount
                
                # Check stop loss
                drawdown = (self.bankroll - self.current_bankroll) / self.bankroll
                if drawdown > self.criteria.stop_loss_percentage:
                    logger.warning(f"Stop loss triggered: {drawdown:.2%} drawdown")
                    break
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        if not self.selections_history:
            return {}
        
        total_selections = len(self.selections_history)
        total_stake = sum(s.stake_amount for s in self.selections_history)
        
        # Calculate ROI
        roi = (self.current_bankroll - self.bankroll) / self.bankroll
        
        # Calculate drawdown
        peak_bankroll = max(self.bankroll, self.current_bankroll)
        drawdown = (peak_bankroll - self.current_bankroll) / peak_bankroll
        
        return {
            'total_selections': total_selections,
            'total_stake': total_stake,
            'current_bankroll': self.current_bankroll,
            'roi': roi,
            'drawdown': drawdown,
            'avg_confidence': np.mean([s.confidence for s in self.selections_history]),
            'avg_edge': np.mean([s.edge for s in self.selections_history]),
            'avg_clv': np.mean([s.clv for s in self.selections_history])
        }


def main():
    """Test selection engine"""
    # Load sample data
    df = pd.read_csv('selection_engine/dataset.csv')
    
    # Initialize selection engine
    criteria = SelectionCriteria()
    engine = SelectionEngine(criteria)
    
    # Load models (would be loaded from file in production)
    # engine.load_models(models)
    
    # Test selection for both profiles
    profile_a_selections = engine.select_matches(df, 'profile_a')
    profile_b_selections = engine.select_matches(df, 'profile_b')
    
    print(f"\n📊 Selection Results:")
    print(f"Profile A (Weekend Top-5): {len(profile_a_selections)} selections")
    print(f"Profile B (UCL): {len(profile_b_selections)} selections")
    
    # Print selection details
    for selection in profile_a_selections[:3]:  # Show first 3
        print(f"\n{selection.home_team} vs {selection.away_team}")
        print(f"  {selection.selection_type.upper()} - Confidence: {selection.confidence:.3f}")
        print(f"  Edge: {selection.edge:.3f}, CLV: {selection.clv:.3f}")
        print(f"  Stake: {selection.stake_percentage:.1%} (${selection.stake_amount:.2f})")


if __name__ == "__main__":
    main()
