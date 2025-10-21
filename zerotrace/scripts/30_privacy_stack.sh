#!/bin/bash
set -euo pipefail

# ZeroTrace Privacy Stack Setup Script
# Installs and configures Tor, proxychains, and verification tools

echo "=== ZeroTrace Privacy Stack Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

# Install privacy tools
echo "Installing Tor and proxychains..."
apt update
apt install -y tor proxychains curl

# Configure Tor
echo "Configuring Tor service..."
systemctl enable tor.service
systemctl start tor.service

# Configure proxychains
echo "Configuring proxychains..."
if [ -f /etc/proxychains.conf ]; then
    # Backup original config
    cp /etc/proxychains.conf /etc/proxychains.conf.backup
    
    # Create minimal Tor-only configuration
    cat > /etc/proxychains.conf << PROXY_EOF
# ZeroTrace proxychains configuration
# Strictly Tor-only for maximum privacy

strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 9050
PROXY_EOF
    
    echo "proxychains configured for Tor-only usage"
else
    echo "Warning: /etc/proxychains.conf not found"
fi

# Test Tor functionality
echo "Testing Tor connection..."
if systemctl is-active --quiet tor.service; then
    echo "Tor service is running"
    
    # Wait for Tor to bootstrap
    echo "Waiting for Tor to bootstrap..."
    sleep 10
    
    # Test with curl through proxychains
    if proxychains curl -s https://check.torproject.org | grep -q "Congratulations"; then
        echo "Tor test: SUCCESS - Connection is using Tor"
    else
        echo "Tor test: WARNING - May not be using Tor"
        echo "Check Tor status: systemctl status tor.service"
    fi
else
    echo "Tor service is not running. Check status: systemctl status tor.service"
fi

# Install verification tools
echo "Installing verification utilities..."
apt install -y net-tools iproute2

echo "=== Privacy Stack Setup Complete ==="
echo "Verification commands:"
echo "  ./verify/check_tor.sh"
echo "  ./verify/check_proxychains.sh"
echo "  ./verify/health_summary.sh"
