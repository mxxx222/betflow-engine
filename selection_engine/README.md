# 🎯 Selection Engine - OU 2.5 with 70%+ Hit Rate

## 📋 Overview

Advanced selection engine for football Over/Under 2.5 markets targeting **70%+ hit rate** through:

- **Profile A**: Weekend top-5 leagues (high liquidity, best CLV signals)
- **Profile B**: UCL (lineup impact, cutoff -75 to -30 min)
- **Confidence buckets**: 70-74%, 75-79%, 80%+ with edge requirements
- **Conservative staking**: Kelly Criterion (25% of full Kelly, 2% max stake)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Pipeline │    │  Model Training │    │ Selection Logic │
│   (3-5 seasons) │───▶│ (LGBM + XGBoost)│───▶│ (70%+ confidence)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Live Pipeline  │
                    │ (Render + n8n)  │
                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Full Pipeline

```bash
python main.py --mode full
```

### 3. Run Individual Components

```bash
# Data pipeline only
python main.py --mode data

# Model training only
python main.py --mode train

# Backtesting only
python main.py --mode backtest

# Live pipeline
python main.py --mode live
```

## 📊 Data Pipeline

### Dataset Structure

- **3-5 seasons** of historical data
- **Top-5 leagues**: Premier League, La Liga, Bundesliga, Serie A, Ligue 1
- **UCL**: All phases (group stage to final)
- **Labels**: OU 2.5 Over/Under with actual goals
- **Tags**: `weekend_round`, `UCL`, `top5_leagues`

### Feature Groups

#### Team Statistics

- Rolling xG/xGA (5-10 matches)
- Finishing/shot quality metrics
- Set-piece xG percentage
- Cards and tempo indicators

#### Context Features

- Rest days (home vs away advantage)
- Travel distance (geographical impact)
- Weather extremes
- Referee card tendencies

#### Market Features

- Opening → closing drift
- Odds consensus vs deviation
- Limit proxy indicators
- Market volatility

#### Squad Features

- Injuries and suspensions
- Key player availability (ELO/min value)
- UCL rotation patterns
- Lineup confirmation status

## 🧠 Model Training

### Base Models

- **LightGBM**: Gradient boosting with early stopping
- **XGBoost**: Extreme gradient boosting
- **Ensemble**: Simple average + rank blending

### Calibration

- **Platt Scaling**: Sigmoid calibration
- **Isotonic Regression**: Non-parametric calibration
- **Per-profile**: Separate calibration for weekend vs UCL

### Feature Engineering

- **Leakage prevention**: No future data
- **Drift detection**: PSI/KS tests
- **Feature selection**: Importance-based filtering

## 🎯 Selection Logic

### Confidence Buckets

```python
# Edge requirements by confidence
BUCKET_70_74 = {"edge_min": 0.03, "selections": "1-2 per round"}
BUCKET_75_79 = {"edge_min": 0.04, "selections": "1-3 per round"}
BUCKET_80_PLUS = {"edge_min": 0.05, "selections": "0-1 per round"}
```

### Selection Criteria

```python
# Must meet ALL criteria
confidence >= 0.70
edge >= edge_min_for_bucket
clv >= 0.02  # 2% minimum closing line value
lineup_confirmed = True  # For UCL
market_drift_1h <= 0.05  # 5% max drift
odds_range = [1.5, 3.0]  # Reasonable odds
```

### Staking Rules

```python
# Kelly Criterion (conservative)
kelly_fraction = 0.25  # 25% of full Kelly
max_stake = 0.02  # 2% of bankroll
stop_loss = 0.10  # 10% drawdown
```

## 🧪 Backtesting

### Walk-Forward Validation

- **Weekly rounds**: Time series cross-validation
- **Historical training**: Up to current week
- **Out-of-sample testing**: Current week only
- **Performance tracking**: Hit rate, ROI, CLV, drawdown

### Metrics

- **Hit Rate**: Percentage of winning selections
- **ROI**: Return on investment
- **CLV**: Closing Line Value
- **Sharpe Ratio**: Risk-adjusted returns
- **Calmar Ratio**: Return vs max drawdown

### Expected Performance

- **Hit Rate**: 70%+ for qualified selections
- **ROI**: 5-15% monthly (conservative staking)
- **Max Drawdown**: <15%
- **Selections**: 1-5 per round (highly selective)

## 🚀 Live Pipeline

### Deployment (Render)

```bash
# Deploy to Render
python main.py --mode live
```

### Scheduler

- **D-1h**: Recompute selections (1 hour before matches)
- **D-30min**: Final recompute (30 minutes before)
- **Daily**: Performance metrics update

### Gatekeeper Logic

```python
# Only publish if ALL conditions met
confidence >= 0.75  # Higher threshold for live
edge >= 0.04  # 4% minimum edge
clv >= 0.02  # 2% minimum CLV
lineup_confirmed = True  # UCL requirement
market_stable = True  # No excessive drift
odds_reasonable = True  # 1.5-3.0 range
```

### Alerts (Slack/Telegram)

```
🎯 Qualified Selection - 80%+ Confidence

Manchester United vs Liverpool
• Selection: OVER
• Confidence: 82%
• Edge: 6.2%
• CLV: 3.1%
• Stake: 1.8% ($180)
• Odds: 2.15
• Cutoff: 14:30
• League: PREMIER-LEAGUE
```

## 📈 Performance Monitoring

### Dashboard Metrics

- **Selection Funnel**: Candidate → Qualified → Placed → CLV
- **Hit Rate by Bucket**: 70-74%, 75-79%, 80%+
- **ROI by Bucket**: Performance per confidence level
- **Kelly vs Flat**: Stake comparison
- **Feature Drift**: Model stability monitoring
- **Lineup Coverage**: UCL availability tracking

### Weekly Reports

```
📊 Weekly Round Report - 2024-W15

Profile A (Weekend Top-5):
• Selections: 3
• Wins: 2
• Hit Rate: 66.7%
• ROI: 8.2%

Profile B (UCL):
• Selections: 1
• Wins: 1
• Hit Rate: 100%
• ROI: 12.5%

Overall:
• Total Selections: 4
• Overall Hit Rate: 75%
• Overall ROI: 9.1%
• Max Drawdown: 3.2%
```

## 🔧 Configuration

### Selection Criteria

```python
SelectionCriteria(
    min_confidence=0.70,
    edge_min_bucket_70_74=0.03,
    edge_min_bucket_75_79=0.04,
    edge_min_bucket_80_plus=0.05,
    clv_min=0.02,
    max_selections_per_round=5,
    max_selections_per_profile=3,
    kelly_fraction=0.25,
    max_stake_percentage=0.02,
    stop_loss_percentage=0.10
)
```

### Profile Settings

```python
PROFILE_A = {
    "name": "Weekend Top-5",
    "leagues": ["premier-league", "la-liga", "bundesliga", "serie-a", "ligue-1"],
    "days": ["saturday", "sunday"],
    "lineup_required": False,
    "cutoff_hours": 1
}

PROFILE_B = {
    "name": "UCL",
    "leagues": ["ucl"],
    "days": ["tuesday", "wednesday"],
    "lineup_required": True,
    "cutoff_hours": 0.5
}
```

## 🚨 Risk Management

### Conservative Approach

- **Max 3-5 selections per round** (highly selective)
- **2% max stake per bet** (bankroll protection)
- **10% stop loss** (drawdown control)
- **Kelly Criterion** (mathematical optimization)
- **Profile limits** (diversification)

### Monitoring

- **Real-time drawdown** tracking
- **Feature drift** detection
- **Model performance** monitoring
- **Market stability** checks

## 📊 Expected Results

### Conservative Targets

- **Hit Rate**: 70%+ (qualified selections only)
- **Monthly ROI**: 2-5% (conservative staking)
- **Max Drawdown**: <15%
- **Selections**: 1-5 per round
- **Payback**: <3 months (if high-liquidity focus)

### League Performance

- **Premier League**: 8-12% ROI (highest liquidity)
- **Bundesliga**: 6-10% ROI (consistent)
- **UCL**: 5-8% ROI (lineup dependent)
- **Championship**: 4-7% ROI (moderate)
- **Serie A/La Liga**: 3-6% ROI (variable)

## 🔄 Development Workflow

### 1. Data Collection

```bash
python main.py --mode data
# Generates: selection_engine/dataset.csv
```

### 2. Model Training

```bash
python main.py --mode train
# Generates: selection_engine/models.pkl
```

### 3. Backtesting

```bash
python main.py --mode backtest
# Generates: selection_engine/backtest_report.md
# Generates: selection_engine/performance_plots.png
```

### 4. Live Deployment

```bash
python main.py --mode live
# Deploys to Render with n8n workflows
```

## 📚 Documentation

### Key Files

- `data_pipeline.py`: Dataset construction
- `model_training.py`: ML model training
- `selection_logic.py`: Selection criteria
- `backtesting.py`: Walk-forward validation
- `live_pipeline.py`: Production deployment
- `main.py`: Orchestration runner

### Reports Generated

- `dataset.csv`: Historical match data
- `models.pkl`: Trained models
- `backtest_report.md`: Performance analysis
- `performance_plots.png`: Visualization
- `final_report.md`: Complete analysis

## ⚠️ Important Notes

### Compliance

- **Analytics-only operation**
- **No betting facilitation**
- **Educational purpose**
- **Risk warnings displayed**

### Performance

- **Past performance** does not guarantee future results
- **Market conditions** can change
- **Model performance** may degrade over time
- **Regular retraining** recommended

### Risk Warnings

- **High confidence** does not guarantee wins
- **Edge requirements** may limit opportunities
- **Market efficiency** can reduce advantages
- **Bankroll management** is critical

---

**🎯 Target**: 70%+ hit rate through conservative selection and risk management for football Over/Under 2.5 markets.
