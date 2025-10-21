#!/bin/bash
set -euo pipefail

# ZeroTrace Tor Verification Script
# Checks Tor service status and functionality

echo "=== Tor Verification ==="

# Check Tor service status
if systemctl is-active --quiet tor.service; then
    echo "✅ Tor service: RUNNING"
else
    echo "❌ Tor service: NOT RUNNING"
    exit 1
fi

# Check Tor service enabled
if systemctl is-enabled --quiet tor.service; then
    echo "✅ Tor service: ENABLED"
else
    echo "❌ Tor service: NOT ENABLED"
fi

# Check Tor port listening
if ss -tln | grep -q ':9050'; then
    echo "✅ Tor SOCKS port (9050): LISTENING"
else
    echo "❌ Tor SOCKS port (9050): NOT LISTENING"
fi

# Test Tor connection
echo "Testing Tor connection..."
TOR_TEST=$(proxychains curl -s https://check.torproject.org 2>/dev/null || echo "FAIL")

if echo "$TOR_TEST" | grep -q "Congratulations"; then
    echo "✅ Tor connection: SUCCESS"
    echo "   Your connection is using Tor"
elif echo "$TOR_TEST" | grep -q "FAIL"; then
    echo "❌ Tor connection: FAILED (curl error)"
else
    echo "❌ Tor connection: NOT USING TOR"
    echo "   Your connection may not be anonymous"
fi

# Check Tor bootstrap status
TOR_STATUS=$(systemctl status tor.service --no-pager | grep -E "(Bootstrapped|bootstrap)" || echo "No bootstrap info")
echo "Tor status: $TOR_STATUS"

echo "=== Tor Verification Complete ==="
