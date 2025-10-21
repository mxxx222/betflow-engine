#!/bin/bash
set -euo pipefail

# ZeroTrace Log Hygiene Setup Script
# Configures log rotation and cleanup for privacy

echo "=== ZeroTrace Log Hygiene Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Use sudo."
    exit 1
fi

# Immediate log cleanup
echo "Performing initial log cleanup..."
journalctl --vacuum-time=2d

# Create systemd timer for regular log cleanup
echo "Setting up automated log cleanup..."

# Create service file
cat > /etc/systemd/system/journal_vacuum.service << SERVICE_EOF
[Unit]
Description=Clean journal logs older than 2 days
After=systemd-journald.service

[Service]
Type=oneshot
ExecStart=/bin/journalctl --vacuum-time=2d
SERVICE_EOF

# Create timer file
cat > /etc/systemd/system/journal_vacuum.timer << TIMER_EOF
[Unit]
Description=Clean journal logs every 6 hours

[Timer]
OnBootSec=15min
OnUnitActiveSec=6h

[Install]
WantedBy=timers.target
TIMER_EOF

# Enable and start the timer
systemctl daemon-reload
systemctl enable journal_vacuum.timer
systemctl start journal_vacuum.timer

# Verify timer setup
echo "Log cleanup timer status:"
systemctl status journal_vacuum.timer --no-pager -l

echo "=== Log Hygiene Setup Complete ==="
echo "Logs will be automatically cleaned every 6 hours"
echo "Manual cleanup: sudo journalctl --vacuum-time=2d"
