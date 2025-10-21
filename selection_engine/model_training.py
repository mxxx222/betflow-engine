"""
Selection Engine Model Training
Gradient boosted trees with logistic calibration for 70%+ hit rate targeting
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from sklearn.calibration import CalibratedClassifierCV, PlattScaling, IsotonicRegression
import lightgbm as lgb
import xgboost as xgb
from typing import Dict, List, Tuple, Optional
import logging
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelectionEngineModel:
    """Selection engine model with calibration and ensemble methods"""
    
    def __init__(self):
        self.models = {}
        self.calibrators = {}
        self.feature_importance = {}
        self.profiles = ['profile_a', 'profile_b']  # Weekend top-5, UCL
        
    def train_models(self, df: pd.DataFrame) -> Dict:
        """Train models for each profile and target"""
        logger.info("Training selection engine models...")
        
        results = {}
        
        for profile in self.profiles:
            logger.info(f"Training models for {profile}")
            
            # Filter data for profile
            profile_data = df[df[profile] == 1].copy()
            
            if len(profile_data) < 100:
                logger.warning(f"Insufficient data for {profile}: {len(profile_data)} matches")
                continue
            
            # Train models for both Over and Under
            for target in ['over_2_5', 'under_2_5']:
                model_key = f"{profile}_{target}"
                logger.info(f"Training {model_key} model")
                
                # Prepare features and target
                X, y = self._prepare_training_data(profile_data, target)
                
                if len(X) < 50:
                    logger.warning(f"Insufficient data for {model_key}: {len(X)} samples")
                    continue
                
                # Train base models
                base_models = self._train_base_models(X, y, model_key)
                
                # Calibrate models
                calibrated_models = self._calibrate_models(base_models, X, y, model_key)
                
                # Store results
                self.models[model_key] = calibrated_models
                results[model_key] = {
                    'n_samples': len(X),
                    'n_features': X.shape[1],
                    'base_models': list(base_models.keys()),
                    'calibrated': True
                }
        
        return results
    
    def _prepare_training_data(self, df: pd.DataFrame, target: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data with feature selection"""
        # Feature groups
        feature_groups = {
            'team_stats': [
                'home_xg', 'away_xg', 'home_xga', 'away_xga',
                'home_strength', 'away_strength', 'strength_diff'
            ],
            'form': [
                'home_form_5', 'away_form_5', 'home_form_10', 'away_form_10',
                'form_diff_5', 'form_diff_10'
            ],
            'context': [
                'home_rest_days', 'away_rest_days', 'rest_advantage',
                'home_travel_distance', 'away_travel_distance',
                'home_squad_issues', 'away_squad_issues', 'squad_issues_diff'
            ],
            'pace': [
                'home_pace', 'away_pace', 'pace_diff', 'total_pace'
            ],
            'market': [
                'market_drift_24h', 'market_drift_1h', 'market_drift_total',
                'odds_volatility', 'implied_over_prob', 'implied_under_prob',
                'vig_corrected_over_prob', 'vig_corrected_under_prob'
            ],
            'context_advanced': [
                'weather_impact', 'lineup_confirmed'
            ]
        }
        
        # Select features
        features = []
        for group, feature_list in feature_groups.items():
            available_features = [f for f in feature_list if f in df.columns]
            features.extend(available_features)
        
        # Add profile-specific features
        if 'profile_a' in df.columns:
            features.extend(['is_weekend', 'is_top5'])
        if 'profile_b' in df.columns:
            features.extend(['is_ucl'])
        
        # Prepare X and y
        X = df[features].fillna(0)
        y = df[target].astype(int)
        
        # Remove any remaining NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Prepared {len(X)} samples with {len(features)} features for {target}")
        return X, y
    
    def _train_base_models(self, X: pd.DataFrame, y: pd.Series, model_key: str) -> Dict:
        """Train base gradient boosted models"""
        models = {}
        
        # LightGBM
        lgb_params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        lgb_model = lgb.LGBMClassifier(**lgb_params, n_estimators=1000)
        lgb_model.fit(X, y, eval_set=[(X, y)], callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)])
        models['lgb'] = lgb_model
        
        # XGBoost
        xgb_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.9,
            'random_state': 42,
            'n_estimators': 1000
        }
        
        xgb_model = xgb.XGBClassifier(**xgb_params)
        xgb_model.fit(X, y, eval_set=[(X, y)], early_stopping_rounds=100, verbose=False)
        models['xgb'] = xgb_model
        
        # Store feature importance
        self.feature_importance[model_key] = {
            'lgb': dict(zip(X.columns, lgb_model.feature_importances_)),
            'xgb': dict(zip(X.columns, xgb_model.feature_importances_))
        }
        
        return models
    
    def _calibrate_models(self, base_models: Dict, X: pd.DataFrame, y: pd.Series, model_key: str) -> Dict:
        """Calibrate models using Platt scaling and Isotonic regression"""
        calibrated_models = {}
        
        for model_name, model in base_models.items():
            # Platt scaling
            platt_calibrator = CalibratedClassifierCV(model, method='sigmoid', cv=3)
            platt_calibrator.fit(X, y)
            
            # Isotonic regression
            isotonic_calibrator = CalibratedClassifierCV(model, method='isotonic', cv=3)
            isotonic_calibrator.fit(X, y)
            
            calibrated_models[f"{model_name}_platt"] = platt_calibrator
            calibrated_models[f"{model_name}_isotonic"] = isotonic_calibrator
        
        return calibrated_models
    
    def predict_probabilities(self, X: pd.DataFrame, profile: str, target: str) -> Dict[str, float]:
        """Get calibrated probabilities from ensemble"""
        model_key = f"{profile}_{target}"
        
        if model_key not in self.models:
            logger.warning(f"No model found for {model_key}")
            return {'over_prob': 0.5, 'under_prob': 0.5}
        
        models = self.models[model_key]
        predictions = {}
        
        # Get predictions from all calibrated models
        for model_name, model in models.items():
            try:
                prob = model.predict_proba(X)[0][1]  # Probability of positive class
                predictions[model_name] = prob
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
                predictions[model_name] = 0.5
        
        # Ensemble prediction (simple average)
        if predictions:
            ensemble_prob = np.mean(list(predictions.values()))
        else:
            ensemble_prob = 0.5
        
        # Return probabilities for both outcomes
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
    
    def get_feature_importance(self, model_key: str) -> Dict:
        """Get feature importance for a model"""
        return self.feature_importance.get(model_key, {})
    
    def save_models(self, filepath: str):
        """Save trained models"""
        model_data = {
            'models': self.models,
            'feature_importance': self.feature_importance,
            'timestamp': datetime.now().isoformat()
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models"""
        model_data = joblib.load(filepath)
        self.models = model_data['models']
        self.feature_importance = model_data['feature_importance']
        logger.info(f"Models loaded from {filepath}")


class ModelEvaluator:
    """Evaluate model performance and calibration"""
    
    def __init__(self):
        self.results = {}
    
    def evaluate_models(self, df: pd.DataFrame, models: Dict) -> Dict:
        """Evaluate all models with time series cross-validation"""
        logger.info("Evaluating models...")
        
        results = {}
        
        for profile in ['profile_a', 'profile_b']:
            profile_data = df[df[profile] == 1].copy()
            
            if len(profile_data) < 100:
                continue
            
            for target in ['over_2_5', 'under_2_5']:
                model_key = f"{profile}_{target}"
                
                if model_key not in models:
                    continue
                
                # Prepare data
                X, y = self._prepare_evaluation_data(profile_data, target)
                
                if len(X) < 50:
                    continue
                
                # Time series cross-validation
                tscv = TimeSeriesSplit(n_splits=5)
                scores = self._cross_validate_models(models[model_key], X, y, tscv)
                
                results[model_key] = scores
        
        return results
    
    def _prepare_evaluation_data(self, df: pd.DataFrame, target: str) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for evaluation"""
        # Same feature preparation as training
        feature_groups = {
            'team_stats': ['home_xg', 'away_xg', 'home_xga', 'away_xga', 'home_strength', 'away_strength', 'strength_diff'],
            'form': ['home_form_5', 'away_form_5', 'home_form_10', 'away_form_10', 'form_diff_5', 'form_diff_10'],
            'context': ['home_rest_days', 'away_rest_days', 'rest_advantage', 'home_travel_distance', 'away_travel_distance'],
            'market': ['market_drift_24h', 'market_drift_1h', 'implied_over_prob', 'implied_under_prob']
        }
        
        features = []
        for group, feature_list in feature_groups.items():
            available_features = [f for f in feature_list if f in df.columns]
            features.extend(available_features)
        
        X = df[features].fillna(0)
        y = df[target].astype(int)
        
        mask = ~(X.isna().any(axis=1) | y.isna())
        return X[mask], y[mask]
    
    def _cross_validate_models(self, models: Dict, X: pd.DataFrame, y: pd.Series, cv) -> Dict:
        """Cross-validate models"""
        scores = {}
        
        for model_name, model in models.items():
            try:
                # Get cross-validation scores
                cv_scores = cross_val_score(model, X, y, cv=cv, scoring='neg_log_loss')
                scores[model_name] = {
                    'log_loss': -cv_scores.mean(),
                    'log_loss_std': cv_scores.std(),
                    'cv_scores': cv_scores.tolist()
                }
            except Exception as e:
                logger.error(f"Error evaluating {model_name}: {e}")
                scores[model_name] = {'error': str(e)}
        
        return scores


def main():
    """Train and evaluate selection engine models"""
    # Load dataset
    df = pd.read_csv('selection_engine/dataset.csv')
    logger.info(f"Loaded dataset with {len(df)} matches")
    
    # Train models
    model_trainer = SelectionEngineModel()
    training_results = model_trainer.train_models(df)
    
    # Evaluate models
    evaluator = ModelEvaluator()
    evaluation_results = evaluator.evaluate_models(df, model_trainer.models)
    
    # Save models
    model_trainer.save_models('selection_engine/models.pkl')
    
    # Print results
    print("\n📊 Model Training Results:")
    for model_key, result in training_results.items():
        print(f"{model_key}: {result['n_samples']} samples, {result['n_features']} features")
    
    print("\n📈 Model Evaluation Results:")
    for model_key, scores in evaluation_results.items():
        print(f"\n{model_key}:")
        for model_name, score in scores.items():
            if 'log_loss' in score:
                print(f"  {model_name}: {score['log_loss']:.4f} ± {score['log_loss_std']:.4f}")
    
    return model_trainer, evaluation_results


if __name__ == "__main__":
    main()
