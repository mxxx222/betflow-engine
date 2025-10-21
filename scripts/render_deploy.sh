#!/bin/bash

# BetFlow Engine MVP - Render Deployment Script
# This script helps prepare and deploy the MVP to Render

set -e

echo "🚀 BetFlow Engine MVP - Render Deployment"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please run from project root."
    exit 1
fi

echo "✅ Found render.yaml configuration"

# Check for required files
echo "📋 Checking required files..."

required_files=(
    "api/main.py"
    "api/requirements.txt"
    "web/package.json"
    "worker/football_odds_ingest.json"
    "scripts/backtest_football_ou25.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Check environment variables
echo "🔧 Checking environment variables..."

required_vars=(
    "RENDER_API_TOKEN"
    "PROVIDERS_ODDS_API_KEY"
    "PROVIDERS_SPORTS_MONKS_KEY"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these variables:"
    echo "export RENDER_API_TOKEN='your_render_token'"
    echo "export PROVIDERS_ODDS_API_KEY='your_odds_api_key'"
    echo "export PROVIDERS_SPORTS_MONKS_KEY='your_sports_monks_key'"
    exit 1
fi

echo "✅ All required environment variables set"

# Create deployment summary
echo "📊 Deployment Summary"
echo "===================="
echo "Repository: https://github.com/mxxx222/betflow-engine"
echo "Focus: Football Over/Under 2.5 markets"
echo "Target ROI: 2-5% monthly with conservative staking"
echo ""

# Services to deploy
echo "🏗️ Services to Deploy:"
echo "1. betflow-api (FastAPI backend)"
echo "2. betflow-worker (n8n background worker)"
echo "3. betflow-web (Next.js dashboard)"
echo "4. betflow-postgres (PostgreSQL database)"
echo "5. betflow-redis (Redis cache)"
echo ""

# Environment variables template
echo "🔧 Environment Variables Template:"
echo "=================================="
cat << 'EOF'
# API Service (betflow-api)
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

# Worker Service (betflow-worker)
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

# Web Service (betflow-web)
NEXT_PUBLIC_API_URL=https://betflow-api.onrender.com
NODE_ENV=production
EOF

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Go to https://render.com and create account"
echo "2. Connect GitHub repository: mxxx222/betflow-engine"
echo "3. Create services in this order:"
echo "   a. PostgreSQL database (betflow-postgres)"
echo "   b. Redis database (betflow-redis)"
echo "   c. Web service (betflow-api)"
echo "   d. Background worker (betflow-worker)"
echo "   e. Web service (betflow-web)"
echo "4. Set environment variables for each service"
echo "5. Deploy and wait for completion"
echo "6. Test endpoints and verify data collection"
echo ""

echo "🔗 Service URLs (after deployment):"
echo "==================================="
echo "• API: https://betflow-api.onrender.com"
echo "• Web Dashboard: https://betflow-web.onrender.com"
echo "• Worker (n8n): https://betflow-worker.onrender.com"
echo "• Health Check: https://betflow-api.onrender.com/health"
echo "• MVP Health: https://betflow-api.onrender.com/mvp/health"
echo ""

echo "🧪 Testing Commands:"
echo "==================="
echo "# Health check"
echo "curl https://betflow-api.onrender.com/health"
echo ""
echo "# MVP status"
echo "curl https://betflow-api.onrender.com/mvp/status"
echo ""
echo "# Football events"
echo "curl https://betflow-api.onrender.com/mvp/events/football"
echo ""
echo "# Backtest results"
echo "curl https://betflow-api.onrender.com/mvp/backtest/results"
echo ""

echo "📚 Documentation:"
echo "================"
echo "• Deployment Guide: RENDER_DEPLOYMENT_GUIDE.md"
echo "• MVP Guide: MVP_DEPLOYMENT.md"
echo "• API Docs: https://betflow-api.onrender.com/docs"
echo ""

echo "⚠️ Important Notes:"
echo "==================="
echo "• This is analytics-only - no betting facilitation"
echo "• Conservative staking: 2% max stake per bet"
echo "• Risk management: 10% stop loss, Kelly Criterion"
echo "• Target ROI: 2-5% monthly with football OU 2.5"
echo ""

echo "✅ Deployment preparation complete!"
echo "Follow the steps above to deploy to Render."
