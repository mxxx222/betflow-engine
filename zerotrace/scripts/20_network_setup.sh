#!/bin/bash
set -euo pipefail

# ZeroTrace Network Setup Script
# Configures Wi-Fi, Ethernet, and regional settings

echo "=== ZeroTrace Network Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

# Load configuration
if [ -f ../.env ]; then
    source ../.env
else
    echo "Warning: .env file not found. Using defaults."
    COUNTRY="FI"
fi

# Set country code for regulatory compliance
echo "Setting country code to: ${COUNTRY:-FI}"
if command -v raspi-config >/dev/null 2>&1; then
    raspi-config nonint do_wifi_country "${COUNTRY:-FI}"
else
    echo "raspi-config not available, setting country code manually"
    # This would typically be in /etc/wpa_supplicant/wpa_supplicant.conf
fi

# Configure Wi-Fi if credentials provided
if [ -n "${WIFI_SSID:-}" ] && [ -n "${WIFI_PSK:-}" ]; then
    echo "Configuring Wi-Fi network: $WIFI_SSID"
    
    # Create wpa_supplicant configuration
    cat > /etc/wpa_supplicant/wpa_supplicant.conf << WPA_EOF
country=${COUNTRY:-FI}
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="$WIFI_SSID"
    psk="$WIFI_PSK"
}
WPA_EOF
    
    # Restart networking
    systemctl restart wpa_supplicant.service 2>/dev/null || true
    systemctl restart networking.service 2>/dev/null || true
    
    echo "Wi-Fi configuration applied. Restarting network services..."
else
    echo "No Wi-Fi credentials provided in .env. Using existing network config."
fi

# Ensure network services are enabled
echo "Ensuring network services are enabled..."
systemctl enable networking.service 2>/dev/null || true
systemctl enable wpa_supplicant.service 2>/dev/null || true

# Test network connectivity
echo "Testing network connectivity..."
if ping -c 3 8.8.8.8 >/dev/null 2>&1; then
    echo "Network connectivity: OK"
else
    echo "Warning: No network connectivity detected"
    echo "Check Ethernet connection or Wi-Fi configuration"
fi

# Display current IP addresses
echo "Current network configuration:"
ip addr show | grep -E "(eth|wlan)[0-9]:" | grep -E "(inet|inet6)" || echo "No IP addresses found"

echo "=== Network Setup Complete ==="
echo "Next step: Run privacy stack setup: sudo ./30_privacy_stack.sh"
