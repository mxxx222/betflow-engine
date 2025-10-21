package cmd

import (
	"fmt"
	"log"
	"time"

	"github.com/spf13/cobra"
	"github.com/stealthguard/net-sec/internal/captive"
)

var (
	testURL         string
	expectedStatus  int
	timeout         time.Duration
	retries         int
	interval        time.Duration
	userAgent       string
	followRedirects bool
	checkDNS        bool
)

// NewDetectCommand creates the 'detect' command for captive portal detection
func NewDetectCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "detect",
		Short: "Detect captive portals using HTTP 204 logic",
		Long: `Detect captive portals by testing connectivity with HTTP 204 status code logic.
Uses the same methodology as major operating systems and browsers to identify
when network access is restricted by captive portals.

Detection Methods:
• HTTP 204 No Content response validation
• DNS resolution testing and hijacking detection  
• Redirect analysis and portal page identification
• SSL/TLS certificate validation bypass detection
• Network connectivity and latency analysis
• Multiple test endpoint validation`,
		Example: `  # Basic captive portal detection
  net-sec detect

  # Custom test endpoint with specific status
  net-sec detect --url http://detectportal.firefox.com/canonical.html --status 200

  # Comprehensive testing with DNS validation
  net-sec detect --check-dns --retries 5 --timeout 10s

  # Monitor for captive portal changes
  net-sec detect --interval 30s --retries 0`,
		RunE: runDetectCommand,
	}

	// Detection flags
	cmd.Flags().StringVar(&testURL, "url", "http://clients3.google.com/generate_204", "Test URL for captive portal detection")
	cmd.Flags().IntVar(&expectedStatus, "status", 204, "Expected HTTP status code")
	cmd.Flags().DurationVar(&timeout, "timeout", 10*time.Second, "Request timeout")
	cmd.Flags().IntVar(&retries, "retries", 3, "Number of retry attempts (0 for continuous)")
	cmd.Flags().DurationVar(&interval, "interval", 5*time.Second, "Interval between tests")
	cmd.Flags().StringVar(&userAgent, "user-agent", "Mozilla/5.0 (compatible; net-sec/1.0)", "HTTP User-Agent header")
	cmd.Flags().BoolVar(&followRedirects, "follow-redirects", false, "Follow HTTP redirects")
	cmd.Flags().BoolVar(&checkDNS, "check-dns", true, "Validate DNS resolution")

	return cmd
}

func runDetectCommand(cmd *cobra.Command, args []string) error {
	log.Printf("Starting captive portal detection...")

	// Create captive portal detector
	detector := captive.NewDetector()

	// Configure detection options
	opts := &captive.DetectorOptions{
		TestURL:         testURL,
		ExpectedStatus:  expectedStatus,
		Timeout:         timeout,
		UserAgent:       userAgent,
		FollowRedirects: followRedirects,
		CheckDNS:        checkDNS,
	}

	// Run detection based on retry configuration
	if retries == 0 {
		// Continuous monitoring mode
		log.Printf("🔄 Starting continuous captive portal monitoring (interval: %v)", interval)
		return runContinuousDetection(detector, opts, interval)
	} else {
		// Single detection with retries
		return runSingleDetection(detector, opts, retries, interval)
	}
}

func runSingleDetection(detector *captive.Detector, opts *captive.DetectorOptions, retries int, interval time.Duration) error {
	for attempt := 1; attempt <= retries; attempt++ {
		log.Printf("🔍 Detection attempt %d/%d", attempt, retries)

		result, err := detector.Detect(opts)
		if err != nil {
			log.Printf("❌ Detection failed: %v", err)
			if attempt < retries {
				log.Printf("⏳ Waiting %v before retry...", interval)
				time.Sleep(interval)
				continue
			}
			return fmt.Errorf("all detection attempts failed: %w", err)
		}

		// Display results
		displayDetectionResult(result)

		// Success - no need to retry
		return nil
	}

	return nil
}

func runContinuousDetection(detector *captive.Detector, opts *captive.DetectorOptions, interval time.Duration) error {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	// Run initial detection
	result, err := detector.Detect(opts)
	if err != nil {
		log.Printf("❌ Initial detection failed: %v", err)
	} else {
		displayDetectionResult(result)
	}

	// Continuous monitoring
	for {
		select {
		case <-ticker.C:
			result, err := detector.Detect(opts)
			if err != nil {
				log.Printf("❌ Detection failed: %v", err)
				continue
			}

			// Only display if status changed or verbose mode
			if verbose || result.StatusChanged {
				displayDetectionResult(result)
			}
		}
	}
}

func displayDetectionResult(result *captive.DetectionResult) {
	// Display main status
	if result.CaptivePortalDetected {
		fmt.Printf("🚫 CAPTIVE PORTAL DETECTED\n")
	} else {
		fmt.Printf("✅ NO CAPTIVE PORTAL - Internet access available\n")
	}

	// Display detailed information
	fmt.Printf("📊 Detection Details:\n")
	fmt.Printf("  Test URL: %s\n", result.TestURL)
	fmt.Printf("  HTTP Status: %d (expected: %d)\n", result.HTTPStatus, result.ExpectedStatus)
	fmt.Printf("  Response Time: %v\n", result.ResponseTime)
	fmt.Printf("  Content Length: %d bytes\n", result.ContentLength)

	if result.RedirectURL != "" {
		fmt.Printf("  Redirect URL: %s\n", result.RedirectURL)
	}

	if result.DNSResolution != nil {
		fmt.Printf("  DNS Resolution: %s → %v\n", result.TestURL, result.DNSResolution.IPs)
		if result.DNSResolution.Hijacked {
			fmt.Printf("  ⚠️  DNS Hijacking Detected\n")
		}
	}

	// Portal information if detected
	if result.CaptivePortalDetected && result.PortalInfo != nil {
		fmt.Printf("🌐 Portal Information:\n")
		fmt.Printf("  Portal URL: %s\n", result.PortalInfo.URL)
		fmt.Printf("  Portal Title: %s\n", result.PortalInfo.Title)
		if result.PortalInfo.LoginRequired {
			fmt.Printf("  Authentication: Login required\n")
		}
	}

	// Network recommendations
	if result.CaptivePortalDetected {
		fmt.Printf("💡 Recommendations:\n")
		fmt.Printf("  • Open browser and navigate to any HTTP website\n")
		fmt.Printf("  • Complete captive portal authentication\n")
		fmt.Printf("  • Consider using cellular data as backup\n")
		if result.PortalInfo != nil && result.PortalInfo.URL != "" {
			fmt.Printf("  • Direct portal URL: %s\n", result.PortalInfo.URL)
		}
	}

	fmt.Println()
}
