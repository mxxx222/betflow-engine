package export

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
)

// IOSExporter handles iOS .mobileconfig file generation
type IOSExporter struct {
	config *IOSConfig
}

// IOSConfig contains iOS configuration options
type IOSConfig struct {
	DisplayName       string
	Description       string
	Organization      string
	Identifier        string
	RemovalDisallowed bool
	ConsentText       string
	WireGuardConfig   *WireGuardConfig
	DNSConfig         *DNSConfig
	VPNConfig         *VPNConfig
}

// WireGuardConfig contains WireGuard VPN configuration
type WireGuardConfig struct {
	ServerAddress       string
	ServerPort          int
	ServerPublicKey     string
	ClientPrivateKey    string
	ClientAddress       string
	DNS                 []string
	AllowedIPs          []string
	PersistentKeepalive int
}

// DNSConfig contains DNS configuration
type DNSConfig struct {
	ServerAddresses          []string
	Domain                   string
	SearchDomains            []string
	SupplementalMatchDomains []string
}

// VPNConfig contains general VPN configuration
type VPNConfig struct {
	ConnectionName       string
	ServerAddress        string
	AuthenticationMethod string
	DisconnectOnSleep    bool
	OnDemandEnabled      bool
	OnDemandRules        []OnDemandRule
}

// OnDemandRule represents VPN on-demand connection rules
type OnDemandRule struct {
	Action             string   `json:"Action"`
	InterfaceTypeMatch string   `json:"InterfaceTypeMatch,omitempty"`
	SSIDMatch          []string `json:"SSIDMatch,omitempty"`
	DNSDomainMatch     []string `json:"DNSDomainMatch,omitempty"`
	URLStringProbe     string   `json:"URLStringProbe,omitempty"`
}

// MobileConfigPayload represents the main payload structure
type MobileConfigPayload struct {
	PayloadContent           []interface{} `plist:"PayloadContent"`
	PayloadDescription       string        `plist:"PayloadDescription"`
	PayloadDisplayName       string        `plist:"PayloadDisplayName"`
	PayloadIdentifier        string        `plist:"PayloadIdentifier"`
	PayloadOrganization      string        `plist:"PayloadOrganization"`
	PayloadRemovalDisallowed bool          `plist:"PayloadRemovalDisallowed"`
	PayloadType              string        `plist:"PayloadType"`
	PayloadUUID              string        `plist:"PayloadUUID"`
	PayloadVersion           int           `plist:"PayloadVersion"`
	ConsentText              string        `plist:"ConsentText,omitempty"`
}

// VPNPayload represents a VPN configuration payload
type VPNPayload struct {
	PayloadDescription string                 `plist:"PayloadDescription"`
	PayloadDisplayName string                 `plist:"PayloadDisplayName"`
	PayloadIdentifier  string                 `plist:"PayloadIdentifier"`
	PayloadType        string                 `plist:"PayloadType"`
	PayloadUUID        string                 `plist:"PayloadUUID"`
	PayloadVersion     int                    `plist:"PayloadVersion"`
	UserDefinedName    string                 `plist:"UserDefinedName"`
	VPNType            string                 `plist:"VPNType"`
	VendorConfig       map[string]interface{} `plist:"VendorConfig"`
	VPN                VPNSettings            `plist:"VPN"`
}

// VPNSettings contains VPN connection settings
type VPNSettings struct {
	AuthenticationMethod string                 `plist:"AuthenticationMethod"`
	RemoteAddress        string                 `plist:"RemoteAddress"`
	OnDemandEnabled      int                    `plist:"OnDemandEnabled"`
	OnDemandRules        []OnDemandRule         `plist:"OnDemandRules,omitempty"`
	DisconnectOnSleep    int                    `plist:"DisconnectOnSleep"`
	VendorConfig         map[string]interface{} `plist:"VendorConfig"`
}

// DNSPayload represents a DNS configuration payload
type DNSPayload struct {
	PayloadDescription string      `plist:"PayloadDescription"`
	PayloadDisplayName string      `plist:"PayloadDisplayName"`
	PayloadIdentifier  string      `plist:"PayloadIdentifier"`
	PayloadType        string      `plist:"PayloadType"`
	PayloadUUID        string      `plist:"PayloadUUID"`
	PayloadVersion     int         `plist:"PayloadVersion"`
	DNSSettings        DNSSettings `plist:"DNSSettings"`
}

// DNSSettings contains DNS configuration settings
type DNSSettings struct {
	DNSProtocol              string   `plist:"DNSProtocol"`
	ServerAddresses          []string `plist:"ServerAddresses"`
	ServerName               string   `plist:"ServerName,omitempty"`
	SearchDomains            []string `plist:"SearchDomains,omitempty"`
	SupplementalMatchDomains []string `plist:"SupplementalMatchDomains,omitempty"`
}

// NewIOSExporter creates a new iOS configuration exporter
func NewIOSExporter() *IOSExporter {
	return &IOSExporter{}
}

// GenerateConfig generates an iOS .mobileconfig file
func (e *IOSExporter) GenerateConfig(config *IOSConfig, outputPath string) error {
	e.config = config

	// Create main payload
	payload := &MobileConfigPayload{
		PayloadContent:           []interface{}{},
		PayloadDescription:       config.Description,
		PayloadDisplayName:       config.DisplayName,
		PayloadIdentifier:        config.Identifier,
		PayloadOrganization:      config.Organization,
		PayloadRemovalDisallowed: config.RemovalDisallowed,
		PayloadType:              "Configuration",
		PayloadUUID:              generateUUID(),
		PayloadVersion:           1,
		ConsentText:              config.ConsentText,
	}

	// Add VPN payload if WireGuard config is provided
	if config.WireGuardConfig != nil {
		vpnPayload := e.createVPNPayload()
		payload.PayloadContent = append(payload.PayloadContent, vpnPayload)
	}

	// Add DNS payload if DNS config is provided
	if config.DNSConfig != nil {
		dnsPayload := e.createDNSPayload()
		payload.PayloadContent = append(payload.PayloadContent, dnsPayload)
	}

	// Generate plist XML
	plistData, err := e.generatePlist(payload)
	if err != nil {
		return fmt.Errorf("failed to generate plist: %w", err)
	}

	// Write to file
	err = os.WriteFile(outputPath, plistData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// createVPNPayload creates a VPN configuration payload for WireGuard
func (e *IOSExporter) createVPNPayload() *VPNPayload {
	wg := e.config.WireGuardConfig

	vendorConfig := map[string]interface{}{
		"public_key":  wg.ServerPublicKey,
		"private_key": wg.ClientPrivateKey,
		"addresses":   wg.ClientAddress,
		"listen_port": 0,
		"mtu":         1280,
		"dns":         strings.Join(wg.DNS, ","),
	}

	// Add peer configuration
	peers := []map[string]interface{}{
		{
			"public_key":           wg.ServerPublicKey,
			"allowed_ips":          strings.Join(wg.AllowedIPs, ","),
			"endpoint":             fmt.Sprintf("%s:%d", wg.ServerAddress, wg.ServerPort),
			"persistent_keepalive": wg.PersistentKeepalive,
		},
	}
	vendorConfig["peers"] = peers

	// Create on-demand rules
	onDemandRules := []OnDemandRule{
		{
			Action:             "Connect",
			InterfaceTypeMatch: "WiFi",
		},
		{
			Action:             "Connect",
			InterfaceTypeMatch: "Cellular",
		},
	}

	vpnSettings := VPNSettings{
		AuthenticationMethod: "None",
		RemoteAddress:        wg.ServerAddress,
		OnDemandEnabled:      1,
		OnDemandRules:        onDemandRules,
		DisconnectOnSleep:    0,
		VendorConfig:         vendorConfig,
	}

	return &VPNPayload{
		PayloadDescription: "WireGuard VPN Configuration",
		PayloadDisplayName: "WireGuard VPN",
		PayloadIdentifier:  e.config.Identifier + ".vpn",
		PayloadType:        "com.apple.vpn.managed",
		PayloadUUID:        generateUUID(),
		PayloadVersion:     1,
		UserDefinedName:    e.config.WireGuardConfig.ServerAddress,
		VPNType:            "VPN",
		VendorConfig:       vendorConfig,
		VPN:                vpnSettings,
	}
}

// createDNSPayload creates a DNS configuration payload
func (e *IOSExporter) createDNSPayload() *DNSPayload {
	dns := e.config.DNSConfig

	dnsSettings := DNSSettings{
		DNSProtocol:              "HTTPS",
		ServerAddresses:          dns.ServerAddresses,
		ServerName:               dns.Domain,
		SearchDomains:            dns.SearchDomains,
		SupplementalMatchDomains: dns.SupplementalMatchDomains,
	}

	return &DNSPayload{
		PayloadDescription: "DNS Configuration",
		PayloadDisplayName: "DNS Settings",
		PayloadIdentifier:  e.config.Identifier + ".dns",
		PayloadType:        "com.apple.dnsSettings.managed",
		PayloadUUID:        generateUUID(),
		PayloadVersion:     1,
		DNSSettings:        dnsSettings,
	}
}

// generatePlist converts the payload to plist XML format
func (e *IOSExporter) generatePlist(payload interface{}) ([]byte, error) {
	// This is a simplified plist generation
	// In a real implementation, you would use a proper plist library
	// like howett.net/plist or github.com/DHowett/go-plist

	// For now, generate a basic XML structure
	plistData := `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>PayloadContent</key>
	<array>
		<!-- VPN and DNS payloads would be inserted here -->
	</array>
	<key>PayloadDescription</key>
	<string>` + e.config.Description + `</string>
	<key>PayloadDisplayName</key>
	<string>` + e.config.DisplayName + `</string>
	<key>PayloadIdentifier</key>
	<string>` + e.config.Identifier + `</string>
	<key>PayloadOrganization</key>
	<string>` + e.config.Organization + `</string>
	<key>PayloadRemovalDisallowed</key>
	<` + fmt.Sprintf("%t", e.config.RemovalDisallowed) + `/>
	<key>PayloadType</key>
	<string>Configuration</string>
	<key>PayloadUUID</key>
	<string>` + generateUUID() + `</string>
	<key>PayloadVersion</key>
	<integer>1</integer>
</dict>
</plist>`

	return []byte(plistData), nil
}

// AndroidExporter handles Android JSON configuration export
type AndroidExporter struct {
	config *AndroidConfig
}

// AndroidConfig contains Android configuration options
type AndroidConfig struct {
	ProfileName     string
	Description     string
	Organization    string
	WireGuardConfig *WireGuardConfig
	DNSConfig       *DNSConfig
	WiFiConfig      *WiFiConfig
	VPNConfig       *AndroidVPNConfig
	Restrictions    *AndroidRestrictions
}

// AndroidVPNConfig contains Android-specific VPN configuration
type AndroidVPNConfig struct {
	ConnectionName   string
	ServerAddress    string
	ServerPort       int
	Protocol         string
	Authentication   string
	AlwaysOn         bool
	BlockConnections bool
	BypassVPN        []string
}

// WiFiConfig contains WiFi configuration for Android
type WiFiConfig struct {
	SSID          string
	Password      string
	Security      string
	Hidden        bool
	ProxySettings string
	ProxyHost     string
	ProxyPort     int
}

// AndroidRestrictions contains Android device restrictions
type AndroidRestrictions struct {
	DisableCamera       bool
	DisableBluetooth    bool
	DisableUSB          bool
	DisableScreenshots  bool
	RequirePasswordLock bool
	PasswordMinLength   int
	MaxPasswordAge      int
}

// AndroidProfile represents the complete Android configuration profile
type AndroidProfile struct {
	ProfileInfo  ProfileInfo          `json:"profile_info"`
	VPNConfig    *AndroidVPNConfig    `json:"vpn_config,omitempty"`
	DNSConfig    *DNSConfig           `json:"dns_config,omitempty"`
	WiFiConfig   *WiFiConfig          `json:"wifi_config,omitempty"`
	Restrictions *AndroidRestrictions `json:"restrictions,omitempty"`
	Applications []AndroidApplication `json:"applications,omitempty"`
	Timestamp    time.Time            `json:"timestamp"`
}

// ProfileInfo contains basic profile information
type ProfileInfo struct {
	Name         string `json:"name"`
	Description  string `json:"description"`
	Organization string `json:"organization"`
	Version      string `json:"version"`
	Platform     string `json:"platform"`
}

// AndroidApplication represents an app configuration
type AndroidApplication struct {
	PackageName   string                 `json:"package_name"`
	AppName       string                 `json:"app_name"`
	InstallType   string                 `json:"install_type"`
	Configuration map[string]interface{} `json:"configuration,omitempty"`
	Permissions   []string               `json:"permissions,omitempty"`
}

// NewAndroidExporter creates a new Android configuration exporter
func NewAndroidExporter() *AndroidExporter {
	return &AndroidExporter{}
}

// GenerateConfig generates an Android JSON configuration file
func (e *AndroidExporter) GenerateConfig(config *AndroidConfig, outputPath string) error {
	e.config = config

	profile := &AndroidProfile{
		ProfileInfo: ProfileInfo{
			Name:         config.ProfileName,
			Description:  config.Description,
			Organization: config.Organization,
			Version:      "1.0",
			Platform:     "Android",
		},
		VPNConfig:    config.VPNConfig,
		DNSConfig:    config.DNSConfig,
		WiFiConfig:   config.WiFiConfig,
		Restrictions: config.Restrictions,
		Timestamp:    time.Now(),
	}

	// Add WireGuard app configuration if WireGuard config is provided
	if config.WireGuardConfig != nil {
		wireGuardApp := e.createWireGuardAppConfig()
		profile.Applications = append(profile.Applications, wireGuardApp)
	}

	// Generate JSON
	jsonData, err := json.MarshalIndent(profile, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	// Write to file
	err = os.WriteFile(outputPath, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// createWireGuardAppConfig creates WireGuard app configuration
func (e *AndroidExporter) createWireGuardAppConfig() AndroidApplication {
	wg := e.config.WireGuardConfig

	// Create WireGuard configuration string
	configStr := fmt.Sprintf(`[Interface]
PrivateKey = %s
Address = %s
DNS = %s

[Peer]
PublicKey = %s
Endpoint = %s:%d
AllowedIPs = %s
PersistentKeepalive = %d`,
		wg.ClientPrivateKey,
		wg.ClientAddress,
		strings.Join(wg.DNS, ", "),
		wg.ServerPublicKey,
		wg.ServerAddress,
		wg.ServerPort,
		strings.Join(wg.AllowedIPs, ", "),
		wg.PersistentKeepalive)

	configuration := map[string]interface{}{
		"tunnel_config": configStr,
		"tunnel_name":   "StealthGuard",
		"auto_start":    true,
		"exclude_apps":  []string{},
	}

	return AndroidApplication{
		PackageName:   "com.wireguard.android",
		AppName:       "WireGuard",
		InstallType:   "REQUIRED_FOR_SETUP",
		Configuration: configuration,
		Permissions: []string{
			"android.permission.INTERNET",
			"android.permission.ACCESS_NETWORK_STATE",
		},
	}
}

// ExportOptions contains common export options
type ExportOptions struct {
	OutputDir        string
	FilePrefix       string
	IncludeTimestamp bool
	Overwrite        bool
}

// generateUUID generates a new UUID string
func generateUUID() string {
	uuid, _ := uuid.NewRandom()
	return uuid.String()
}

// generateFileName generates an appropriate filename for export
func generateFileName(prefix, extension string, includeTimestamp bool) string {
	filename := prefix
	if includeTimestamp {
		timestamp := time.Now().Format("20060102-150405")
		filename = fmt.Sprintf("%s-%s", prefix, timestamp)
	}
	return fmt.Sprintf("%s.%s", filename, extension)
}

// ensureOutputDir ensures the output directory exists
func ensureOutputDir(outputPath string) error {
	dir := filepath.Dir(outputPath)
	return os.MkdirAll(dir, 0755)
}
