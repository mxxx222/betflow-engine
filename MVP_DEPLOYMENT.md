# 🚀 BetFlow Engine MVP Deployment Guide

## 📋 Overview

This guide covers deploying the BetFlow Engine MVP to Render, focusing on **football Over/Under 2.5 markets** with conservative risk management and 2-5% monthly ROI targets.

## 🎯 MVP Focus

- **Sport**: Football (Soccer)
- **Market**: Over/Under 2.5 Goals
- **Strategy**: Pre-match analytics only
- **Target ROI**: 2-5% monthly with conservative staking
- **Risk Management**: 2% max stake, 10% stop loss, Kelly Criterion

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   n8n Worker    │    │   Next.js      │
│   (API)         │◄───┤   (Background)  │    │   (Dashboard)  │
│   Port: 8000    │    │   Port: 5678    │    │   Port: 3000   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Database)    │
                    └─────────────────┘
```

## 🚀 Quick Deploy to Render

### 1. Prerequisites

```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render auth login

# Set environment variables
export RENDER_API_TOKEN="your_render_api_token"
```

### 2. Deploy Services

```bash
# Clone repository
git clone https://github.com/mxxx222/betflow-engine.git
cd betflow-engine

# Deploy using script
python scripts/deploy_to_render.py
```

### 3. Manual Deployment (Alternative)

#### API Service
```yaml
# render.yaml
services:
  - type: web
    name: betflow-api
    env: python
    plan: starter
    buildCommand: |
      pip install -r api/requirements.txt
      pip install -r engine/requirements.txt
      alembic -c db/alembic.ini upgrade head
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

#### Worker Service
```yaml
  - type: worker
    name: betflow-worker
    env: python
    plan: starter
    buildCommand: |
      pip install -r api/requirements.txt
      pip install -r engine/requirements.txt
    startCommand: python -m n8n start
```

#### Web Service
```yaml
  - type: web
    name: betflow-web
    env: node
    plan: starter
    buildCommand: |
      cd web
      npm install
      npm run build
    startCommand: cd web && npm start
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/betflow

# Redis (for caching)
REDIS_URL=redis://host:6379

# API Keys (REQUIRED)
PROVIDERS_ODDS_API_KEY=your_odds_api_key
PROVIDERS_SPORTS_MONKS_KEY=your_sports_monks_key

# Security
JWT_SECRET=your_jwt_secret
API_RATE_LIMIT=100

# Worker
N8N_WEBHOOK_URL=https://betflow-worker.onrender.com/webhook
```

### API Keys Setup

1. **OddsAPI** (Primary)
   - Sign up at: https://the-odds-api.com/
   - Get API key from dashboard
   - Set `PROVIDERS_ODDS_API_KEY`

2. **SportsMonks** (Backup)
   - Sign up at: https://sportmonks.com/
   - Get API key from dashboard
   - Set `PROVIDERS_SPORTS_MONKS_KEY`

## 📊 MVP Endpoints

### Health Check
```bash
GET https://betflow-api.onrender.com/mvp/health
```

### Football Events
```bash
GET https://betflow-api.onrender.com/mvp/events/football?leagues=premier-league,championship
```

### Over/Under 2.5 Odds
```bash
GET https://betflow-api.onrender.com/mvp/odds/football/{event_id}?market=over_under_2_5
```

### Signals
```bash
POST https://betflow-api.onrender.com/mvp/signals/football
{
  "leagues": ["premier-league", "championship"],
  "min_edge": 0.02,
  "max_edge": 0.15
}
```

### Backtest Results
```bash
GET https://betflow-api.onrender.com/mvp/backtest/results?days=14
```

### Risk Limits
```bash
GET https://betflow-api.onrender.com/mvp/risk/limits
```

## 🔄 Data Collection Workflow

### 1. Odds Collection (Every 5 minutes)
```json
{
  "name": "Football OU 2.5 Odds Ingest",
  "schedule": "*/5 * * * *",
  "providers": ["OddsAPI", "SportsMonks"],
  "leagues": ["premier-league", "championship", "bundesliga"],
  "market": "over_under_2_5"
}
```

### 2. Signal Computation (Every 10 minutes)
```json
{
  "name": "Football OU 2.5 Signal Compute",
  "trigger": "after_odds_ingest",
  "models": ["ELO", "Poisson"],
  "market": "over_under_2_5"
}
```

## 📈 Risk Management

### Conservative Staking Rules
- **Max Stake**: 2% of bankroll per bet
- **Kelly Criterion**: 25% of full Kelly
- **Stop Loss**: 10% drawdown
- **Daily Limit**: £200 max stake
- **Weekly Limit**: £1000 max stake

### League-Specific Limits
```python
LEAGUE_RISK_LIMITS = {
    "premier-league": {"max_stake": 0.03, "min_confidence": 0.7},
    "championship": {"max_stake": 0.025, "min_confidence": 0.65},
    "bundesliga": {"max_stake": 0.025, "min_confidence": 0.65},
    "serie-a": {"max_stake": 0.025, "min_confidence": 0.65},
    "la-liga": {"max_stake": 0.025, "min_confidence": 0.65}
}
```

## 🧪 Backtesting

### Run 2-Week Backtest
```bash
python scripts/backtest_football_ou25.py
```

### Expected Results
- **Total Matches**: 150-200
- **Win Rate**: 55-65%
- **ROI**: 5-10%
- **Max Drawdown**: <15%
- **Avg Edge**: 3-5%

### League Performance
- **Premier League**: 8-12% ROI
- **Championship**: 5-8% ROI
- **Bundesliga**: 6-10% ROI
- **Serie A**: 4-7% ROI
- **La Liga**: 5-8% ROI

## 📊 Monitoring

### Key Metrics
- **Odds Update Frequency**: Every 5 minutes
- **Signal Generation**: Every 10 minutes
- **API Response Time**: <500ms
- **Database Performance**: <100ms queries
- **Error Rate**: <1%

### Alerts
- Odds collection failures
- Signal generation errors
- API response time >1s
- Database connection issues
- High drawdown warnings

## 🔒 Security & Compliance

### Analytics-Only Operation
- ✅ No betting facilitation
- ✅ Educational analytics only
- ✅ No fund movement
- ✅ No execution automation
- ✅ Risk warnings displayed

### API Security
- API key authentication
- Rate limiting (100 req/min)
- CORS protection
- Audit logging
- Input validation

## 🚨 Troubleshooting

### Common Issues

1. **API Keys Not Working**
   ```bash
   # Check environment variables
   echo $PROVIDERS_ODDS_API_KEY
   echo $PROVIDERS_SPORTS_MONKS_KEY
   ```

2. **Database Connection Issues**
   ```bash
   # Check DATABASE_URL format
   postgresql://user:password@host:port/database
   ```

3. **Worker Not Starting**
   ```bash
   # Check n8n configuration
   # Verify webhook URLs
   ```

4. **Signals Not Generating**
   ```bash
   # Check model status
   GET /mvp/status
   ```

### Logs
```bash
# API logs
render logs --service betflow-api

# Worker logs  
render logs --service betflow-worker

# Web logs
render logs --service betflow-web
```

## 📈 Performance Optimization

### Expected Performance
- **Cold Start**: 30-60 seconds
- **Warm Response**: <500ms
- **Concurrent Users**: 50-100
- **Data Volume**: 1000+ events/day

### Optimization Tips
1. Use Redis caching for odds
2. Implement connection pooling
3. Optimize database queries
4. Use CDN for static assets
5. Monitor memory usage

## 🎯 Success Metrics

### MVP Success Criteria
- ✅ Deploy to Render successfully
- ✅ Collect odds every 5 minutes
- ✅ Generate signals every 10 minutes
- ✅ 2-week backtest shows 5%+ ROI
- ✅ Dashboard displays real-time data
- ✅ Risk limits enforced
- ✅ No betting facilitation

### ROI Targets
- **Conservative**: 2-3% monthly
- **Moderate**: 3-5% monthly  
- **Aggressive**: 5-8% monthly
- **Max Drawdown**: <15%
- **Win Rate**: >55%

## 🔄 Next Steps

### Phase 1 (MVP) - Current
- ✅ Football OU 2.5 pre-match
- ✅ Conservative staking
- ✅ Risk management
- ✅ Backtesting

### Phase 2 (Expansion)
- 🔄 Live markets (if low latency)
- 🔄 Tennis markets
- 🔄 MLB markets
- 🔄 Advanced models

### Phase 3 (Scale)
- 🔄 Multiple sports
- 🔄 Real-time processing
- 🔄 Machine learning
- 🔄 Advanced analytics

## 📞 Support

### Documentation
- API Docs: `/docs` endpoint
- Runbook: `docs/RUNBOOK.md`
- Security: `docs/SECURITY.md`
- Compliance: `docs/COMPLIANCE.md`

### Monitoring
- Health: `/health`
- Metrics: `/metrics`
- Status: `/mvp/status`

---

**⚠️ Legal Notice**: This platform provides educational analytics only. No betting facilitation or fund movement. Use at your own risk. Past performance does not guarantee future results.
