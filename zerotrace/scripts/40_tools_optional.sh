#!/bin/bash
set -euo pipefail

# ZeroTrace Optional Tools Setup Script
# Installs security analysis tools (optional, controlled by .env)

echo "=== ZeroTrace Optional Tools Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

# Load configuration
if [ -f ../.env ]; then
    source ../.env
else
    echo "Warning: .env file not found. Using default (no tools installed)."
    INSTALL_TOOLS="false"
fi

# Check if tools should be installed
if [ "${INSTALL_TOOLS:-false}" != "true" ]; then
    echo "Tools installation disabled (INSTALL_TOOLS=false)."
    echo "To install tools, set INSTALL_TOOLS=true in .env and rerun this script."
    exit 0
fi

echo "Installing optional security tools..."

# Network analysis tools
echo "Installing network analysis tools..."
apt install -y nmap wireshark tshark

# Monitoring tools
echo "Installing system monitoring tools..."
apt install -y iftop iotop htop

# Metasploit framework (large installation)
echo "Installing Metasploit framework..."
apt install -y metasploit-framework

# Additional useful tools
echo "Installing additional utilities..."
apt install -y netcat socat dnsutils whois

echo "=== Optional Tools Setup Complete ==="
echo "Installed tools: nmap, wireshark, metasploit, iftop, iotop"
echo "Warning: These tools increase attack surface. Use only when needed."
