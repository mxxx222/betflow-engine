# Host-Side Imaging Notes

## Required Tools

- Raspberry Pi Imager (recommended): https://www.raspberrypi.com/software/
- Balena Etcher: https://www.balena.io/etcher/
- SHA256sum utility (for verification)

## Parrot OS Download

1. Visit: https://parrotsec.org/download/
2. Select "Parrot Home" edition
3. Choose "Raspberry Pi" architecture
4. Download the latest lightweight image

## Verification Steps

```bash
# Download checksum file from Parrot website
# Verify image integrity
sha256sum parrot-home-rpi-*.img

# Compare with official checksum
cat parrot-home-rpi-*.sha256
```

## Imaging Process

### Using Raspberry Pi Imager
1. Open Raspberry Pi Imager
2. Choose OS: "Use custom" → select downloaded Parrot image
3. Choose Storage: Select your microSD card
4. Click Write → Confirm

### Using Balena Etcher
1. Open Balena Etcher
2. Select image file
3. Select drive (microSD)
4. Click Flash

## Headless Preparation (Optional)

After imaging, before ejecting microSD:

1. **Enable SSH**: Create empty file named `ssh` in boot partition
2. **Configure Wi-Fi**: Create `wpa_supplicant.conf` with your network details

## Safety Notes

- Double-check you're writing to the correct drive
- Ensure microSD card has enough capacity (32GB+ recommended)
- Verify download integrity to avoid corrupted images
