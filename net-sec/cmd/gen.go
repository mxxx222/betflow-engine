package cmd

import (
	"fmt"
	"log"

	"github.com/spf13/cobra"
	"github.com/stealthguard/net-sec/internal/wireguard"
)

var (
	serverEndpoint string
	serverKey      string
	clientName     string
	clientIP       string
	dns            []string
	mtu            int
	keepalive      int
	outputPath     string
	generateKeys   bool
)

// NewGenCommand creates the 'gen' command for WireGuard configuration generation
func NewGenCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "gen",
		Short: "Generate WireGuard VPN configurations",
		Long: `Generate WireGuard VPN configurations with automatic key generation,
IP allocation, and enterprise security policies.

Supports:
• Automatic public/private key pair generation
• Client configuration with server endpoint
• DNS configuration with DoH/DoT support
• MTU optimization and keepalive settings
• Kill-switch and leak protection policies
• Multiple output formats (conf, json, yaml)`,
		Example: `  # Generate client config with auto key generation
  net-sec gen --server wg.company.com:51820 --client mobile-user --ip 10.0.0.100/24

  # Generate with custom DNS and MTU settings
  net-sec gen --server vpn.enterprise.com:51820 --client laptop-001 \
    --ip 10.1.0.50/24 --dns 1.1.1.1 --dns 9.9.9.9 --mtu 1420

  # Generate keys only
  net-sec gen --generate-keys --output /etc/wireguard/`,
		RunE: runGenCommand,
	}

	// Command flags
	cmd.Flags().StringVar(&serverEndpoint, "server", "", "WireGuard server endpoint (host:port)")
	cmd.Flags().StringVar(&serverKey, "server-key", "", "Server public key (generated if empty)")
	cmd.Flags().StringVar(&clientName, "client", "net-sec-client", "Client identifier")
	cmd.Flags().StringVar(&clientIP, "ip", "", "Client IP address with CIDR (e.g., 10.0.0.100/24)")
	cmd.Flags().StringSliceVar(&dns, "dns", []string{"1.1.1.1", "9.9.9.9"}, "DNS servers")
	cmd.Flags().IntVar(&mtu, "mtu", 1420, "Interface MTU size")
	cmd.Flags().IntVar(&keepalive, "keepalive", 25, "Persistent keepalive interval (seconds)")
	cmd.Flags().StringVarP(&outputPath, "output", "o", "", "Output file path (default: stdout)")
	cmd.Flags().BoolVar(&generateKeys, "generate-keys", false, "Generate new key pair only")

	// Required flags
	cmd.MarkFlagRequired("server")

	return cmd
}

func runGenCommand(cmd *cobra.Command, args []string) error {
	log.Printf("Generating WireGuard configuration...")

	// Create WireGuard generator
	generator := wireguard.NewGenerator()

	// Configure generator options
	opts := &wireguard.GeneratorOptions{
		ServerEndpoint:  serverEndpoint,
		ServerPublicKey: serverKey,
		ClientName:      clientName,
		ClientIP:        clientIP,
		DNS:             dns,
		MTU:             mtu,
		Keepalive:       keepalive,
		GenerateKeys:    generateKeys || serverKey == "",
	}

	// Generate configuration
	config, err := generator.GenerateConfig(opts)
	if err != nil {
		return fmt.Errorf("failed to generate WireGuard config: %w", err)
	}

	// Output configuration
	if outputPath != "" {
		if err := config.WriteToFile(outputPath); err != nil {
			return fmt.Errorf("failed to write config to file: %w", err)
		}
		log.Printf("✅ WireGuard configuration written to: %s", outputPath)

		// Also write keys to separate files if generated
		if opts.GenerateKeys {
			if err := config.WriteKeysToFiles(outputPath); err != nil {
				log.Printf("⚠️  Warning: failed to write key files: %v", err)
			} else {
				log.Printf("🔑 Key files written alongside configuration")
			}
		}
	} else {
		// Output to stdout
		fmt.Print(config.String())
	}

	// Display configuration summary
	if verbose {
		summary := config.GetSummary()
		log.Printf("Configuration Summary:")
		log.Printf("  Client: %s", summary.ClientName)
		log.Printf("  Client IP: %s", summary.ClientIP)
		log.Printf("  Server: %s", summary.ServerEndpoint)
		log.Printf("  DNS: %v", summary.DNS)
		log.Printf("  MTU: %d", summary.MTU)
		log.Printf("  Keepalive: %d seconds", summary.Keepalive)
		if summary.KeysGenerated {
			log.Printf("  🔑 New keys generated")
		}
	}

	return nil
}
