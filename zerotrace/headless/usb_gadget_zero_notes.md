# Pi Zero/Zero 2 USB Gadget Mode Notes

## Overview

Raspberry Pi Zero and Zero 2 support USB On-The-Go (OTG) functionality, allowing them to appear as various USB devices to a host computer. This is particularly useful for headless setup without additional networking hardware.

## Common USB Gadget Modes

### 1. Ethernet over USB (Most Useful for Headless)

The Pi appears as a USB Ethernet device. The host computer can:
- Assign an IP address to the Pi
- SSH into the Pi
- Share internet connection with the Pi

### 2. Serial over USB

The Pi appears as a serial device, accessible via terminal emulator.

### 3. Mass Storage

The Pi appears as a USB drive (not recommended for daily use).

## Configuration for Ethernet Gadget Mode

### Step 1: Enable USB OTG

Add to `/boot/config.txt`:
```
dtoverlay=dwc2
```

### Step 2: Enable Gadget Module

Add to `/boot/cmdline.txt` (after `rootwait`):
```
modules-load=dwc2,g_ether
```

### Step 3: Configure Network (Pi Side)

Add to `/etc/network/interfaces` or use dhcpcd:
```
auto usb0
iface usb0 inet static
    address 192.168.7.2
    netmask 255.255.255.0
    gateway 192.168.7.1
```

### Step 4: Host Computer Setup

#### Linux:
- The Pi should appear as a new network interface
- Assign static IP or use DHCP

#### Windows:
- May require RNDIS drivers
- Download from Raspberry Pi Foundation if needed

#### macOS:
- Usually works automatically
- Check Network preferences for new interface

## Pi 4 Differences

**Important**: Raspberry Pi 4 does NOT support USB gadget mode in the same way. The USB-C port on Pi 4 is for power input only and cannot act as a USB device.

For Pi 4 headless setup, you must use:
- Ethernet cable
- Wi-Fi (with wpa_supplicant.conf)
- Bluetooth tethering (advanced)
- Serial console (requires USB-TTL adapter)

## Troubleshooting

### Common Issues:
1. **Driver problems on host**: Ensure proper drivers installed
2. **IP address conflicts**: Use different subnet than your main network
3. **Kernel module not loading**: Check dmesg for errors
4. **Power issues**: Some hosts don't provide enough power over USB

### Verification:
```bash
# On Pi, check if usb0 interface exists
ip link show usb0

# On host, check for new network device
ip link show  # Linux
netstat -rn   # macOS/Windows
```

## Security Notes

- USB gadget mode creates a direct connection between Pi and host
- No network isolation - the host can access Pi directly
- Consider this when choosing between Wi-Fi and USB gadget for headless setup
- For production use, prefer Wi-Fi with proper security configuration
