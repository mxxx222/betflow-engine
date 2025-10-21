package wireguard

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/crypto/curve25519"
)

// Generator handles WireGuard configuration generation
type Generator struct {
	keysDir    string
	configsDir string
}

// GeneratorOptions contains configuration options for generation
type GeneratorOptions struct {
	ServerEndpoint  string
	ServerPublicKey string
	ClientName      string
	ClientIP        string
	DNS             []string
	MTU             int
	Keepalive       int
	GenerateKeys    bool
}

// Config represents a WireGuard configuration
type Config struct {
	Interface Interface `json:"interface"`
	Peer      Peer      `json:"peer"`
	Metadata  Metadata  `json:"metadata"`
}

// Interface represents the [Interface] section
type Interface struct {
	PrivateKey string   `json:"private_key"`
	Address    string   `json:"address"`
	DNS        []string `json:"dns"`
	MTU        int      `json:"mtu"`
	PostUp     []string `json:"post_up,omitempty"`
	PostDown   []string `json:"post_down,omitempty"`
}

// Peer represents the [Peer] section
type Peer struct {
	PublicKey           string   `json:"public_key"`
	AllowedIPs          []string `json:"allowed_ips"`
	Endpoint            string   `json:"endpoint"`
	PersistentKeepalive int      `json:"persistent_keepalive"`
}

// Metadata contains additional configuration metadata
type Metadata struct {
	ClientName    string    `json:"client_name"`
	CreatedAt     time.Time `json:"created_at"`
	KeysGenerated bool      `json:"keys_generated"`
}

// Summary contains configuration summary information
type Summary struct {
	ClientName     string
	ClientIP       string
	ServerEndpoint string
	DNS            []string
	MTU            int
	Keepalive      int
	KeysGenerated  bool
}

// KeyPair represents a WireGuard key pair
type KeyPair struct {
	PrivateKey string
	PublicKey  string
}

// NewGenerator creates a new WireGuard configuration generator
func NewGenerator() *Generator {
	home, _ := os.UserHomeDir()
	baseDir := filepath.Join(home, ".net-sec")

	return &Generator{
		keysDir:    filepath.Join(baseDir, "keys"),
		configsDir: filepath.Join(baseDir, "configs"),
	}
}

// GenerateConfig generates a WireGuard configuration
func (g *Generator) GenerateConfig(opts *GeneratorOptions) (*Config, error) {
	// Ensure directories exist
	if err := os.MkdirAll(g.keysDir, 0700); err != nil {
		return nil, fmt.Errorf("failed to create keys directory: %w", err)
	}
	if err := os.MkdirAll(g.configsDir, 0700); err != nil {
		return nil, fmt.Errorf("failed to create configs directory: %w", err)
	}

	// Validate inputs
	if err := g.validateOptions(opts); err != nil {
		return nil, fmt.Errorf("invalid options: %w", err)
	}

	// Generate keys if needed
	var keyPair *KeyPair
	var err error

	if opts.GenerateKeys {
		keyPair, err = g.GenerateKeyPair()
		if err != nil {
			return nil, fmt.Errorf("failed to generate keys: %w", err)
		}
	}

	// Generate server public key if not provided
	serverPublicKey := opts.ServerPublicKey
	if serverPublicKey == "" && opts.GenerateKeys {
		// For demo purposes, generate a server key pair
		serverKeyPair, err := g.GenerateKeyPair()
		if err != nil {
			return nil, fmt.Errorf("failed to generate server keys: %w", err)
		}
		serverPublicKey = serverKeyPair.PublicKey
	}

	// Create configuration
	config := &Config{
		Interface: Interface{
			PrivateKey: keyPair.PrivateKey,
			Address:    opts.ClientIP,
			DNS:        opts.DNS,
			MTU:        opts.MTU,
			PostUp:     g.generatePostUpCommands(opts),
			PostDown:   g.generatePostDownCommands(opts),
		},
		Peer: Peer{
			PublicKey:           serverPublicKey,
			AllowedIPs:          []string{"0.0.0.0/0", "::/0"},
			Endpoint:            opts.ServerEndpoint,
			PersistentKeepalive: opts.Keepalive,
		},
		Metadata: Metadata{
			ClientName:    opts.ClientName,
			CreatedAt:     time.Now(),
			KeysGenerated: opts.GenerateKeys,
		},
	}

	return config, nil
}

// GenerateKeyPair generates a new WireGuard key pair
func (g *Generator) GenerateKeyPair() (*KeyPair, error) {
	// Generate private key
	var privateKey [32]byte
	if _, err := rand.Read(privateKey[:]); err != nil {
		return nil, fmt.Errorf("failed to generate private key: %w", err)
	}

	// Generate public key
	var publicKey [32]byte
	curve25519.ScalarBaseMult(&publicKey, &privateKey)

	return &KeyPair{
		PrivateKey: base64.StdEncoding.EncodeToString(privateKey[:]),
		PublicKey:  base64.StdEncoding.EncodeToString(publicKey[:]),
	}, nil
}

// validateOptions validates generator options
func (g *Generator) validateOptions(opts *GeneratorOptions) error {
	if opts.ServerEndpoint == "" {
		return fmt.Errorf("server endpoint is required")
	}

	// Validate endpoint format
	if !strings.Contains(opts.ServerEndpoint, ":") {
		return fmt.Errorf("server endpoint must include port (host:port)")
	}

	// Validate client IP if provided
	if opts.ClientIP != "" {
		if _, _, err := net.ParseCIDR(opts.ClientIP); err != nil {
			return fmt.Errorf("invalid client IP format (use CIDR notation): %w", err)
		}
	}

	// Validate DNS servers
	for _, dns := range opts.DNS {
		if net.ParseIP(dns) == nil {
			return fmt.Errorf("invalid DNS server IP: %s", dns)
		}
	}

	// Validate MTU
	if opts.MTU < 1280 || opts.MTU > 1500 {
		return fmt.Errorf("MTU must be between 1280 and 1500")
	}

	// Validate keepalive
	if opts.Keepalive < 0 || opts.Keepalive > 65535 {
		return fmt.Errorf("keepalive must be between 0 and 65535")
	}

	return nil
}

// generatePostUpCommands generates PostUp commands for security
func (g *Generator) generatePostUpCommands(opts *GeneratorOptions) []string {
	var commands []string

	// Add iptables rules for kill-switch (Linux)
	commands = append(commands, []string{
		"iptables -I OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL -j REJECT",
		"ip6tables -I OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL -j REJECT",
	}...)

	return commands
}

// generatePostDownCommands generates PostDown commands
func (g *Generator) generatePostDownCommands(opts *GeneratorOptions) []string {
	var commands []string

	// Remove iptables rules
	commands = append(commands, []string{
		"iptables -D OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL -j REJECT",
		"ip6tables -D OUTPUT ! -o %i -m mark ! --mark $(wg show %i fwmark) -m addrtype ! --dst-type LOCAL -j REJECT",
	}...)

	return commands
}

// String returns the configuration as a WireGuard config file string
func (c *Config) String() string {
	var builder strings.Builder

	// Write header comment
	builder.WriteString(fmt.Sprintf("# WireGuard configuration for %s\n", c.Metadata.ClientName))
	builder.WriteString(fmt.Sprintf("# Generated on %s\n", c.Metadata.CreatedAt.Format("2006-01-02 15:04:05")))
	builder.WriteString("# DO NOT EDIT MANUALLY\n\n")

	// Write [Interface] section
	builder.WriteString("[Interface]\n")
	builder.WriteString(fmt.Sprintf("PrivateKey = %s\n", c.Interface.PrivateKey))
	builder.WriteString(fmt.Sprintf("Address = %s\n", c.Interface.Address))

	if len(c.Interface.DNS) > 0 {
		builder.WriteString(fmt.Sprintf("DNS = %s\n", strings.Join(c.Interface.DNS, ", ")))
	}

	if c.Interface.MTU > 0 {
		builder.WriteString(fmt.Sprintf("MTU = %d\n", c.Interface.MTU))
	}

	// Write PostUp commands
	for _, cmd := range c.Interface.PostUp {
		builder.WriteString(fmt.Sprintf("PostUp = %s\n", cmd))
	}

	// Write PostDown commands
	for _, cmd := range c.Interface.PostDown {
		builder.WriteString(fmt.Sprintf("PostDown = %s\n", cmd))
	}

	builder.WriteString("\n")

	// Write [Peer] section
	builder.WriteString("[Peer]\n")
	builder.WriteString(fmt.Sprintf("PublicKey = %s\n", c.Peer.PublicKey))
	builder.WriteString(fmt.Sprintf("AllowedIPs = %s\n", strings.Join(c.Peer.AllowedIPs, ", ")))
	builder.WriteString(fmt.Sprintf("Endpoint = %s\n", c.Peer.Endpoint))

	if c.Peer.PersistentKeepalive > 0 {
		builder.WriteString(fmt.Sprintf("PersistentKeepalive = %d\n", c.Peer.PersistentKeepalive))
	}

	return builder.String()
}

// WriteToFile writes the configuration to a file
func (c *Config) WriteToFile(filename string) error {
	// Ensure directory exists
	dir := filepath.Dir(filename)
	if err := os.MkdirAll(dir, 0750); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Write configuration file
	if err := os.WriteFile(filename, []byte(c.String()), 0600); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// WriteKeysToFiles writes private and public keys to separate files
func (c *Config) WriteKeysToFiles(basePath string) error {
	dir := filepath.Dir(basePath)
	name := strings.TrimSuffix(filepath.Base(basePath), filepath.Ext(basePath))

	// Write private key
	privateKeyPath := filepath.Join(dir, name+"_private.key")
	if err := os.WriteFile(privateKeyPath, []byte(c.Interface.PrivateKey), 0600); err != nil {
		return fmt.Errorf("failed to write private key: %w", err)
	}

	// Write public key (derived from private key)
	publicKey, err := c.derivePublicKey()
	if err != nil {
		return fmt.Errorf("failed to derive public key: %w", err)
	}

	publicKeyPath := filepath.Join(dir, name+"_public.key")
	if err := os.WriteFile(publicKeyPath, []byte(publicKey), 0644); err != nil {
		return fmt.Errorf("failed to write public key: %w", err)
	}

	return nil
}

// derivePublicKey derives the public key from the private key
func (c *Config) derivePublicKey() (string, error) {
	privateKeyBytes, err := base64.StdEncoding.DecodeString(c.Interface.PrivateKey)
	if err != nil {
		return "", fmt.Errorf("failed to decode private key: %w", err)
	}

	if len(privateKeyBytes) != 32 {
		return "", fmt.Errorf("invalid private key length")
	}

	var privateKey, publicKey [32]byte
	copy(privateKey[:], privateKeyBytes)
	curve25519.ScalarBaseMult(&publicKey, &privateKey)

	return base64.StdEncoding.EncodeToString(publicKey[:]), nil
}

// GetSummary returns a summary of the configuration
func (c *Config) GetSummary() Summary {
	return Summary{
		ClientName:     c.Metadata.ClientName,
		ClientIP:       c.Interface.Address,
		ServerEndpoint: c.Peer.Endpoint,
		DNS:            c.Interface.DNS,
		MTU:            c.Interface.MTU,
		Keepalive:      c.Peer.PersistentKeepalive,
		KeysGenerated:  c.Metadata.KeysGenerated,
	}
}
