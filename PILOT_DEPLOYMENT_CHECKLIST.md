# 🚀 Pilot Deployment Checklist

## Pre-Deployment (Waiting for CI)

### ✅ 1. Environment Setup
```bash
# Set production parameters
export USE_MOJO=1 SLO_P95_MS=1 SLO_P99_MS=5 MAX_FALLBACK_RATIO=0.05

# Run setup script
./scripts/setup_production_env.sh
```

### ✅ 2. Rollback Path Preparation
```bash
# Prepare rollback path
make rollback-prepare

# Verify rollback status
make rollback-status
```

### ✅ 3. Monitoring Setup
```bash
# Start monitoring
make monitor-slo

# Check health
make health

# Monitor logs
make monitor-logs
```

## Phase 1: 10% Canary (When CI = Green)

### 🚀 Start Canary
```bash
make pilot-up
```

### 📊 Monitor for 15-30 minutes
```bash
# Health monitoring
watch -n 30 make health

# SLO monitoring
make monitor-slo

# Log monitoring
make monitor-logs
```

### ✅ SLO Requirements
- **p95 latency**: < 1ms
- **p99 latency**: < 5ms
- **Error rate**: < 0.1%
- **Fallback ratio**: < 5%
- **CPU usage**: < 70%

### 🚫 Canary Gate Conditions (Block scaling if any are true)
- p95 >= 1ms OR p99 >= 5ms
- error_rate >= 0.1%
- fallback_ratio >= 5%
- memory usage trending upward

### 🏥 Health Snapshot Requirements
- status=healthy
- use_mojo=true
- mojo_available=true

## Phase 2: 50% Scale (After 15-30 min if green)

### 📈 Scale to 50%
```bash
make pilot-scale-50
```

### 📊 Monitor for 1-2 hours
```bash
# Continue monitoring
watch -n 60 make bench
watch -n 30 make health
```

### ✅ Same SLO requirements as Phase 1

## Phase 3: 100% Production (After 1-2 hours if green)

### 🌟 Scale to Full Production
```bash
make pilot-full
```

### 📊 Monitor for 24 hours
```bash
# Continue monitoring
watch -n 30 make health
make monitor-slo
```

## Emergency Procedures

### 🚨 Rollback if Issues
```bash
# Execute rollback
make rollback-execute

# Verify rollback
make health

# Return to current when fixed
make rollback-return
```

### 📊 Monitoring Commands
```bash
make health              # Health check
make monitor-slo        # SLO monitoring
make monitor-logs       # Application logs
make monitor-metrics    # Current metrics
make monitor-status     # Monitoring status
```

## Expected ROI Timeline

### 📈 Performance Expectations
- **10-50× speedup** from Mojo optimization
- **60-90% CPU savings** from efficient computation
- **Stable fallback** and SLO monitoring reduce disruption costs
- **ROI timeline**: 2-4 weeks to see full benefits

### 🎯 Success Metrics
- **Latency**: p95 < 1ms, p99 < 5ms
- **Reliability**: Error rate < 0.1%
- **Efficiency**: CPU usage < 70%
- **Stability**: No memory leaks or performance degradation

## Monitoring URLs

### 🌐 Dashboard Access
- **Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## Rollback Commands

### 🔄 Rollback Management
```bash
make rollback-prepare    # Prepare rollback path
make rollback-execute    # Execute rollback
make rollback-return     # Return to current
make rollback-status     # Check status
```

## Success Criteria

### ✅ Phase 1 Success (10% canary)
- All SLOs met for 15-30 minutes
- No canary gate violations
- Health snapshot shows healthy status
- Mojo engine available and active

### ✅ Phase 2 Success (50% scale)
- All SLOs met for 1-2 hours
- No performance degradation
- Stable resource usage
- No error rate increase

### ✅ Phase 3 Success (100% production)
- All SLOs met for 24 hours
- Full production traffic handling
- No rollback needed
- Performance improvements visible

## Troubleshooting

### 🚨 Common Issues
1. **High latency**: Check Mojo engine status
2. **High error rate**: Check API endpoints
3. **High fallback ratio**: Check Mojo availability
4. **High CPU usage**: Check resource limits
5. **Memory leaks**: Check for memory trends

### 🔧 Debug Commands
```bash
# Check system status
make health
make monitor-status

# Check logs
make monitor-logs

# Check metrics
make monitor-metrics

# Check rollback status
make rollback-status
```

## Final Notes

### ⚠️ Important Reminders
- **Monitor continuously** during pilot phases
- **Don't scale** if canary gate is closed
- **Rollback immediately** if SLOs are violated
- **Document any issues** for future reference
- **Celebrate success** when all phases complete! 🎉

### 📞 Emergency Contacts
- **Primary**: Development team
- **Secondary**: DevOps team
- **Escalation**: Technical lead

---

**🎯 Ready for pilot deployment when CI goes green!**
