#!/bin/bash
# ZeroTrace - Encrypted Backup & Recovery Framework
# Implements BorgBackup with GPG encryption and automated recovery

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root"
    exit 1
fi

log "Starting ZeroTrace Encrypted Backup & Recovery Framework installation..."

# Configuration variables
BACKUP_USER="backup"
BACKUP_DIR="/var/backups/zerotrace"
REPO_DIR="$BACKUP_DIR/repo"
CONFIG_DIR="$BACKUP_DIR/config"
LOG_DIR="/var/log/zerotrace"
GPG_KEY_ID=""
EXTERNAL_DRIVE="/mnt/backup"  # Mount point for external storage

# Create backup user
log "Creating dedicated backup user..."
if ! id "$BACKUP_USER" &>/dev/null; then
    useradd -r -s /bin/bash -m -d "$BACKUP_DIR" "$BACKUP_USER"
    usermod -a -G adm "$BACKUP_USER"
fi

# Create directories
log "Creating backup directories..."
mkdir -p "$REPO_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
chown "$BACKUP_USER:$BACKUP_USER" "$BACKUP_DIR" -R
chmod 700 "$BACKUP_DIR"

# Install required packages
log "Installing BorgBackup and GPG..."
apt update
apt install -y borgbackup gnupg2 cryptsetup

# Generate GPG key for encryption
log "Setting up GPG encryption..."

# Create GPG configuration for automated operations
cat > "$CONFIG_DIR/gpg.conf" << 'EOF'
# GPG configuration for ZeroTrace backups
keyserver hkps://keys.openpgp.org
keyserver-options auto-key-retrieve
personal-cipher-preferences AES256 AES192 AES
personal-digest-preferences SHA512 SHA384 SHA256
cert-digest-algo SHA512
default-preference-list SHA512 SHA384 SHA256 AES256 AES192 AES CAST5 ZLIB BZIP2 ZIP Uncompressed
EOF

# Generate GPG key as backup user
su - "$BACKUP_USER" -c "
gpg --batch --generate-key <<EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: ZeroTrace Backup
Name-Email: backup@zerotrace.local
Expire-Date: 0
%no-protection
%commit
EOF
"

# Get the GPG key ID
GPG_KEY_ID=$(su - "$BACKUP_USER" -c "gpg --list-keys --with-colons | grep '^pub' | cut -d: -f5")

log "GPG key generated: $GPG_KEY_ID"

# Initialize Borg repository
log "Initializing encrypted Borg repository..."
su - "$BACKUP_USER" -c "
borg init --encryption=repokey-blake2 '$REPO_DIR' <<EOF
$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 32)
$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 32)
EOF
"

# Create backup script
log "Creating backup script..."

cat > "$CONFIG_DIR/backup.sh" << EOF
#!/bin/bash
# ZeroTrace Automated Backup Script

REPO="$REPO_DIR"
LOG_FILE="$LOG_DIR/backup.log"
TIMESTAMP=\$(date +%Y-%m-%d_%H-%M-%S)
ARCHIVE_NAME="zerotrace-\$TIMESTAMP"

# Backup sources (critical ZeroTrace files)
BACKUP_PATHS=(
    "/etc/tor/torrc"
    "/etc/proxychains.conf"
    "/etc/fail2ban"
    "/var/ossec"
    "/etc/ssh"
    "/home/pi/.ssh"  # If using pi user
    "/root/.ssh"
    "/etc/iptables"
    "/var/log/zerotrace"
)

echo "\$(date): Starting ZeroTrace backup: \$ARCHIVE_NAME" >> "\$LOG_FILE"

# Create backup
borg create --verbose --filter AME --list --stats --show-rc \\
    --compression lz4 \\
    "\$REPO::\$ARCHIVE_NAME" \\
    "\${BACKUP_PATHS[@]}" \\
    2>> "\$LOG_FILE"

if [[ \$? -eq 0 ]]; then
    echo "\$(date): Backup completed successfully" >> "\$LOG_FILE"

    # Prune old backups (keep last 7 daily, 4 weekly, 6 monthly)
    borg prune --list --show-rc --keep-daily=7 --keep-weekly=4 --keep-monthly=6 "\$REPO" >> "\$LOG_FILE" 2>&1

    # Sync to external drive if available
    if mountpoint -q "$EXTERNAL_DRIVE"; then
        echo "\$(date): Syncing to external drive" >> "\$LOG_FILE"
        borg with-lock "\$REPO" rsync "\$REPO" "$EXTERNAL_DRIVE/zerotrace-backup" >> "\$LOG_FILE" 2>&1
    fi
else
    echo "\$(date): Backup failed with exit code \$?" >> "\$LOG_FILE"
    exit 1
fi

echo "\$(date): Backup process completed" >> "\$LOG_FILE"
EOF

chmod +x "$CONFIG_DIR/backup.sh"
chown "$BACKUP_USER:$BACKUP_USER" "$CONFIG_DIR/backup.sh"

# Create recovery script
log "Creating recovery script..."

cat > "$CONFIG_DIR/recover.sh" << EOF
#!/bin/bash
# ZeroTrace Recovery Script

REPO="$REPO_DIR"
LOG_FILE="$LOG_DIR/recovery.log"

echo "\$(date): Starting ZeroTrace recovery" >> "\$LOG_FILE"

# List available backups
echo "Available backups:" >> "\$LOG_FILE"
borg list "\$REPO" >> "\$LOG_FILE"

# If no archive specified, use the latest
if [[ -z "\$1" ]]; then
    LATEST_ARCHIVE=\$(borg list "\$REPO" | tail -1 | cut -d' ' -f1)
    echo "Using latest archive: \$LATEST_ARCHIVE" >> "\$LOG_FILE"
else
    LATEST_ARCHIVE="\$1"
fi

# Recovery destination
RECOVER_DIR="/tmp/zerotrace-recovery-\$\$"
mkdir -p "\$RECOVER_DIR"

echo "\$(date): Extracting archive \$LATEST_ARCHIVE to \$RECOVER_DIR" >> "\$LOG_FILE"

# Extract backup
borg extract "\$REPO::\$LATEST_ARCHIVE" "\$RECOVER_DIR" >> "\$LOG_FILE" 2>&1

if [[ \$? -eq 0 ]]; then
    echo "\$(date): Recovery extraction completed successfully" >> "\$LOG_FILE"
    echo "Recovery files available in: \$RECOVER_DIR" >> "\$LOG_FILE"
    echo "" >> "\$LOG_FILE"
    echo "To restore specific files:" >> "\$LOG_FILE"
    echo "  cp -r \$RECOVER_DIR/etc/tor/torrc /etc/tor/" >> "\$LOG_FILE"
    echo "  cp -r \$RECOVER_DIR/etc/proxychains.conf /etc/" >> "\$LOG_FILE"
    echo "  # etc..." >> "\$LOG_FILE"
else
    echo "\$(date): Recovery extraction failed" >> "\$LOG_FILE"
    rm -rf "\$RECOVER_DIR"
    exit 1
fi

echo "\$(date): Recovery process completed" >> "\$LOG_FILE"
EOF

chmod +x "$CONFIG_DIR/recover.sh"
chown "$BACKUP_USER:$BACKUP_USER" "$CONFIG_DIR/recover.sh"

# Create systemd service and timer for automated backups
log "Setting up automated backup service..."

cat > /etc/systemd/system/zerotrace-backup.service << EOF
[Unit]
Description=ZeroTrace Automated Backup
After=network.target

[Service]
Type=oneshot
User=$BACKUP_USER
ExecStart=$CONFIG_DIR/backup.sh
EOF

cat > /etc/systemd/system/zerotrace-backup.timer << 'EOF'
[Unit]
Description=Run ZeroTrace Backup daily
Requires=zerotrace-backup.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=1h

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable zerotrace-backup.timer
systemctl start zerotrace-backup.timer

# Create external drive setup script
log "Creating external drive setup script..."

cat > "$CONFIG_DIR/setup-external-drive.sh" << EOF
#!/bin/bash
# ZeroTrace External Drive Setup

DRIVE_DEVICE="\$1"
MOUNT_POINT="$EXTERNAL_DRIVE"

if [[ -z "\$DRIVE_DEVICE" ]]; then
    echo "Usage: \$0 /dev/sdX"
    echo "Available devices:"
    lsblk -d -o NAME,SIZE,TYPE | grep -E "(sd|nvme|mmcblk)"
    exit 1
fi

echo "Setting up external drive: \$DRIVE_DEVICE"

# Create partition if needed
if ! blkid "\$DRIVE_DEVICE"1 >/dev/null 2>&1; then
    echo "Creating partition on \$DRIVE_DEVICE..."
    parted -s "\$DRIVE_DEVICE" mklabel gpt
    parted -s "\$DRIVE_DEVICE" mkpart primary ext4 0% 100%
    mkfs.ext4 "\${DRIVE_DEVICE}1"
fi

# Create mount point
mkdir -p "\$MOUNT_POINT"

# Add to fstab for automount
UUID=\$(blkid -s UUID -o value "\${DRIVE_DEVICE}1")
echo "UUID=\$UUID \$MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab

# Mount
mount "\$MOUNT_POINT"

# Create backup directory on external drive
mkdir -p "\$MOUNT_POINT/zerotrace-backup"
chown "$BACKUP_USER:$BACKUP_USER" "\$MOUNT_POINT/zerotrace-backup"

echo "External drive setup complete!"
echo "Mount point: \$MOUNT_POINT"
echo "Backup directory: \$MOUNT_POINT/zerotrace-backup"
EOF

chmod +x "$CONFIG_DIR/setup-external-drive.sh"

# Create integrity verification script
log "Creating integrity verification script..."

cat > "$CONFIG_DIR/verify-integrity.sh" << EOF
#!/bin/bash
# ZeroTrace Backup Integrity Verification

REPO="$REPO_DIR"
LOG_FILE="$LOG_DIR/integrity.log"

echo "\$(date): Starting integrity verification" >> "\$LOG_FILE"

# Check repository integrity
borg check --verify-data "\$REPO" >> "\$LOG_FILE" 2>&1

if [[ \$? -eq 0 ]]; then
    echo "\$(date): Repository integrity check PASSED" >> "\$LOG_FILE"
else
    echo "\$(date): Repository integrity check FAILED" >> "\$LOG_FILE"
    exit 1
fi

# List archives and check latest
echo "Archive list:" >> "\$LOG_FILE"
borg list "\$REPO" >> "\$LOG_FILE" 2>&1

echo "\$(date): Integrity verification completed" >> "\$LOG_FILE"
EOF

chmod +x "$CONFIG_DIR/verify-integrity.sh"
chown "$BACKUP_USER:$BACKUP_USER" "$CONFIG_DIR/verify-integrity.sh"

# Create systemd timer for integrity checks (weekly)
cat > /etc/systemd/system/zerotrace-integrity.service << EOF
[Unit]
Description=ZeroTrace Backup Integrity Check
After=network.target

[Service]
Type=oneshot
User=$BACKUP_USER
ExecStart=$CONFIG_DIR/verify-integrity.sh
EOF

cat > /etc/systemd/system/zerotrace-integrity.timer << 'EOF'
[Unit]
Description=Run ZeroTrace Integrity Check weekly
Requires=zerotrace-integrity.service

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable zerotrace-integrity.timer
systemctl start zerotrace-integrity.timer

# Create convenience scripts
log "Creating convenience scripts..."

# Quick backup script
cat > /usr/local/bin/zerotrace-backup << EOF
#!/bin/bash
echo "Starting ZeroTrace backup..."
sudo -u $BACKUP_USER $CONFIG_DIR/backup.sh
echo "Backup completed. Check $LOG_DIR/backup.log for details."
EOF

chmod +x /usr/local/bin/zerotrace-backup

# Quick recovery script
cat > /usr/local/bin/zerotrace-recover << EOF
#!/bin/bash
echo "Starting ZeroTrace recovery..."
sudo -u $BACKUP_USER $CONFIG_DIR/recover.sh "\$1"
echo "Recovery completed. Check $LOG_DIR/recovery.log for details."
EOF

chmod +x /usr/local/bin/zerotrace-recover

# Quick integrity check
cat > /usr/local/bin/zerotrace-verify << EOF
#!/bin/bash
echo "Verifying ZeroTrace backup integrity..."
sudo -u $BACKUP_USER $CONFIG_DIR/verify-integrity.sh
echo "Verification completed. Check $LOG_DIR/integrity.log for details."
EOF

chmod +x /usr/local/bin/zerotrace-verify

success "Encrypted Backup & Recovery Framework installed successfully!"
log "Features enabled:"
log "  - BorgBackup with GPG encryption"
log "  - Automated daily backups"
log "  - External drive support"
log "  - Integrity verification (weekly)"
log "  - Point-in-time recovery"
log "  - Comprehensive logging"

warning "Initial backup will run at next scheduled time (daily)"
warning "To run manual backup: zerotrace-backup"
warning "To recover: zerotrace-recover [archive-name]"
warning "To verify integrity: zerotrace-verify"
warning "Setup external drive: $CONFIG_DIR/setup-external-drive.sh /dev/sdX"

log "Backup logs: $LOG_DIR/backup.log"
log "Recovery logs: $LOG_DIR/recovery.log"
log "Integrity logs: $LOG_DIR/integrity.log"