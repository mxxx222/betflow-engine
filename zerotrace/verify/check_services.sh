#!/bin/bash
set -euo pipefail

# ZeroTrace Services Verification Script
# Checks status of essential privacy services

echo "=== Services Verification ==="

# List of essential services
ESSENTIAL_SERVICES=("tor.service" "systemd-journald.service" "networking.service" "wpa_supplicant.service")

# List of services that should be disabled
DISABLE_SERVICES=("bluetooth.service" "avahi-daemon.service" "ssh.service")

# Check essential services
for service in "${ESSENTIAL_SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service: RUNNING"
    else
        echo "❌ $service: NOT RUNNING"
    fi
    
    if systemctl is-enabled --quiet "$service"; then
        echo "✅ $service: ENABLED"
    else
        echo "❌ $service: NOT ENABLED"
    fi
done

echo ""

# Check services that should be disabled
for service in "${DISABLE_SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "⚠️  $service: RUNNING (should be disabled for privacy)"
    else
        echo "✅ $service: NOT RUNNING"
    fi
    
    if systemctl is-enabled --quiet "$service"; then
        echo "⚠️  $service: ENABLED (should be disabled for privacy)"
    else
        echo "✅ $service: NOT ENABLED"
    fi
done

echo ""

# Check log vacuum timer
if systemctl is-active --quiet journal_vacuum.timer; then
    echo "✅ journal_vacuum.timer: RUNNING"
else
    echo "❌ journal_vacuum.timer: NOT RUNNING"
fi

if systemctl is-enabled --quiet journal_vacuum.timer; then
    echo "✅ journal_vacuum.timer: ENABLED"
else
    echo "❌ journal_vacuum.timer: NOT ENABLED"
fi

echo "=== Services Verification Complete ==="
