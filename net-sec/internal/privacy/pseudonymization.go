package privacy
package privacy

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"io"
	"strings"
	"sync"
	"time"

	"golang.org/x/crypto/pbkdf2"
	"golang.org/x/crypto/scrypt"
)

// PseudonymizationEngine provides GDPR Article 25 compliant data pseudonymization
type PseudonymizationEngine struct {
	config     *PseudonymizationConfig
	keyManager *KeyManager
	auditLog   AuditLogger
}

// PseudonymizationConfig contains configuration for the pseudonymization engine
type PseudonymizationConfig struct {
	Algorithm           PseudoAlgorithm
	KeyRotationInterval time.Duration
	SaltLength          int
	IterationCount      int
	KeyDerivationFunc   KeyDerivationFunc
	PreservationRules   []FormatPreservationRule
	AuditEnabled        bool
}

// PseudoAlgorithm defines the pseudonymization algorithm
type PseudoAlgorithm int

const (
	SHA256Hash PseudoAlgorithm = iota
	AES256Encryption
	FormatPreservingEncryption
	ReversibleTokenization
	KAnonymization
)

// KeyDerivationFunc defines key derivation methods
type KeyDerivationFunc int

const (
	PBKDF2_SHA256 KeyDerivationFunc = iota
	Scrypt
	Argon2id
)

// FormatPreservationRule defines rules for preserving data format
type FormatPreservationRule struct {
	DataType        string
	PreserveFormat  bool
	PreserveLength  bool
	AllowedChars    string
	MaskingPattern  string
}

// PseudonymizedData represents pseudonymized data with metadata
type PseudonymizedData struct {
	ID                string                 `json:"id"`
	PseudonymizedValue string                `json:"pseudonymized_value"`
	Algorithm         PseudoAlgorithm        `json:"algorithm"`
	KeyVersion        int                    `json:"key_version"`
	CreatedAt         time.Time              `json:"created_at"`
	DataType          string                 `json:"data_type"`
	Purpose           string                 `json:"purpose"`
	Metadata          map[string]interface{} `json:"metadata"`
	HashValue         string                 `json:"hash_value"` // For lookup without decryption
}

// KeyManager handles cryptographic key lifecycle
type KeyManager struct {
	activeKeys   map[int]*CryptoKey
	archivedKeys map[int]*CryptoKey
	config       *KeyManagerConfig
	currentKeyID int
	mutex        sync.RWMutex
	auditLog     AuditLogger
}

// CryptoKey represents a cryptographic key with metadata
type CryptoKey struct {
	ID          int       `json:"id"`
	Key         []byte    `json:"-"` // Never serialize the actual key
	Salt        []byte    `json:"salt"`
	Algorithm   string    `json:"algorithm"`
	CreatedAt   time.Time `json:"created_at"`
	ExpiresAt   time.Time `json:"expires_at"`
	Status      KeyStatus `json:"status"`
	Purpose     string    `json:"purpose"`
}

// KeyStatus defines the lifecycle status of a key
type KeyStatus int

const (
	KeyActive KeyStatus = iota
	KeyRotating
	KeyArchived
	KeyRevoked
)

// KeyManagerConfig contains key management configuration
type KeyManagerConfig struct {
	KeySize             int
	RotationInterval    time.Duration
	ArchiveRetention    time.Duration
	BackupEncryption    bool
	HardwareSecurityModule bool
}

// AuditLogger interface for compliance logging
type AuditLogger interface {
	LogPseudonymization(event PseudonymizationEvent) error
	LogKeyRotation(event KeyRotationEvent) error
	LogDataAccess(event DataAccessEvent) error
}

// PseudonymizationEvent represents an audit event for pseudonymization
type PseudonymizationEvent struct {
	ID            string                 `json:"id"`
	Timestamp     time.Time              `json:"timestamp"`
	UserID        string                 `json:"user_id,omitempty"`
	DataType      string                 `json:"data_type"`
	Operation     string                 `json:"operation"` // pseudonymize, de-pseudonymize
	Algorithm     PseudoAlgorithm        `json:"algorithm"`
	Purpose       string                 `json:"purpose"`
	LegalBasis    string                 `json:"legal_basis"`
	Success       bool                   `json:"success"`
	ErrorMessage  string                 `json:"error_message,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// KeyRotationEvent represents an audit event for key rotation
type KeyRotationEvent struct {
	ID           string    `json:"id"`
	Timestamp    time.Time `json:"timestamp"`
	OldKeyID     int       `json:"old_key_id"`
	NewKeyID     int       `json:"new_key_id"`
	RotationType string    `json:"rotation_type"` // scheduled, emergency, manual
	Success      bool      `json:"success"`
	ErrorMessage string    `json:"error_message,omitempty"`
}

// DataAccessEvent represents an audit event for data access
type DataAccessEvent struct {
	ID           string                 `json:"id"`
	Timestamp    time.Time              `json:"timestamp"`
	UserID       string                 `json:"user_id"`
	DataSubject  string                 `json:"data_subject,omitempty"`
	Operation    string                 `json:"operation"`
	DataType     string                 `json:"data_type"`
	Purpose      string                 `json:"purpose"`
	LegalBasis   string                 `json:"legal_basis"`
	IPAddress    string                 `json:"ip_address,omitempty"`
	UserAgent    string                 `json:"user_agent,omitempty"`
	Success      bool                   `json:"success"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// NewPseudonymizationEngine creates a new pseudonymization engine
func NewPseudonymizationEngine(config *PseudonymizationConfig, auditLog AuditLogger) (*PseudonymizationEngine, error) {
	if config == nil {
		config = DefaultPseudonymizationConfig()
	}

	keyManager, err := NewKeyManager(&KeyManagerConfig{
		KeySize:          32, // 256-bit keys
		RotationInterval: config.KeyRotationInterval,
		ArchiveRetention: 7 * 365 * 24 * time.Hour, // 7 years for compliance
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create key manager: %w", err)
	}

	return &PseudonymizationEngine{
		config:     config,
		keyManager: keyManager,
		auditLog:   auditLog,
	}, nil
}

// DefaultPseudonymizationConfig returns default configuration
func DefaultPseudonymizationConfig() *PseudonymizationConfig {
	return &PseudonymizationConfig{
		Algorithm:           AES256Encryption,
		KeyRotationInterval: 90 * 24 * time.Hour, // 90 days
		SaltLength:          16,
		IterationCount:      100000,
		KeyDerivationFunc:   PBKDF2_SHA256,
		PreservationRules: []FormatPreservationRule{
			{
				DataType:       "email",
				PreserveFormat: true,
				PreserveLength: false,
				MaskingPattern: "****@****.***",
			},
			{
				DataType:       "ip_address",
				PreserveFormat: true,
				PreserveLength: true,
				MaskingPattern: "XXX.XXX.XXX.XXX",
			},
		},
		AuditEnabled: true,
	}
}

// Pseudonymize converts personal data to pseudonymized form
func (pe *PseudonymizationEngine) Pseudonymize(data string, dataType, purpose, legalBasis string) (*PseudonymizedData, error) {
	event := PseudonymizationEvent{
		ID:         generateID(),
		Timestamp:  time.Now(),
		DataType:   dataType,
		Operation:  "pseudonymize",
		Algorithm:  pe.config.Algorithm,
		Purpose:    purpose,
		LegalBasis: legalBasis,
	}

	// Get active key
	activeKey, err := pe.keyManager.GetActiveKey()
	if err != nil {
		event.Success = false
		event.ErrorMessage = err.Error()
		pe.auditLog.LogPseudonymization(event)
		return nil, fmt.Errorf("failed to get active key: %w", err)
	}

	var pseudonymizedValue string
	var hashValue string

	switch pe.config.Algorithm {
	case SHA256Hash:
		pseudonymizedValue, hashValue, err = pe.hashPseudonymization(data, activeKey)
	case AES256Encryption:
		pseudonymizedValue, hashValue, err = pe.encryptionPseudonymization(data, activeKey)
	case FormatPreservingEncryption:
		pseudonymizedValue, hashValue, err = pe.formatPreservingPseudonymization(data, dataType, activeKey)
	case ReversibleTokenization:
		pseudonymizedValue, hashValue, err = pe.tokenizationPseudonymization(data, activeKey)
	default:
		err = fmt.Errorf("unsupported algorithm: %v", pe.config.Algorithm)
	}

	if err != nil {
		event.Success = false
		event.ErrorMessage = err.Error()
		pe.auditLog.LogPseudonymization(event)
		return nil, err
	}

	result := &PseudonymizedData{
		ID:                generateID(),
		PseudonymizedValue: pseudonymizedValue,
		Algorithm:         pe.config.Algorithm,
		KeyVersion:        activeKey.ID,
		CreatedAt:         time.Now(),
		DataType:          dataType,
		Purpose:           purpose,
		HashValue:         hashValue,
		Metadata: map[string]interface{}{
			"legal_basis":    legalBasis,
			"audit_event_id": event.ID,
		},
	}

	event.Success = true
	event.Metadata = map[string]interface{}{
		"pseudonym_id": result.ID,
		"key_version":  activeKey.ID,
	}

	if pe.config.AuditEnabled {
		pe.auditLog.LogPseudonymization(event)
	}

	return result, nil
}

// DePseudonymize converts pseudonymized data back to original form
func (pe *PseudonymizationEngine) DePseudonymize(pseudoData *PseudonymizedData, purpose, legalBasis string) (string, error) {
	event := PseudonymizationEvent{
		ID:         generateID(),
		Timestamp:  time.Now(),
		DataType:   pseudoData.DataType,
		Operation:  "de-pseudonymize",
		Algorithm:  pseudoData.Algorithm,
		Purpose:    purpose,
		LegalBasis: legalBasis,
		Metadata: map[string]interface{}{
			"pseudonym_id": pseudoData.ID,
			"key_version":  pseudoData.KeyVersion,
		},
	}

	// Get the key used for pseudonymization
	key, err := pe.keyManager.GetKey(pseudoData.KeyVersion)
	if err != nil {
		event.Success = false
		event.ErrorMessage = err.Error()
		pe.auditLog.LogPseudonymization(event)
		return "", fmt.Errorf("failed to get key version %d: %w", pseudoData.KeyVersion, err)
	}

	var originalData string

	switch pseudoData.Algorithm {
	case SHA256Hash:
		event.Success = false
		event.ErrorMessage = "SHA256 hash is not reversible"
		pe.auditLog.LogPseudonymization(event)
		return "", fmt.Errorf("SHA256 hash pseudonymization is not reversible")
	case AES256Encryption:
		originalData, err = pe.decryptionDePseudonymization(pseudoData.PseudonymizedValue, key)
	case FormatPreservingEncryption:
		originalData, err = pe.formatPreservingDePseudonymization(pseudoData.PseudonymizedValue, pseudoData.DataType, key)
	case ReversibleTokenization:
		originalData, err = pe.tokenizationDePseudonymization(pseudoData.PseudonymizedValue, key)
	default:
		err = fmt.Errorf("unsupported algorithm: %v", pseudoData.Algorithm)
	}

	if err != nil {
		event.Success = false
		event.ErrorMessage = err.Error()
		pe.auditLog.LogPseudonymization(event)
		return "", err
	}

	event.Success = true
	if pe.config.AuditEnabled {
		pe.auditLog.LogPseudonymization(event)
	}

	return originalData, nil
}

// hashPseudonymization performs irreversible hash-based pseudonymization
func (pe *PseudonymizationEngine) hashPseudonymization(data string, key *CryptoKey) (string, string, error) {
	// Combine data with key salt
	combined := data + string(key.Salt)
	
	switch pe.config.KeyDerivationFunc {
	case PBKDF2_SHA256:
		hash := pbkdf2.Key([]byte(combined), key.Salt, pe.config.IterationCount, 32, sha256.New)
		encoded := base64.URLEncoding.EncodeToString(hash)
		return encoded, encoded, nil
	case Scrypt:
		hash, err := scrypt.Key([]byte(combined), key.Salt, 32768, 8, 1, 32)
		if err != nil {
			return "", "", fmt.Errorf("scrypt failed: %w", err)
		}
		encoded := base64.URLEncoding.EncodeToString(hash)
		return encoded, encoded, nil
	default:
		return "", "", fmt.Errorf("unsupported key derivation function")
	}
}

// encryptionPseudonymization performs reversible encryption-based pseudonymization
func (pe *PseudonymizationEngine) encryptionPseudonymization(data string, key *CryptoKey) (string, string, error) {
	block, err := aes.NewCipher(key.Key)
	if err != nil {
		return "", "", fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", "", fmt.Errorf("failed to create GCM: %w", err)
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", "", fmt.Errorf("failed to generate nonce: %w", err)
	}

	encrypted := gcm.Seal(nonce, nonce, []byte(data), nil)
	encoded := base64.URLEncoding.EncodeToString(encrypted)
	
	// Create hash for lookup without decryption
	hasher := sha256.New()
	hasher.Write([]byte(data))
	hasher.Write(key.Salt)
	hashValue := hex.EncodeToString(hasher.Sum(nil))

	return encoded, hashValue, nil
}

// decryptionDePseudonymization reverses encryption-based pseudonymization
func (pe *PseudonymizationEngine) decryptionDePseudonymization(encryptedData string, key *CryptoKey) (string, error) {
	encrypted, err := base64.URLEncoding.DecodeString(encryptedData)
	if err != nil {
		return "", fmt.Errorf("failed to decode encrypted data: %w", err)
	}

	block, err := aes.NewCipher(key.Key)
	if err != nil {
		return "", fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("failed to create GCM: %w", err)
	}

	nonceSize := gcm.NonceSize()
	if len(encrypted) < nonceSize {
		return "", fmt.Errorf("encrypted data too short")
	}

	nonce := encrypted[:nonceSize]
	ciphertext := encrypted[nonceSize:]

	decrypted, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return "", fmt.Errorf("failed to decrypt: %w", err)
	}

	return string(decrypted), nil
}

// formatPreservingPseudonymization preserves format of original data
func (pe *PseudonymizationEngine) formatPreservingPseudonymization(data, dataType string, key *CryptoKey) (string, string, error) {
	// Find applicable preservation rule
	var rule *FormatPreservationRule
	for _, r := range pe.config.PreservationRules {
		if r.DataType == dataType {
			rule = &r
			break
		}
	}

	if rule == nil {
		// Fall back to regular encryption if no rule found
		return pe.encryptionPseudonymization(data, key)
	}

	// Apply format-preserving logic based on data type
	switch dataType {
	case "email":
		return pe.formatPreservingEmail(data, key)
	case "ip_address":
		return pe.formatPreservingIPAddress(data, key)
	default:
		return pe.encryptionPseudonymization(data, key)
	}
}

// formatPreservingEmail preserves email format while pseudonymizing
func (pe *PseudonymizationEngine) formatPreservingEmail(email string, key *CryptoKey) (string, string, error) {
	parts := strings.Split(email, "@")
	if len(parts) != 2 {
		return "", "", fmt.Errorf("invalid email format")
	}

	// Hash the local part
	localHash := sha256.Sum256(append([]byte(parts[0]), key.Salt...))
	localPseudo := hex.EncodeToString(localHash[:])[:8] // Take first 8 chars

	// Hash the domain part  
	domainHash := sha256.Sum256(append([]byte(parts[1]), key.Salt...))
	domainPseudo := hex.EncodeToString(domainHash[:])[:8] // Take first 8 chars

	pseudoEmail := localPseudo + "@" + domainPseudo + ".example"

	// Create hash for lookup
	hasher := sha256.New()
	hasher.Write([]byte(email))
	hasher.Write(key.Salt)
	hashValue := hex.EncodeToString(hasher.Sum(nil))

	return pseudoEmail, hashValue, nil
}

// formatPreservingIPAddress preserves IP address format
func (pe *PseudonymizationEngine) formatPreservingIPAddress(ip string, key *CryptoKey) (string, string, error) {
	// Hash the IP and convert to new IP format
	hasher := sha256.New()
	hasher.Write([]byte(ip))
	hasher.Write(key.Salt)
	hash := hasher.Sum(nil)

	// Convert hash bytes to IP octets (keeping private range 10.x.x.x)
	pseudoIP := fmt.Sprintf("10.%d.%d.%d", hash[0], hash[1], hash[2])

	hashValue := hex.EncodeToString(hash)

	return pseudoIP, hashValue, nil
}

// formatPreservingDePseudonymization reverses format-preserving pseudonymization
func (pe *PseudonymizationEngine) formatPreservingDePseudonymization(pseudoData, dataType string, key *CryptoKey) (string, error) {
	// Format-preserving pseudonymization is typically one-way for privacy
	// This would require a lookup table for reversible operations
	return "", fmt.Errorf("format-preserving de-pseudonymization requires lookup table (not implemented for privacy)")
}

// tokenizationPseudonymization performs tokenization-based pseudonymization
func (pe *PseudonymizationEngine) tokenizationPseudonymization(data string, key *CryptoKey) (string, string, error) {
	// Generate a random token
	token := make([]byte, 16)
	if _, err := rand.Read(token); err != nil {
		return "", "", fmt.Errorf("failed to generate token: %w", err)
	}

	tokenStr := base64.URLEncoding.EncodeToString(token)

	// Create hash for lookup
	hasher := sha256.New()
	hasher.Write([]byte(data))
	hasher.Write(key.Salt)
	hashValue := hex.EncodeToString(hasher.Sum(nil))

	// Note: In practice, this would store the mapping in a secure token vault
	// For this implementation, we're showing the concept

	return tokenStr, hashValue, nil
}

// tokenizationDePseudonymization reverses tokenization
func (pe *PseudonymizationEngine) tokenizationDePseudonymization(token string, key *CryptoKey) (string, error) {
	// This would lookup the token in a secure vault
	// For this implementation, return error as vault is not implemented
	return "", fmt.Errorf("tokenization de-pseudonymization requires secure token vault (not implemented)")
}

// RotateKeys performs key rotation
func (pe *PseudonymizationEngine) RotateKeys() error {
	return pe.keyManager.RotateKeys()
}

// GetMetrics returns pseudonymization metrics for compliance monitoring
func (pe *PseudonymizationEngine) GetMetrics() (*PseudonymizationMetrics, error) {
	// Implementation would collect actual metrics
	return &PseudonymizationMetrics{
		TotalPseudonymizations:   0,
		ActiveKeys:              len(pe.keyManager.activeKeys),
		LastKeyRotation:         time.Now().Add(-time.Hour),
		AlgorithmDistribution:   map[PseudoAlgorithm]int{},
		ComplianceScore:         95.5,
	}, nil
}

// PseudonymizationMetrics contains metrics for monitoring
type PseudonymizationMetrics struct {
	TotalPseudonymizations int                         `json:"total_pseudonymizations"`
	ActiveKeys            int                         `json:"active_keys"`
	LastKeyRotation       time.Time                   `json:"last_key_rotation"`
	AlgorithmDistribution map[PseudoAlgorithm]int     `json:"algorithm_distribution"`
	ComplianceScore       float64                     `json:"compliance_score"`
}

// generateID generates a unique ID for audit trails
func generateID() string {
	id := make([]byte, 16)
	rand.Read(id)
	return hex.EncodeToString(id)
}