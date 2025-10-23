#!/bin/bash
# Production Environment Setup Script
# Sets up monitoring, rollback, and canary configuration for pilot deployment

set -e

echo "🚀 Setting up production environment for pilot deployment..."

# 1. Set production parameters
echo "📋 Setting production parameters..."
export USE_MOJO=1
export SLO_P95_MS=1
export SLO_P99_MS=5
export MAX_FALLBACK_RATIO=0.05
export PILOT_TRAFFIC=10
export ENVIRONMENT=pilot

echo "✅ Production parameters set:"
echo "  - USE_MOJO=1"
echo "  - SLO_P95_MS=1"
echo "  - SLO_P99_MS=5"
echo "  - MAX_FALLBACK_RATIO=0.05"
echo "  - PILOT_TRAFFIC=10"

# 2. Prepare rollback path
echo "🔄 Preparing rollback path..."
make rollback-prepare

if [ $? -eq 0 ]; then
    echo "✅ Rollback path prepared successfully"
else
    echo "❌ Rollback path preparation failed"
    exit 1
fi

# 3. Check system health
echo "🏥 Checking system health..."
make health

if [ $? -eq 0 ]; then
    echo "✅ System health check passed"
else
    echo "❌ System health check failed"
    exit 1
fi

# 4. Start monitoring
echo "📊 Starting monitoring services..."
echo "  - SLO Monitor: python monitoring/slo_monitor.py"
echo "  - Health Check: make health"
echo "  - Logs: make monitor-logs"

# 5. Display monitoring commands
echo ""
echo "📋 Monitoring Commands:"
echo "  make health              # Health check"
echo "  make monitor-slo        # SLO monitoring"
echo "  make monitor-logs       # Application logs"
echo "  make monitor-metrics    # Current metrics"
echo "  make monitor-status     # Monitoring status"
echo ""

# 6. Display canary deployment commands
echo "🚀 Canary Deployment Commands:"
echo "  make pilot-up           # Start 10% traffic"
echo "  make pilot-scale-50      # Scale to 50% traffic"
echo "  make pilot-full         # Scale to 100% traffic"
echo ""

# 7. Display rollback commands
echo "🔄 Rollback Commands:"
echo "  make rollback-status    # Check rollback status"
echo "  make rollback-execute   # Execute rollback"
echo "  make rollback-return    # Return to current version"
echo ""

# 8. Display SLO thresholds
echo "📊 SLO Thresholds:"
echo "  - p95 latency: < 1ms"
echo "  - p99 latency: < 5ms"
echo "  - Error rate: < 0.1%"
echo "  - Fallback ratio: < 5%"
echo "  - CPU usage: < 70%"
echo ""

# 9. Display monitoring URLs
echo "🌐 Monitoring URLs:"
echo "  - Health: http://localhost:8000/health"
echo "  - Metrics: http://localhost:8000/metrics"
echo "  - Grafana: http://localhost:3001"
echo "  - Prometheus: http://localhost:9090"
echo ""

# 10. Display canary gate conditions
echo "🚫 Canary Gate Conditions (prevents scaling if any are true):"
echo "  - p95 >= 1ms OR p99 >= 5ms"
echo "  - error_rate >= 0.1%"
echo "  - fallback_ratio >= 5%"
echo "  - memory usage trending upward"
echo ""

# 11. Display health snapshot requirements
echo "🏥 Health Snapshot Requirements:"
echo "  - status=healthy"
echo "  - use_mojo=true"
echo "  - mojo_available=true"
echo ""

echo "✅ Production environment setup complete!"
echo ""
echo "🎯 Ready for pilot deployment when CI goes green!"
echo "   Run: make pilot-up"
echo ""
echo "📊 Monitor with: watch -n 30 make health"
echo "📋 Logs with: make monitor-logs"
echo "📊 SLO with: make monitor-slo"
