# Best Flash & Setup Guide for Raspberry Pi 4

## Recommended Setup Method

### Option 1: HDMI + Keyboard (Easiest for Pi 4)

**What you need:**
- microSD card (32GB+)
- HDMI cable + monitor/TV
- USB keyboard
- Raspberry Pi Imager on your computer
- Power supply for Pi 4

**Steps:**

1. **Download Parrot OS**:
   - Get Parrot OS Home (light) for Raspberry Pi from https://parrotsec.org/download/

2. **Flash with Raspberry Pi Imager** (recommended):
   - Install Raspberry Pi Imager on your computer
   - Choose OS: "Use custom" → select downloaded Parrot image
   - Choose Storage: Select your microSD card
   - Click Write → Confirm

3. **First Boot with Display**:
   - Insert microSD into Pi 4
   - Connect HDMI to monitor
   - Connect USB keyboard
   - Connect power supply
   - Follow on-screen setup instructions
   - Set username/password (change defaults!)

4. **Enable Remote Access**:
   ```bash
   # Enable SSH for future headless access
   sudo systemctl enable ssh
   sudo systemctl start ssh
   
   # Find your IP address
   ip addr show
   ```

### Option 2: Headless Wi-Fi Setup (No Display Needed)

**What you need:**
- microSD card
- Computer with SD card reader
- Raspberry Pi Imager
- Wi-Fi network credentials

**Steps:**

1. **Flash with Raspberry Pi Imager** with advanced options:
   - Use Raspberry Pi Imager
   - Click the gear icon ⚙️ for advanced options
   - Set hostname: zerotrace-pi
   - Enable SSH (password authentication)
   - Configure Wi-Fi: Enter your SSID and password
   - Set locale: FI (Finland)
   - Flash the image

2. **Boot Pi 4**:
   - Insert microSD card
   - Connect power supply
   - Wait 2-3 minutes for boot

3. **Find and Connect**:
   ```bash
   # Scan for Pi on network
   nmap -sn 192.168.1.0/24 | grep -i raspberry
   
   # Or use mDNS (if supported)
   ssh parrot@zerotrace-pi.local
   ```

## Micro-USB Note for Pi 4

**Important**: Raspberry Pi 4 uses USB-C for power, NOT micro-USB.

- **Pi 4**: USB-C power input (like modern phones)
- **Pi Zero**: Micro-USB power input
- **Data transfer**: Pi 4 cannot use USB for data transfer like Pi Zero can

## Recommended ZeroTrace Setup Flow

Once you have access (via HDMI or SSH):

```bash
# 1. Run post-boot setup
sudo ./scripts/10_post_boot.sh

# 2. Configure network (if not already done)
sudo ./scripts/20_network_setup.sh

# 3. Install privacy stack
sudo ./scripts/30_privacy_stack.sh

# 4. Verify everything works
./verify/health_summary.sh

# 5. Optional: Install security tools
# Edit .env: INSTALL_TOOLS=true
sudo ./scripts/40_tools_optional.sh
```

## Touchscreen Consideration

If you have a Raspberry Pi touchscreen:
- **Pros**: Direct interaction, good for initial setup
- **Cons**: Not needed for ZeroTrace (designed for headless/remote operation)
- **Recommendation**: Use for initial setup, then operate remotely via SSH

## Quickest Method Summary

1. **Flash with Raspberry Pi Imager** (with built-in Wi-Fi/SSH config)
2. **Boot Pi 4** with power and Ethernet/Wi-Fi
3. **SSH into Pi** using hostname or IP
4. **Run automated scripts** from zerotrace directory

This avoids needing any peripherals after the initial flash!
