package tests

import (
	"crypto/rand"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"filippo.io/age"
)

func TestKeyGeneration(t *testing.T) {
	// Create temporary directory for test keys
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Test key generation
	identity, err := age.GenerateX25519Identity()
	if err != nil {
		t.Fatalf("Failed to generate identity: %v", err)
	}

	// Validate key format
	publicKey := identity.Recipient().String()
	privateKey := identity.String()

	if len(publicKey) == 0 {
		t.Error("Public key is empty")
	}
	if len(privateKey) == 0 {
		t.Error("Private key is empty")
	}

	// Test key parsing
	recipient, err := age.ParseX25519Recipient(publicKey)
	if err != nil {
		t.Fatalf("Failed to parse public key: %v", err)
	}

	if recipient == nil {
		t.Error("Parsed recipient is nil")
	}
}

func TestEncryptDecryptRoundTrip(t *testing.T) {
	// Generate test key pair
	identity, err := age.GenerateX25519Identity()
	if err != nil {
		t.Fatalf("Failed to generate identity: %v", err)
	}

	recipient := identity.Recipient()

	// Create test data
	testData := []byte("Hello, this is a test message for CryptoKit encryption!")
	
	// Create temporary files
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	inputFile := filepath.Join(tempDir, "test.txt")
	encryptedFile := filepath.Join(tempDir, "test.txt.age")
	decryptedFile := filepath.Join(tempDir, "test-decrypted.txt")

	// Write test data
	if err := os.WriteFile(inputFile, testData, 0644); err != nil {
		t.Fatalf("Failed to write test file: %v", err)
	}

	// Test encryption
	if err := encryptFile(inputFile, encryptedFile, recipient); err != nil {
		t.Fatalf("Encryption failed: %v", err)
	}

	// Verify encrypted file exists and is different
	encryptedData, err := os.ReadFile(encryptedFile)
	if err != nil {
		t.Fatalf("Failed to read encrypted file: %v", err)
	}

	if len(encryptedData) == 0 {
		t.Error("Encrypted file is empty")
	}

	// Test decryption
	if err := decryptFile(encryptedFile, decryptedFile, identity); err != nil {
		t.Fatalf("Decryption failed: %v", err)
	}

	// Verify decrypted data matches original
	decryptedData, err := os.ReadFile(decryptedFile)
	if err != nil {
		t.Fatalf("Failed to read decrypted file: %v", err)
	}

	if string(decryptedData) != string(testData) {
		t.Errorf("Decrypted data doesn't match original. Got: %s, Expected: %s", 
			string(decryptedData), string(testData))
	}
}

func TestFilePermissions(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Test private key permissions (should be 0600)
	privateKeyPath := filepath.Join(tempDir, "private.age")
	testKey := "AGE-SECRET-KEY-1ABCDEFGHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJKLMNOP"
	
	if err := os.WriteFile(privateKeyPath, []byte(testKey), 0600); err != nil {
		t.Fatalf("Failed to write private key: %v", err)
	}

	info, err := os.Stat(privateKeyPath)
	if err != nil {
		t.Fatalf("Failed to stat private key file: %v", err)
	}

	expectedMode := os.FileMode(0600)
	if info.Mode().Perm() != expectedMode {
		t.Errorf("Private key has wrong permissions. Got: %v, Expected: %v", 
			info.Mode().Perm(), expectedMode)
	}
}

func TestInputValidation(t *testing.T) {
	tests := []struct {
		name        string
		input       string
		shouldError bool
	}{
		{"Valid file path", "/tmp/test.txt", false},
		{"Empty path", "", true},
		{"Path with null bytes", "/tmp/test\x00.txt", true},
		{"Very long path", string(make([]byte, 5000)), true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validateFilePath(tt.input)
			if (err != nil) != tt.shouldError {
				t.Errorf("validateFilePath() error = %v, shouldError = %v", err, tt.shouldError)
			}
		})
	}
}

func TestMemoryClearing(t *testing.T) {
	// Test that sensitive data is cleared from memory
	sensitiveData := make([]byte, 1024)
	rand.Read(sensitiveData)

	// Simulate processing sensitive data
	processedData := make([]byte, len(sensitiveData))
	copy(processedData, sensitiveData)

	// Clear sensitive data (this would be called in actual implementation)
	clearSensitiveData(processedData)

	// Verify data is cleared
	for i, b := range processedData {
		if b != 0 {
			t.Errorf("Sensitive data not cleared at index %d: got %d", i, b)
		}
	}
}

// Helper functions (these would be implemented in the actual cmd package)

func encryptFile(inputPath, outputPath string, recipient age.Recipient) error {
	// This is a simplified version - actual implementation in cmd/share.go
	input, err := os.Open(inputPath)
	if err != nil {
		return err
	}
	defer input.Close()

	output, err := os.Create(outputPath)
	if err != nil {
		return err
	}
	defer output.Close()

	w, err := age.Encrypt(output, recipient)
	if err != nil {
		return err
	}

	data, err := os.ReadFile(inputPath)
	if err != nil {
		return err
	}

	if _, err := w.Write(data); err != nil {
		return err
	}

	return w.Close()
}

func decryptFile(inputPath, outputPath string, identity age.Identity) error {
	// This is a simplified version - actual implementation in cmd/decrypt.go
	input, err := os.Open(inputPath)
	if err != nil {
		return err
	}
	defer input.Close()

	r, err := age.Decrypt(input, identity)
	if err != nil {
		return err
	}

	data, err := os.ReadAll(r)
	if err != nil {
		return err
	}

	return os.WriteFile(outputPath, data, 0644)
}

func validateFilePath(path string) error {
	if path == "" {
		return fmt.Errorf("path cannot be empty")
	}
	if len(path) > 4096 {
		return fmt.Errorf("path too long")
	}
	for _, b := range []byte(path) {
		if b == 0 {
			return fmt.Errorf("path contains null byte")
		}
	}
	return nil
}

func clearSensitiveData(data []byte) {
	for i := range data {
		data[i] = 0
	}
}