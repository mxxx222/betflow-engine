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
	output  string
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "crypto-kit",
	Short: "Enterprise-grade cryptographic toolkit for field operations",
	Long: `CryptoKit: Offline-friendly cryptographic toolkit for StealthGuard Enterprise

A comprehensive CLI tool for:
• File encryption and sharing with age cryptography
• Hardware key integration (YubiKey/HSM)
• Cross-platform disk encryption management
• Key rotation and audit logging
• Zero-trust field operations

Examples:
  crypto-kit share --file report.pdf --recipient pubkey.age
  crypto-kit decrypt --file report.pdf.age --key hardware
  crypto-kit disk --init /dev/sdb --algo XTS-AES-256
  crypto-kit rotate --policy 90d --vault bitwarden`,
	Version: "1.0.0-enterprise",
}

// Execute adds all child commands to the root command and sets flags appropriately.
func Execute() error {
	return rootCmd.Execute()
}

func init() {
	cobra.OnInitialize(initConfig)

	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.crypto-kit.yaml)")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "enable verbose output")
	rootCmd.PersistentFlags().StringVarP(&output, "output", "o", "", "output file or directory")

	// Bind flags to viper
	viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))
	viper.BindPFlag("output", rootCmd.PersistentFlags().Lookup("output"))
}

// initConfig reads in config file and ENV variables if set.
func initConfig() {
	if cfgFile != "" {
		// Use config file from the flag.
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory.
		home, err := os.UserHomeDir()
		cobra.CheckErr(err)

		// Search config in home directory with name ".crypto-kit" (without extension).
		viper.AddConfigPath(home)
		viper.SetConfigType("yaml")
		viper.SetConfigName(".crypto-kit")
	}

	viper.AutomaticEnv() // read in environment variables that match

	// If a config file is found, read it in.
	if err := viper.ReadInConfig(); err == nil && verbose {
		fmt.Fprintln(os.Stderr, "Using config file:", viper.ConfigFileUsed())
	}
}

// Helper function for verbose logging
func logVerbose(format string, args ...interface{}) {
	if verbose || viper.GetBool("verbose") {
		fmt.Fprintf(os.Stderr, "[DEBUG] "+format+"\n", args...)
	}
}