#!/bin/bash
set -euo pipefail

# ZeroTrace Post-Boot Setup Script
# Performs initial system setup: updates, user configuration, basic hardening

echo "=== ZeroTrace Post-Boot Setup ==="

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
fi

# System update and upgrade
echo "Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "Installing essential tools..."
apt install -y curl wget git vim sudo

# User management - ensure sudo access for primary user
if [ -n "$SUDO_USER" ]; then
    echo "Ensuring sudo access for user: $SUDO_USER"
    if ! groups "$SUDO_USER" | grep -q sudo; then
        usermod -aG sudo "$SUDO_USER"
        echo "Added $SUDO_USER to sudo group"
    fi
fi

# Security hardening basics
echo "Applying basic security hardening..."

# Change default passwords (if they exist)
if id "parrot" &>/dev/null; then
    echo "WARNING: Default 'parrot' user detected. Please change password:"
    passwd parrot
fi

if id "root" &>/dev/null; then
    echo "Please set a strong root password:"
    passwd root
fi

# Disable unnecessary services (adjust based on Parrot OS default)
echo "Disabling potentially unnecessary services..."
systemctl disable bluetooth.service 2>/dev/null || true
systemctl stop bluetooth.service 2>/dev/null || true

# Configure sudo timeout
echo "Configuring sudo timeout (15 minutes)..."
if [ -f /etc/sudoers ]; then
    if ! grep -q "Defaults    timestamp_timeout=15" /etc/sudoers; then
        echo "Defaults    timestamp_timeout=15" >> /etc/sudoers
    fi
fi

# Set up basic firewall (if ufw is available)
if command -v ufw >/dev/null 2>&1; then
    echo "Configuring firewall..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw enable
else
    echo "ufw not available, consider installing for firewall management"
fi

echo "=== Post-Boot Setup Complete ==="
echo "Next steps:"
echo "1. Run network setup: sudo ./20_network_setup.sh"
echo "2. Configure privacy stack: sudo ./30_privacy_stack.sh"
