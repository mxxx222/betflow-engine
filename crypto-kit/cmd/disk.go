package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"

	"github.com/spf13/cobra"
)

var (
	diskDevice string
	diskAlgo   string
	diskInit   bool
	diskMount  string
	diskLabel  string
)

// diskCmd represents the disk command
var diskCmd = &cobra.Command{
	Use:   "disk",
	Short: "Cross-platform disk encryption management",
	Long: `Manage disk encryption across different operating systems.

Supports:
• Linux: LUKS with cryptsetup
• macOS: APFS encryption with diskutil
• Windows: BitLocker with PowerShell
• Hardware key integration for unlock

Examples:
  crypto-kit disk --init --device /dev/sdb --algo XTS-AES-256 --label SecureData
  crypto-kit disk --mount /dev/sdb --label SecureData  
  crypto-kit disk --init --device /dev/disk2 --algo AES-XTS (macOS)`,
	RunE: runDisk,
}

func init() {
	rootCmd.AddCommand(diskCmd)

	diskCmd.Flags().StringVar(&diskDevice, "device", "", "target device (e.g., /dev/sdb, /dev/disk2)")
	diskCmd.Flags().StringVar(&diskAlgo, "algo", "XTS-AES-256", "encryption algorithm")
	diskCmd.Flags().BoolVar(&diskInit, "init", false, "initialize disk encryption")
	diskCmd.Flags().StringVar(&diskMount, "mount", "", "mount point for encrypted disk")
	diskCmd.Flags().StringVar(&diskLabel, "label", "CryptoKit", "volume label")
}

func runDisk(cmd *cobra.Command, args []string) error {
	logVerbose("Starting disk encryption management")

	if diskDevice == "" {
		return fmt.Errorf("device parameter is required")
	}

	logVerbose("Operating System: %s", runtime.GOOS)
	logVerbose("Device: %s", diskDevice)
	logVerbose("Algorithm: %s", diskAlgo)

	// Check if device exists (basic validation)
	if _, err := os.Stat(diskDevice); os.IsNotExist(err) {
		return fmt.Errorf("device does not exist: %s", diskDevice)
	}

	switch runtime.GOOS {
	case "linux":
		return handleLinuxDisk()
	case "darwin":
		return handleMacOSDisk()
	case "windows":
		return handleWindowsDisk()
	default:
		return fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}
}

func handleLinuxDisk() error {
	logVerbose("Using Linux cryptsetup for disk encryption")

	if diskInit {
		fmt.Printf("🔒 Initializing LUKS encryption on %s...\n", diskDevice)
		
		// Check if cryptsetup is available
		if _, err := exec.LookPath("cryptsetup"); err != nil {
			return fmt.Errorf("cryptsetup not found. Install with: sudo apt install cryptsetup")
		}

		// Warn user about data destruction
		fmt.Printf("⚠️  WARNING: This will DESTROY all data on %s!\n", diskDevice)
		fmt.Printf("Press CTRL+C to abort or ENTER to continue...")
		fmt.Scanln()

		// Create LUKS container
		cmd := exec.Command("sudo", "cryptsetup", "luksFormat", 
			"--type", "luks2",
			"--cipher", strings.ToLower(diskAlgo),
			"--hash", "sha256",
			"--key-size", "256",
			diskDevice)
		
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		if err := cmd.Run(); err != nil {
			return fmt.Errorf("failed to create LUKS container: %w", err)
		}

		fmt.Printf("✅ LUKS container created successfully\n")

		// Open the container
		containerName := diskLabel + "_encrypted"
		openCmd := exec.Command("sudo", "cryptsetup", "open", diskDevice, containerName)
		openCmd.Stdin = os.Stdin
		openCmd.Stdout = os.Stdout
		openCmd.Stderr = os.Stderr

		if err := openCmd.Run(); err != nil {
			return fmt.Errorf("failed to open LUKS container: %w", err)
		}

		// Create filesystem
		mkfsCmd := exec.Command("sudo", "mkfs.ext4", "-L", diskLabel, "/dev/mapper/"+containerName)
		if err := mkfsCmd.Run(); err != nil {
			return fmt.Errorf("failed to create filesystem: %w", err)
		}

		fmt.Printf("✅ Encrypted disk initialized: /dev/mapper/%s\n", containerName)
		
		// Provide usage instructions
		printLinuxInstructions(diskDevice, containerName)

	} else {
		return fmt.Errorf("specify --init to initialize disk encryption")
	}

	return nil
}

func handleMacOSDisk() error {
	logVerbose("Using macOS diskutil for disk encryption")

	if diskInit {
		fmt.Printf("🔒 Initializing APFS encryption on %s...\n", diskDevice)
		
		// Check if diskutil is available (should be on macOS)
		if _, err := exec.LookPath("diskutil"); err != nil {
			return fmt.Errorf("diskutil not found")
		}

		// Warn user about data destruction
		fmt.Printf("⚠️  WARNING: This will DESTROY all data on %s!\n", diskDevice)
		fmt.Printf("Press CTRL+C to abort or ENTER to continue...")
		fmt.Scanln()

		// Erase and format as encrypted APFS
		cmd := exec.Command("diskutil", "apfs", "createContainer",
			"-passphrase", "-",
			diskDevice)
		
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		if err := cmd.Run(); err != nil {
			return fmt.Errorf("failed to create encrypted APFS container: %w", err)
		}

		fmt.Printf("✅ Encrypted APFS container created successfully\n")
		
		// Provide usage instructions
		printMacOSInstructions(diskDevice)

	} else {
		return fmt.Errorf("specify --init to initialize disk encryption")
	}

	return nil
}

func handleWindowsDisk() error {
	logVerbose("Using Windows BitLocker for disk encryption")
	
	if diskInit {
		fmt.Printf("🔒 Initializing BitLocker encryption on %s...\n", diskDevice)
		
		// Check if PowerShell is available
		if _, err := exec.LookPath("powershell"); err != nil {
			return fmt.Errorf("PowerShell not found")
		}

		// Warn user about data destruction
		fmt.Printf("⚠️  WARNING: This will encrypt %s with BitLocker!\n", diskDevice)
		fmt.Printf("Press CTRL+C to abort or ENTER to continue...")
		fmt.Scanln()

		// Enable BitLocker (this is a simplified example)
		psScript := fmt.Sprintf(`
			Enable-BitLocker -MountPoint "%s" -EncryptionMethod AES256 -UsedSpaceOnly
		`, diskDevice)

		cmd := exec.Command("powershell", "-Command", psScript)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		if err := cmd.Run(); err != nil {
			return fmt.Errorf("failed to enable BitLocker: %w", err)
		}

		fmt.Printf("✅ BitLocker encryption initiated on %s\n", diskDevice)
		
		// Provide usage instructions
		printWindowsInstructions(diskDevice)

	} else {
		return fmt.Errorf("specify --init to initialize disk encryption")
	}

	return nil
}

func printLinuxInstructions(device, containerName string) {
	fmt.Printf("\n📋 Linux LUKS Usage Instructions:\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Mount: sudo cryptsetup open %s %s && sudo mount /dev/mapper/%s /mnt\n", device, containerName, containerName)
	fmt.Printf("Unmount: sudo umount /mnt && sudo cryptsetup close %s\n", containerName)
	fmt.Printf("Status: sudo cryptsetup status %s\n", containerName)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
}

func printMacOSInstructions(device string) {
	fmt.Printf("\n📋 macOS APFS Usage Instructions:\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Mount: diskutil mount %s\n", device)
	fmt.Printf("Unmount: diskutil unmount %s\n", device)
	fmt.Printf("Status: diskutil info %s\n", device)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
}

func printWindowsInstructions(device string) {
	fmt.Printf("\n📋 Windows BitLocker Usage Instructions:\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Status: manage-bde -status %s\n", device)
	fmt.Printf("Unlock: manage-bde -unlock %s\n", device)
	fmt.Printf("Lock: manage-bde -lock %s\n", device)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
}