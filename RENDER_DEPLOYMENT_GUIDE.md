# 🚀 Render Deployment Guide - BetFlow Engine MVP

## 📋 Prerequisites

1. **Render Account**: Sign up at https://render.com
2. **GitHub Repository**: https://github.com/mxxx222/betflow-engine
3. **API Keys**: Get OddsAPI and SportsMonks keys

## 🎯 Deployment Steps

### Step 1: Create Web Service (API)

1. Go to Render Dashboard → "New" → "Web Service"
2. Connect GitHub repository: `mxxx222/betflow-engine`
3. Configure service:

```yaml
Name: betflow-api
Environment: Python 3
Build Command: |
  pip install -r api/requirements.txt
  pip install -r engine/requirements.txt
  alembic -c db/alembic.ini upgrade head
Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Step 2: Create Background Worker

1. Go to Render Dashboard → "New" → "Background Worker"
2. Connect same GitHub repository
3. Configure worker:

```yaml
Name: betflow-worker
Environment: Python 3
Build Command: |
  pip install -r api/requirements.txt
  pip install -r engine/requirements.txt
Start Command: python -m n8n start
```

### Step 3: Create Web Service (Frontend)

1. Go to Render Dashboard → "New" → "Web Service"
2. Connect same GitHub repository
3. Configure service:

```yaml
Name: betflow-web
Environment: Node
Build Command: |
  cd web
  npm install
  npm run build
Start Command: cd web && npm start
```

### Step 4: Create PostgreSQL Database

1. Go to Render Dashboard → "New" → "PostgreSQL"
2. Configure database:

```yaml
Name: betflow-postgres
Database Name: betflow
User: betflow_user
```

### Step 5: Create Redis Database

1. Go to Render Dashboard → "New" → "Redis"
2. Configure Redis:

```yaml
Name: betflow-redis
Plan: Starter
```

## 🔧 Environment Variables

### For API Service (betflow-api)

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

### For Worker Service (betflow-worker)

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

### For Web Service (betflow-web)

```bash
NEXT_PUBLIC_API_URL=https://betflow-api.onrender.com
NODE_ENV=production
```

## 🔑 API Keys Setup

### 1. OddsAPI (Primary Provider)
1. Go to https://the-odds-api.com/
2. Sign up for free account
3. Get API key from dashboard
4. Set `PROVIDERS_ODDS_API_KEY` in environment variables

### 2. SportsMonks (Backup Provider)
1. Go to https://sportmonks.com/
2. Sign up for free account
3. Get API key from dashboard
4. Set `PROVIDERS_SPORTS_MONKS_KEY` in environment variables

## 🚀 Deployment Process

### 1. Deploy Services in Order
1. **Database first**: PostgreSQL + Redis
2. **API second**: betflow-api
3. **Worker third**: betflow-worker
4. **Web last**: betflow-web

### 2. Wait for Deployments
- Each service takes 5-10 minutes to deploy
- Check logs for any errors
- Verify environment variables are set

### 3. Test Endpoints
```bash
# Health check
curl https://betflow-api.onrender.com/health

# MVP health check
curl https://betflow-api.onrender.com/mvp/health

# Football events
curl https://betflow-api.onrender.com/mvp/events/football
```

## 📊 Service URLs

After deployment, you'll have:

- **API**: `https://betflow-api.onrender.com`
- **Web Dashboard**: `https://betflow-web.onrender.com`
- **Worker (n8n)**: `https://betflow-worker.onrender.com`
- **Database**: Internal connection only
- **Redis**: Internal connection only

## 🔄 Post-Deployment Setup

### 1. Initialize Database
```bash
# Run migrations (should happen automatically)
# Check API logs for migration status
```

### 2. Start Data Collection
1. Go to n8n worker: `https://betflow-worker.onrender.com`
2. Login with admin credentials
3. Import workflows from `worker/` directory
4. Activate football odds collection workflow

### 3. Verify Data Flow
1. Check API logs for odds collection
2. Verify signals are being generated
3. Test dashboard displays data

## 🧪 Testing MVP

### 1. Run Backtest
```bash
# SSH into API service or run locally
python scripts/backtest_football_ou25.py
```

### 2. Check Performance
```bash
# Get system status
curl https://betflow-api.onrender.com/mvp/status

# Get backtest results
curl https://betflow-api.onrender.com/mvp/backtest/results

# Get risk limits
curl https://betflow-api.onrender.com/mvp/risk/limits
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python/Node versions
   - Verify all dependencies
   - Check build logs for errors

2. **Database Connection**
   - Verify DATABASE_URL format
   - Check database is running
   - Test connection from API service

3. **API Keys Not Working**
   - Verify keys are correct
   - Check provider documentation
   - Test keys independently

4. **Worker Not Starting**
   - Check n8n configuration
   - Verify environment variables
   - Check worker logs

### Debug Commands

```bash
# Check service logs
render logs --service betflow-api
render logs --service betflow-worker
render logs --service betflow-web

# Check database
render logs --service betflow-postgres
render logs --service betflow-redis
```

## 📈 Expected Performance

### MVP Metrics
- **Cold Start**: 30-60 seconds
- **API Response**: <500ms
- **Data Collection**: Every 5 minutes
- **Signal Generation**: Every 10 minutes
- **ROI Target**: 2-5% monthly

### Resource Usage
- **API**: 512MB RAM, 1 CPU
- **Worker**: 512MB RAM, 1 CPU  
- **Web**: 256MB RAM, 1 CPU
- **Database**: 1GB storage
- **Redis**: 25MB storage

## 🎯 Success Criteria

### Deployment Success
- ✅ All services deployed
- ✅ Database connected
- ✅ API responding
- ✅ Worker collecting data
- ✅ Web dashboard accessible

### MVP Success
- ✅ Odds collected every 5 minutes
- ✅ Signals generated every 10 minutes
- ✅ Backtest shows 5%+ ROI
- ✅ Risk limits enforced
- ✅ No betting facilitation

## 🔄 Next Steps

1. **Monitor Performance**: Check logs and metrics
2. **Run Backtest**: Validate strategy performance
3. **Adjust Risk Limits**: Based on backtest results
4. **Scale if Needed**: Upgrade plans for higher load
5. **Add More Markets**: Expand beyond OU 2.5

---

**⚠️ Important**: This is an analytics-only platform. No betting facilitation or fund movement. Use for educational purposes only.
