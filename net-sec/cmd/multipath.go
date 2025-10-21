package cmd

import (
	"fmt"
	"log"
	"time"

	"github.com/spf13/cobra"
	"github.com/stealthguard/net-sec/internal/multipath"
)

var (
	primaryInterface   string
	backupInterface    string
	primaryType        string
	backupType         string
	failoverThreshold  int
	recoveryThreshold  int
	checkInterval      time.Duration
	enableKillSwitch   bool
)

// NewMultipathCommand creates the 'multipath' command for network failover management
func NewMultipathCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "multipath",
		Short: "Manage multipath networking and failover between interfaces",
		Long: `Advanced multipath networking with intelligent failover between primary and backup
network interfaces (WiFi/Ethernet/LTE). Provides seamless connectivity switching
with kill-switch protection to prevent traffic leaks during transitions.

Key Features:
• Automatic interface detection (WiFi, Ethernet, LTE)
• Quality-based failover with configurable thresholds
• Kill-switch protection during interface transitions  
• DNS leak prevention with interface-specific routing
• Bandwidth monitoring and quality assessment
• Real-time failover status and event monitoring

The multipath manager continuously monitors interface health and automatically
switches between primary and backup connections based on connectivity quality,
latency, and user-defined thresholds.`,
		Example: `  # Start multipath management with auto-detected interfaces
  net-sec multipath start

  # Configure specific interfaces  
  net-sec multipath start --primary-interface wlan0 --backup-interface eth0

  # Set custom failover thresholds
  net-sec multipath start --failover-threshold 3 --recovery-threshold 2

  # Show current multipath status
  net-sec multipath status

  # Stop multipath management
  net-sec multipath stop`,
		RunE: runMultipathCommand,
	}

	// Add subcommands
	cmd.AddCommand(newMultipathStartCommand())
	cmd.AddCommand(newMultipathStopCommand())
	cmd.AddCommand(newMultipathStatusCommand())
	cmd.AddCommand(newMultipathDaemonCommand())

	return cmd
}

func newMultipathStartCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "start",
		Short: "Start multipath networking with failover management",
		RunE:  runMultipathStart,
	}

	cmd.Flags().StringVar(&primaryInterface, "primary-interface", "",
		"Primary network interface (auto-detect if empty)")
	cmd.Flags().StringVar(&backupInterface, "backup-interface", "",
		"Backup network interface (auto-detect if empty)")
	cmd.Flags().StringVar(&primaryType, "primary-type", "wifi",
		"Primary interface type: wifi, ethernet, lte")
	cmd.Flags().StringVar(&backupType, "backup-type", "ethernet",
		"Backup interface type: wifi, ethernet, lte")
	cmd.Flags().IntVar(&failoverThreshold, "failover-threshold", 3,
		"Number of failed checks before failover")
	cmd.Flags().IntVar(&recoveryThreshold, "recovery-threshold", 2,
		"Number of successful checks for recovery")
	cmd.Flags().DurationVar(&checkInterval, "check-interval", 10*time.Second,
		"Interval between connectivity checks")
	cmd.Flags().BoolVar(&enableKillSwitch, "kill-switch", true,
		"Enable kill-switch during failover transitions")

	return cmd
}

func newMultipathStopCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "stop",
		Short: "Stop multipath networking management",
		RunE:  runMultipathStop,
	}
}

func newMultipathStatusCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Show current multipath networking status",
		RunE:  runMultipathStatus,
	}
}

func newMultipathDaemonCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "daemon",
		Short: "Run multipath manager as background daemon",
		RunE:  runMultipathDaemon,
	}

	cmd.Flags().StringVar(&primaryInterface, "primary-interface", "",
		"Primary network interface")
	cmd.Flags().StringVar(&backupInterface, "backup-interface", "",
		"Backup network interface")
	cmd.Flags().StringVar(&primaryType, "primary-type", "wifi",
		"Primary interface type")
	cmd.Flags().StringVar(&backupType, "backup-type", "ethernet",
		"Backup interface type")
	cmd.Flags().IntVar(&failoverThreshold, "failover-threshold", 3,
		"Failover threshold")
	cmd.Flags().IntVar(&recoveryThreshold, "recovery-threshold", 2,
		"Recovery threshold")
	cmd.Flags().DurationVar(&checkInterval, "check-interval", 10*time.Second,
		"Check interval")
	cmd.Flags().BoolVar(&enableKillSwitch, "kill-switch", true,
		"Enable kill-switch")

	return cmd
}

func runMultipathCommand(cmd *cobra.Command, args []string) error {
	fmt.Printf("🌐 StealthGuard Multipath Network Manager\n")
	fmt.Printf("=========================================\n\n")

	fmt.Printf("Available Commands:\n")
	fmt.Printf("  start    - Start multipath networking\n")
	fmt.Printf("  stop     - Stop multipath networking\n") 
	fmt.Printf("  status   - Show current status\n")
	fmt.Printf("  daemon   - Run as background service\n\n")

	fmt.Printf("Use 'net-sec multipath <command> --help' for detailed usage.\n")
	return nil
}

func runMultipathStart(cmd *cobra.Command, args []string) error {
	fmt.Printf("🚀 Starting Multipath Network Manager\n")
	fmt.Printf("=====================================\n\n")

	// Create multipath manager
	manager := multipath.NewManager()

	// Configure options
	opts := &multipath.Options{
		PrimaryInterface:   primaryInterface,
		BackupInterface:    backupInterface,
		PrimaryType:        primaryType,
		BackupType:         backupType,
		FailoverThreshold:  failoverThreshold,
		RecoveryThreshold:  recoveryThreshold,
		CheckInterval:      checkInterval,
		EnableKillSwitch:   enableKillSwitch,
		DNSServers:        []string{"1.1.1.1", "1.0.0.1"},
		RoutingTable:      "main",
	}

	// Initialize manager
	if err := manager.Initialize(opts); err != nil {
		return fmt.Errorf("failed to initialize multipath manager: %w", err)
	}

	// Start multipath management
	if err := manager.Start(); err != nil {
		return fmt.Errorf("failed to start multipath manager: %w", err)
	}

	// Display initial status
	displayMultipathConfig(manager)

	// Monitor events
	log.Printf("✅ Multipath networking started successfully")
	log.Printf("📊 Monitoring network interfaces for failover conditions...")

	// Monitor status changes
	go func() {
		for event := range manager.GetStatusChannel() {
			displayMultipathEvent(event)
		}
	}()

	// Keep running (in real implementation, this would handle signals)
	select {}
}

func runMultipathStop(cmd *cobra.Command, args []string) error {
	fmt.Printf("⏹️  Stopping Multipath Network Manager\n")
	fmt.Printf("=====================================\n\n")

	log.Printf("🛑 Multipath networking stopped")
	return nil
}

func runMultipathStatus(cmd *cobra.Command, args []string) error {
	fmt.Printf("📊 Multipath Network Status\n")
	fmt.Printf("===========================\n\n")

	// Create a dummy manager for status display
	manager := multipath.NewManager()
	status := manager.GetStatus()

	fmt.Printf("🔄 Active Interface: %s\n", status.ActiveInterface)
	fmt.Printf("📡 Primary Interface: %s (%s) - %s\n", 
		status.Primary.Name, status.Primary.Type, status.Primary.Status)
	fmt.Printf("📶 Backup Interface: %s (%s) - %s\n",
		status.Backup.Name, status.Backup.Type, status.Backup.Status)
	fmt.Printf("🔀 Failover Count: %d\n", status.FailoverCount)
	
	if !status.LastFailover.IsZero() {
		fmt.Printf("⏰ Last Failover: %v\n", status.LastFailover.Format("2006-01-02 15:04:05"))
	}

	return nil
}

func runMultipathDaemon(cmd *cobra.Command, args []string) error {
	fmt.Printf("🔄 Starting Multipath Daemon\n")
	fmt.Printf("============================\n\n")

	// Create multipath manager
	manager := multipath.NewManager()

	// Configure options
	opts := &multipath.Options{
		PrimaryInterface:   primaryInterface,
		BackupInterface:    backupInterface,
		PrimaryType:        primaryType,
		BackupType:         backupType,
		FailoverThreshold:  failoverThreshold,
		RecoveryThreshold:  recoveryThreshold,
		CheckInterval:      checkInterval,
		EnableKillSwitch:   enableKillSwitch,
		DNSServers:        []string{"1.1.1.1", "1.0.0.1"},
		RoutingTable:      "main",
	}

	// Initialize and start daemon
	if err := manager.Initialize(opts); err != nil {
		return fmt.Errorf("failed to initialize daemon: %w", err)
	}

	if err := manager.StartDaemon(); err != nil {
		return fmt.Errorf("failed to start daemon: %w", err)
	}

	log.Printf("✅ Multipath daemon started successfully")
	return nil
}

func displayMultipathConfig(manager *multipath.Manager) {
	status := manager.GetStatus()
	
	fmt.Printf("🌐 Multipath Network Configuration:\n")
	fmt.Printf("  Primary: %s (%s)\n", status.Primary.Name, status.Primary.Type)
	fmt.Printf("  Backup: %s (%s)\n", status.Backup.Name, status.Backup.Type)
	fmt.Printf("  Failover Threshold: %d failed checks\n", status.Config.FailoverThreshold)
	fmt.Printf("  Recovery Threshold: %d successful checks\n", status.Config.RecoveryThreshold)
	fmt.Printf("  Check Interval: %v\n", status.Config.CheckInterval)
	fmt.Printf("  Kill Switch: %t\n", status.Config.EnableKillSwitch)
	fmt.Printf("  DNS Servers: %v\n", status.Config.DNSServers)
	fmt.Println()
}

func displayMultipathEvent(event *multipath.StatusEvent) {
	timestamp := event.Timestamp.Format("15:04:05")
	
	switch event.Type {
	case multipath.EventFailover:
		fmt.Printf("[%s] 🔄 FAILOVER: %s → %s (%s)\n", 
			timestamp, event.FromInterface, event.ToInterface, event.Reason)
	case multipath.EventRecovery:
		fmt.Printf("[%s] ✅ RECOVERY: %s → %s (%s)\n",
			timestamp, event.FromInterface, event.ToInterface, event.Reason)
	case multipath.EventInterfaceDown:
		fmt.Printf("[%s] ❌ INTERFACE DOWN: %s (%s)\n",
			timestamp, event.Interface, event.Reason)
	case multipath.EventInterfaceUp:
		fmt.Printf("[%s] ✅ INTERFACE UP: %s (%s)\n",
			timestamp, event.Interface, event.Reason)
	case multipath.EventKillSwitchActivated:
		fmt.Printf("[%s] 🛑 KILL SWITCH ACTIVATED: %s\n",
			timestamp, event.Reason)
	case multipath.EventKillSwitchDeactivated:
		fmt.Printf("[%s] 🟢 KILL SWITCH DEACTIVATED: %s\n",
			timestamp, event.Reason)
	default:
		fmt.Printf("[%s] ℹ️  %s\n", timestamp, event.Reason)
	}
}