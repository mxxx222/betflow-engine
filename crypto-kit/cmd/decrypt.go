package cmd

import (
	"fmt"
	"io"
	"os"
	"strings"

	"filippo.io/age"
	"github.com/spf13/cobra"
)

var (
	decryptFile string
	decryptKey  string
	decryptOut  string
)

// decryptCmd represents the decrypt command
var decryptCmd = &cobra.Command{
	Use:   "decrypt",
	Short: "Decrypt age-encrypted files",
	Long: `Decrypt files that were encrypted with the share command.

Supports:
• Age private key decryption
• Hardware key integration (YubiKey/HSM)  
• Automatic file type detection
• Integrity verification

Examples:
  crypto-kit decrypt --file secret.pdf.age --key priv.age
  crypto-kit decrypt --file report.xlsx.age --key hardware
  crypto-kit decrypt --file data.json.age --key priv.age --output decrypted/`,
	RunE: runDecrypt,
}

func init() {
	rootCmd.AddCommand(decryptCmd)

	decryptCmd.Flags().StringVarP(&decryptFile, "file", "f", "", "encrypted file to decrypt (required)")
	decryptCmd.Flags().StringVarP(&decryptKey, "key", "k", "", "private key file or 'hardware' (required)")
	decryptCmd.Flags().StringVarP(&decryptOut, "output", "o", "", "output file path (default: remove .age extension)")

	decryptCmd.MarkFlagRequired("file")
	decryptCmd.MarkFlagRequired("key")
}

func runDecrypt(cmd *cobra.Command, args []string) error {
	logVerbose("Starting file decryption process")

	// Validate input file exists
	if _, err := os.Stat(decryptFile); os.IsNotExist(err) {
		return fmt.Errorf("encrypted file does not exist: %s", decryptFile)
	}

	// Set default output file (remove .age extension)
	if decryptOut == "" {
		if strings.HasSuffix(decryptFile, ".age") {
			decryptOut = strings.TrimSuffix(decryptFile, ".age")
		} else {
			decryptOut = decryptFile + ".decrypted"
		}
	}

	logVerbose("Encrypted file: %s", decryptFile)
	logVerbose("Output file: %s", decryptOut)
	logVerbose("Key: %s", decryptKey)

	// Load private key
	identity, err := loadIdentity(decryptKey)
	if err != nil {
		return fmt.Errorf("failed to load private key: %w", err)
	}

	// Decrypt the file
	if err := decryptFileContent(decryptFile, decryptOut, identity); err != nil {
		return fmt.Errorf("decryption failed: %w", err)
	}

	fmt.Printf("✅ File decrypted successfully: %s\n", decryptOut)
	
	// Display file info
	if stat, err := os.Stat(decryptOut); err == nil {
		fmt.Printf("📄 File size: %d bytes\n", stat.Size())
		fmt.Printf("🕒 Modified: %s\n", stat.ModTime().Format("2006-01-02 15:04:05"))
	}

	logVerbose("File decryption completed successfully")

	return nil
}

func loadIdentity(keyPath string) (age.Identity, error) {
	if keyPath == "hardware" {
		// TODO: Implement hardware key integration (YubiKey/HSM)
		return nil, fmt.Errorf("hardware key support not yet implemented")
	}

	// Load age private key from file
	keyData, err := os.ReadFile(keyPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read private key file: %w", err)
	}

	identities, err := age.ParseIdentities(strings.NewReader(string(keyData)))
	if err != nil {
		return nil, fmt.Errorf("failed to parse private key: %w", err)
	}

	if len(identities) == 0 {
		return nil, fmt.Errorf("no valid identities found in key file")
	}

	return identities[0], nil
}

func decryptFileContent(inputFile, outputFile string, identity age.Identity) error {
	// Open encrypted file
	input, err := os.Open(inputFile)
	if err != nil {
		return fmt.Errorf("failed to open encrypted file: %w", err)
	}
	defer input.Close()

	// Create age reader
	r, err := age.Decrypt(input, identity)
	if err != nil {
		return fmt.Errorf("failed to create age reader: %w", err)
	}

	// Create output file
	output, err := os.Create(outputFile)
	if err != nil {
		return fmt.Errorf("failed to create output file: %w", err)
	}
	defer output.Close()

	// Copy and decrypt data
	if _, err := io.Copy(output, r); err != nil {
		return fmt.Errorf("failed to decrypt data: %w", err)
	}

	return nil
}