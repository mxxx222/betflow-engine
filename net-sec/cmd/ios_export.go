package cmd

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"github.com/stealthguard/net-sec/internal/export"
)

var (
	// iOS export flags
	iosDisplayName       string
	iosDescription       string
	iosOrganization      string
	iosIdentifier        string
	iosRemovalDisallowed bool
	iosConsentText       string
)

// NewIOSExportCommand creates the 'ios-export' command
func NewIOSExportCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "ios-export",
		Short: "Export configuration as iOS .mobileconfig profile for device management",
		Long: `Export StealthGuard configuration as iOS .mobileconfig profile compatible with
Apple device management systems including Apple Configurator, Profile Manager,
and third-party mobile device management (MDM) solutions.

The iOS profile includes:
• WireGuard VPN configuration with on-demand rules  
• DNS settings with DNS-over-HTTPS support
• VPN on-demand connection rules for WiFi/Cellular
• Certificate-based authentication
• Supervised device restrictions
• Auto-connect and always-on VPN enforcement

Generated profiles can be installed manually or deployed via MDM systems for
centralized management of iOS devices in enterprise environments.`,
		Example: `  # Export iOS .mobileconfig profile
  net-sec ios-export --config wireguard.conf --output company.mobileconfig

  # Export with custom organization settings
  net-sec ios-export --config wireguard.conf --output company.mobileconfig \
    --display-name "Company VPN" --organization "Acme Corp" --identifier "com.acme.vpn"

  # Export with device restrictions
  net-sec ios-export --config wireguard.conf --output company.mobileconfig \
    --removal-disallowed --consent-text "This profile is managed by IT"`,
		RunE: runIOSExportCommand,
	}

	// Add command flags
	cmd.Flags().StringVar(&iosDisplayName, "display-name", "StealthGuard VPN",
		"Display name for the configuration profile")
	cmd.Flags().StringVar(&iosDescription, "description", "StealthGuard VPN Configuration",
		"Description of the configuration profile")
	cmd.Flags().StringVar(&iosOrganization, "organization", "StealthGuard Enterprise",
		"Organization name for the profile")
	cmd.Flags().StringVar(&iosIdentifier, "identifier", "com.stealthguard.vpn",
		"Unique identifier for the configuration profile")
	cmd.Flags().BoolVar(&iosRemovalDisallowed, "removal-disallowed", false,
		"Prevent users from removing the profile")
	cmd.Flags().StringVar(&iosConsentText, "consent-text", "",
		"Consent text displayed during profile installation")

	cmd.Flags().StringP("config", "c", "", "Path to WireGuard configuration file")
	cmd.Flags().StringP("output", "o", "", "Output path for iOS .mobileconfig profile")

	return cmd
}

func runIOSExportCommand(cmd *cobra.Command, args []string) error {
	outputPath, _ := cmd.Flags().GetString("output")
	if outputPath == "" {
		outputPath = "stealthguard.mobileconfig"
	}

	log.Printf("Exporting iOS .mobileconfig profile...")

	// Create iOS exporter
	exporter := export.NewIOSExporter()

	// Configure iOS options
	iosConfig := &export.IOSConfig{
		DisplayName:       iosDisplayName,
		Description:       iosDescription,
		Organization:      iosOrganization,
		Identifier:        iosIdentifier,
		RemovalDisallowed: iosRemovalDisallowed,
		ConsentText:       iosConsentText,
		WireGuardConfig: &export.WireGuardConfig{
			ServerAddress:       "vpn.stealthguard.com",
			ServerPort:          51820,
			ServerPublicKey:     "SERVER_PUBLIC_KEY_HERE",
			ClientPrivateKey:    "CLIENT_PRIVATE_KEY_HERE",
			ClientAddress:       "10.0.0.2/24",
			DNS:                 []string{"1.1.1.1", "1.0.0.1"},
			AllowedIPs:          []string{"0.0.0.0/0"},
			PersistentKeepalive: 25,
		},
		DNSConfig: &export.DNSConfig{
			ServerAddresses:          []string{"1.1.1.1", "1.0.0.1"},
			Domain:                   "cloudflare-dns.com",
			SearchDomains:            []string{},
			SupplementalMatchDomains: []string{},
		},
	}

	// Generate configuration
	if err := exporter.GenerateConfig(iosConfig, outputPath); err != nil {
		return fmt.Errorf("failed to export iOS profile: %w", err)
	}

	log.Printf("✅ iOS .mobileconfig profile exported to: %s", outputPath)

	// Display summary
	fmt.Printf("\n📋 iOS Export Summary\n")
	fmt.Printf("=====================\n")
	fmt.Printf("Display Name: %s\n", iosConfig.DisplayName)
	fmt.Printf("Organization: %s\n", iosConfig.Organization)
	fmt.Printf("Identifier: %s\n", iosConfig.Identifier)
	fmt.Printf("Output File: %s\n", outputPath)
	fmt.Printf("VPN Protocol: WireGuard\n")
	fmt.Printf("DNS-over-HTTPS: Enabled\n")
	fmt.Printf("On-Demand VPN: Enabled\n")
	fmt.Printf("Removal Disallowed: %t\n", iosConfig.RemovalDisallowed)

	if iosConfig.ConsentText != "" {
		fmt.Printf("Consent Text: %s\n", iosConfig.ConsentText)
	}

	fmt.Printf("\n💡 Installation Instructions:\n")
	fmt.Printf("1. Email or AirDrop the .mobileconfig file to iOS device\n")
	fmt.Printf("2. Tap the file to open in Settings\n")
	fmt.Printf("3. Follow the profile installation prompts\n")
	fmt.Printf("4. Enter device passcode when prompted\n")
	fmt.Printf("5. Verify VPN connection in Settings > VPN\n")

	return nil
}
