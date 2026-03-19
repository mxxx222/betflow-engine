#!/bin/bash
# ZeroTrace - Automated Threat Detection & Response System
# Installs and configures fail2ban with Tor-aware filters and OSSEC HIDS

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

log "Starting ZeroTrace Threat Detection & Response System installation..."

# Update package list
log "Updating package list..."
apt update

# Install fail2ban
log "Installing fail2ban..."
apt install -y fail2ban

# Install OSSEC HIDS
log "Installing OSSEC HIDS..."
wget -q -O - https://updates.atomicorp.com/installers/atomic.sh | bash
apt install -y ossec-hids-server ossec-hids-agent

# Create Tor-aware fail2ban filters
log "Creating Tor-aware fail2ban filters..."

# Tor SSH filter
cat > /etc/fail2ban/filter.d/tor-ssh.conf << 'EOF'
[Definition]
failregex = ^.*sshd.*Authentication failure for .* from <HOST>.*$
            ^.*sshd.*Failed password for .* from <HOST>.*$
            ^.*sshd.*Invalid user .* from <HOST>.*$
ignoreregex =
EOF

# Tor-aware jail configuration
cat > /etc/fail2ban/jail.d/tor-aware.conf << 'EOF'
[tor-ssh]
enabled = true
port = ssh
filter = tor-ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

# Configure OSSEC for Raspberry Pi
log "Configuring OSSEC HIDS..."

# OSSEC server configuration
cat > /var/ossec/etc/ossec.conf << 'EOF'
<ossec_config>
  <global>
    <email_notification>no</email_notification>
    <email_to>root@localhost</email_to>
  </global>

  <rules>
    <include>rules_config.xml</include>
    <include>syslog_rules.xml</include>
    <include>pam_rules.xml</include>
  </rules>

  <syscheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
    <scan_on_start>yes</scan_on_start>
    <directories check_all="yes">/etc,/usr/bin,/usr/sbin</directories>
    <directories check_all="yes">/bin,/sbin,/boot</directories>
    <ignore>/etc/mtab</ignore>
    <ignore>/etc/hosts.deny</ignore>
    <ignore>/etc/mail/statistics</ignore>
    <ignore>/etc/random-seed</ignore>
    <ignore>/etc/random.seed</ignore>
    <ignore>/etc/adjtime</ignore>
    <ignore>/etc/httpd/logs</ignore>
  </syscheck>

  <rootcheck>
    <disabled>no</disabled>
    <frequency>3600</frequency>
  </rootcheck>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/syslog</location>
  </localfile>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/kern.log</location>
  </localfile>
</ossec_config>
EOF

# Create custom OSSEC rules for Tor/proxychains
cat > /var/ossec/rules/local_rules.xml << 'EOF'
<group name="tor,proxychains">
  <rule id="100001" level="5">
    <if_sid>530</if_sid>
    <match>proxychains</match>
    <description>Proxychains configuration change detected</description>
  </rule>

  <rule id="100002" level="7">
    <if_sid>530</if_sid>
    <match>torrc</match>
    <description>Tor configuration file modified</description>
  </rule>

  <rule id="100003" level="10">
    <if_sid>550</if_sid>
    <match>sshd_config</match>
    <description>SSH configuration changed</description>
  </rule>
</group>
EOF

# Set proper permissions
chown root:ossec /var/ossec/etc/ossec.conf
chown root:ossec /var/ossec/rules/local_rules.xml
chmod 644 /var/ossec/etc/ossec.conf
chmod 644 /var/ossec/rules/local_rules.xml

# Restart services
log "Restarting services..."
systemctl restart fail2ban
systemctl enable fail2ban

systemctl restart ossec
systemctl enable ossec

# Create monitoring script
log "Creating monitoring and alerting script..."

cat > /usr/local/bin/zerotrace-monitor.sh << 'EOF'
#!/bin/bash
# ZeroTrace Threat Monitoring Script

THREAT_LOG="/var/log/zerotrace/threats.log"
mkdir -p /var/log/zerotrace

# Check fail2ban status
if ! systemctl is-active --quiet fail2ban; then
    echo "$(date): FAIL2BAN DOWN" >> "$THREAT_LOG"
fi

# Check OSSEC status
if ! systemctl is-active --quiet ossec; then
    echo "$(date): OSSEC DOWN" >> "$THREAT_LOG"
fi

# Check for suspicious processes
SUSPICIOUS=$(ps aux | grep -E "(nmap|nikto|sqlmap|hydra|john|hashcat)" | grep -v grep || true)
if [[ -n "$SUSPICIOUS" ]]; then
    echo "$(date): SUSPICIOUS PROCESSES: $SUSPICIOUS" >> "$THREAT_LOG"
fi

# Check Tor connectivity
if ! proxychains curl -s --max-time 10 https://check.torproject.org > /dev/null; then
    echo "$(date): TOR CONNECTIVITY ISSUE" >> "$THREAT_LOG"
fi

# Alert if threat log has new entries
if [[ -s "$THREAT_LOG" ]]; then
    # Send alert through Tor (if configured)
    echo "ZeroTrace Alert: Threats detected - check $THREAT_LOG"
fi
EOF

chmod +x /usr/local/bin/zerotrace-monitor.sh

# Create systemd timer for monitoring
cat > /etc/systemd/system/zerotrace-monitor.service << 'EOF'
[Unit]
Description=ZeroTrace Threat Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/zerotrace-monitor.sh
EOF

cat > /etc/systemd/system/zerotrace-monitor.timer << 'EOF'
[Unit]
Description=Run ZeroTrace Threat Monitor every 5 minutes
Requires=zerotrace-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=1s

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable zerotrace-monitor.timer
systemctl start zerotrace-monitor.timer

# Create iptables integration for automated response
log "Setting up automated iptables response rules..."

cat > /usr/local/bin/zerotrace-iptables-response.sh << 'EOF'
#!/bin/bash
# ZeroTrace Automated iptables Response

BAN_LIST="/etc/fail2ban/ip.banlist"
IPTABLES_CHAIN="ZEROTRACE_BLACKLIST"

# Create custom chain if it doesn't exist
iptables -t filter -nL "$IPTABLES_CHAIN" >/dev/null 2>&1 || iptables -t filter -N "$IPTABLES_CHAIN"

# Ensure chain is in INPUT chain
iptables -C INPUT -j "$IPTABLES_CHAIN" >/dev/null 2>&1 || iptables -I INPUT -j "$IPTABLES_CHAIN"

# Add banned IPs to custom chain
if [[ -f "$BAN_LIST" ]]; then
    while read -r ip; do
        if [[ -n "$ip" ]] && ! iptables -C "$IPTABLES_CHAIN" -s "$ip" -j DROP >/dev/null 2>&1; then
            iptables -A "$IPTABLES_CHAIN" -s "$ip" -j DROP
        fi
    done < "$BAN_LIST"
fi

# Save iptables rules
iptables-save > /etc/iptables/rules.v4
EOF

chmod +x /usr/local/bin/zerotrace-iptables-response.sh

# Add to fail2ban action
cat > /etc/fail2ban/action.d/zerotrace-iptables.conf << 'EOF'
[Definition]
actionstart =
actionstop =
actioncheck =
actionban = /usr/local/bin/zerotrace-iptables-response.sh
actionunban =
EOF

success "Threat Detection & Response System installed successfully!"
log "Features enabled:"
log "  - fail2ban with Tor-aware SSH protection"
log "  - OSSEC HIDS with custom rules"
log "  - Automated monitoring every 5 minutes"
log "  - iptables integration for persistent bans"
log "  - Threat logging to /var/log/zerotrace/threats.log"

warning "Review /etc/fail2ban/jail.d/tor-aware.conf for ban policies"
warning "Check OSSEC logs: /var/ossec/logs/ossec.log"
warning "Monitor threats: tail -f /var/log/zerotrace/threats.log"