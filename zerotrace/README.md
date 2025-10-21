# ZeroTrace - Privacy-Focused Raspberry Pi Setup

A reproducible, privacy-focused setup for Raspberry Pi devices (Pi 4 4GB+ or Zero 2) based on Parrot OS Home (light). This project provides deterministic, scriptable automation for building anonymous and secure systems.

## Hardware Requirements

- Raspberry Pi 4 (4GB+) or Zero 2
- microSD card (32GB+ recommended)
- Temporary keyboard/mouse and HDMI display (optional for headless setup)
- Computer with SD card writer

## Quickstart (5 Commands)

```bash
# 1. Flash Parrot OS to microSD (on host computer)
# Use Raspberry Pi Imager or Balena Etcher

# 2. Enable headless access (optional)
# Create wpa_supplicant.conf and ssh file in boot partition

# 3. Boot Pi and run initial setup
sudo ./scripts/10_post_boot.sh

# 4. Configure networking
sudo ./scripts/20_network_setup.sh

# 5. Install privacy stack and verify
sudo ./scripts/30_privacy_stack.sh
./verify/health_summary.sh
```

## Project Structure

```
zerotrace/
├── README.md              # This guide
├── .env.example           # Configuration template
├── LICENSE               # MIT License
├── scripts/              # Main automation scripts
│   ├── 00_flash_notes.md # Host-side imaging notes
│   ├── 10_post_boot.sh   # Post-boot setup
│   ├── 20_network_setup.sh # Network configuration
│   ├── 30_privacy_stack.sh # Tor + privacy tools
│   ├── 40_tools_optional.sh # Optional security tools
│   ├── 50_logs_hygiene.sh # Log management
│   ├── 60_zerotrace_framework.sh # ZeroTrace framework
├── verify/               # Verification scripts
│   ├── check_tor.sh      # Tor functionality check
│   ├── check_proxychains.sh # Proxychains verification
│   ├── check_services.sh # Service status checks
│   ├── health_summary.sh # Overall health check
├── headless/            # Headless setup resources
│   ├── boot_ssh_flag.md # SSH enable instructions
│   ├── wpa_supplicant_sample.conf # Wi-Fi template
│   ├── usb_gadget_zero_notes.md # Pi Zero USB gadget
├── systemd/             # Systemd service files
│   ├── journal_vacuum.service # Log cleanup service
│   └── journal_vacuum.timer  # Log cleanup timer
```

## Phase 1: OS Imaging (Host Computer)

### Download Parrot OS

Download Parrot OS Home (light) for Raspberry Pi from the official website:
- https://parrotsec.org/download/

### Flash the Image

Use Raspberry Pi Imager or Balena Etcher to write the image to your microSD card.

### Verification (Optional)

```bash
# Verify checksum (adjust filename as needed)
sha256sum parrot-home-rpi-*.img

# Compare with official checksums from Parrot website
```

## Phase 2: First Boot Setup

### Normal Setup (with Display)

1. Insert microSD card into Pi
2. Connect HDMI display, keyboard, and mouse
3. Power on the Pi
4. Follow on-screen setup instructions
5. Set username/password (change defaults!)

### Headless Setup (without Display)

1. **Enable SSH**: Create empty file named `ssh` in boot partition
2. **Configure Wi-Fi**: Create `wpa_supplicant.conf` in boot partition:

```bash
country=FI
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_SSID"
    psk="YOUR_WIFI_PASSWORD"
}
```

3. Insert microSD, power on Pi
4. Find Pi IP via router admin or `nmap -sn 192.168.1.0/24`
5. SSH in: `ssh username@pi-ip-address`

## Phase 3: Automated Setup

Run scripts in order (as root/sudo):

```bash
# 1. Post-boot setup (users, updates, basic hardening)
sudo ./scripts/10_post_boot.sh

# 2. Network configuration (Wi-Fi/Ethernet)
sudo ./scripts/20_network_setup.sh

# 3. Privacy stack installation (Tor, proxychains)
sudo ./scripts/30_privacy_stack.sh

# 4. Optional: Security tools (nmap, wireshark, metasploit)
# Edit .env first: INSTALL_TOOLS=true
sudo ./scripts/40_tools_optional.sh

# 5. Log hygiene setup
sudo ./scripts/50_logs_hygiene.sh

# 6. Optional: ZeroTrace framework
# Edit .env first: INSTALL_ZEROTRACE=true
sudo ./scripts/60_zerotrace_framework.sh
```

## Phase 4: Verification

```bash
# Individual checks
./verify/check_tor.sh
./verify/check_proxychains.sh
./verify/check_services.sh

# Comprehensive health check
./verify/health_summary.sh
```

## Configuration (.env)

Copy `.env.example` to `.env` and customize:

```bash
# Feature toggles
INSTALL_TOOLS=false
INSTALL_ZEROTRACE=false

# Wi-Fi settings (for headless)
WIFI_SSID=""
WIFI_PSK=""

# Regional settings
COUNTRY=FI
```

## Risk Model & Security Notes

### Default Protections
- All traffic routed through Tor via proxychains
- Default passwords must be changed
- Unnecessary services disabled
- Minimal inbound network exposure
- Regular log cleanup

### Potential Risks
- **MITM Attacks**: Mitigated by Tor encryption
- **DNS Leaks**: Prevented by Tor's built-in DNS
- **Timing Attacks**: Tor provides some protection
- **Exit Node Risks**: Use HTTPS and consider additional VPN

### Safe Defaults
- Proxychains configured with Tor only (no chain)
- Journal logs vacuumed every 2 days
- No open inbound ports by default
- Country code set to FI for regulatory compliance

## Troubleshooting Playbook

### Connectivity Issues
- **Wi-Fi not working**: Check country code in wpa_supplicant.conf
- **Router MAC filtering**: Add Pi MAC address to router whitelist
- **Wrong hostname**: Use `hostname` command to check

### Tor Bootstrap Failures
- **Stuck at 0%**: Check internet connectivity, try different bridges
- **DNS issues**: Verify /etc/resolv.conf, try `tor --verify-config`

### Headless Access Problems
- **SSH disabled**: Ensure `ssh` file exists in boot partition
- **mDNS not working**: Try IP address directly
- **USB gadget issues**: Pi Zero requires specific OTG configuration

### Pi Model Differences
- **Pi Zero/Zero 2**: USB OTG mode for networking
- **Pi 4**: USB-C for power only, video via micro-HDMI

## Maintenance

### Log Management
```bash
# Manual log cleanup
sudo journalctl --vacuum-time=2d

# Check timer status
systemctl status journal_vacuum.timer
```

### Updates
```bash
# Regular updates (use proxychains for privacy)
sudo proxychains apt update && sudo proxychains apt upgrade
```

## License

MIT License - See LICENSE file for details.

## Support

For issues, check the troubleshooting section above. Ensure all scripts are run in order and verification scripts pass before proceeding.
