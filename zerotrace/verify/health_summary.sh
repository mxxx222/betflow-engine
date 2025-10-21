#!/bin/bash
set -euo pipefail

# ZeroTrace Health Summary Script
# Provides overall system health status for privacy setup

echo "=== ZeroTrace Health Summary ==="
echo "$(date)"
echo ""

# Run all verification scripts and capture output
TOR_RESULT=$(./check_tor.sh 2>&1)
PROXY_RESULT=$(./check_proxychains.sh 2>&1)
SERVICE_RESULT=$(./check_services.sh 2>&1)

# Count passes and failures
PASS_COUNT=$(echo "$TOR_RESULT$PROXY_RESULT$SERVICE_RESULT" | grep -c "✅")
FAIL_COUNT=$(echo "$TOR_RESULT$PROXY_RESULT$SERVICE_RESULT" | grep -c "❌")
WARN_COUNT=$(echo "$TOR_RESULT$PROXY_RESULT$SERVICE_RESULT" | grep -c "⚠️")

# Display summary
echo "📊 SUMMARY:"
echo "✅ Passes: $PASS_COUNT"
echo "❌ Failures: $FAIL_COUNT"
echo "⚠️  Warnings: $WARN_COUNT"
echo ""

# Overall status
if [ "$FAIL_COUNT" -eq 0 ]; then
    if [ "$WARN_COUNT" -eq 0 ]; then
        echo "🎉 STATUS: EXCELLENT - All checks passed"
        echo "   Your ZeroTrace setup is working properly"
    else
        echo "📋 STATUS: GOOD - All essential checks passed"
        echo "   Some non-critical warnings present"
    fi
else
    echo "❌ STATUS: NEEDS ATTENTION - Critical failures detected"
    echo "   Review the detailed output below"
fi

echo ""
echo "=== Detailed Results ==="
echo ""

# Show detailed results
echo "Tor Verification:"
echo "$TOR_RESULT" | tail -7
echo ""

echo "Proxychains Verification:"
echo "$PROXY_RESULT" | tail -7
echo ""

echo "Services Verification:"
echo "$SERVICE_RESULT" | tail -15
echo ""

echo "=== Health Summary Complete ==="

# Exit with appropriate code
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
elif [ "$WARN_COUNT" -gt 0 ]; then
    exit 2
else
    exit 0
fi
