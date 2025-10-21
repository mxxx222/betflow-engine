package cmd

import (
	"fmt"
	"os"

	"filippo.io/age"
	"github.com/spf13/cobra"
)

// keygenCmd represents the keygen command
var keygenCmd = &cobra.Command{
	Use:   "keygen",
	Short: "Generate new age key pairs",
	Long: `Generate new age cryptographic key pairs for encryption and decryption.

Creates:
• X25519 private key (for decryption)
• X25519 public key (for encryption)  
• Secure file permissions (600 for private, 644 for public)
• Automatic key pair validation

Examples:
  crypto-kit keygen
  crypto-kit keygen --output /secure/keys/
  crypto-kit keygen --force (overwrite existing keys)`,
	RunE: runKeygen,
}

var keygenForce bool

func init() {
	rootCmd.AddCommand(keygenCmd)
	
	keygenCmd.Flags().BoolVar(&keygenForce, "force", false, "overwrite existing keys")
}

func runKeygen(cmd *cobra.Command, args []string) error {
	logVerbose("Starting key generation process")

	publicPath := getKeyPath("public")
	privatePath := getKeyPath("private")

	// Check if keys already exist
	if !keygenForce {
		if _, err := os.Stat(publicPath); err == nil {
			return fmt.Errorf("public key already exists: %s (use --force to overwrite)", publicPath)
		}
		if _, err := os.Stat(privatePath); err == nil {
			return fmt.Errorf("private key already exists: %s (use --force to overwrite)", privatePath)
		}
	}

	// Generate new key pair
	fmt.Printf("🔐 Generating new age key pair...\n")
	
	identity, err := age.GenerateX25519Identity()
	if err != nil {
		return fmt.Errorf("failed to generate key pair: %w", err)
	}

	publicKey := identity.Recipient().String()
	privateKey := identity.String()

	logVerbose("Public key: %s", publicKey)
	logVerbose("Private key: %s", privateKey[:20]+"...")

	// Save keys
	if err := saveKeyPair(publicKey, privateKey); err != nil {
		return fmt.Errorf("failed to save key pair: %w", err)
	}

	fmt.Printf("✅ Key pair generated successfully!\n")
	fmt.Printf("📄 Public key:  %s\n", publicPath)
	fmt.Printf("🔑 Private key: %s\n", privatePath)

	// Display usage instructions
	printKeygenInstructions(publicPath, privatePath)

	logVerbose("Key generation completed successfully")

	return nil
}

func printKeygenInstructions(publicPath, privatePath string) {
	fmt.Printf("\n📋 Usage Instructions:\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Encrypt: crypto-kit share --file secret.pdf --recipient %s\n", publicPath)
	fmt.Printf("Decrypt: crypto-kit decrypt --file secret.pdf.age --key %s\n", privatePath)
	fmt.Printf("Share public key with people who need to send you encrypted files\n")
	fmt.Printf("Keep private key secure and never share it!\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("🔒 Age encryption: https://age-encryption.org/\n")
}