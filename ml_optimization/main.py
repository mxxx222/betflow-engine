#!/usr/bin/env python3
"""
ML Optimization Main Runner
Automated ML optimization with calibration and validation for high ROI targeting
"""
import asyncio
import logging
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from auto_ml_engine import AutoMLEngine, OptimizationConfig
from auto_calibration import AutoCalibrationSystem, CalibrationConfig
from result_validation import ResultValidator, ValidationConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLOptimizationRunner:
    """Main runner for ML optimization pipeline"""
    
    def __init__(self):
        self.optimization_config = OptimizationConfig()
        self.calibration_config = CalibrationConfig()
        self.validation_config = ValidationConfig()
        
        self.ml_engine = AutoMLEngine(self.optimization_config)
        self.calibration_system = AutoCalibrationSystem(self.calibration_config)
        self.validator = ResultValidator(self.validation_config)
        
    async def run_full_optimization(self, df: pd.DataFrame, target_column: str = 'over_2_5'):
        """Run complete ML optimization pipeline"""
        logger.info("🚀 Starting full ML optimization pipeline")
        
        # Step 1: ML Optimization
        logger.info("📊 Step 1: ML Model Optimization...")
        optimization_result = await self.ml_engine.optimize_for_roi(df, target_column)
        
        # Step 2: Model Calibration
        logger.info("📈 Step 2: Model Calibration...")
        X, y = self._prepare_data(df, target_column)
        calibration_result = await self.calibration_system.calibrate_model(
            optimization_result.best_model, X, y
        )
        
        # Step 3: Result Validation
        logger.info("🔍 Step 3: Result Validation...")
        validation_result = await self.validator.validate_model_performance(
            optimization_result.best_model, X, y, "optimized_model"
        )
        
        # Step 4: Generate comprehensive report
        logger.info("📄 Step 4: Generating reports...")
        self._generate_comprehensive_report(
            optimization_result, calibration_result, validation_result
        )
        
        # Step 5: Save all results
        logger.info("💾 Step 5: Saving results...")
        self._save_all_results(optimization_result, calibration_result, validation_result)
        
        logger.info("✅ Full ML optimization pipeline complete!")
        return optimization_result, calibration_result, validation_result
    
    async def run_optimization_only(self, df: pd.DataFrame, target_column: str = 'over_2_5'):
        """Run only ML optimization"""
        logger.info("🔧 Running ML optimization only...")
        result = await self.ml_engine.optimize_for_roi(df, target_column)
        self.ml_engine.save_model('ml_optimization/optimized_model.pkl')
        return result
    
    async def run_calibration_only(self, model_path: str, df: pd.DataFrame, target_column: str = 'over_2_5'):
        """Run only model calibration"""
        logger.info("📊 Running calibration only...")
        
        # Load model
        self.ml_engine.load_model(model_path)
        model = self.ml_engine.best_model
        
        # Prepare data
        X, y = self._prepare_data(df, target_column)
        
        # Run calibration
        result = await self.calibration_system.calibrate_model(model, X, y)
        self.calibration_system.save_calibration('ml_optimization/calibration_data.pkl')
        
        return result
    
    async def run_validation_only(self, model_path: str, df: pd.DataFrame, target_column: str = 'over_2_5'):
        """Run only result validation"""
        logger.info("🔍 Running validation only...")
        
        # Load model
        self.ml_engine.load_model(model_path)
        model = self.ml_engine.best_model
        
        # Prepare data
        X, y = self._prepare_data(df, target_column)
        
        # Run validation
        result = await self.validator.validate_model_performance(model, X, y, "loaded_model")
        self.validator.save_validation_data('ml_optimization/validation_data.pkl')
        
        return result
    
    def _prepare_data(self, df: pd.DataFrame, target_column: str):
        """Prepare data for ML operations"""
        # Select features
        feature_columns = [col for col in df.columns 
                          if col not in [target_column, 'match_id', 'date', 'home_team', 'away_team', 'league']]
        
        X = df[feature_columns].fillna(0)
        y = df[target_column].astype(int)
        
        # Remove NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        return X, y
    
    def _generate_comprehensive_report(self, optimization_result, calibration_result, validation_result):
        """Generate comprehensive optimization report"""
        report = f"""
# ML Optimization Comprehensive Report

## Executive Summary
- **Optimization Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Target ROI**: {self.optimization_config.target_roi:.1%}
- **Achieved ROI**: {optimization_result.roi_achieved:.2%}
- **Hit Rate**: {optimization_result.hit_rate_achieved:.1%}
- **Model Performance**: {validation_result.performance_status}

## ML Optimization Results
- **Best Model**: {optimization_result.best_params.get('model_type', 'unknown')}
- **Optimization Time**: {optimization_result.optimization_time:.1f}s
- **Trials Completed**: {optimization_result.trials_completed}
- **Best Score**: {optimization_result.best_score:.4f}

## Calibration Results
- **Method**: {calibration_result.method}
- **Reliability Score**: {calibration_result.reliability_score:.3f}
- **Brier Score**: {calibration_result.brier_score:.3f}
- **Drift Detected**: {calibration_result.drift_detected}
- **Recalibration Needed**: {calibration_result.recalibration_needed}

## Validation Results
- **Performance Status**: {validation_result.performance_status}
- **Confidence Score**: {validation_result.confidence_score:.3f}
- **Reliability Score**: {validation_result.reliability_score:.3f}
- **Auto-Retrain Needed**: {validation_result.auto_retrain_needed}

## Performance Metrics
- **Accuracy**: {validation_result.metrics.get('accuracy', 0):.3f}
- **Precision**: {validation_result.metrics.get('precision', 0):.3f}
- **Recall**: {validation_result.metrics.get('recall', 0):.3f}
- **F1 Score**: {validation_result.metrics.get('f1', 0):.3f}
- **AUC**: {validation_result.metrics.get('auc', 0):.3f}
- **Brier Score**: {validation_result.metrics.get('brier_score', 0):.3f}

## Hit Rates by Confidence Threshold
"""
        
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            hit_rate = validation_result.metrics.get(f'hit_rate_{threshold}', 0)
            report += f"- **{threshold:.0%}**: {hit_rate:.1%}\n"
        
        report += "\n## ROI Simulation\n"
        for threshold in [0.6, 0.7, 0.8, 0.9]:
            roi = validation_result.metrics.get(f'roi_{threshold}', 0)
            selections = validation_result.metrics.get(f'selections_{threshold}', 0)
            report += f"- **{threshold:.0%}**: {roi:.1f}% ROI ({selections} selections)\n"
        
        if validation_result.alerts:
            report += "\n## Alerts\n"
            for alert in validation_result.alerts:
                report += f"- {alert}\n"
        
        if validation_result.recommendations:
            report += "\n## Recommendations\n"
            for rec in validation_result.recommendations:
                report += f"- {rec}\n"
        
        # Feature importance
        if optimization_result.feature_importance:
            report += "\n## Top 10 Feature Importance\n"
            sorted_features = sorted(optimization_result.feature_importance.items(), 
                                  key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in sorted_features:
                report += f"- **{feature}**: {importance:.4f}\n"
        
        report += "\n## Next Steps\n"
        if validation_result.auto_retrain_needed:
            report += "- **Immediate**: Auto-retrain model due to performance degradation\n"
        elif calibration_result.recalibration_needed:
            report += "- **Short-term**: Recalibrate model for better performance\n"
        else:
            report += "- **Monitor**: Continue monitoring model performance\n"
        
        if validation_result.alerts:
            report += "- **Review**: Address performance alerts\n"
        
        report += "- **Deploy**: Deploy optimized model to production\n"
        report += "- **Monitor**: Set up continuous monitoring\n"
        
        # Save report
        with open('ml_optimization/comprehensive_report.md', 'w') as f:
            f.write(report)
        
        logger.info("📄 Comprehensive report saved to ml_optimization/comprehensive_report.md")
    
    def _save_all_results(self, optimization_result, calibration_result, validation_result):
        """Save all optimization results"""
        # Save individual results
        self.ml_engine.save_model('ml_optimization/optimized_model.pkl')
        self.calibration_system.save_calibration('ml_optimization/calibration_data.pkl')
        self.validator.save_validation_data('ml_optimization/validation_data.pkl')
        
        # Save combined results
        combined_results = {
            'optimization': optimization_result,
            'calibration': calibration_result,
            'validation': validation_result,
            'timestamp': datetime.now().isoformat(),
            'config': {
                'optimization': self.optimization_config,
                'calibration': self.calibration_config,
                'validation': self.validation_config
            }
        }
        
        import joblib
        joblib.dump(combined_results, 'ml_optimization/combined_results.pkl')
        
        logger.info("💾 All results saved successfully")
    
    def plot_optimization_results(self, save_path: str = None):
        """Plot optimization results"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create comprehensive plots
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            
            # Plot 1: Performance metrics
            if hasattr(self.validator, 'performance_history') and self.validator.performance_history:
                timestamps = [h.timestamp for h in self.validator.performance_history]
                accuracies = [h.metrics.get('accuracy', 0) for h in self.validator.performance_history]
                aucs = [h.metrics.get('auc', 0) for h in self.validator.performance_history]
                
                axes[0, 0].plot(timestamps, accuracies, 'o-', label='Accuracy')
                axes[0, 0].plot(timestamps, aucs, 'o-', label='AUC')
                axes[0, 0].set_title('Performance Trends')
                axes[0, 0].set_ylabel('Score')
                axes[0, 0].legend()
                axes[0, 0].grid(True)
            
            # Plot 2: Calibration curve
            if hasattr(self.calibration_system, 'current_calibration') and self.calibration_system.current_calibration:
                cal_curve = self.calibration_system.current_calibration.calibration_curve
                if cal_curve['bin_centers']:
                    axes[0, 1].plot(cal_curve['bin_centers'], cal_curve['fractions'], 'o-', label='Calibrated')
                    axes[0, 1].plot([0, 1], [0, 1], '--', label='Perfect')
                    axes[0, 1].set_title('Calibration Curve')
                    axes[0, 1].set_xlabel('Mean Predicted Probability')
                    axes[0, 1].set_ylabel('Fraction of Positives')
                    axes[0, 1].legend()
                    axes[0, 1].grid(True)
            
            # Plot 3: Feature importance
            if hasattr(self.ml_engine, 'best_model') and self.ml_engine.best_model:
                # This would need to be implemented based on the specific model type
                axes[0, 2].text(0.5, 0.5, 'Feature Importance\n(Implementation needed)', 
                              ha='center', va='center', transform=axes[0, 2].transAxes)
                axes[0, 2].set_title('Feature Importance')
            
            # Plot 4: ROI by threshold
            if hasattr(self.validator, 'validation_results') and self.validator.validation_results:
                latest_result = self.validator.validation_results[-1]
                thresholds = [0.6, 0.7, 0.8, 0.9]
                rois = [latest_result.metrics.get(f'roi_{t}', 0) for t in thresholds]
                
                axes[1, 0].bar(thresholds, rois)
                axes[1, 0].set_title('ROI by Confidence Threshold')
                axes[1, 0].set_xlabel('Threshold')
                axes[1, 0].set_ylabel('ROI (%)')
                axes[1, 0].grid(True)
            
            # Plot 5: Hit rates by threshold
            if hasattr(self.validator, 'validation_results') and self.validator.validation_results:
                latest_result = self.validator.validation_results[-1]
                thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
                hit_rates = [latest_result.metrics.get(f'hit_rate_{t}', 0) for t in thresholds]
                
                axes[1, 1].bar(thresholds, hit_rates)
                axes[1, 1].set_title('Hit Rate by Confidence Threshold')
                axes[1, 1].set_xlabel('Threshold')
                axes[1, 1].set_ylabel('Hit Rate')
                axes[1, 1].grid(True)
            
            # Plot 6: Performance summary
            if hasattr(self.validator, 'validation_results') and self.validator.validation_results:
                latest_result = self.validator.validation_results[-1]
                metrics = ['accuracy', 'precision', 'recall', 'f1', 'auc']
                values = [latest_result.metrics.get(m, 0) for m in metrics]
                
                axes[1, 2].bar(metrics, values)
                axes[1, 2].set_title('Performance Metrics Summary')
                axes[1, 2].set_ylabel('Score')
                axes[1, 2].tick_params(axis='x', rotation=45)
                axes[1, 2].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"📊 Optimization plots saved to {save_path}")
            else:
                plt.show()
        
        except Exception as e:
            logger.error(f"Error plotting optimization results: {e}")


def main():
    """Main function for ML optimization"""
    parser = argparse.ArgumentParser(description='ML Optimization Runner')
    parser.add_argument('--mode', choices=['full', 'optimize', 'calibrate', 'validate'], 
                       default='full', help='Optimization mode to run')
    parser.add_argument('--data', default='selection_engine/dataset.csv', 
                       help='Path to dataset')
    parser.add_argument('--target', default='over_2_5', 
                       help='Target column name')
    parser.add_argument('--model', help='Path to model file (for calibrate/validate modes)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load data
    try:
        df = pd.read_csv(args.data)
        logger.info(f"📂 Loaded dataset: {len(df)} samples")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return 1
    
    runner = MLOptimizationRunner()
    
    if args.mode == 'full':
        asyncio.run(runner.run_full_optimization(df, args.target))
    elif args.mode == 'optimize':
        asyncio.run(runner.run_optimization_only(df, args.target))
    elif args.mode == 'calibrate':
        if not args.model:
            logger.error("Model path required for calibration mode")
            return 1
        asyncio.run(runner.run_calibration_only(args.model, df, args.target))
    elif args.mode == 'validate':
        if not args.model:
            logger.error("Model path required for validation mode")
            return 1
        asyncio.run(runner.run_validation_only(args.model, df, args.target))
    
    return 0


if __name__ == "__main__":
    exit(main())

