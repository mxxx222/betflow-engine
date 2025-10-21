package privacy

import (
	"crypto/rand"
	"fmt"
	"time"
)

// NewKeyManager creates a new key manager instance
func NewKeyManager(config *KeyManagerConfig) (*KeyManager, error) {
	km := &KeyManager{
		activeKeys:   make(map[int]*CryptoKey),
		archivedKeys: make(map[int]*CryptoKey),
		config:       config,
		currentKeyID: 1,
	}

	// Generate initial key
	if err := km.generateInitialKey(); err != nil {
		return nil, fmt.Errorf("failed to generate initial key: %w", err)
	}

	// Start key rotation scheduler
	go km.keyRotationScheduler()

	return km, nil
}

// GetActiveKey returns the current active key
func (km *KeyManager) GetActiveKey() (*CryptoKey, error) {
	km.mutex.RLock()
	defer km.mutex.RUnlock()

	for _, key := range km.activeKeys {
		if key.Status == KeyActive {
			return key, nil
		}
	}

	return nil, fmt.Errorf("no active key found")
}

// GetKey retrieves a key by ID (active or archived)
func (km *KeyManager) GetKey(keyID int) (*CryptoKey, error) {
	km.mutex.RLock()
	defer km.mutex.RUnlock()

	// Check active keys first
	if key, exists := km.activeKeys[keyID]; exists {
		return key, nil
	}

	// Check archived keys
	if key, exists := km.archivedKeys[keyID]; exists {
		return key, nil
	}

	return nil, fmt.Errorf("key with ID %d not found", keyID)
}

// RotateKeys performs key rotation
func (km *KeyManager) RotateKeys() error {
	km.mutex.Lock()
	defer km.mutex.Unlock()

	event := KeyRotationEvent{
		ID:           generateID(),
		Timestamp:    time.Now(),
		RotationType: "manual",
	}

	// Get current active key
	var oldKey *CryptoKey
	for _, key := range km.activeKeys {
		if key.Status == KeyActive {
			oldKey = key
			break
		}
	}

	if oldKey != nil {
		event.OldKeyID = oldKey.ID
	}

	// Generate new key
	newKey, err := km.generateKey()
	if err != nil {
		event.Success = false
		event.ErrorMessage = err.Error()
		if km.auditLog != nil {
			km.auditLog.LogKeyRotation(event)
		}
		return fmt.Errorf("failed to generate new key: %w", err)
	}

	event.NewKeyID = newKey.ID

	// Mark old key as rotating, new key as active
	if oldKey != nil {
		oldKey.Status = KeyRotating
		// Archive old key after grace period
		go km.archiveKeyAfterGracePeriod(oldKey, 24*time.Hour)
	}

	km.activeKeys[newKey.ID] = newKey
	event.Success = true

	if km.auditLog != nil {
		km.auditLog.LogKeyRotation(event)
	}

	return nil
}

// generateInitialKey generates the first key for the system
func (km *KeyManager) generateInitialKey() error {
	key, err := km.generateKey()
	if err != nil {
		return err
	}

	km.activeKeys[key.ID] = key
	return nil
}

// generateKey creates a new cryptographic key
func (km *KeyManager) generateKey() (*CryptoKey, error) {
	keyBytes := make([]byte, km.config.KeySize)
	if _, err := rand.Read(keyBytes); err != nil {
		return nil, fmt.Errorf("failed to generate key bytes: %w", err)
	}

	salt := make([]byte, 16) // 128-bit salt
	if _, err := rand.Read(salt); err != nil {
		return nil, fmt.Errorf("failed to generate salt: %w", err)
	}

	km.currentKeyID++
	key := &CryptoKey{
		ID:        km.currentKeyID,
		Key:       keyBytes,
		Salt:      salt,
		Algorithm: "AES-256-GCM",
		CreatedAt: time.Now(),
		ExpiresAt: time.Now().Add(km.config.RotationInterval),
		Status:    KeyActive,
		Purpose:   "pseudonymization",
	}

	return key, nil
}

// keyRotationScheduler runs scheduled key rotations
func (km *KeyManager) keyRotationScheduler() {
	ticker := time.NewTicker(km.config.RotationInterval)
	defer ticker.Stop()

	for range ticker.C {
		if err := km.RotateKeys(); err != nil {
			// Log error but continue - manual intervention may be needed
			fmt.Printf("Scheduled key rotation failed: %v\n", err)
		}
	}
}

// archiveKeyAfterGracePeriod archives a key after a grace period
func (km *KeyManager) archiveKeyAfterGracePeriod(key *CryptoKey, gracePeriod time.Duration) {
	time.Sleep(gracePeriod)

	km.mutex.Lock()
	defer km.mutex.Unlock()

	// Move key from active to archived
	delete(km.activeKeys, key.ID)
	key.Status = KeyArchived
	km.archivedKeys[key.ID] = key

	// Schedule deletion after archive retention period
	go km.deleteKeyAfterRetention(key, km.config.ArchiveRetention)
}

// deleteKeyAfterRetention securely deletes a key after retention period
func (km *KeyManager) deleteKeyAfterRetention(key *CryptoKey, retentionPeriod time.Duration) {
	time.Sleep(retentionPeriod)

	km.mutex.Lock()
	defer km.mutex.Unlock()

	// Securely wipe key material
	for i := range key.Key {
		key.Key[i] = 0
	}

	key.Status = KeyRevoked
	delete(km.archivedKeys, key.ID)
}

// GetKeyMetrics returns metrics about key management
func (km *KeyManager) GetKeyMetrics() *KeyMetrics {
	km.mutex.RLock()
	defer km.mutex.RUnlock()

	return &KeyMetrics{
		ActiveKeys:   len(km.activeKeys),
		ArchivedKeys: len(km.archivedKeys),
		TotalKeys:    km.currentKeyID,
		LastRotation: time.Now(), // This would track actual last rotation
	}
}

// KeyMetrics contains key management metrics
type KeyMetrics struct {
	ActiveKeys   int       `json:"active_keys"`
	ArchivedKeys int       `json:"archived_keys"`
	TotalKeys    int       `json:"total_keys"`
	LastRotation time.Time `json:"last_rotation"`
}
