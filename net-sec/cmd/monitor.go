package cmd

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spf13/cobra"
	"github.com/stealthguard/net-sec/internal/monitor"
)

var (
	monitorType     string
	monitorInterval time.Duration
	alertThreshold  float64
	logOutput       string
	enableAlerts    bool
)

// NewMonitorCommand creates the 'monitor' command for network monitoring
func NewMonitorCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "monitor",
		Short: "Monitor network connectivity and security status",
		Long: `Continuous monitoring of network connectivity, security status, and performance
metrics with real-time alerting and comprehensive logging.

Monitoring Features:
• Real-time connectivity and quality monitoring
• Captive portal detection and alerting
• Interface failover status and performance
• Kill-switch activation and security events
• DNS leak detection and resolution monitoring
• Bandwidth usage and performance metrics`,
		Example: `  # Basic network monitoring
  net-sec monitor

  # Monitor with custom interval and alerting
  net-sec monitor --type security --interval 30s --alerts

  # Monitor specific aspects with logging
  net-sec monitor --type connectivity --log /var/log/net-sec-monitor.log

  # Performance monitoring with thresholds
  net-sec monitor --type performance --threshold 0.8 --interval 10s`,
		RunE: runMonitorCommand,
	}

	// Monitor configuration flags
	cmd.Flags().StringVar(&monitorType, "type", "all", "Monitor type (connectivity/security/performance/all)")
	cmd.Flags().DurationVar(&monitorInterval, "interval", 30*time.Second, "Monitoring check interval")
	cmd.Flags().Float64Var(&alertThreshold, "threshold", 0.9, "Alert threshold (0.0-1.0)")
	cmd.Flags().StringVar(&logOutput, "log", "", "Log file path (stdout if empty)")
	cmd.Flags().BoolVar(&enableAlerts, "alerts", false, "Enable system alerting")

	return cmd
}

func runMonitorCommand(cmd *cobra.Command, args []string) error {
	fmt.Printf("📊 StealthGuard Network Monitor\n")
	fmt.Printf("===============================\n\n")

	// Create and initialize monitor
	mon := monitor.NewMonitor()
	monitorConfig := &monitor.MonitorConfig{
		CheckInterval:        30 * time.Second,
		NetworkCheckInterval: 10 * time.Second,
		VPNCheckInterval:     15 * time.Second,
		DNSCheckInterval:     20 * time.Second,
		CaptiveCheckInterval: 30 * time.Second,
		LogLevel:             "info",
		EnableAlerts:         true,
		EnableDashboard:      true,
		DashboardPort:        8080,
		MetricsRetention:     24 * time.Hour,
	}

	if err := mon.Initialize(monitorConfig); err != nil {
		fmt.Printf("❌ Failed to initialize monitor: %v\n", err)
		os.Exit(1)
	}

	// Start monitoring
	if err := mon.Start(); err != nil {
		fmt.Printf("❌ Failed to start monitor: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("✅ Network security monitor started\n")
	fmt.Printf("📊 Monitoring network interfaces, VPN, DNS, and captive portals...\n\n")

	// Handle graceful shutdown
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)

	// Monitor event stream
	go func() {
		for event := range mon.GetEventStream() {
			displayMonitoringEvent(event)
		}
	}()

	// Wait for shutdown signal
	<-c
	fmt.Printf("\n🛑 Shutting down monitor...\n")

	if err := mon.Stop(); err != nil {
		fmt.Printf("❌ Error stopping monitor: %v\n", err)
	}

	fmt.Printf("✅ Monitor stopped\n")
	return nil
}

func displayMonitoringStatus(monitor *monitor.Monitor) {
	status := monitor.GetStatus()

	fmt.Printf("📊 Network Monitoring Status\n")
	fmt.Printf("============================\n")
	fmt.Printf("Overall Status: %s\n", status.OverallStatus.String())
	fmt.Printf("Network: %s\n", status.NetworkStatus.Status.String())
	fmt.Printf("VPN: %s\n", status.VPNStatus.Status.String())
	fmt.Printf("DNS: %s\n", status.DNSStatus.Status.String())
	fmt.Printf("Last Updated: %v\n", status.Timestamp.Format("2006-01-02 15:04:05"))
	fmt.Printf("Active Alerts: %d\n", len(status.ActiveAlerts))
	fmt.Printf("Security Score: %.1f\n", status.SecurityMetrics.SecurityScore)
	fmt.Println()
}

func displayMonitoringEvent(event *monitor.MonitorEvent) {
	timestamp := event.Timestamp.Format("15:04:05")

	switch event.Type {
	case monitor.EventNetworkChange:
		fmt.Printf("[%s] 🔄 NETWORK CHANGE: %s\n", timestamp, event.Message)
	case monitor.EventVPNConnected:
		fmt.Printf("[%s] ✅ VPN CONNECTED: %s\n", timestamp, event.Message)
	case monitor.EventVPNDisconnected:
		fmt.Printf("[%s] ❌ VPN DISCONNECTED: %s\n", timestamp, event.Message)
	case monitor.EventCaptivePortalDetected:
		fmt.Printf("[%s] � CAPTIVE PORTAL: %s\n", timestamp, event.Message)
	case monitor.EventSecurityThreat:
		fmt.Printf("[%s] � SECURITY THREAT: %s\n", timestamp, event.Message)
	case monitor.EventPerformanceIssue:
		fmt.Printf("[%s] ⚠️  PERFORMANCE ISSUE: %s\n", timestamp, event.Message)
	case monitor.EventSystemStartup:
		fmt.Printf("[%s] � SYSTEM STARTUP: %s\n", timestamp, event.Message)
	case monitor.EventSystemShutdown:
		fmt.Printf("[%s] � SYSTEM SHUTDOWN: %s\n", timestamp, event.Message)
	case monitor.EventAlert:
		fmt.Printf("[%s] 🔔 ALERT: %s\n", timestamp, event.Message)
	default:
		fmt.Printf("[%s] ℹ️  %s\n", timestamp, event.Message)
	}

	// Display additional details if available
	if len(event.Details) > 0 {
		for key, value := range event.Details {
			fmt.Printf("      %s: %v\n", key, value)
		}
	}
}
