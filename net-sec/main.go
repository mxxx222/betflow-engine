package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/stealthguard/net-sec/cmd"
	"github.com/stealthguard/net-sec/internal/config"
	"github.com/stealthguard/net-sec/internal/logger"
)

var (
	version = "1.0.0-enterprise"
	commit  = "dev"
	date    = "unknown"
)

func main() {
	// Initialize configuration
	if err := config.Init(); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to initialize configuration: %v\n", err)
		os.Exit(1)
	}

	// Initialize logger
	logger.Init(config.Get().LogLevel, config.Get().LogFormat)

	// Create root command with context
	ctx := context.Background()
	rootCmd := cmd.NewRootCommand(version, commit, date)

	// Execute command
	if err := rootCmd.ExecuteContext(ctx); err != nil {
		log.Printf("Command execution failed: %v", err)
		os.Exit(1)
	}
}
