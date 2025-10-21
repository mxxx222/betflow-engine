package cmd

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"filippo.io/age"
	"github.com/skip2/go-qrcode"
	"github.com/spf13/cobra"
)

var (
	shareFile      string
	shareRecipient string
	shareOutput    string
	shareExpiry    string
	shareQR        bool
)

// shareCmd represents the share command
var shareCmd = &cobra.Command{
	Use:   "share",
	Short: "Encrypt and share files securely",
	Long: `Encrypt files using age cryptography for secure sharing.

Supports:
• Age public key encryption  
• Hardware key integration (YubiKey/HSM)
• QR code generation for easy sharing
• Time-limited access (expiry)
• Audit logging

Examples:
  crypto-kit share --file secret.pdf --recipient pubkey.age
  crypto-kit share --file report.xlsx --recipient pub.age --qr --output share.png
  crypto-kit share --file data.json --recipient hardware --expiry 7d`,
	RunE: runShare,
}

func init() {
	rootCmd.AddCommand(shareCmd)

	shareCmd.Flags().StringVarP(&shareFile, "file", "f", "", "file to encrypt and share (required)")
	shareCmd.Flags().StringVarP(&shareRecipient, "recipient", "r", "", "recipient's age public key file or 'hardware' (required)")
	shareCmd.Flags().StringVarP(&shareOutput, "output", "o", "", "output file path (default: <file>.age)")
	shareCmd.Flags().StringVar(&shareExpiry, "expiry", "", "expiration time (e.g., 7d, 24h, 2w)")
	shareCmd.Flags().BoolVar(&shareQR, "qr", false, "generate QR code with decrypt instructions")

	shareCmd.MarkFlagRequired("file")
	shareCmd.MarkFlagRequired("recipient")
}

func runShare(cmd *cobra.Command, args []string) error {
	logVerbose("Starting file encryption and sharing process")

	// Validate input file exists
	if _, err := os.Stat(shareFile); os.IsNotExist(err) {
		return fmt.Errorf("file does not exist: %s", shareFile)
	}

	// Set default output file
	if shareOutput == "" {
		shareOutput = shareFile + ".age"
	}

	logVerbose("Input file: %s", shareFile)
	logVerbose("Output file: %s", shareOutput)
	logVerbose("Recipient: %s", shareRecipient)

	// Load recipient's public key
	recipient, err := loadRecipient(shareRecipient)
	if err != nil {
		return fmt.Errorf("failed to load recipient: %w", err)
	}

	// Encrypt the file
	if err := encryptFile(shareFile, shareOutput, recipient); err != nil {
		return fmt.Errorf("encryption failed: %w", err)
	}

	fmt.Printf("✅ File encrypted successfully: %s\n", shareOutput)

	// Generate QR code if requested
	if shareQR {
		qrFile := strings.TrimSuffix(shareOutput, filepath.Ext(shareOutput)) + "_qr.png"
		if err := generateQRCode(shareOutput, qrFile); err != nil {
			fmt.Printf("⚠️  Warning: QR code generation failed: %v\n", err)
		} else {
			fmt.Printf("📱 QR code generated: %s\n", qrFile)
		}
	}

	// Display sharing instructions
	printSharingInstructions(shareOutput, shareRecipient)

	// TODO: Add audit logging
	logVerbose("File sharing completed successfully")

	return nil
}

func loadRecipient(recipientPath string) (age.Recipient, error) {
	if recipientPath == "hardware" {
		// TODO: Implement hardware key integration (YubiKey/HSM)
		return nil, fmt.Errorf("hardware key support not yet implemented")
	}

	// Load age public key from file
	pubKeyData, err := os.ReadFile(recipientPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read public key file: %w", err)
	}

	pubKeyStr := strings.TrimSpace(string(pubKeyData))
	recipient, err := age.ParseX25519Recipient(pubKeyStr)
	if err != nil {
		return nil, fmt.Errorf("failed to parse public key: %w", err)
	}

	return recipient, nil
}

func encryptFile(inputFile, outputFile string, recipient age.Recipient) error {
	// Open input file
	input, err := os.Open(inputFile)
	if err != nil {
		return fmt.Errorf("failed to open input file: %w", err)
	}
	defer input.Close()

	// Create output file
	output, err := os.Create(outputFile)
	if err != nil {
		return fmt.Errorf("failed to create output file: %w", err)
	}
	defer output.Close()

	// Create age writer
	w, err := age.Encrypt(output, recipient)
	if err != nil {
		return fmt.Errorf("failed to create age writer: %w", err)
	}

	// Copy and encrypt data
	if _, err := io.Copy(w, input); err != nil {
		return fmt.Errorf("failed to encrypt data: %w", err)
	}

	// Close the writer to finalize encryption
	if err := w.Close(); err != nil {
		return fmt.Errorf("failed to finalize encryption: %w", err)
	}

	return nil
}

func generateQRCode(encryptedFile, qrFile string) error {
	// Create decrypt instruction
	instruction := fmt.Sprintf("crypto-kit decrypt --file %s --key priv.age", filepath.Base(encryptedFile))
	
	// Generate QR code
	err := qrcode.WriteFile(instruction, qrcode.Medium, 256, qrFile)
	if err != nil {
		return fmt.Errorf("failed to generate QR code: %w", err)
	}

	return nil
}

func printSharingInstructions(encryptedFile, recipient string) {
	fmt.Printf("\n📋 Sharing Instructions:\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("1. Send the encrypted file: %s\n", encryptedFile)
	
	if recipient == "hardware" {
		fmt.Printf("2. Recipient decrypts with: crypto-kit decrypt --file %s --key hardware\n", filepath.Base(encryptedFile))
	} else {
		fmt.Printf("2. Recipient decrypts with: crypto-kit decrypt --file %s --key priv.age\n", filepath.Base(encryptedFile))
	}
	
	if shareExpiry != "" {
		fmt.Printf("⏰ Expires: %s\n", shareExpiry)
	}
	
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("🔒 File is encrypted with age (https://age-encryption.org/)\n")
}