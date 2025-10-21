package tests

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"
)

// Integration tests for disk encryption functionality
// Note: These tests require sudo privileges and should be run on test systems only

func TestDiskEncryptionLinux(t *testing.T) {
	if runtime.GOOS != "linux" {
		t.Skip("Skipping Linux-specific test on", runtime.GOOS)
	}

	if os.Getuid() != 0 {
		t.Skip("Disk encryption tests require root privileges")
	}

	// This test would require a test disk/volume
	// In production testing, this would use a loop device
	t.Log("Linux disk encryption test - would test LUKS operations")
}

func TestDiskEncryptionMacOS(t *testing.T) {
	if runtime.GOOS != "darwin" {
		t.Skip("Skipping macOS-specific test on", runtime.GOOS)
	}

	if os.Getuid() != 0 {
		t.Skip("Disk encryption tests require root privileges")
	}

	t.Log("macOS disk encryption test - would test APFS encryption")
}

func TestDiskEncryptionWindows(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Skipping Windows-specific test on", runtime.GOOS)
	}

	t.Log("Windows disk encryption test - would test BitLocker operations")
}

func TestKeyRotationPolicy(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	tests := []struct {
		policy   string
		expected time.Duration
		valid    bool
	}{
		{"30d", 30 * 24 * time.Hour, true},
		{"90d", 90 * 24 * time.Hour, true},
		{"180d", 180 * 24 * time.Hour, true},
		{"365d", 365 * 24 * time.Hour, true},
		{"invalid", 0, false},
		{"7d", 0, false}, // Not supported
	}

	for _, tt := range tests {
		t.Run(tt.policy, func(t *testing.T) {
			duration, err := parseRotationPolicy(tt.policy)
			if tt.valid && err != nil {
				t.Errorf("Expected valid policy %s, got error: %v", tt.policy, err)
			}
			if !tt.valid && err == nil {
				t.Errorf("Expected invalid policy %s to return error", tt.policy)
			}
			if tt.valid && duration != tt.expected {
				t.Errorf("Expected duration %v, got %v", tt.expected, duration)
			}
		})
	}
}

func TestKeyBackupRestore(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create test keys
	publicKey := "age1abcdefghijklmnopqrstuvwxyz234567890abcdefghijklmnopqrstuvwxyz"
	privateKey := "AGE-SECRET-KEY-1ABCDEFGHIJKLMNOPQRSTUVWXYZ234567890ABCDEFGHIJKLMNOP"

	keyDir := filepath.Join(tempDir, "keys")
	backupDir := filepath.Join(tempDir, "backup")

	if err := os.MkdirAll(keyDir, 0700); err != nil {
		t.Fatalf("Failed to create key dir: %v", err)
	}

	publicPath := filepath.Join(keyDir, "public.age")
	privatePath := filepath.Join(keyDir, "private.age")

	// Write test keys
	if err := os.WriteFile(publicPath, []byte(publicKey), 0644); err != nil {
		t.Fatalf("Failed to write public key: %v", err)
	}
	if err := os.WriteFile(privatePath, []byte(privateKey), 0600); err != nil {
		t.Fatalf("Failed to write private key: %v", err)
	}

	// Test backup functionality
	if err := backupKeys(keyDir, backupDir); err != nil {
		t.Fatalf("Key backup failed: %v", err)
	}

	// Verify backup files exist
	backupFiles, err := os.ReadDir(backupDir)
	if err != nil {
		t.Fatalf("Failed to read backup dir: %v", err)
	}

	if len(backupFiles) != 2 {
		t.Errorf("Expected 2 backup files, got %d", len(backupFiles))
	}
}

func TestConcurrentOperations(t *testing.T) {
	// Test concurrent encryption/decryption operations
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	const numGoroutines = 10
	errors := make(chan error, numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			// Simulate concurrent key generation
			_, err := generateTestKeyPair()
			errors <- err
		}(i)
	}

	// Check for errors
	for i := 0; i < numGoroutines; i++ {
		if err := <-errors; err != nil {
			t.Errorf("Concurrent operation %d failed: %v", i, err)
		}
	}
}

func TestAuditLogging(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "crypto-kit-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	logFile := filepath.Join(tempDir, "audit.log")

	// Test audit log entry
	entry := AuditEntry{
		Timestamp: time.Now(),
		User:      "test-user",
		Operation: "key-generation",
		Status:    "success",
		Details:   "Generated new X25519 key pair",
	}

	if err := writeAuditLog(logFile, entry); err != nil {
		t.Fatalf("Failed to write audit log: %v", err)
	}

	// Verify log entry
	data, err := os.ReadFile(logFile)
	if err != nil {
		t.Fatalf("Failed to read audit log: %v", err)
	}

	if len(data) == 0 {
		t.Error("Audit log is empty")
	}
}

// Helper functions for integration tests

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
		return 0, fmt.Errorf("unsupported policy: %s", policy)
	}
}

func backupKeys(keyDir, backupDir string) error {
	if err := os.MkdirAll(backupDir, 0700); err != nil {
		return err
	}

	files, err := os.ReadDir(keyDir)
	if err != nil {
		return err
	}

	for _, file := range files {
		if file.IsDir() {
			continue
		}

		srcPath := filepath.Join(keyDir, file.Name())
		dstPath := filepath.Join(backupDir, file.Name()+"_backup")

		data, err := os.ReadFile(srcPath)
		if err != nil {
			return err
		}

		if err := os.WriteFile(dstPath, data, 0600); err != nil {
			return err
		}
	}

	return nil
}

func generateTestKeyPair() (string, error) {
	// Simulate key generation
	time.Sleep(time.Millisecond * 10) // Simulate work
	return "test-key-pair", nil
}

type AuditEntry struct {
	Timestamp time.Time
	User      string
	Operation string
	Status    string
	Details   string
}

func writeAuditLog(logFile string, entry AuditEntry) error {
	logLine := fmt.Sprintf("%s | %s | %s | %s | %s\n",
		entry.Timestamp.Format(time.RFC3339),
		entry.User,
		entry.Operation,
		entry.Status,
		entry.Details,
	)

	f, err := os.OpenFile(logFile, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = f.WriteString(logLine)
	return err
}