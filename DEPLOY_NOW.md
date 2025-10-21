# 🚀 Deploy BetFlow Engine MVP to Render - Step by Step

## 🎯 Quick Start (5 minutes)

### Step 1: Get API Keys (2 minutes)

1. **OddsAPI** (Primary provider)
   - Go to: https://the-odds-api.com/
   - Sign up (free tier available)
   - Copy your API key

2. **SportsMonks** (Backup provider)  
   - Go to: https://sportmonks.com/
   - Sign up (free tier available)
   - Copy your API key

### Step 2: Deploy to Render (3 minutes)

1. **Go to Render**: https://render.com
2. **Sign up/Login** with GitHub
3. **Connect Repository**: `mxxx222/betflow-engine`
4. **Create Services** (in this order):

#### A. PostgreSQL Database
- **Type**: PostgreSQL
- **Name**: `betflow-postgres`
- **Plan**: Starter (Free)
- **Database Name**: `betflow`
- **User**: `betflow_user`

#### B. Redis Database  
- **Type**: Redis
- **Name**: `betflow-redis`
- **Plan**: Starter (Free)

#### C. Web Service (API)
- **Type**: Web Service
- **Name**: `betflow-api`
- **Environment**: Python 3
- **Build Command**:
  ```bash
  pip install -r api/requirements.txt
  pip install -r engine/requirements.txt
  alembic -c db/alembic.ini upgrade head
  ```
- **Start Command**:
  ```bash
  uvicorn api.main:app --host 0.0.0.0 --port $PORT
  ```

#### D. Background Worker
- **Type**: Background Worker
- **Name**: `betflow-worker`
- **Environment**: Python 3
- **Build Command**:
  ```bash
  pip install -r api/requirements.txt
  pip install -r engine/requirements.txt
  ```
- **Start Command**:
  ```bash
  python -m n8n start
  ```

#### E. Web Service (Frontend)
- **Type**: Web Service
- **Name**: `betflow-web`
- **Environment**: Node
- **Build Command**:
  ```bash
  cd web
  npm install
  npm run build
  ```
- **Start Command**:
  ```bash
  cd web && npm start
  ```

### Step 3: Configure Environment Variables

For each service, add these environment variables:

#### For API Service (betflow-api):
```bash
DATABASE_URL=postgresql://betflow_user:password@betflow-postgres:5432/betflow
REDIS_URL=redis://betflow-redis:6379
API_RATE_LIMIT=100
JWT_SECRET=your-jwt-secret-here
ADMIN_EMAIL=admin@betflow-engine.com
PROVIDERS_ODDS_API_KEY=your_odds_api_key_here
PROVIDERS_SPORTS_MONKS_KEY=your_sports_monks_key_here
N8N_WEBHOOK_URL=https://betflow-worker.onrender.com/webhook
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### For Worker Service (betflow-worker):
```bash
DATABASE_URL=postgresql://betflow_user:password@betflow-postgres:5432/betflow
REDIS_URL=redis://betflow-redis:6379
N8N_WEBHOOK_URL=https://betflow-worker.onrender.com/webhook
PROVIDERS_ODDS_API_KEY=your_odds_api_key_here
PROVIDERS_SPORTS_MONKS_KEY=your_sports_monks_key_here
ENVIRONMENT=production
LOG_LEVEL=INFO
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password
```

#### For Web Service (betflow-web):
```bash
NEXT_PUBLIC_API_URL=https://betflow-api.onrender.com
NODE_ENV=production
```

## 🧪 Test Your Deployment

### 1. Health Check
```bash
curl https://betflow-api.onrender.com/health
```

### 2. MVP Status
```bash
curl https://betflow-api.onrender.com/mvp/status
```

### 3. Football Events
```bash
curl https://betflow-api.onrender.com/mvp/events/football
```

### 4. Backtest Results
```bash
curl https://betflow-api.onrender.com/mvp/backtest/results
```

## 📊 Expected Results

### Service URLs
- **API**: `https://betflow-api.onrender.com`
- **Dashboard**: `https://betflow-web.onrender.com`
- **Worker**: `https://betflow-worker.onrender.com`

### Performance
- **Cold Start**: 30-60 seconds
- **API Response**: <500ms
- **Data Collection**: Every 5 minutes
- **Signal Generation**: Every 10 minutes

### ROI Target
- **Conservative**: 2-3% monthly
- **Moderate**: 3-5% monthly
- **Focus**: Football Over/Under 2.5 only

## 🎯 What You'll Get

### Analytics Dashboard
- Real-time football odds
- Over/Under 2.5 market focus
- Edge analysis and signals
- Risk management tools
- Performance tracking

### Automated Data Collection
- Odds from multiple providers
- Signal computation every 10 minutes
- Risk monitoring and alerts
- Conservative staking rules

### Backtesting System
- 2-week historical analysis
- League-specific performance
- ROI reporting per league
- Risk-adjusted returns

## 🔒 Compliance & Security

- ✅ **Analytics-only operation**
- ✅ **No betting facilitation**
- ✅ **Educational purpose only**
- ✅ **Conservative risk management**
- ✅ **Audit logging**

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python/Node versions
   - Verify dependencies
   - Check build logs

2. **Database Connection**
   - Verify DATABASE_URL format
   - Check database is running
   - Test connection

3. **API Keys Not Working**
   - Verify keys are correct
   - Check provider documentation
   - Test keys independently

### Debug Commands
```bash
# Check service logs in Render dashboard
# Look for errors in build/deploy logs
# Test individual endpoints
```

## 📈 Next Steps

1. **Monitor Performance**: Check logs and metrics
2. **Run Backtest**: Validate strategy performance  
3. **Adjust Risk Limits**: Based on backtest results
4. **Scale if Needed**: Upgrade plans for higher load

---

**⚠️ Legal Notice**: This platform provides educational analytics only. No betting facilitation or fund movement. Use at your own risk. Past performance does not guarantee future results.

**🎯 Focus**: Football Over/Under 2.5 markets with 2-5% monthly ROI target through conservative staking and risk management.
