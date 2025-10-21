#!/bin/bash
set -euo pipefail

# ZeroTrace Framework Setup Script
# Optional: Clones and sets up ZeroTrace framework

echo "=== ZeroTrace Framework Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

# Load configuration
if [ -f ../.env ]; then
    source ../.env
else
    echo "Warning: .env file not found. Using default (no framework installed)."
    INSTALL_ZEROTRACE="false"
fi

# Check if framework should be installed
if [ "${INSTALL_ZEROTRACE:-false}" != "true" ]; then
    echo "Framework installation disabled (INSTALL_ZEROTRACE=false)."
    echo "To install framework, set INSTALL_ZEROTRACE=true in .env and rerun this script."
    exit 0
fi

echo "Installing ZeroTrace framework..."

# Framework repository (example - replace with actual ZeroTrace repo)
FRAMEWORK_REPO="https://github.com/zerotrace/framework.git"
FRAMEWORK_DIR="/opt/zerotrace-framework"

# Clone repository
echo "Cloning ZeroTrace framework..."
if [ -d "$FRAMEWORK_DIR" ]; then
    echo "Framework directory exists, updating..."
    cd "$FRAMEWORK_DIR" && git pull
else
    git clone "$FRAMEWORK_REPO" "$FRAMEWORK_DIR"
fi

# Verify repository integrity
echo "Verifying framework integrity..."
cd "$FRAMEWORK_DIR"

# Check for expected files
REQUIRED_FILES=("README.md" "install.sh" "config.example.yaml")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "WARNING: Required file $file not found in framework"
    fi
done

# Basic checksum verification (if checksum file exists)
if [ -f "checksums.txt" ]; then
    echo "Verifying checksums..."
    if sha256sum -c checksums.txt 2>/dev/null; then
        echo "Checksum verification: PASSED"
    else
        echo "Checksum verification: WARNING - Some files may be modified"
    fi
fi

# Run framework installer if available
if [ -f "install.sh" ]; then
    echo "Running framework installer..."
    chmod +x install.sh
    ./install.sh
else
    echo "No installer found. Manual setup may be required."
fi

echo "=== ZeroTrace Framework Setup Complete ==="
echo "Framework installed to: $FRAMEWORK_DIR"
echo "Review the framework documentation before use."
