package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

// Config represents the application configuration
type Config struct {
	LogLevel   string           `mapstructure:"log_level"`
	LogFormat  string           `mapstructure:"log_format"`
	DataDir    string           `mapstructure:"data_dir"`
	ConfigDir  string           `mapstructure:"config_dir"`
	WireGuard  WireGuardConfig  `mapstructure:"wireguard"`
	Captive    CaptiveConfig    `mapstructure:"captive"`
	Multipath  MultipathConfig  `mapstructure:"multipath"`
	Monitoring MonitoringConfig `mapstructure:"monitoring"`
	Export     ExportConfig     `mapstructure:"export"`
}

// WireGuardConfig contains WireGuard-specific configuration
type WireGuardConfig struct {
	KeysDir     string   `mapstructure:"keys_dir"`
	ConfigsDir  string   `mapstructure:"configs_dir"`
	DefaultDNS  []string `mapstructure:"default_dns"`
	DefaultMTU  int      `mapstructure:"default_mtu"`
	DefaultPort int      `mapstructure:"default_port"`
	AllowedIPs  []string `mapstructure:"allowed_ips"`
	Keepalive   int      `mapstructure:"keepalive"`
	PostUp      []string `mapstructure:"post_up"`
	PostDown    []string `mapstructure:"post_down"`
}

// CaptiveConfig contains captive portal detection configuration
type CaptiveConfig struct {
	TestURLs        []string `mapstructure:"test_urls"`
	ExpectedStatus  int      `mapstructure:"expected_status"`
	Timeout         int      `mapstructure:"timeout"`
	Retries         int      `mapstructure:"retries"`
	Interval        int      `mapstructure:"interval"`
	UserAgent       string   `mapstructure:"user_agent"`
	FollowRedirects bool     `mapstructure:"follow_redirects"`
	CheckDNS        bool     `mapstructure:"check_dns"`
}

// MultipathConfig contains multipath networking configuration
type MultipathConfig struct {
	PrimaryInterface  string   `mapstructure:"primary_interface"`
	BackupInterface   string   `mapstructure:"backup_interface"`
	FailoverThreshold int      `mapstructure:"failover_threshold"`
	RecoveryThreshold int      `mapstructure:"recovery_threshold"`
	CheckInterval     int      `mapstructure:"check_interval"`
	EnableKillSwitch  bool     `mapstructure:"enable_kill_switch"`
	DNSServers        []string `mapstructure:"dns_servers"`
	RoutingTable      string   `mapstructure:"routing_table"`
}

// MonitoringConfig contains monitoring configuration
type MonitoringConfig struct {
	Enabled         bool    `mapstructure:"enabled"`
	Interval        int     `mapstructure:"interval"`
	AlertThreshold  float64 `mapstructure:"alert_threshold"`
	LogOutput       string  `mapstructure:"log_output"`
	EnableAlerts    bool    `mapstructure:"enable_alerts"`
	MetricsEndpoint string  `mapstructure:"metrics_endpoint"`
}

// ExportConfig contains export configuration
type ExportConfig struct {
	IOSOrganization string `mapstructure:"ios_organization"`
	IOSIdentifier   string `mapstructure:"ios_identifier"`
	AndroidPackage  string `mapstructure:"android_package"`
	TemplatesDir    string `mapstructure:"templates_dir"`
}

var globalConfig *Config

// Init initializes the configuration system
func Init() error {
	// Set default values
	setDefaults()

	// Set up viper
	viper.SetConfigName(".net-sec")
	viper.SetConfigType("yaml")

	// Add config paths
	home, err := os.UserHomeDir()
	if err != nil {
		return fmt.Errorf("failed to get user home directory: %w", err)
	}

	viper.AddConfigPath(home)
	viper.AddConfigPath("/etc/net-sec/")
	viper.AddConfigPath(".")

	// Set environment variable prefix
	viper.SetEnvPrefix("NETSEC")
	viper.AutomaticEnv()

	// Try to read config file
	if err := viper.ReadInConfig(); err != nil {
		// Config file not found is OK, we'll use defaults
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return fmt.Errorf("failed to read config file: %w", err)
		}
	}

	// Unmarshal config
	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// Ensure data directories exist
	if err := ensureDirectories(&cfg); err != nil {
		return fmt.Errorf("failed to create directories: %w", err)
	}

	globalConfig = &cfg
	return nil
}

// Get returns the global configuration
func Get() *Config {
	if globalConfig == nil {
		panic("configuration not initialized")
	}
	return globalConfig
}

// setDefaults sets default configuration values
func setDefaults() {
	home, _ := os.UserHomeDir()
	dataDir := filepath.Join(home, ".net-sec")

	// General defaults
	viper.SetDefault("log_level", "info")
	viper.SetDefault("log_format", "text")
	viper.SetDefault("data_dir", dataDir)
	viper.SetDefault("config_dir", dataDir)

	// WireGuard defaults
	viper.SetDefault("wireguard.keys_dir", filepath.Join(dataDir, "keys"))
	viper.SetDefault("wireguard.configs_dir", filepath.Join(dataDir, "configs"))
	viper.SetDefault("wireguard.default_dns", []string{"1.1.1.1", "9.9.9.9"})
	viper.SetDefault("wireguard.default_mtu", 1420)
	viper.SetDefault("wireguard.default_port", 51820)
	viper.SetDefault("wireguard.allowed_ips", []string{"0.0.0.0/0", "::/0"})
	viper.SetDefault("wireguard.keepalive", 25)
	viper.SetDefault("wireguard.post_up", []string{})
	viper.SetDefault("wireguard.post_down", []string{})

	// Captive portal defaults
	viper.SetDefault("captive.test_urls", []string{
		"http://clients3.google.com/generate_204",
		"http://detectportal.firefox.com/canonical.html",
		"http://www.msftconnecttest.com/connecttest.txt",
	})
	viper.SetDefault("captive.expected_status", 204)
	viper.SetDefault("captive.timeout", 10)
	viper.SetDefault("captive.retries", 3)
	viper.SetDefault("captive.interval", 5)
	viper.SetDefault("captive.user_agent", "Mozilla/5.0 (compatible; net-sec/1.0)")
	viper.SetDefault("captive.follow_redirects", false)
	viper.SetDefault("captive.check_dns", true)

	// Multipath defaults
	viper.SetDefault("multipath.primary_interface", "")
	viper.SetDefault("multipath.backup_interface", "")
	viper.SetDefault("multipath.failover_threshold", 3)
	viper.SetDefault("multipath.recovery_threshold", 5)
	viper.SetDefault("multipath.check_interval", 5)
	viper.SetDefault("multipath.enable_kill_switch", false)
	viper.SetDefault("multipath.dns_servers", []string{"1.1.1.1", "9.9.9.9"})
	viper.SetDefault("multipath.routing_table", "main")

	// Monitoring defaults
	viper.SetDefault("monitoring.enabled", false)
	viper.SetDefault("monitoring.interval", 30)
	viper.SetDefault("monitoring.alert_threshold", 0.9)
	viper.SetDefault("monitoring.log_output", "")
	viper.SetDefault("monitoring.enable_alerts", false)
	viper.SetDefault("monitoring.metrics_endpoint", "")

	// Export defaults
	viper.SetDefault("export.ios_organization", "StealthGuard Technologies")
	viper.SetDefault("export.ios_identifier", "com.stealthguard.wireguard")
	viper.SetDefault("export.android_package", "com.wireguard.android")
	viper.SetDefault("export.templates_dir", filepath.Join(dataDir, "templates"))
}

// ensureDirectories creates necessary directories
func ensureDirectories(cfg *Config) error {
	dirs := []string{
		cfg.DataDir,
		cfg.ConfigDir,
		cfg.WireGuard.KeysDir,
		cfg.WireGuard.ConfigsDir,
		cfg.Export.TemplatesDir,
	}

	for _, dir := range dirs {
		if dir != "" {
			if err := os.MkdirAll(dir, 0750); err != nil {
				return fmt.Errorf("failed to create directory %s: %w", dir, err)
			}
		}
	}

	return nil
}

// WriteConfig writes the current configuration to file
func WriteConfig() error {
	return viper.WriteConfig()
}

// WriteConfigAs writes the current configuration to a specific file
func WriteConfigAs(filename string) error {
	return viper.WriteConfigAs(filename)
}
