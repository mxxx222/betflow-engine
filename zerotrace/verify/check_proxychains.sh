#!/bin/bash
set -euo pipefail

# ZeroTrace Proxychains Verification Script
# Checks proxychains configuration and functionality

echo "=== Proxychains Verification ==="

# Check proxychains configuration file
if [ -f /etc/proxychains.conf ]; then
    echo "✅ Proxychains config: FOUND"
    
    # Check for Tor configuration
    if grep -q "socks5 127.0.0.1 9050" /etc/proxychains.conf; then
        echo "✅ Tor proxy: CONFIGURED"
    else
        echo "❌ Tor proxy: NOT CONFIGURED"
    fi
    
    # Check for strict chain mode
    if grep -q "strict_chain" /etc/proxychains.conf; then
        echo "✅ Strict chain: ENABLED"
    else
        echo "❌ Strict chain: DISABLED"
    fi
    
    # Check for proxy DNS
    if grep -q "proxy_dns" /etc/proxychains.conf; then
        echo "✅ Proxy DNS: ENABLED"
    else
        echo "❌ Proxy DNS: DISABLED"
    fi
    
else
    echo "❌ Proxychains config: NOT FOUND"
    exit 1
fi

# Test proxychains functionality
echo "Testing proxychains functionality..."

# Test with a simple HTTP request
TEST_URL="http://httpbin.org/ip"
DIRECT_IP=$(curl -s "$TEST_URL" 2>/dev/null | grep -o '"[0-9.]*"' | head -1 || echo "FAIL")
PROXY_IP=$(proxychains curl -s "$TEST_URL" 2>/dev/null | grep -o '"[0-9.]*"' | head -1 || echo "FAIL")

if [ "$DIRECT_IP" != "$PROXY_IP" ] && [ "$DIRECT_IP" != "FAIL" ] && [ "$PROXY_IP" != "FAIL" ]; then
    echo "✅ Proxychains: WORKING"
    echo "   Direct IP: $DIRECT_IP"
    echo "   Proxy IP:  $PROXY_IP"
else
    echo "❌ Proxychains: NOT WORKING PROPERLY"
    echo "   Direct: $DIRECT_IP, Proxy: $PROXY_IP"
fi

# Test DNS resolution through proxy
if proxychains host google.com 2>/dev/null | grep -q "has address"; then
    echo "✅ DNS through proxy: WORKING"
else
    echo "❌ DNS through proxy: FAILED"
fi

echo "=== Proxychains Verification Complete ==="
