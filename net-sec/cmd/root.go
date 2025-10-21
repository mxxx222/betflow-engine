package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	cfgFile string
	verbose bool
)

// NewRootCommand creates the root command for the net-sec CLI
func NewRootCommand(version, commit, date string) *cobra.Command {
	rootCmd := &cobra.Command{
		Use:   "net-sec",
		Short: "Enterprise networking security toolkit",
		Long: `net-sec is a comprehensive enterprise networking security CLI tool that provides:

• WireGuard VPN configuration generation and management
• Captive portal detection with HTTP 204 status monitoring
• Multipath networking with WiFi + LTE failover automation
• Cross-platform mobile configuration export (iOS/Android)
• Network kill-switch and failsafe mechanisms
• Enterprise-grade logging and monitoring

Part of the StealthGuard Enterprise Security Ecosystem.`,
		Version: fmt.Sprintf("%s (commit: %s, built: %s)", version, commit, date),
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			if verbose {
				viper.Set("log.level", "debug")
			}
		},
	}

	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.net-sec.yaml)")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "enable verbose logging")

	// Add subcommands
	rootCmd.AddCommand(NewGenCommand())
	rootCmd.AddCommand(NewIOSExportCommand())
	rootCmd.AddCommand(NewAndroidExportCommand())
	rootCmd.AddCommand(NewDetectCommand())
	rootCmd.AddCommand(NewMultipathCommand())
	rootCmd.AddCommand(NewTestCommand())
	rootCmd.AddCommand(NewMonitorCommand())

	// Initialize config on startup
	cobra.OnInitialize(initConfig)

	return rootCmd
}

// initConfig reads in config file and ENV variables
func initConfig() {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		home, err := os.UserHomeDir()
		cobra.CheckErr(err)

		viper.AddConfigPath(home)
		viper.AddConfigPath(".")
		viper.SetConfigType("yaml")
		viper.SetConfigName(".net-sec")
	}

	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err == nil && verbose {
		fmt.Fprintln(os.Stderr, "Using config file:", viper.ConfigFileUsed())
	}
}
