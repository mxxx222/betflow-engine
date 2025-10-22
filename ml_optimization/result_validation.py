"""
Automated Result Validation and Feedback Loop
Continuous validation of ML model performance with automatic optimization
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for result validation"""
    validation_window: int = 30  # Days to look back for validation
    min_samples_for_validation: int = 50  # Minimum samples needed
    performance_thresholds: Dict[str, float] = None  # Performance thresholds
    alert_thresholds: Dict[str, float] = None  # Alert thresholds
    auto_retrain_threshold: float = 0.15  # Performance drop threshold for auto-retrain
    
    def __post_init__(self):
        if self.performance_thresholds is None:
            self.performance_thresholds = {
                'min_accuracy': 0.70,
                'min_precision': 0.65,
                'min_recall': 0.60,
                'min_f1': 0.62,
                'min_auc': 0.75,
                'max_brier': 0.25
            }
        
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'accuracy_drop': 0.05,
                'precision_drop': 0.05,
                'recall_drop': 0.05,
                'f1_drop': 0.05,
                'auc_drop': 0.03,
                'brier_increase': 0.05
            }


@dataclass
class ValidationResult:
    """Result of model validation"""
    timestamp: datetime
    model_id: str
    validation_period: str
    metrics: Dict[str, float]
    performance_status: str
    alerts: List[str]
    recommendations: List[str]
    auto_retrain_needed: bool
    confidence_score: float
    reliability_score: float


@dataclass
class PerformanceHistory:
    """Performance history tracking"""
    timestamp: datetime
    model_id: str
    metrics: Dict[str, float]
    predictions: np.ndarray
    actuals: np.ndarray
    confidence_scores: np.ndarray


class ResultValidator:
    """Automated result validation and feedback system"""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.performance_history = []
        self.validation_results = []
        self.alert_history = []
        self.model_versions = {}
        
    async def validate_model_performance(self, model, X: pd.DataFrame, y: pd.Series, 
                                       model_id: str = "default") -> ValidationResult:
        """Validate model performance and generate feedback"""
        logger.info(f"🔍 Validating model performance for {model_id}")
        
        # Get predictions
        predictions = model.predict(X)
        prediction_probas = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else predictions
        
        # Calculate metrics
        metrics = self._calculate_comprehensive_metrics(y, predictions, prediction_probas)
        
        # Check performance status
        performance_status = self._assess_performance_status(metrics)
        
        # Generate alerts
        alerts = self._generate_alerts(metrics, model_id)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, alerts)
        
        # Check if auto-retrain is needed
        auto_retrain_needed = self._check_auto_retrain_needed(metrics, model_id)
        
        # Calculate confidence and reliability scores
        confidence_score = self._calculate_confidence_score(metrics)
        reliability_score = self._calculate_reliability_score(metrics)
        
        # Create validation result
        result = ValidationResult(
            timestamp=datetime.now(),
            model_id=model_id,
            validation_period=f"last_{len(X)}_samples",
            metrics=metrics,
            performance_status=performance_status,
            alerts=alerts,
            recommendations=recommendations,
            auto_retrain_needed=auto_retrain_needed,
            confidence_score=confidence_score,
            reliability_score=reliability_score
        )
        
        # Store performance history
        self._store_performance_history(model_id, metrics, predictions, y, prediction_probas)
        
        # Store validation result
        self.validation_results.append(result)
        
        logger.info(f"✅ Validation complete: {performance_status}, {len(alerts)} alerts")
        return result
    
    def _calculate_comprehensive_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                                       y_proba: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        metrics = {}
        
        # Basic classification metrics
        metrics['accuracy'] = accuracy_score(y_true, y_pred)
        metrics['precision'] = precision_score(y_true, y_pred, average='weighted')
        metrics['recall'] = recall_score(y_true, y_pred, average='weighted')
        metrics['f1'] = f1_score(y_true, y_pred, average='weighted')
        
        # Probability-based metrics
        if len(np.unique(y_proba)) > 1:  # Check if probabilities are meaningful
            metrics['auc'] = roc_auc_score(y_true, y_proba)
            metrics['log_loss'] = log_loss(y_true, y_proba)
            metrics['brier_score'] = brier_score_loss(y_true, y_proba)
        else:
            metrics['auc'] = 0.5
            metrics['log_loss'] = np.inf
            metrics['brier_score'] = 1.0
        
        # Confidence-based metrics
        metrics['mean_confidence'] = np.mean(y_proba)
        metrics['std_confidence'] = np.std(y_proba)
        metrics['confidence_range'] = np.max(y_proba) - np.min(y_proba)
        
        # Hit rate by confidence threshold
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
        for threshold in thresholds:
            high_conf_mask = y_proba >= threshold
            if high_conf_mask.sum() > 0:
                hit_rate = (y_pred[high_conf_mask] == y_true[high_conf_mask]).mean()
                metrics[f'hit_rate_{threshold}'] = hit_rate
            else:
                metrics[f'hit_rate_{threshold}'] = 0.0
        
        # ROI simulation
        roi_metrics = self._simulate_roi_metrics(y_proba, y_true)
        metrics.update(roi_metrics)
        
        return metrics
    
    def _simulate_roi_metrics(self, y_proba: np.ndarray, y_true: np.ndarray) -> Dict[str, float]:
        """Simulate ROI metrics for different confidence thresholds"""
        roi_metrics = {}
        
        thresholds = [0.6, 0.7, 0.8, 0.9]
        odds = 2.0  # Assume 2.0 odds for simulation
        
        for threshold in thresholds:
            # Select high-confidence predictions
            high_conf_mask = y_proba >= threshold
            if high_conf_mask.sum() == 0:
                roi_metrics[f'roi_{threshold}'] = 0.0
                roi_metrics[f'selections_{threshold}'] = 0
                continue
            
            # Calculate hit rate
            high_conf_pred = (y_proba >= 0.5).astype(int)[high_conf_mask]
            high_conf_actual = y_true[high_conf_mask]
            hit_rate = (high_conf_pred == high_conf_actual).mean()
            
            # Simulate ROI
            roi = (hit_rate * (odds - 1) - (1 - hit_rate)) * 100
            
            roi_metrics[f'roi_{threshold}'] = roi
            roi_metrics[f'selections_{threshold}'] = high_conf_mask.sum()
        
        return roi_metrics
    
    def _assess_performance_status(self, metrics: Dict[str, float]) -> str:
        """Assess overall performance status"""
        thresholds = self.config.performance_thresholds
        
        # Check each threshold
        checks = {
            'accuracy': metrics['accuracy'] >= thresholds['min_accuracy'],
            'precision': metrics['precision'] >= thresholds['min_precision'],
            'recall': metrics['recall'] >= thresholds['min_recall'],
            'f1': metrics['f1'] >= thresholds['min_f1'],
            'auc': metrics['auc'] >= thresholds['min_auc'],
            'brier': metrics['brier_score'] <= thresholds['max_brier']
        }
        
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        
        if passed_checks == total_checks:
            return "Excellent"
        elif passed_checks >= total_checks * 0.8:
            return "Good"
        elif passed_checks >= total_checks * 0.6:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_alerts(self, metrics: Dict[str, float], model_id: str) -> List[str]:
        """Generate performance alerts"""
        alerts = []
        alert_thresholds = self.config.alert_thresholds
        
        # Get historical performance for comparison
        historical_metrics = self._get_historical_metrics(model_id)
        
        if historical_metrics:
            # Check for performance drops
            for metric, threshold in alert_thresholds.items():
                if metric in metrics and metric in historical_metrics:
                    current_value = metrics[metric]
                    historical_value = historical_metrics[metric]
                    
                    if metric.endswith('_drop'):
                        # Check for drops
                        drop = historical_value - current_value
                        if drop > threshold:
                            alerts.append(f"⚠️ {metric.replace('_drop', '')} dropped by {drop:.3f}")
                    elif metric.endswith('_increase'):
                        # Check for increases (for metrics where increase is bad)
                        increase = current_value - historical_value
                        if increase > threshold:
                            alerts.append(f"⚠️ {metric.replace('_increase', '')} increased by {increase:.3f}")
        
        # Check absolute thresholds
        if metrics['accuracy'] < 0.6:
            alerts.append("🚨 Critical: Accuracy below 60%")
        
        if metrics['auc'] < 0.6:
            alerts.append("🚨 Critical: AUC below 60%")
        
        if metrics['brier_score'] > 0.4:
            alerts.append("🚨 Critical: Brier score above 0.4")
        
        # Check confidence distribution
        if metrics['confidence_range'] < 0.2:
            alerts.append("⚠️ Low confidence range - model may be underconfident")
        
        if metrics['mean_confidence'] > 0.9:
            alerts.append("⚠️ High mean confidence - model may be overconfident")
        
        return alerts
    
    def _generate_recommendations(self, metrics: Dict[str, float], alerts: List[str]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        if metrics['accuracy'] < 0.7:
            recommendations.append("📈 Improve model accuracy - consider feature engineering or more data")
        
        if metrics['precision'] < 0.65:
            recommendations.append("🎯 Improve precision - reduce false positives")
        
        if metrics['recall'] < 0.6:
            recommendations.append("🔍 Improve recall - reduce false negatives")
        
        if metrics['auc'] < 0.75:
            recommendations.append("📊 Improve AUC - better class separation needed")
        
        if metrics['brier_score'] > 0.25:
            recommendations.append("📉 Improve calibration - probabilities not well-calibrated")
        
        # Confidence-based recommendations
        if metrics['confidence_range'] < 0.3:
            recommendations.append("🎲 Increase confidence range - model needs more discrimination")
        
        if metrics['mean_confidence'] < 0.4:
            recommendations.append("💪 Increase model confidence - more training data needed")
        
        # ROI-based recommendations
        roi_thresholds = [0.6, 0.7, 0.8, 0.9]
        for threshold in roi_thresholds:
            roi_key = f'roi_{threshold}'
            if roi_key in metrics and metrics[roi_key] < 0:
                recommendations.append(f"💰 Negative ROI at {threshold:.0%} threshold - adjust selection criteria")
        
        # Alert-based recommendations
        if any("Critical" in alert for alert in alerts):
            recommendations.append("🚨 Critical issues detected - immediate model review required")
        
        if len(alerts) > 3:
            recommendations.append("⚠️ Multiple alerts - comprehensive model review recommended")
        
        return recommendations
    
    def _check_auto_retrain_needed(self, metrics: Dict[str, float], model_id: str) -> bool:
        """Check if automatic retraining is needed"""
        # Get historical performance
        historical_metrics = self._get_historical_metrics(model_id)
        
        if not historical_metrics:
            return False  # No history to compare
        
        # Check for significant performance drop
        key_metrics = ['accuracy', 'auc', 'f1']
        performance_drops = []
        
        for metric in key_metrics:
            if metric in metrics and metric in historical_metrics:
                drop = historical_metrics[metric] - metrics[metric]
                performance_drops.append(drop)
        
        if performance_drops:
            avg_drop = np.mean(performance_drops)
            if avg_drop > self.config.auto_retrain_threshold:
                logger.warning(f"🔄 Auto-retrain triggered: {avg_drop:.3f} average performance drop")
                return True
        
        return False
    
    def _calculate_confidence_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall confidence score"""
        # Weight different metrics
        weights = {
            'accuracy': 0.25,
            'auc': 0.25,
            'f1': 0.20,
            'precision': 0.15,
            'recall': 0.15
        }
        
        confidence_score = 0.0
        for metric, weight in weights.items():
            if metric in metrics:
                confidence_score += metrics[metric] * weight
        
        return min(1.0, max(0.0, confidence_score))
    
    def _calculate_reliability_score(self, metrics: Dict[str, float]) -> float:
        """Calculate reliability score based on consistency"""
        # Check consistency across different thresholds
        hit_rates = [metrics.get(f'hit_rate_{t}', 0) for t in [0.5, 0.6, 0.7, 0.8, 0.9]]
        
        if len(hit_rates) > 1:
            # Calculate coefficient of variation (lower is better)
            mean_hit_rate = np.mean(hit_rates)
            std_hit_rate = np.std(hit_rates)
            
            if mean_hit_rate > 0:
                cv = std_hit_rate / mean_hit_rate
                reliability = 1 - cv  # Convert to reliability score
            else:
                reliability = 0.0
        else:
            reliability = 0.5
        
        return max(0.0, min(1.0, reliability))
    
    def _get_historical_metrics(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get historical performance metrics for comparison"""
        # Get recent performance history for this model
        recent_history = [h for h in self.performance_history 
                         if h.model_id == model_id and 
                         (datetime.now() - h.timestamp).days <= self.config.validation_window]
        
        if not recent_history:
            return None
        
        # Calculate average metrics
        all_metrics = [h.metrics for h in recent_history]
        avg_metrics = {}
        
        for metric_name in all_metrics[0].keys():
            values = [m.get(metric_name, 0) for m in all_metrics if metric_name in m]
            if values:
                avg_metrics[metric_name] = np.mean(values)
        
        return avg_metrics
    
    def _store_performance_history(self, model_id: str, metrics: Dict[str, float], 
                                 predictions: np.ndarray, actuals: np.ndarray, 
                                 confidence_scores: np.ndarray):
        """Store performance history"""
        history_entry = PerformanceHistory(
            timestamp=datetime.now(),
            model_id=model_id,
            metrics=metrics,
            predictions=predictions,
            actuals=actuals,
            confidence_scores=confidence_scores
        )
        
        self.performance_history.append(history_entry)
        
        # Keep only recent history
        cutoff_date = datetime.now() - timedelta(days=self.config.validation_window * 2)
        self.performance_history = [h for h in self.performance_history if h.timestamp > cutoff_date]
    
    def generate_validation_report(self, result: ValidationResult) -> str:
        """Generate comprehensive validation report"""
        report = f"""
# Model Validation Report

## Validation Summary
- **Model ID**: {result.model_id}
- **Timestamp**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **Validation Period**: {result.validation_period}
- **Performance Status**: {result.performance_status}
- **Confidence Score**: {result.confidence_score:.3f}
- **Reliability Score**: {result.reliability_score:.3f}

## Performance Metrics
- **Accuracy**: {result.metrics.get('accuracy', 0):.3f}
- **Precision**: {result.metrics.get('precision', 0):.3f}
- **Recall**: {result.metrics.get('recall', 0):.3f}
- **F1 Score**: {result.metrics.get('f1', 0):.3f}
- **AUC**: {result.metrics.get('auc', 0):.3f}
- **Brier Score**: {result.metrics.get('brier_score', 0):.3f}

## Hit Rates by Threshold
"""
        
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            hit_rate = result.metrics.get(f'hit_rate_{threshold}', 0)
            report += f"- **{threshold:.0%}**: {hit_rate:.1%}\n"
        
        report += "\n## ROI Simulation\n"
        for threshold in [0.6, 0.7, 0.8, 0.9]:
            roi = result.metrics.get(f'roi_{threshold}', 0)
            selections = result.metrics.get(f'selections_{threshold}', 0)
            report += f"- **{threshold:.0%}**: {roi:.1f}% ROI ({selections} selections)\n"
        
        if result.alerts:
            report += "\n## Alerts\n"
            for alert in result.alerts:
                report += f"- {alert}\n"
        
        if result.recommendations:
            report += "\n## Recommendations\n"
            for rec in result.recommendations:
                report += f"- {rec}\n"
        
        if result.auto_retrain_needed:
            report += "\n## ⚠️ Auto-Retrain Required\n"
            report += "Model performance has degraded significantly. Automatic retraining is recommended.\n"
        
        return report
    
    def plot_performance_trends(self, model_id: str = None, save_path: str = None):
        """Plot performance trends over time"""
        try:
            # Filter history by model_id if specified
            if model_id:
                history = [h for h in self.performance_history if h.model_id == model_id]
            else:
                history = self.performance_history
            
            if len(history) < 2:
                logger.warning("Not enough history for trend analysis")
                return
            
            # Extract data
            timestamps = [h.timestamp for h in history]
            accuracies = [h.metrics.get('accuracy', 0) for h in history]
            aucs = [h.metrics.get('auc', 0) for h in history]
            f1s = [h.metrics.get('f1', 0) for h in history]
            
            # Create plots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Accuracy trend
            axes[0, 0].plot(timestamps, accuracies, 'o-', label='Accuracy')
            axes[0, 0].set_title('Accuracy Trend')
            axes[0, 0].set_ylabel('Accuracy')
            axes[0, 0].grid(True)
            
            # AUC trend
            axes[0, 1].plot(timestamps, aucs, 'o-', label='AUC', color='orange')
            axes[0, 1].set_title('AUC Trend')
            axes[0, 1].set_ylabel('AUC')
            axes[0, 1].grid(True)
            
            # F1 trend
            axes[1, 0].plot(timestamps, f1s, 'o-', label='F1', color='green')
            axes[1, 0].set_title('F1 Score Trend')
            axes[1, 0].set_ylabel('F1 Score')
            axes[1, 0].grid(True)
            
            # Combined metrics
            axes[1, 1].plot(timestamps, accuracies, 'o-', label='Accuracy')
            axes[1, 1].plot(timestamps, aucs, 'o-', label='AUC')
            axes[1, 1].plot(timestamps, f1s, 'o-', label='F1')
            axes[1, 1].set_title('Combined Metrics Trend')
            axes[1, 1].set_ylabel('Score')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"📊 Performance trends saved to {save_path}")
            else:
                plt.show()
        
        except Exception as e:
            logger.error(f"Error plotting performance trends: {e}")
    
    def save_validation_data(self, filepath: str):
        """Save validation data"""
        validation_data = {
            'performance_history': self.performance_history,
            'validation_results': self.validation_results,
            'alert_history': self.alert_history,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
        
        import joblib
        joblib.dump(validation_data, filepath)
        logger.info(f"💾 Validation data saved to {filepath}")
    
    def load_validation_data(self, filepath: str):
        """Load validation data"""
        import joblib
        validation_data = joblib.load(filepath)
        
        self.performance_history = validation_data['performance_history']
        self.validation_results = validation_data['validation_results']
        self.alert_history = validation_data['alert_history']
        self.config = validation_data['config']
        
        logger.info(f"📂 Validation data loaded from {filepath}")


async def main():
    """Test the result validation system"""
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
    
    # Initialize validator
    config = ValidationConfig(
        validation_window=30,
        min_samples_for_validation=50
    )
    
    validator = ResultValidator(config)
    
    # Run validation
    result = await validator.validate_model_performance(model, X, y, "test_model")
    
    # Generate report
    report = validator.generate_validation_report(result)
    print(report)
    
    # Save validation data
    validator.save_validation_data('ml_optimization/validation_data.pkl')
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

