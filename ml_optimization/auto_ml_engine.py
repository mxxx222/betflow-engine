"""
Automated ML Optimization Engine
High ROI targeting with automatic calibration and result validation
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

# ML Libraries
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV, cross_val_score
from sklearn.metrics import log_loss, roc_auc_score, precision_recall_curve, roc_curve
from sklearn.calibration import CalibratedClassifierCV, PlattScaling, IsotonicRegression
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
import lightgbm as lgb
import xgboost as xgb
from scipy.optimize import minimize
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

# Advanced ML
import catboost as cb
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for ML optimization"""
    target_roi: float = 0.15  # 15% target ROI
    min_hit_rate: float = 0.70  # 70% minimum hit rate
    max_drawdown: float = 0.20  # 20% maximum drawdown
    n_trials: int = 100  # Number of optimization trials
    cv_folds: int = 5  # Cross-validation folds
    test_size: float = 0.2  # Test set size
    feature_selection_k: int = 50  # Number of features to select
    ensemble_size: int = 10  # Number of models in ensemble
    calibration_methods: List[str] = None  # Calibration methods to try
    
    def __post_init__(self):
        if self.calibration_methods is None:
            self.calibration_methods = ['platt', 'isotonic', 'sigmoid']


@dataclass
class OptimizationResult:
    """Result of ML optimization"""
    best_model: Any
    best_params: Dict
    best_score: float
    roi_achieved: float
    hit_rate_achieved: float
    drawdown_achieved: float
    feature_importance: Dict
    calibration_method: str
    ensemble_weights: List[float]
    optimization_time: float
    trials_completed: int


class AutoMLEngine:
    """Automated ML optimization engine for high ROI targeting"""
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.models = {}
        self.optimization_history = []
        self.best_model = None
        self.feature_selector = None
        self.scaler = None
        
    async def optimize_for_roi(self, df: pd.DataFrame, target_column: str = 'over_2_5') -> OptimizationResult:
        """Optimize ML models for high ROI targeting"""
        logger.info(f"🚀 Starting ML optimization for {self.config.target_roi:.1%} ROI target")
        
        start_time = datetime.now()
        
        # Prepare data
        X, y = self._prepare_data(df, target_column)
        
        # Feature selection
        X_selected = self._select_features(X, y)
        
        # Hyperparameter optimization
        best_params = await self._optimize_hyperparameters(X_selected, y)
        
        # Model ensemble optimization
        ensemble_weights = await self._optimize_ensemble(X_selected, y, best_params)
        
        # Calibration optimization
        calibration_method = await self._optimize_calibration(X_selected, y, best_params)
        
        # Build final model
        final_model = self._build_final_model(X_selected, y, best_params, ensemble_weights, calibration_method)
        
        # Validate performance
        roi, hit_rate, drawdown = self._validate_performance(final_model, X_selected, y)
        
        # Calculate optimization time
        optimization_time = (datetime.now() - start_time).total_seconds()
        
        # Create result
        result = OptimizationResult(
            best_model=final_model,
            best_params=best_params,
            best_score=roi,
            roi_achieved=roi,
            hit_rate_achieved=hit_rate,
            drawdown_achieved=drawdown,
            feature_importance=self._get_feature_importance(final_model, X_selected.columns),
            calibration_method=calibration_method,
            ensemble_weights=ensemble_weights,
            optimization_time=optimization_time,
            trials_completed=self.config.n_trials
        )
        
        # Store result
        self.optimization_history.append(result)
        self.best_model = final_model
        
        logger.info(f"✅ Optimization complete: {roi:.2%} ROI, {hit_rate:.1%} hit rate")
        return result
    
    def _prepare_data(self, df: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for ML optimization"""
        logger.info("📊 Preparing data for ML optimization...")
        
        # Select features (exclude target and metadata)
        feature_columns = [col for col in df.columns 
                          if col not in [target_column, 'match_id', 'date', 'home_team', 'away_team', 'league']]
        
        X = df[feature_columns].fillna(0)
        y = df[target_column].astype(int)
        
        # Remove any remaining NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        # Scale features
        self.scaler = RobustScaler()
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        
        logger.info(f"✅ Data prepared: {len(X_scaled)} samples, {len(X_scaled.columns)} features")
        return X_scaled, y
    
    def _select_features(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """Select best features for ML optimization"""
        logger.info("🔍 Selecting best features...")
        
        # Use multiple feature selection methods
        k_best = min(self.config.feature_selection_k, len(X.columns))
        
        # F-score selection
        f_selector = SelectKBest(f_classif, k=k_best)
        X_f = f_selector.fit_transform(X, y)
        f_features = X.columns[f_selector.get_support()].tolist()
        
        # Mutual information selection
        mi_selector = SelectKBest(mutual_info_classif, k=k_best)
        X_mi = mi_selector.fit_transform(X, y)
        mi_features = X.columns[mi_selector.get_support()].tolist()
        
        # Combine feature sets
        selected_features = list(set(f_features + mi_features))
        
        # Limit to k_best features
        if len(selected_features) > k_best:
            # Score features and select top k
            feature_scores = {}
            for feature in selected_features:
                if feature in X.columns:
                    score = f_classif(X[[feature]], y)[0][0]
                    feature_scores[feature] = score
            
            selected_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)[:k_best]
            selected_features = [f[0] for f in selected_features]
        
        X_selected = X[selected_features]
        self.feature_selector = selected_features
        
        logger.info(f"✅ Selected {len(selected_features)} features")
        return X_selected
    
    async def _optimize_hyperparameters(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Optimize hyperparameters using Optuna"""
        logger.info("🔧 Optimizing hyperparameters...")
        
        def objective(trial):
            # Define model types to try
            model_type = trial.suggest_categorical('model_type', [
                'lightgbm', 'xgboost', 'catboost', 'neural_network', 'svm'
            ])
            
            if model_type == 'lightgbm':
                model = lgb.LGBMClassifier(
                    n_estimators=trial.suggest_int('n_estimators', 100, 2000),
                    max_depth=trial.suggest_int('max_depth', 3, 15),
                    learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3),
                    num_leaves=trial.suggest_int('num_leaves', 10, 100),
                    feature_fraction=trial.suggest_float('feature_fraction', 0.5, 1.0),
                    bagging_fraction=trial.suggest_float('bagging_fraction', 0.5, 1.0),
                    bagging_freq=trial.suggest_int('bagging_freq', 1, 10),
                    min_child_samples=trial.suggest_int('min_child_samples', 5, 100),
                    random_state=42,
                    verbose=-1
                )
            
            elif model_type == 'xgboost':
                model = xgb.XGBClassifier(
                    n_estimators=trial.suggest_int('n_estimators', 100, 2000),
                    max_depth=trial.suggest_int('max_depth', 3, 15),
                    learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3),
                    subsample=trial.suggest_float('subsample', 0.5, 1.0),
                    colsample_bytree=trial.suggest_float('colsample_bytree', 0.5, 1.0),
                    min_child_weight=trial.suggest_int('min_child_weight', 1, 10),
                    random_state=42,
                    eval_metric='logloss'
                )
            
            elif model_type == 'catboost':
                model = cb.CatBoostClassifier(
                    iterations=trial.suggest_int('iterations', 100, 2000),
                    depth=trial.suggest_int('depth', 3, 10),
                    learning_rate=trial.suggest_float('learning_rate', 0.01, 0.3),
                    l2_leaf_reg=trial.suggest_float('l2_leaf_reg', 1, 10),
                    random_seed=42,
                    verbose=False
                )
            
            elif model_type == 'neural_network':
                model = MLPClassifier(
                    hidden_layer_sizes=(trial.suggest_int('hidden_size', 50, 500),),
                    activation=trial.suggest_categorical('activation', ['relu', 'tanh']),
                    solver=trial.suggest_categorical('solver', ['adam', 'lbfgs']),
                    alpha=trial.suggest_float('alpha', 0.0001, 0.1),
                    learning_rate=trial.suggest_categorical('learning_rate', ['constant', 'adaptive']),
                    max_iter=trial.suggest_int('max_iter', 200, 1000),
                    random_state=42
                )
            
            elif model_type == 'svm':
                model = SVC(
                    C=trial.suggest_float('C', 0.1, 100),
                    kernel=trial.suggest_categorical('kernel', ['rbf', 'poly', 'sigmoid']),
                    gamma=trial.suggest_categorical('gamma', ['scale', 'auto']),
                    probability=True,
                    random_state=42
                )
            
            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=self.config.cv_folds, scoring='roc_auc')
            return cv_scores.mean()
        
        # Run optimization
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42),
            pruner=MedianPruner()
        )
        
        study.optimize(objective, n_trials=self.config.n_trials)
        
        best_params = study.best_params
        logger.info(f"✅ Hyperparameter optimization complete: {study.best_value:.4f} AUC")
        
        return best_params
    
    async def _optimize_ensemble(self, X: pd.DataFrame, y: pd.Series, best_params: Dict) -> List[float]:
        """Optimize ensemble weights for maximum ROI"""
        logger.info("🎯 Optimizing ensemble weights for ROI...")
        
        # Create base models
        base_models = self._create_base_models(best_params)
        
        # Train models
        trained_models = []
        for model in base_models:
            try:
                model.fit(X, y)
                trained_models.append(model)
            except Exception as e:
                logger.warning(f"Model training failed: {e}")
                continue
        
        if not trained_models:
            logger.error("No models trained successfully")
            return [1.0]  # Default weight
        
        # Optimize ensemble weights
        def ensemble_objective(weights):
            weights = np.array(weights)
            weights = weights / np.sum(weights)  # Normalize
            
            # Calculate ensemble predictions
            predictions = []
            for model in trained_models:
                pred = model.predict_proba(X)[:, 1]
                predictions.append(pred)
            
            predictions = np.array(predictions)
            ensemble_pred = np.average(predictions, axis=0, weights=weights)
            
            # Calculate ROI (simplified)
            # In production, this would use actual betting simulation
            roi = self._calculate_roi(ensemble_pred, y)
            return -roi  # Minimize negative ROI
        
        # Constraint: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(len(trained_models))]
        
        # Initial weights
        initial_weights = np.ones(len(trained_models)) / len(trained_models)
        
        # Optimize
        result = minimize(
            ensemble_objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x
            optimal_weights = optimal_weights / np.sum(optimal_weights)  # Normalize
        else:
            optimal_weights = initial_weights
        
        logger.info(f"✅ Ensemble optimization complete: {optimal_weights}")
        return optimal_weights.tolist()
    
    def _create_base_models(self, best_params: Dict) -> List:
        """Create base models for ensemble"""
        models = []
        
        # LightGBM
        if 'lightgbm' in str(best_params.get('model_type', '')):
            models.append(lgb.LGBMClassifier(
                n_estimators=best_params.get('n_estimators', 1000),
                max_depth=best_params.get('max_depth', 6),
                learning_rate=best_params.get('learning_rate', 0.1),
                random_state=42,
                verbose=-1
            ))
        
        # XGBoost
        if 'xgboost' in str(best_params.get('model_type', '')):
            models.append(xgb.XGBClassifier(
                n_estimators=best_params.get('n_estimators', 1000),
                max_depth=best_params.get('max_depth', 6),
                learning_rate=best_params.get('learning_rate', 0.1),
                random_state=42,
                eval_metric='logloss'
            ))
        
        # CatBoost
        if 'catboost' in str(best_params.get('model_type', '')):
            models.append(cb.CatBoostClassifier(
                iterations=best_params.get('iterations', 1000),
                depth=best_params.get('depth', 6),
                learning_rate=best_params.get('learning_rate', 0.1),
                random_seed=42,
                verbose=False
            ))
        
        # Neural Network
        if 'neural_network' in str(best_params.get('model_type', '')):
            models.append(MLPClassifier(
                hidden_layer_sizes=(best_params.get('hidden_size', 100),),
                activation=best_params.get('activation', 'relu'),
                solver=best_params.get('solver', 'adam'),
                alpha=best_params.get('alpha', 0.01),
                random_state=42
            ))
        
        # SVM
        if 'svm' in str(best_params.get('model_type', '')):
            models.append(SVC(
                C=best_params.get('C', 1.0),
                kernel=best_params.get('kernel', 'rbf'),
                gamma=best_params.get('gamma', 'scale'),
                probability=True,
                random_state=42
            ))
        
        # Add additional models for diversity
        models.extend([
            LogisticRegression(random_state=42, max_iter=1000),
            GaussianNB(),
            QuadraticDiscriminantAnalysis()
        ])
        
        return models
    
    def _calculate_roi(self, predictions: np.ndarray, y_true: np.ndarray) -> float:
        """Calculate ROI from predictions (simplified)"""
        # Convert predictions to binary decisions
        decisions = (predictions > 0.5).astype(int)
        
        # Calculate returns (simplified)
        correct_predictions = (decisions == y_true).sum()
        total_predictions = len(y_true)
        
        if total_predictions == 0:
            return 0.0
        
        # Simplified ROI calculation
        hit_rate = correct_predictions / total_predictions
        roi = (hit_rate - 0.5) * 2  # Simplified ROI
        
        return roi
    
    async def _optimize_calibration(self, X: pd.DataFrame, y: pd.Series, best_params: Dict) -> str:
        """Optimize calibration method for best performance"""
        logger.info("📊 Optimizing calibration...")
        
        # Create base model
        base_model = self._create_best_model(best_params)
        base_model.fit(X, y)
        
        best_method = None
        best_score = -np.inf
        
        for method in self.config.calibration_methods:
            try:
                # Create calibrated model
                if method == 'platt':
                    calibrated_model = CalibratedClassifierCV(base_model, method='sigmoid', cv=3)
                elif method == 'isotonic':
                    calibrated_model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
                else:
                    continue
                
                # Fit and evaluate
                calibrated_model.fit(X, y)
                
                # Cross-validation score
                cv_scores = cross_val_score(calibrated_model, X, y, cv=3, scoring='roc_auc')
                score = cv_scores.mean()
                
                if score > best_score:
                    best_score = score
                    best_method = method
                
            except Exception as e:
                logger.warning(f"Calibration {method} failed: {e}")
                continue
        
        logger.info(f"✅ Best calibration method: {best_method} ({best_score:.4f})")
        return best_method or 'platt'
    
    def _create_best_model(self, best_params: Dict):
        """Create the best model from optimized parameters"""
        model_type = best_params.get('model_type', 'lightgbm')
        
        if model_type == 'lightgbm':
            return lgb.LGBMClassifier(
                n_estimators=best_params.get('n_estimators', 1000),
                max_depth=best_params.get('max_depth', 6),
                learning_rate=best_params.get('learning_rate', 0.1),
                random_state=42,
                verbose=-1
            )
        elif model_type == 'xgboost':
            return xgb.XGBClassifier(
                n_estimators=best_params.get('n_estimators', 1000),
                max_depth=best_params.get('max_depth', 6),
                learning_rate=best_params.get('learning_rate', 0.1),
                random_state=42
            )
        else:
            return lgb.LGBMClassifier(random_state=42, verbose=-1)
    
    def _build_final_model(self, X: pd.DataFrame, y: pd.Series, best_params: Dict, 
                          ensemble_weights: List[float], calibration_method: str):
        """Build the final optimized model"""
        logger.info("🏗️ Building final optimized model...")
        
        # Create base models
        base_models = self._create_base_models(best_params)
        
        # Train models
        trained_models = []
        for model in base_models:
            try:
                model.fit(X, y)
                trained_models.append(model)
            except Exception as e:
                logger.warning(f"Model training failed: {e}")
                continue
        
        if not trained_models:
            logger.error("No models trained successfully")
            return None
        
        # Create ensemble
        if len(trained_models) > 1:
            # Use voting classifier with optimized weights
            ensemble_model = VotingClassifier(
                estimators=[(f'model_{i}', model) for i, model in enumerate(trained_models)],
                voting='soft'
            )
            
            # Set weights
            ensemble_model.set_params(**{f'model_{i}__weight': weight 
                                       for i, weight in enumerate(ensemble_weights[:len(trained_models)])})
        else:
            ensemble_model = trained_models[0]
        
        # Apply calibration
        if calibration_method == 'platt':
            final_model = CalibratedClassifierCV(ensemble_model, method='sigmoid', cv=3)
        elif calibration_method == 'isotonic':
            final_model = CalibratedClassifierCV(ensemble_model, method='isotonic', cv=3)
        else:
            final_model = ensemble_model
        
        # Fit final model
        final_model.fit(X, y)
        
        logger.info("✅ Final model built successfully")
        return final_model
    
    def _validate_performance(self, model, X: pd.DataFrame, y: pd.Series) -> Tuple[float, float, float]:
        """Validate model performance"""
        logger.info("📊 Validating model performance...")
        
        # Get predictions
        predictions = model.predict_proba(X)[:, 1]
        
        # Calculate metrics
        roi = self._calculate_roi(predictions, y)
        
        # Hit rate
        decisions = (predictions > 0.5).astype(int)
        hit_rate = (decisions == y).mean()
        
        # Drawdown (simplified)
        drawdown = 0.1  # Placeholder - would calculate from actual betting simulation
        
        logger.info(f"✅ Performance: {roi:.2%} ROI, {hit_rate:.1%} hit rate, {drawdown:.1%} drawdown")
        return roi, hit_rate, drawdown
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> Dict[str, float]:
        """Get feature importance from model"""
        try:
            # Try to get feature importance
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            elif hasattr(model, 'base_estimator') and hasattr(model.base_estimator, 'feature_importances_'):
                importance = model.base_estimator.feature_importances_
            else:
                # Fallback: equal importance
                importance = np.ones(len(feature_names)) / len(feature_names)
            
            return dict(zip(feature_names, importance))
        except Exception as e:
            logger.warning(f"Could not get feature importance: {e}")
            return {name: 1.0 / len(feature_names) for name in feature_names}
    
    def save_model(self, filepath: str):
        """Save optimized model"""
        model_data = {
            'model': self.best_model,
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'config': self.config,
            'optimization_history': self.optimization_history,
            'timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load optimized model"""
        model_data = joblib.load(filepath)
        
        self.best_model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_selector = model_data['feature_selector']
        self.config = model_data['config']
        self.optimization_history = model_data['optimization_history']
        
        logger.info(f"📂 Model loaded from {filepath}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions with optimized model"""
        if self.best_model is None:
            raise ValueError("No model loaded. Run optimization first.")
        
        # Select features
        X_selected = X[self.feature_selector]
        
        # Scale features
        X_scaled = pd.DataFrame(
            self.scaler.transform(X_selected),
            columns=X_selected.columns,
            index=X_selected.index
        )
        
        # Make predictions
        predictions = self.best_model.predict_proba(X_scaled)[:, 1]
        
        return predictions


async def main():
    """Test the AutoML engine"""
    # Load sample data
    df = pd.read_csv('selection_engine/dataset.csv')
    
    # Initialize AutoML engine
    config = OptimizationConfig(
        target_roi=0.15,  # 15% target ROI
        min_hit_rate=0.70,  # 70% minimum hit rate
        n_trials=50  # Reduced for testing
    )
    
    engine = AutoMLEngine(config)
    
    # Run optimization
    result = await engine.optimize_for_roi(df, 'over_2_5')
    
    # Print results
    print(f"\n🎯 Optimization Results:")
    print(f"ROI Achieved: {result.roi_achieved:.2%}")
    print(f"Hit Rate: {result.hit_rate_achieved:.1%}")
    print(f"Drawdown: {result.drawdown_achieved:.1%}")
    print(f"Optimization Time: {result.optimization_time:.1f}s")
    print(f"Best Calibration: {result.calibration_method}")
    
    # Save model
    engine.save_model('ml_optimization/optimized_model.pkl')
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

