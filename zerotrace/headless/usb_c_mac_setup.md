# Headless Setup via USB-C to MacBook

## For Raspberry Pi Zero 2 W (Recommended for USB Gadget Mode)

This guide covers setting up your Raspberry Pi Zero 2 W using only a USB-C data cable connected to your MacBook, without any HDMI screen or additional peripherals.

## Prerequisites

- Raspberry Pi Zero 2 W (with USB data port)
- USB-C to Micro-USB data cable (or appropriate adapter)
- MacBook with internet connection
- microSD card with Parrot OS flashed

## Step 1: Enable USB Ethernet Gadget Mode

### On the microSD card (before booting):

1. **Mount the boot partition** on your Mac:
   ```bash
   # Find the SD card (usually /dev/disk2s1)
   diskutil list
   
   # Mount the partition
   diskutil mount /dev/disk2s1
   ```

2. **Enable USB gadget mode** by editing /Volumes/boot/config.txt:
   Add this line at the end:
   ```
   dtoverlay=dwc2
   ```

3. **Enable Ethernet gadget** by editing /Volumes/boot/cmdline.txt:
   Find the line starting with rootwait and add after it:
   ```
   modules-load=dwc2,g_ether
   ```

4. **Enable SSH** by creating an empty file:
   ```bash
   touch /Volumes/boot/ssh
   ```

5. **Unmount safely**:
   ```bash
   diskutil unmount /Volumes/boot
   ```

## Step 2: Configure Network on Pi

Create a network configuration file on the boot partition:

```bash
# Create interfaces file
cat > /Volumes/boot/interfaces << 'INTERFACES_EOF'
auto usb0
iface usb0 inet static
    address 192.168.7.2
    netmask 255.255.255.0
    gateway 192.168.7.1
INTERFACES_EOF
```

## Step 3: Connect and Setup on MacBook

1. **Insert microSD** into Pi Zero 2 W
2. **Connect USB data cable** from Pi to MacBook
3. **Power on the Pi** (using the same USB cable for power)

4. **On your MacBook, configure network**:
   ```bash
   # Check if new network interface appears
   networksetup -listallhardwareports
   
   # Configure the USB Ethernet interface
   sudo ifconfig enX inet 192.168.7.1 netmask 255.255.255.0
   ```
   (Replace enX with your actual interface name, usually en7 or en8)

5. **Enable internet sharing** (optional):
   - System Preferences → Sharing → Internet Sharing
   - Share from: Wi-Fi
   - To computers using: USB Ethernet
   - Check "Internet Sharing"

## Step 4: SSH into Pi

```bash
# SSH into the Pi
ssh parrot@192.168.7.2

# Default password is usually "parrot" - CHANGE THIS IMMEDIATELY
passwd
```

## Step 5: Run Automated Setup

Once connected via SSH, run the ZeroTrace scripts:

```bash
# 1. Post-boot setup
sudo ./scripts/10_post_boot.sh

# 2. Network setup (configure Wi-Fi for future use)
sudo ./scripts/20_network_setup.sh

# 3. Privacy stack installation
sudo ./scripts/30_privacy_stack.sh

# 4. Verify everything works
./verify/health_summary.sh
```

## Troubleshooting

### If connection fails:

1. **Check interface on Mac**:
   ```bash
   ifconfig | grep 192.168.7
   ```

2. **Check Pi response**:
   ```bash
   ping 192.168.7.2
   ```

3. **Reset network on Mac**:
   ```bash
   sudo networksetup -setmanual "USB Ethernet" 192.168.7.1 255.255.255.0
   ```

4. **Check if Pi is getting power** - the green LED should blink

### Alternative: Serial Console

If USB Ethernet doesn't work, you can use serial console:

1. Enable serial console in /Volumes/boot/config.txt:
   ```
   enable_uart=1
   ```

2. Use a USB-TTL serial adapter
3. Connect with screen or minicom:
   ```bash
   screen /dev/tty.usbserial 115200
   ```

## Important Notes

- **Pi 4 Warning**: Raspberry Pi 4 cannot act as USB device. This method only works with Pi Zero/Zero 2 W.
- **Power**: Some MacBooks may not provide enough power. Use a powered USB hub if needed.
- **Security**: Change all default passwords immediately after first login.
- **Persistence**: Once setup is complete, configure Wi-Fi for standalone operation.
