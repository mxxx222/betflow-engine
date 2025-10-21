# 🤖 ML Optimization Engine - High ROI Targeting

## 📋 Overview

Automated ML optimization system for high ROI targeting with automatic calibration and result validation. Designed for **70%+ hit rate** and **15%+ ROI** through advanced machine learning techniques.

## 🎯 Key Features

### **Automated ML Optimization**
- **Hyperparameter tuning** with Optuna (TPE sampler)
- **Model ensemble** optimization (LGBM, XGBoost, CatBoost, Neural Networks, SVM)
- **Feature selection** with multiple methods (F-score, mutual information)
- **ROI targeting** optimization with custom loss functions

### **Automatic Calibration**
- **Multiple calibration methods** (Platt scaling, Isotonic regression)
- **Drift detection** with performance monitoring
- **Continuous recalibration** based on performance thresholds
- **Reliability scoring** for model confidence

### **Result Validation**
- **Comprehensive metrics** (Accuracy, Precision, Recall, F1, AUC, Brier score)
- **Performance trending** with historical analysis
- **Alert system** for performance degradation
- **Auto-retrain triggers** for model maintenance

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  ML Optimization│    │ Auto Calibration│    │ Result Validation│
│  (Optuna +      │───▶│ (Platt +        │───▶│ (Metrics +      │
│   Ensemble)     │    │  Isotonic)      │    │  Trending)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Feedback Loop  │
                    │ (Auto-retrain)  │
                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Full Optimization
```bash
python main.py --mode full --data ../selection_engine/dataset.csv
```

### 3. Run Individual Components
```bash
# ML optimization only
python main.py --mode optimize --data ../selection_engine/dataset.csv

# Calibration only
python main.py --mode calibrate --model optimized_model.pkl --data ../selection_engine/dataset.csv

# Validation only
python main.py --mode validate --model optimized_model.pkl --data ../selection_engine/dataset.csv
```

## 📊 ML Optimization Engine

### **Hyperparameter Optimization**
```python
# Optuna-based optimization
study = optuna.create_study(
    direction='maximize',
    sampler=TPESampler(seed=42),
    pruner=MedianPruner()
)

# Models optimized:
- LightGBM: n_estimators, max_depth, learning_rate, num_leaves
- XGBoost: n_estimators, max_depth, learning_rate, subsample
- CatBoost: iterations, depth, learning_rate, l2_leaf_reg
- Neural Networks: hidden_size, activation, solver, alpha
- SVM: C, kernel, gamma
```

### **Ensemble Optimization**
```python
# Weight optimization for ensemble
def ensemble_objective(weights):
    ensemble_pred = np.average(predictions, axis=0, weights=weights)
    roi = calculate_roi(ensemble_pred, y_true)
    return -roi  # Minimize negative ROI

# Constraint: weights sum to 1
constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
```

### **Feature Selection**
```python
# Multiple feature selection methods
- F-score selection (SelectKBest with f_classif)
- Mutual information selection (SelectKBest with mutual_info_classif)
- Combined feature sets with importance scoring
- Top-k feature selection based on scores
```

## 📈 Automatic Calibration

### **Calibration Methods**
- **Platt Scaling**: Sigmoid calibration with cross-validation
- **Isotonic Regression**: Non-parametric calibration
- **Drift Detection**: PSI/KS tests for model stability

### **Reliability Scoring**
```python
def calculate_reliability_score(model, X, y):
    predictions = model.predict_proba(X)[:, 1]
    brier_score = brier_score_loss(y, predictions)
    reliability = 1 - brier_score  # Convert to reliability
    return max(0, reliability)
```

### **Continuous Monitoring**
- **Performance thresholds**: Target reliability >95%
- **Drift detection**: Performance drop >5%
- **Auto-recalibration**: When thresholds exceeded
- **Calibration curves**: Visual validation of probability calibration

## 🔍 Result Validation

### **Comprehensive Metrics**
```python
metrics = {
    'accuracy': accuracy_score(y_true, y_pred),
    'precision': precision_score(y_true, y_pred, average='weighted'),
    'recall': recall_score(y_true, y_pred, average='weighted'),
    'f1': f1_score(y_true, y_pred, average='weighted'),
    'auc': roc_auc_score(y_true, y_proba),
    'brier_score': brier_score_loss(y_true, y_proba),
    'hit_rate_0.5': hit_rate_at_threshold(y_true, y_proba, 0.5),
    'hit_rate_0.7': hit_rate_at_threshold(y_true, y_proba, 0.7),
    'hit_rate_0.8': hit_rate_at_threshold(y_true, y_proba, 0.8),
    'roi_0.7': simulate_roi(y_true, y_proba, threshold=0.7),
    'roi_0.8': simulate_roi(y_true, y_proba, threshold=0.8)
}
```

### **Performance Trending**
- **Historical analysis**: 30-day rolling window
- **Performance alerts**: Threshold-based notifications
- **Auto-retrain triggers**: 15% performance drop threshold
- **Confidence scoring**: Overall model confidence assessment

### **ROI Simulation**
```python
def simulate_roi(predictions, y_true, threshold=0.7, odds=2.0):
    high_conf_mask = predictions >= threshold
    if high_conf_mask.sum() == 0:
        return 0.0
    
    hit_rate = (predictions[high_conf_mask] > 0.5) == y_true[high_conf_mask]
    hit_rate = hit_rate.mean()
    
    # Simulate ROI
    roi = (hit_rate * (odds - 1) - (1 - hit_rate)) * 100
    return roi
```

## 🎯 Target Performance

### **Optimization Targets**
- **ROI**: 15%+ target ROI
- **Hit Rate**: 70%+ for qualified selections
- **Reliability**: 95%+ calibration reliability
- **AUC**: 75%+ for model discrimination
- **Brier Score**: <0.25 for probability calibration

### **Performance Thresholds**
```python
performance_thresholds = {
    'min_accuracy': 0.70,
    'min_precision': 0.65,
    'min_recall': 0.60,
    'min_f1': 0.62,
    'min_auc': 0.75,
    'max_brier': 0.25
}
```

### **Alert Thresholds**
```python
alert_thresholds = {
    'accuracy_drop': 0.05,
    'precision_drop': 0.05,
    'recall_drop': 0.05,
    'f1_drop': 0.05,
    'auc_drop': 0.03,
    'brier_increase': 0.05
}
```

## 📊 Usage Examples

### **Full Pipeline**
```python
# Run complete optimization pipeline
runner = MLOptimizationRunner()
result = await runner.run_full_optimization(df, 'over_2_5')

# Results include:
# - Optimized model with best hyperparameters
# - Calibrated probabilities
# - Performance validation
# - Comprehensive report
```

### **Individual Components**
```python
# ML optimization only
optimization_result = await runner.run_optimization_only(df, 'over_2_5')

# Calibration only
calibration_result = await runner.run_calibration_only('model.pkl', df, 'over_2_5')

# Validation only
validation_result = await runner.run_validation_only('model.pkl', df, 'over_2_5')
```

### **Custom Configuration**
```python
# Custom optimization config
config = OptimizationConfig(
    target_roi=0.20,  # 20% target ROI
    min_hit_rate=0.75,  # 75% minimum hit rate
    n_trials=200,  # More optimization trials
    cv_folds=10  # More cross-validation folds
)

engine = AutoMLEngine(config)
result = await engine.optimize_for_roi(df, 'over_2_5')
```

## 📈 Expected Results

### **Optimization Performance**
- **ROI Achievement**: 15-25% (depending on data quality)
- **Hit Rate**: 70-80% (for high-confidence selections)
- **Model Performance**: 75-85% AUC
- **Calibration**: 95%+ reliability score

### **Validation Metrics**
- **Accuracy**: 70-80%
- **Precision**: 65-75%
- **Recall**: 60-70%
- **F1 Score**: 62-72%
- **Brier Score**: 0.15-0.25

### **ROI by Confidence Threshold**
- **70% threshold**: 5-15% ROI
- **80% threshold**: 10-20% ROI
- **90% threshold**: 15-25% ROI

## 🔧 Configuration

### **Optimization Config**
```python
OptimizationConfig(
    target_roi=0.15,  # 15% target ROI
    min_hit_rate=0.70,  # 70% minimum hit rate
    max_drawdown=0.20,  # 20% maximum drawdown
    n_trials=100,  # Number of optimization trials
    cv_folds=5,  # Cross-validation folds
    feature_selection_k=50,  # Number of features to select
    ensemble_size=10  # Number of models in ensemble
)
```

### **Calibration Config**
```python
CalibrationConfig(
    recalibration_frequency=7,  # Days between recalibration
    min_samples_for_calibration=100,  # Minimum samples needed
    target_reliability=0.95,  # Target reliability score
    drift_threshold=0.05,  # Drift detection threshold
    performance_threshold=0.70  # Minimum performance threshold
)
```

### **Validation Config**
```python
ValidationConfig(
    validation_window=30,  # Days to look back for validation
    min_samples_for_validation=50,  # Minimum samples needed
    auto_retrain_threshold=0.15  # Performance drop threshold for auto-retrain
)
```

## 📊 Reports Generated

### **Comprehensive Report**
- **Executive Summary**: Key performance indicators
- **Optimization Results**: Best model and parameters
- **Calibration Results**: Reliability and drift detection
- **Validation Results**: Performance metrics and alerts
- **Feature Importance**: Top 10 most important features
- **Recommendations**: Next steps and actions

### **Performance Plots**
- **Performance Trends**: Accuracy, AUC, F1 over time
- **Calibration Curve**: Probability calibration visualization
- **ROI by Threshold**: ROI simulation for different confidence levels
- **Hit Rate Analysis**: Hit rates by confidence threshold
- **Feature Importance**: Top features ranked by importance

## 🚨 Monitoring & Alerts

### **Performance Alerts**
- **Critical**: Accuracy <60%, AUC <60%, Brier >0.4
- **Warning**: Performance drops >5%
- **Info**: Model drift detected, recalibration needed

### **Auto-Retrain Triggers**
- **Performance drop**: 15% average performance decrease
- **Drift detection**: Significant model drift
- **Threshold breaches**: Multiple metric thresholds exceeded

### **Continuous Monitoring**
- **Daily validation**: Automatic performance checks
- **Weekly recalibration**: Model recalibration if needed
- **Monthly optimization**: Full model reoptimization

## 🔄 Feedback Loop

### **Automatic Optimization**
1. **Performance monitoring** → Detect degradation
2. **Alert generation** → Notify of issues
3. **Auto-retrain trigger** → Initiate retraining
4. **Model update** → Deploy improved model
5. **Validation** → Confirm improvement

### **Continuous Improvement**
- **Data drift detection**: Monitor input data changes
- **Model drift detection**: Monitor prediction quality
- **Performance trending**: Track long-term performance
- **Automated retraining**: Trigger retraining when needed

## 📚 Documentation

### **Key Files**
- `auto_ml_engine.py`: ML optimization with Optuna
- `auto_calibration.py`: Automatic model calibration
- `result_validation.py`: Performance validation and monitoring
- `main.py`: Orchestration runner

### **Generated Files**
- `optimized_model.pkl`: Best optimized model
- `calibration_data.pkl`: Calibration results
- `validation_data.pkl`: Validation results
- `comprehensive_report.md`: Complete analysis report
- `optimization_plots.png`: Performance visualizations

## ⚠️ Important Notes

### **Performance Expectations**
- **Past performance** does not guarantee future results
- **Market conditions** can affect model performance
- **Data quality** is critical for optimization success
- **Regular monitoring** is essential for maintaining performance

### **Risk Management**
- **Model validation** before deployment
- **Performance monitoring** in production
- **Automatic fallbacks** for model failures
- **Human oversight** for critical decisions

---

**🎯 Target**: 15%+ ROI through automated ML optimization with 70%+ hit rate and continuous calibration for football Over/Under 2.5 markets.
