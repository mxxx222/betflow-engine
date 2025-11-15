#!/bin/bash
# Start Pilot Deployment Script
# Simplified pilot deployment without full Docker build

set -e

echo "🚀 Starting BetFlow Engine Pilot Deployment..."

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
echo "  - ENVIRONMENT=pilot"

# 2. Start SLO monitoring
echo "📊 Starting SLO monitoring..."
python monitoring/slo_monitor.py --api-url http://localhost:8000 --interval 30 &
SLO_PID=$!

echo "✅ SLO Monitor started (PID: $SLO_PID)"

# 3. Display monitoring commands
echo ""
echo "📋 Monitoring Commands:"
echo "  make health              # Health check"
echo "  make monitor-slo        # SLO monitoring"
echo "  make monitor-logs       # Application logs"
echo "  make monitor-metrics    # Current metrics"
echo "  make monitor-status     # Monitoring status"

# 4. Display canary deployment commands
echo ""
echo "🚀 Canary Deployment Commands:"
echo "  make pilot-up           # Start 10% traffic"
echo "  make pilot-scale-50      # Scale to 50% traffic"
echo "  make pilot-full         # Scale to 100% traffic"

# 5. Display rollback commands
echo ""
echo "🔄 Rollback Commands:"
echo "  make rollback-status    # Check rollback status"
echo "  make rollback-execute   # Execute rollback"
echo "  make rollback-return    # Return to current version"

# 6. Display SLO thresholds
echo ""
echo "📊 SLO Thresholds:"
echo "  - p95 latency: < 1ms"
echo "  - p99 latency: < 5ms"
echo "  - Error rate: < 0.1%"
echo "  - Fallback ratio: < 5%"
echo "  - CPU usage: < 70%"

# 7. Display monitoring URLs
echo ""
echo "🌐 Monitoring URLs:"
echo "  - Health: http://localhost:8000/health"
echo "  - Metrics: http://localhost:8000/metrics"
echo "  - Grafana: http://localhost:3001"
echo "  - Prometheus: http://localhost:9090"

# 8. Display canary gate conditions
echo ""
echo "🚫 Canary Gate Conditions (prevents scaling if any are true):"
echo "  - p95 >= 1ms OR p99 >= 5ms"
echo "  - error_rate >= 0.1%"
echo "  - fallback_ratio >= 5%"
echo "  - memory usage trending upward"

# 9. Display health snapshot requirements
echo ""
echo "🏥 Health Snapshot Requirements:"
echo "  - status=healthy"
echo "  - use_mojo=true"
echo "  - mojo_available=true"

# 10. Display deployment checklist
echo ""
echo "📋 Deployment Checklist:"
echo "  Phase 1: 10% Canary (15-30 min)"
echo "    - Start: make pilot-up"
echo "    - Monitor: watch -n 30 make health"
echo "    - Validate: SLOs met, canary gate open"
echo ""
echo "  Phase 2: 50% Scale (1-2 hours)"
echo "    - Scale: make pilot-scale-50"
echo "    - Monitor: watch -n 60 make bench"
echo "    - Validate: SLOs maintained"
echo ""
echo "  Phase 3: 100% Production (24 hours)"
echo "    - Scale: make pilot-full"
echo "    - Monitor: watch -n 30 make health"
echo "    - Validate: Full production performance"

echo ""
echo "✅ Pilot deployment environment ready!"
echo ""
echo "🎯 Ready for pilot deployment when CI goes green!"
echo "   Run: make pilot-up"
echo ""
echo "📊 Monitor with: watch -n 30 make health"
echo "📋 Logs with: make monitor-logs"
echo "📊 SLO with: make monitor-slo"

# Keep script running
echo ""
echo "🔄 Monitoring active... Press Ctrl+C to stop"
trap 'echo "🛑 Stopping SLO monitor..."; kill $SLO_PID 2>/dev/null; exit 0' INT
wait $SLO_PID

