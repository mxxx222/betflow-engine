"""
Automatic Model Calibration System
Continuous calibration and result validation for high ROI targeting
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import asyncio
import joblib
import json
from pathlib import Path
from sklearn.calibration import CalibratedClassifierCV, PlattScaling, IsotonicRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CalibrationConfig:
    """Configuration for automatic calibration"""
    recalibration_frequency: int = 7  # Days between recalibration
    min_samples_for_calibration: int = 100  # Minimum samples needed
    calibration_methods: List[str] = None  # Methods to try
    target_reliability: float = 0.95  # Target reliability score
    drift_threshold: float = 0.05  # Drift detection threshold
    performance_threshold: float = 0.70  # Minimum performance threshold
    
    def __post_init__(self):
        if self.calibration_methods is None:
            self.calibration_methods = ['platt', 'isotonic', 'sigmoid']


@dataclass
class CalibrationResult:
    """Result of calibration process"""
    method: str
    reliability_score: float
    brier_score: float
    log_loss: float
    calibration_curve: Dict
    performance_metrics: Dict
    drift_detected: bool
    recalibration_needed: bool


class AutoCalibrationSystem:
    """Automatic model calibration and validation system"""
    
    def __init__(self, config: CalibrationConfig = None):
        self.config = config or CalibrationConfig()
        self.calibration_history = []
        self.current_calibration = None
        self.performance_tracker = []
        self.drift_detector = None
        
    async def calibrate_model(self, model, X: pd.DataFrame, y: pd.Series, 
                            method: str = None) -> CalibrationResult:
        """Calibrate model for optimal performance"""
        logger.info(f"📊 Calibrating model with method: {method or 'auto'}")
        
        # Determine best calibration method
        if method is None:
            method = await self._select_best_calibration_method(model, X, y)
        
        # Apply calibration
        calibrated_model = self._apply_calibration(model, method)
        calibrated_model.fit(X, y)
        
        # Evaluate calibration
        reliability_score = self._calculate_reliability_score(calibrated_model, X, y)
        brier_score = self._calculate_brier_score(calibrated_model, X, y)
        log_loss_score = self._calculate_log_loss(calibrated_model, X, y)
        
        # Get calibration curve
        calibration_curve = self._get_calibration_curve(calibrated_model, X, y)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(calibrated_model, X, y)
        
        # Check for drift
        drift_detected = self._detect_drift(calibrated_model, X, y)
        
        # Determine if recalibration is needed
        recalibration_needed = self._should_recalibrate(
            reliability_score, brier_score, drift_detected
        )
        
        # Create result
        result = CalibrationResult(
            method=method,
            reliability_score=reliability_score,
            brier_score=brier_score,
            log_loss=log_loss_score,
            calibration_curve=calibration_curve,
            performance_metrics=performance_metrics,
            drift_detected=drift_detected,
            recalibration_needed=recalibration_needed
        )
        
        # Store result
        self.calibration_history.append(result)
        self.current_calibration = result
        
        logger.info(f"✅ Calibration complete: {reliability_score:.3f} reliability, {brier_score:.3f} brier")
        return result
    
    async def _select_best_calibration_method(self, model, X: pd.DataFrame, y: pd.Series) -> str:
        """Select the best calibration method"""
        logger.info("🔍 Selecting best calibration method...")
        
        best_method = None
        best_score = -np.inf
        
        for method in self.config.calibration_methods:
            try:
                # Apply calibration
                calibrated_model = self._apply_calibration(model, method)
                calibrated_model.fit(X, y)
                
                # Evaluate
                reliability_score = self._calculate_reliability_score(calibrated_model, X, y)
                
                if reliability_score > best_score:
                    best_score = reliability_score
                    best_method = method
                
            except Exception as e:
                logger.warning(f"Calibration method {method} failed: {e}")
                continue
        
        logger.info(f"✅ Best calibration method: {best_method} ({best_score:.3f})")
        return best_method or 'platt'
    
    def _apply_calibration(self, model, method: str):
        """Apply calibration method to model"""
        if method == 'platt':
            return CalibratedClassifierCV(model, method='sigmoid', cv=3)
        elif method == 'isotonic':
            return CalibratedClassifierCV(model, method='isotonic', cv=3)
        elif method == 'sigmoid':
            return CalibratedClassifierCV(model, method='sigmoid', cv=5)
        else:
            return model  # No calibration
    
    def _calculate_reliability_score(self, model, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate reliability score for calibration"""
        try:
            # Get predictions
            predictions = model.predict_proba(X)[:, 1]
            
            # Calculate reliability (how well calibrated the probabilities are)
            # Use Brier score as reliability measure (lower is better)
            brier_score = brier_score_loss(y, predictions)
            reliability = 1 - brier_score  # Convert to reliability score
            
            return max(0, reliability)  # Ensure non-negative
        
        except Exception as e:
            logger.warning(f"Error calculating reliability score: {e}")
            return 0.5  # Default reliability
    
    def _calculate_brier_score(self, model, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate Brier score for calibration quality"""
        try:
            predictions = model.predict_proba(X)[:, 1]
            return brier_score_loss(y, predictions)
        except Exception as e:
            logger.warning(f"Error calculating Brier score: {e}")
            return 1.0  # Worst possible score
    
    def _calculate_log_loss(self, model, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate log loss for model performance"""
        try:
            predictions = model.predict_proba(X)[:, 1]
            return log_loss(y, predictions)
        except Exception as e:
            logger.warning(f"Error calculating log loss: {e}")
            return np.inf  # Worst possible score
    
    def _get_calibration_curve(self, model, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Get calibration curve data"""
        try:
            predictions = model.predict_proba(X)[:, 1]
            
            # Create bins for calibration curve
            n_bins = 10
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]
            
            # Calculate calibration curve
            calibration_curve = {
                'bin_centers': [],
                'fractions': [],
                'counts': []
            }
            
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = (predictions > bin_lower) & (predictions <= bin_upper)
                prop_in_bin = in_bin.mean()
                
                if prop_in_bin > 0:
                    fraction_of_positives = y[in_bin].mean()
                    calibration_curve['bin_centers'].append((bin_lower + bin_upper) / 2)
                    calibration_curve['fractions'].append(fraction_of_positives)
                    calibration_curve['counts'].append(in_bin.sum())
            
            return calibration_curve
        
        except Exception as e:
            logger.warning(f"Error creating calibration curve: {e}")
            return {'bin_centers': [], 'fractions': [], 'counts': []}
    
    def _calculate_performance_metrics(self, model, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Calculate performance metrics"""
        try:
            predictions = model.predict_proba(X)[:, 1]
            
            # Basic metrics
            auc = roc_auc_score(y, predictions)
            
            # Hit rate at different thresholds
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
            hit_rates = {}
            
            for threshold in thresholds:
                decisions = (predictions >= threshold).astype(int)
                hit_rate = (decisions == y).mean()
                hit_rates[f'threshold_{threshold}'] = hit_rate
            
            # ROI simulation (simplified)
            roi_simulation = self._simulate_roi(predictions, y)
            
            return {
                'auc': auc,
                'hit_rates': hit_rates,
                'roi_simulation': roi_simulation,
                'mean_prediction': predictions.mean(),
                'std_prediction': predictions.std()
            }
        
        except Exception as e:
            logger.warning(f"Error calculating performance metrics: {e}")
            return {}
    
    def _simulate_roi(self, predictions: np.ndarray, y_true: np.ndarray) -> Dict:
        """Simulate ROI for different confidence thresholds"""
        roi_results = {}
        
        thresholds = [0.6, 0.7, 0.8, 0.9]
        
        for threshold in thresholds:
            # Select high-confidence predictions
            high_conf_mask = predictions >= threshold
            if high_conf_mask.sum() == 0:
                roi_results[f'threshold_{threshold}'] = 0.0
                continue
            
            # Simulate betting
            high_conf_predictions = predictions[high_conf_mask]
            high_conf_actual = y_true[high_conf_mask]
            
            # Calculate hit rate
            hit_rate = (high_conf_predictions > 0.5) == high_conf_actual
            hit_rate = hit_rate.mean()
            
            # Simulate ROI (simplified)
            # Assume 2.0 odds for simplicity
            odds = 2.0
            roi = (hit_rate * (odds - 1) - (1 - hit_rate)) * 100
            
            roi_results[f'threshold_{threshold}'] = roi
        
        return roi_results
    
    def _detect_drift(self, model, X: pd.DataFrame, y: pd.Series) -> bool:
        """Detect if model drift has occurred"""
        try:
            if len(self.performance_tracker) < 10:
                return False  # Not enough history
            
            # Get current performance
            current_performance = self._calculate_current_performance(model, X, y)
            
            # Compare with historical performance
            historical_performance = np.mean([p['reliability_score'] for p in self.performance_tracker[-10:]])
            
            # Check for significant drift
            drift_magnitude = abs(current_performance - historical_performance)
            drift_detected = drift_magnitude > self.config.drift_threshold
            
            if drift_detected:
                logger.warning(f"🚨 Model drift detected: {drift_magnitude:.3f} > {self.config.drift_threshold}")
            
            return drift_detected
        
        except Exception as e:
            logger.warning(f"Error detecting drift: {e}")
            return False
    
    def _calculate_current_performance(self, model, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate current model performance"""
        try:
            predictions = model.predict_proba(X)[:, 1]
            brier_score = brier_score_loss(y, predictions)
            return 1 - brier_score  # Convert to reliability score
        except Exception as e:
            logger.warning(f"Error calculating current performance: {e}")
            return 0.5
    
    def _should_recalibrate(self, reliability_score: float, brier_score: float, 
                          drift_detected: bool) -> bool:
        """Determine if recalibration is needed"""
        # Check reliability threshold
        if reliability_score < self.config.target_reliability:
            return True
        
        # Check Brier score threshold
        if brier_score > 0.25:  # High Brier score indicates poor calibration
            return True
        
        # Check for drift
        if drift_detected:
            return True
        
        # Check performance threshold
        if reliability_score < self.config.performance_threshold:
            return True
        
        return False
    
    async def continuous_calibration(self, model, X: pd.DataFrame, y: pd.Series):
        """Run continuous calibration process"""
        logger.info("🔄 Starting continuous calibration...")
        
        # Initial calibration
        result = await self.calibrate_model(model, X, y)
        
        # Store performance
        self.performance_tracker.append({
            'timestamp': datetime.now(),
            'reliability_score': result.reliability_score,
            'brier_score': result.brier_score,
            'drift_detected': result.drift_detected
        })
        
        # Check if recalibration is needed
        if result.recalibration_needed:
            logger.info("🔄 Recalibration needed, running optimization...")
            
            # Run additional optimization
            optimized_result = await self._optimize_calibration(model, X, y)
            
            # Update performance tracker
            self.performance_tracker.append({
                'timestamp': datetime.now(),
                'reliability_score': optimized_result.reliability_score,
                'brier_score': optimized_result.brier_score,
                'drift_detected': optimized_result.drift_detected,
                'optimized': True
            })
        
        return result
    
    async def _optimize_calibration(self, model, X: pd.DataFrame, y: pd.Series) -> CalibrationResult:
        """Optimize calibration parameters"""
        logger.info("⚙️ Optimizing calibration parameters...")
        
        # Try different calibration methods
        best_result = None
        best_score = -np.inf
        
        for method in self.config.calibration_methods:
            try:
                result = await self.calibrate_model(model, X, y, method)
                
                # Score based on reliability and Brier score
                score = result.reliability_score - result.brier_score
                
                if score > best_score:
                    best_score = score
                    best_result = result
                
            except Exception as e:
                logger.warning(f"Calibration optimization failed for {method}: {e}")
                continue
        
        if best_result is None:
            # Fallback to default calibration
            best_result = await self.calibrate_model(model, X, y, 'platt')
        
        logger.info(f"✅ Calibration optimization complete: {best_result.reliability_score:.3f}")
        return best_result
    
    def plot_calibration_curve(self, result: CalibrationResult, save_path: str = None):
        """Plot calibration curve"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Calibration curve
            if result.calibration_curve['bin_centers']:
                ax1.plot(result.calibration_curve['bin_centers'], 
                        result.calibration_curve['fractions'], 
                        'o-', label='Calibrated')
                ax1.plot([0, 1], [0, 1], '--', label='Perfect calibration')
                ax1.set_xlabel('Mean Predicted Probability')
                ax1.set_ylabel('Fraction of Positives')
                ax1.set_title('Calibration Curve')
                ax1.legend()
                ax1.grid(True)
            
            # Performance metrics
            if result.performance_metrics:
                metrics = result.performance_metrics
                
                # Hit rates by threshold
                if 'hit_rates' in metrics:
                    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
                    hit_rates = [metrics['hit_rates'].get(f'threshold_{t}', 0) for t in thresholds]
                    
                    ax2.bar(thresholds, hit_rates)
                    ax2.set_xlabel('Confidence Threshold')
                    ax2.set_ylabel('Hit Rate')
                    ax2.set_title('Hit Rate by Threshold')
                    ax2.grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"📊 Calibration curve saved to {save_path}")
            else:
                plt.show()
        
        except Exception as e:
            logger.error(f"Error plotting calibration curve: {e}")
    
    def get_calibration_report(self, result: CalibrationResult) -> str:
        """Generate calibration report"""
        report = f"""
# Model Calibration Report

## Calibration Results
- **Method**: {result.method}
- **Reliability Score**: {result.reliability_score:.3f}
- **Brier Score**: {result.brier_score:.3f}
- **Log Loss**: {result.log_loss:.3f}
- **Drift Detected**: {result.drift_detected}
- **Recalibration Needed**: {result.recalibration_needed}

## Performance Metrics
"""
        
        if result.performance_metrics:
            metrics = result.performance_metrics
            
            if 'auc' in metrics:
                report += f"- **AUC**: {metrics['auc']:.3f}\n"
            
            if 'hit_rates' in metrics:
                report += "\n### Hit Rates by Threshold\n"
                for threshold, hit_rate in metrics['hit_rates'].items():
                    report += f"- **{threshold}**: {hit_rate:.1%}\n"
            
            if 'roi_simulation' in metrics:
                report += "\n### ROI Simulation\n"
                for threshold, roi in metrics['roi_simulation'].items():
                    report += f"- **{threshold}**: {roi:.1f}%\n"
        
        report += f"""
## Calibration Quality
- **Target Reliability**: {self.config.target_reliability:.1%}
- **Achieved**: {'✅' if result.reliability_score >= self.config.target_reliability else '❌'}
- **Calibration Status**: {'Good' if result.brier_score < 0.25 else 'Needs Improvement'}

## Recommendations
"""
        
        if result.recalibration_needed:
            report += "- **Recalibration Required**: Model performance has degraded\n"
            report += "- **Action**: Run full recalibration process\n"
        else:
            report += "- **Status**: Model calibration is optimal\n"
            report += "- **Action**: Continue monitoring\n"
        
        if result.drift_detected:
            report += "- **Drift Detected**: Model may need retraining\n"
            report += "- **Action**: Consider updating training data\n"
        
        return report
    
    def save_calibration(self, filepath: str):
        """Save calibration results"""
        calibration_data = {
            'current_calibration': self.current_calibration,
            'calibration_history': self.calibration_history,
            'performance_tracker': self.performance_tracker,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(calibration_data, filepath)
        logger.info(f"💾 Calibration data saved to {filepath}")
    
    def load_calibration(self, filepath: str):
        """Load calibration results"""
        calibration_data = joblib.load(filepath)
        
        self.current_calibration = calibration_data['current_calibration']
        self.calibration_history = calibration_data['calibration_history']
        self.performance_tracker = calibration_data['performance_tracker']
        self.config = calibration_data['config']
        
        logger.info(f"📂 Calibration data loaded from {filepath}")


async def main():
    """Test the auto calibration system"""
    # Load sample data
    df = pd.read_csv('selection_engine/dataset.csv')
    
    # Prepare data
    feature_columns = [col for col in df.columns 
                      if col not in ['over_2_5', 'match_id', 'date', 'home_team', 'away_team', 'league']]
    X = df[feature_columns].fillna(0)
    y = df['over_2_5'].astype(int)
    
    # Create a simple model for testing
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Initialize calibration system
    config = CalibrationConfig(
        target_reliability=0.95,
        drift_threshold=0.05
    )
    
    calibrator = AutoCalibrationSystem(config)
    
    # Run calibration
    result = await calibrator.calibrate_model(model, X, y)
    
    # Generate report
    report = calibrator.get_calibration_report(result)
    print(report)
    
    # Save calibration
    calibrator.save_calibration('ml_optimization/calibration_data.pkl')
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

