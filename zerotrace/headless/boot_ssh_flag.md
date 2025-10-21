# Headless SSH Enable Instructions

## For Raspberry Pi OS (and most derivatives including Parrot OS)

To enable SSH on first boot for headless setup:

1. **After flashing** the microSD card, but before booting:
2. **Mount the boot partition** on your computer
3. **Create an empty file** named `ssh` (no extension) in the root of the boot partition
4. **Unmount safely** and insert into Raspberry Pi

### Example commands (Linux/Mac):

```bash
# Find the SD card partition (usually /dev/sdX1 or /dev/mmcblk0p1)
lsblk

# Mount the boot partition
sudo mkdir -p /mnt/sd_boot
sudo mount /dev/sdX1 /mnt/sd_boot

# Create ssh file
sudo touch /mnt/sd_boot/ssh

# Unmount
sudo umount /mnt/sd_boot
```

### Windows:
- Open File Explorer
- Find the boot drive (usually labeled "boot")
- Right-click → New → Text Document
- Rename to `ssh` (remove .txt extension)
- Eject safely

## Important Notes

- The `ssh` file will be automatically deleted on first boot
- SSH will remain enabled after first boot
- For additional security, consider:
  - Changing default SSH port
  - Using key-based authentication
  - Disabling root login
  - Configuring firewall rules

## Troubleshooting

If SSH doesn't work:
- Verify the `ssh` file was created in the correct partition
- Check that the file has no extension (not `ssh.txt`)
- Ensure proper Wi-Fi configuration (if using headless Wi-Fi)
- Check router for assigned IP address
