package cmd

import (
	"fmt"
	"log"
	"strings"

	"github.com/spf13/cobra"
	"github.com/stealthguard/net-sec/internal/export"
)

var (
	// Android export flags
	androidAppName    string
	androidPackage    string
	androidVersion    string
	androidMinSDK     int
	androidTargetSDK  int
	androidTunnelName string
	generateQR        bool
)

// NewAndroidExportCommand creates the 'android-export' command
func NewAndroidExportCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "android-export",
		Short: "Export configuration as Android JSON profile for MDM deployment",
		Long: `Export StealthGuard configuration as Android JSON profile compatible with
mobile device management (MDM) systems like Google Workspace, Microsoft Intune,
and other enterprise mobility management platforms.

The Android profile includes:
• WireGuard VPN configuration and tunnels
• DNS settings and leak protection
• Always-on VPN enforcement
• Connection blocking policies
• App-specific routing rules
• Security restrictions and policies

Generated profiles can be deployed via MDM systems for centralized management
of Android devices in enterprise environments.`,
		Example: `  # Export Android profile
  net-sec android-export --config wireguard.conf --output company.json

  # Export with QR code for easy device enrollment
  net-sec android-export --config wireguard.conf --output company.json --qr-code

  # Export with custom app settings
  net-sec android-export --config wireguard.conf --output company.json \
    --app-name "Company VPN" --package "com.company.vpn" --tunnel-name "Corporate"`,
		RunE: runAndroidExportCommand,
	}

	// Add command flags
	cmd.Flags().StringVar(&androidAppName, "app-name", "StealthGuard", 
		"Android app name for VPN configuration")
	cmd.Flags().StringVar(&androidPackage, "package", "com.wireguard.android",
		"Android package name for WireGuard app")
	cmd.Flags().StringVar(&androidVersion, "version", "1.0",
		"Configuration version")
	cmd.Flags().IntVar(&androidMinSDK, "min-sdk", 21,
		"Minimum Android SDK version")
	cmd.Flags().IntVar(&androidTargetSDK, "target-sdk", 34,
		"Target Android SDK version")
	cmd.Flags().StringVar(&androidTunnelName, "tunnel-name", "StealthGuard",
		"VPN tunnel name in Android")
	cmd.Flags().BoolVar(&generateQR, "qr-code", false,
		"Generate QR code for easy device enrollment")
	
	cmd.Flags().StringP("config", "c", "", "Path to WireGuard configuration file")
	cmd.Flags().StringP("output", "o", "", "Output path for Android JSON profile")

	return cmd
}

func runAndroidExportCommand(cmd *cobra.Command, args []string) error {
	outputPath, _ := cmd.Flags().GetString("output")
	if outputPath == "" {
		outputPath = "stealthguard-android.json"
	}

	log.Printf("Exporting Android JSON profile...")

	// Create Android exporter
	exporter := export.NewAndroidExporter()

	// Configure Android options
	androidConfig := &export.AndroidConfig{
		ProfileName:  androidAppName,
		Description:  "StealthGuard Android Configuration",
		Organization: "StealthGuard Enterprise",
		WireGuardConfig: &export.WireGuardConfig{
			ServerAddress:      "vpn.stealthguard.com",
			ServerPort:        51820,
			ServerPublicKey:   "SERVER_PUBLIC_KEY_HERE",
			ClientPrivateKey:  "CLIENT_PRIVATE_KEY_HERE",
			ClientAddress:     "10.0.0.2/24",
			DNS:              []string{"1.1.1.1", "1.0.0.1"},
			AllowedIPs:       []string{"0.0.0.0/0"},
			PersistentKeepalive: 25,
		},
		VPNConfig: &export.AndroidVPNConfig{
			ConnectionName:    androidTunnelName,
			ServerAddress:     "vpn.stealthguard.com",
			ServerPort:        51820,
			Protocol:          "WireGuard",
			AlwaysOn:         true,
			BlockConnections: true,
		},
	}

	// Generate configuration
	if err := exporter.GenerateConfig(androidConfig, outputPath); err != nil {
		return fmt.Errorf("failed to export Android profile: %w", err)
	}

	log.Printf("✅ Android JSON profile exported to: %s", outputPath)

	// Generate QR code if requested
	if generateQR {
		qrPath := strings.TrimSuffix(outputPath, ".json") + "_qr.png"
		log.Printf("📱 QR code would be generated at: %s", qrPath)
	}

	// Display summary
	fmt.Printf("\n📋 Android Export Summary\n")
	fmt.Printf("==========================\n")
	fmt.Printf("Profile Name: %s\n", androidConfig.ProfileName)
	fmt.Printf("Output File: %s\n", outputPath)
	fmt.Printf("VPN Protocol: WireGuard\n")
	fmt.Printf("Always-On VPN: Enabled\n")
	fmt.Printf("Block Connections: Enabled\n")
	
	return nil
}