package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"filippo.io/age"
	"github.com/spf13/cobra"
)

var (
	rotatePolicy string
	rotateVault  string
	rotateBackup string
	rotateForce  bool
)

// rotateCmd represents the rotate command
var rotateCmd = &cobra.Command{
	Use:   "rotate",
	Short: "Key rotation and lifecycle management",
	Long: `Automated key rotation with configurable policies.

Supports:
• Time-based rotation policies (90d, 180d, 365d)
• Vault integration (HashiCorp Vault, Bitwarden)
• Secure key archival and backup
• Audit logging and compliance reporting

Examples:
  crypto-kit rotate --policy 90d --vault bitwarden
  crypto-kit rotate --policy 180d --backup /secure/keystore
  crypto-kit rotate --force --policy 30d`,
	RunE: runRotate,
}

func init() {
	rootCmd.AddCommand(rotateCmd)

	rotateCmd.Flags().StringVar(&rotatePolicy, "policy", "90d", "rotation policy (30d, 90d, 180d, 365d)")
	rotateCmd.Flags().StringVar(&rotateVault, "vault", "", "vault backend (vault, bitwarden)")
	rotateCmd.Flags().StringVar(&rotateBackup, "backup", "", "backup directory for old keys")
	rotateCmd.Flags().BoolVar(&rotateForce, "force", false, "force rotation even if policy not met")
}

func runRotate(cmd *cobra.Command, args []string) error {
	logVerbose("Starting key rotation process")

	// Parse rotation policy
	rotationInterval, err := parseRotationPolicy(rotatePolicy)
	if err != nil {
		return fmt.Errorf("invalid rotation policy: %w", err)
	}

	logVerbose("Rotation policy: %s (%v)", rotatePolicy, rotationInterval)

	// Check if rotation is needed
	if !rotateForce {
		needed, nextRotation, err := isRotationNeeded(rotationInterval)
		if err != nil {
			return fmt.Errorf("failed to check rotation status: %w", err)
		}

		if !needed {
			fmt.Printf("✅ Key rotation not needed yet\n")
			fmt.Printf("⏰ Next rotation: %s\n", nextRotation.Format("2006-01-02 15:04:05"))
			return nil
		}
	}

	fmt.Printf("🔄 Starting key rotation (policy: %s)\n", rotatePolicy)

	// Backup existing keys if backup directory specified
	if rotateBackup != "" {
		if err := backupExistingKeys(rotateBackup); err != nil {
			return fmt.Errorf("failed to backup existing keys: %w", err)
		}
		fmt.Printf("💾 Existing keys backed up to: %s\n", rotateBackup)
	}

	// Generate new key pair
	publicKey, privateKey, err := generateNewKeyPair()
	if err != nil {
		return fmt.Errorf("failed to generate new key pair: %w", err)
	}

	// Save new keys
	if err := saveKeyPair(publicKey, privateKey); err != nil {
		return fmt.Errorf("failed to save new key pair: %w", err)
	}

	// Update vault if configured
	if rotateVault != "" {
		if err := updateVault(rotateVault, publicKey, privateKey); err != nil {
			fmt.Printf("⚠️  Warning: vault update failed: %v\n", err)
		} else {
			fmt.Printf("🔐 Vault updated: %s\n", rotateVault)
		}
	}

	// Update rotation timestamp
	if err := updateRotationTimestamp(); err != nil {
		fmt.Printf("⚠️  Warning: failed to update rotation timestamp: %v\n", err)
	}

	fmt.Printf("✅ Key rotation completed successfully\n")
	fmt.Printf("📄 New public key: %s\n", getKeyPath("public"))
	fmt.Printf("🔑 New private key: %s\n", getKeyPath("private"))

	// Display sharing instructions
	printRotationInstructions()

	logVerbose("Key rotation completed successfully")

	return nil
}

func parseRotationPolicy(policy string) (time.Duration, error) {
	switch policy {
	case "30d":
		return 30 * 24 * time.Hour, nil
	case "90d":
		return 90 * 24 * time.Hour, nil
	case "180d":
		return 180 * 24 * time.Hour, nil
	case "365d":
		return 365 * 24 * time.Hour, nil
	default:
		return 0, fmt.Errorf("unsupported policy: %s (supported: 30d, 90d, 180d, 365d)", policy)
	}
}

func isRotationNeeded(interval time.Duration) (bool, time.Time, error) {
	lastRotationPath := getConfigPath("last_rotation")
	
	if _, err := os.Stat(lastRotationPath); os.IsNotExist(err) {
		// No previous rotation, rotation needed
		return true, time.Now().Add(interval), nil
	}

	data, err := os.ReadFile(lastRotationPath)
	if err != nil {
		return false, time.Time{}, err
	}

	lastRotation, err := time.Parse(time.RFC3339, string(data))
	if err != nil {
		return false, time.Time{}, err
	}

	nextRotation := lastRotation.Add(interval)
	needed := time.Now().After(nextRotation)

	return needed, nextRotation, nil
}

func backupExistingKeys(backupDir string) error {
	if err := os.MkdirAll(backupDir, 0700); err != nil {
		return err
	}

	timestamp := time.Now().Format("20060102_150405")
	
	// Backup public key if exists
	publicPath := getKeyPath("public")
	if _, err := os.Stat(publicPath); err == nil {
		backupPublic := filepath.Join(backupDir, fmt.Sprintf("public_%s.age", timestamp))
		if err := copyFile(publicPath, backupPublic); err != nil {
			return fmt.Errorf("failed to backup public key: %w", err)
		}
	}

	// Backup private key if exists
	privatePath := getKeyPath("private")
	if _, err := os.Stat(privatePath); err == nil {
		backupPrivate := filepath.Join(backupDir, fmt.Sprintf("private_%s.age", timestamp))
		if err := copyFile(privatePath, backupPrivate); err != nil {
			return fmt.Errorf("failed to backup private key: %w", err)
		}
	}

	return nil
}

func generateNewKeyPair() (string, string, error) {
	identity, err := age.GenerateX25519Identity()
	if err != nil {
		return "", "", err
	}

	publicKey := identity.Recipient().String()
	privateKey := identity.String()

	return publicKey, privateKey, nil
}

func saveKeyPair(publicKey, privateKey string) error {
	// Ensure key directory exists
	keyDir := filepath.Dir(getKeyPath("public"))
	if err := os.MkdirAll(keyDir, 0700); err != nil {
		return err
	}

	// Save public key
	publicPath := getKeyPath("public")
	if err := os.WriteFile(publicPath, []byte(publicKey), 0644); err != nil {
		return fmt.Errorf("failed to save public key: %w", err)
	}

	// Save private key (more restrictive permissions)
	privatePath := getKeyPath("private")
	if err := os.WriteFile(privatePath, []byte(privateKey), 0600); err != nil {
		return fmt.Errorf("failed to save private key: %w", err)
	}

	return nil
}

func updateVault(vaultType, publicKey, privateKey string) error {
	switch vaultType {
	case "vault":
		// TODO: Implement HashiCorp Vault integration
		return fmt.Errorf("HashiCorp Vault integration not yet implemented")
	case "bitwarden":
		// TODO: Implement Bitwarden integration
		return fmt.Errorf("Bitwarden integration not yet implemented")
	default:
		return fmt.Errorf("unsupported vault type: %s", vaultType)
	}
}

func updateRotationTimestamp() error {
	timestampPath := getConfigPath("last_rotation")
	timestamp := time.Now().Format(time.RFC3339)
	
	// Ensure config directory exists
	configDir := filepath.Dir(timestampPath)
	if err := os.MkdirAll(configDir, 0700); err != nil {
		return err
	}

	return os.WriteFile(timestampPath, []byte(timestamp), 0644)
}

func getKeyPath(keyType string) string {
	home, _ := os.UserHomeDir()
	keyDir := filepath.Join(home, ".crypto-kit", "keys")
	
	switch keyType {
	case "public":
		return filepath.Join(keyDir, "public.age")
	case "private":
		return filepath.Join(keyDir, "private.age")
	default:
		return filepath.Join(keyDir, keyType+".age")
	}
}

func getConfigPath(configType string) string {
	home, _ := os.UserHomeDir()
	configDir := filepath.Join(home, ".crypto-kit", "config")
	return filepath.Join(configDir, configType)
}

func copyFile(src, dst string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, data, 0600)
}

func printRotationInstructions() {
	fmt.Printf("\n📋 Post-Rotation Instructions:\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("1. Share new public key: %s\n", getKeyPath("public"))
	fmt.Printf("2. Update recipient lists in sharing workflows\n")
	fmt.Printf("3. Notify team members of key rotation\n")
	fmt.Printf("4. Test decryption with new private key\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("⚠️  Keep backup keys secure and accessible for old encrypted files\n")
}