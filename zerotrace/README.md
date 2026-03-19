# ZeroTrace - Privacy-Focused Raspberry Pi Device Security Framework

A comprehensive, reproducible, privacy-focused setup specifically designed for Raspberry Pi devices (Pi 4 4GB+ or Zero 2) running Parrot OS. This project provides deterministic, scriptable automation for building anonymous and secure privacy-focused systems.

## 🛡️ Device-Specific Features

### Hardware Compatibility
- **Raspberry Pi 4** (4GB+ recommended) - Full feature support
- **Raspberry Pi Zero 2** - USB gadget mode support
- **microSD cards** (32GB+ recommended)
- **USB WiFi adapters** for monitor mode capabilities
- **External drives** for encrypted backups

### Privacy-Focused Architecture
- **Tor-only routing** via proxychains configuration
- **Log hygiene** with automated cleanup
- **Service minimization** - only essential services
- **Network isolation** and traffic analysis resistance
- **Encrypted backup** and recovery systems

## ⚡ Quick Start (3 Commands)

```bash
# 1. Flash Parrot OS to microSD (host computer)
# Use Raspberry Pi Imager with Parrot OS Home (light) for ARM64

# 2. Boot Pi and run automated setup
sudo ./scripts/10_post_boot.sh
sudo ./scripts/20_network_setup.sh  
sudo ./scripts/30_privacy_stack.sh

# 3. Install high-ROI security add-ons (optional but recommended)
sudo ./scripts/90_install_addons.sh
```

## 🏗️ Project Structure

```
zerotrace/
├── README.md                    # This guide
├── .env.example                 # Configuration template
├── .gitignore                   # Security-focused exclusions
├── LICENSE                      # MIT License
├── scripts/                     # Automated setup scripts
│   ├── 00_flash_notes.md       # Host imaging instructions
│   ├── 10_post_boot.sh         # Initial system setup
│   ├── 20_network_setup.sh     # Network configuration
│   ├── 30_privacy_stack.sh     # Tor + proxychains setup
│   ├── 40_tools_optional.sh    # Optional security tools
│   ├── 50_logs_hygiene.sh      # Log management
│   ├── 60_zerotrace_framework.sh # Framework installation
│   ├── 70_threat_detection.sh  # Security monitoring
│   ├── 80_backup_recovery.sh   # Encrypted backups
│   └── 90_install_addons.sh    # Unified add-ons installer
├── verify/                      # Health verification scripts
│   ├── check_tor.sh            # Tor connectivity test
│   ├── check_proxychains.sh    # Proxychains verification  
│   ├── check_services.sh       # Service status
│   ├── check_addons.sh         # Add-ons verification
│   └── health_summary.sh       # Complete health check
├── auto-diagnostics/            # Device-specific diagnostics
├── headless/                   # Headless setup resources
├── systemd/                    # Service configurations
└── verify/                     # System health checks
```

## 🎯 Core Features

### Base Privacy Configuration
- **Tor Integration**: All traffic routed through Tor network
- **Proxychains Configuration**: Force applications through Tor
- **DNS Privacy**: Tor-based DNS resolution
- **Log Management**: Automated journal cleanup
- **Service Hardening**: Disable unnecessary services

### High-ROI Add-ons (Optional)
- **Threat Detection System (85% ROI)**: fail2ban + OSSEC HIDS
- **Encrypted Backup Framework (78% ROI)**: BorgBackup + GPG
- **Performance Monitoring (65% ROI)**: Prometheus + Grafana

### Device-Specific Optimizations
- **Raspberry Pi 4**: Optimized for 4GB+ RAM configuration
- **Raspberry Pi Zero 2**: USB gadget mode for networking
- **Thermal Management**: Automatic throttling prevention
- **SD Card Protection**: Health monitoring and wear reduction
- **Power Management**: Optimal power consumption

## 🔧 Configuration

### Environment Setup
```bash
# Copy and customize configuration
cp .env.example .env

# Edit for your specific setup
nano .env
```

### Key Configuration Options
```bash
# Feature toggles
INSTALL_TOOLS=false
INSTALL_ZEROTRACE=false

# Hardware-specific
WIFI_SSID="your_network"
WIFI_PSK="your_password"
COUNTRY=FI  # For regulatory compliance
```

## 🚀 Deployment Options

### Normal Setup (with Display)
1. Connect HDMI, keyboard, mouse
2. Boot from flashed microSD
3. Follow on-screen setup
4. Run automation scripts

### Headless Setup (Remote Access)
1. Create `ssh` file in boot partition
2. Configure `wpa_supplicant.conf` in boot partition
3. SSH into device after boot
4. Run automation scripts remotely

## 🔍 Verification

### Basic Health Check
```bash
./verify/health_summary.sh
```

### Individual Component Tests
```bash
./verify/check_tor.sh        # Test Tor connectivity
./verify/check_proxychains.sh # Verify proxychains
./verify/check_services.sh   # Check service status
./verify/check_addons.sh     # Verify add-ons (if installed)
```

### Manual Tor Test
```bash
# Should show Tor exit node IP
curl --max-time 10 https://check.torproject.org
```

## 🔒 Security Features

### Privacy Protection
- **Traffic Anonymization**: All traffic through Tor network
- **DNS Privacy**: Tor's built-in DNS resolver
- **Metadata Protection**: Minimal logging and metadata
- **Network Analysis Resistance**: Traffic timing obfuscation

### System Hardening
- **Service Minimization**: Only essential services running
- **Log Hygiene**: Automatic log cleanup and rotation
- **User Hardening**: Non-root user with minimal privileges
- **Network Isolation**: Minimal inbound network exposure

### Threat Detection
- **Automated Monitoring**: fail2ban with Tor-aware rules
- **HIDS Integration**: OSSEC for file integrity monitoring
- **Network Monitoring**: Detection of suspicious activities
- **Automated Response**: IP blocking and service isolation

## 🛠️ Maintenance

### Regular Updates
```bash
# Update system through Tor (privacy-preserving)
sudo proxychains apt update && sudo proxychains apt upgrade
```

### Health Monitoring
```bash
# Check system health
./verify/health_summary.sh

# Monitor logs
tail -f /var/log/zerotrace/threats.log  # If threat detection installed
tail -f /var/log/zerotrace/backup.log   # If backup system installed
```

### Backup Management
```bash
# Manual backup (if backup system installed)
zerotrace-backup

# Verify backup integrity
zerotrace-verify
```

## ⚠️ Important Notes

### Legal Compliance
- Use only on networks you own or have permission to access
- Comply with local laws and regulations
- This tool is for legitimate privacy protection and security research

### Hardware Requirements
- **Minimum**: 2GB RAM, 16GB microSD
- **Recommended**: 4GB+ RAM, 32GB+ microSD
- **Optimal**: 8GB RAM, 64GB+ microSD + external storage

### Performance Considerations
- **Tor Speed**: Expect slower internet speeds (trade-off for privacy)
- **Battery Life**: Intensive use may require external power
- **Heat Management**: Monitor temperatures under heavy load

## 🆘 Troubleshooting

### Common Issues
- **Tor not connecting**: Check internet connectivity and Tor service
- **Slow performance**: Normal for Tor-based routing
- **WiFi issues**: Verify country code in configuration
- **SSH not working**: Ensure `ssh` file created in boot partition

### Device-Specific Issues
- **Pi Zero USB issues**: Use specific USB gadget configuration
- **Pi 4 thermal throttling**: Ensure adequate cooling
- **SD card performance**: Consider high-speed, high-endurance cards

### Getting Help
1. Check verification scripts output
2. Review log files in `/var/log/zerotrace/`
3. Consult device-specific documentation in `auto-diagnostics/`
4. Verify Tor connectivity and proxychains configuration

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

This is a device-specific security framework. Contributions for:
- Hardware compatibility improvements
- Performance optimizations
- Security enhancements
- Device-specific features

## 🔗 Related Projects

- **Parrot OS**: Base operating system
- **Tor Project**: Privacy network
- **fail2ban**: Intrusion prevention
- **OSSEC**: Host intrusion detection
- **BorgBackup**: Encrypted backups

---

**ZeroTrace**: Privacy-focused security framework for Raspberry Pi devices. Secure, automated, and reproducible privacy protection.
