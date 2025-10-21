package captive

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
)

// Detector handles captive portal detection
type Detector struct {
	client    *http.Client
	dnsClient *net.Resolver
}

// DetectorOptions contains detection configuration options
type DetectorOptions struct {
	TestURL         string
	ExpectedStatus  int
	Timeout         time.Duration
	UserAgent       string
	FollowRedirects bool
	CheckDNS        bool
}

// DetectionResult contains the results of captive portal detection
type DetectionResult struct {
	CaptivePortalDetected bool          `json:"captive_portal_detected"`
	TestURL               string        `json:"test_url"`
	HTTPStatus            int           `json:"http_status"`
	ExpectedStatus        int           `json:"expected_status"`
	ResponseTime          time.Duration `json:"response_time"`
	ContentLength         int64         `json:"content_length"`
	RedirectURL           string        `json:"redirect_url,omitempty"`
	DNSResolution         *DNSResult    `json:"dns_resolution,omitempty"`
	PortalInfo            *PortalInfo   `json:"portal_info,omitempty"`
	StatusChanged         bool          `json:"status_changed"`
	Error                 string        `json:"error,omitempty"`
}

// DNSResult contains DNS resolution information
type DNSResult struct {
	IPs      []string      `json:"ips"`
	Hijacked bool          `json:"hijacked"`
	Duration time.Duration `json:"duration"`
}

// PortalInfo contains information about detected captive portal
type PortalInfo struct {
	URL           string `json:"url"`
	Title         string `json:"title"`
	LoginRequired bool   `json:"login_required"`
	Provider      string `json:"provider,omitempty"`
}

// NewDetector creates a new captive portal detector
func NewDetector() *Detector {
	// Create HTTP client with custom transport
	transport := &http.Transport{
		Dial: (&net.Dialer{
			Timeout:   5 * time.Second,
			KeepAlive: 0, // Disable keep-alive for testing
		}).Dial,
		TLSHandshakeTimeout:   5 * time.Second,
		ResponseHeaderTimeout: 10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
		DisableKeepAlives:     true,
		DisableCompression:    true,
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   10 * time.Second,
	}

	// Create DNS resolver
	dnsClient := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{
				Timeout: 2 * time.Second,
			}
			return d.DialContext(ctx, network, address)
		},
	}

	return &Detector{
		client:    client,
		dnsClient: dnsClient,
	}
}

// Detect performs captive portal detection
func (d *Detector) Detect(opts *DetectorOptions) (*DetectionResult, error) {
	result := &DetectionResult{
		TestURL:        opts.TestURL,
		ExpectedStatus: opts.ExpectedStatus,
	}

	// Configure HTTP client
	d.client.Timeout = opts.Timeout

	// Configure redirect policy
	if !opts.FollowRedirects {
		d.client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			// Store redirect URL but don't follow
			result.RedirectURL = req.URL.String()
			return http.ErrUseLastResponse
		}
	} else {
		d.client.CheckRedirect = nil
	}

	// Perform DNS check if requested
	if opts.CheckDNS {
		dnsResult, err := d.checkDNS(opts.TestURL)
		if err == nil {
			result.DNSResolution = dnsResult
		}
	}

	// Perform HTTP test
	start := time.Now()
	resp, err := d.performHTTPTest(opts)
	result.ResponseTime = time.Since(start)

	if err != nil {
		result.Error = err.Error()
		result.CaptivePortalDetected = true // Assume captive portal if request fails
		return result, nil
	}
	defer resp.Body.Close()

	// Analyze response
	result.HTTPStatus = resp.StatusCode
	result.ContentLength = resp.ContentLength

	// Check if status matches expected
	if resp.StatusCode == opts.ExpectedStatus {
		result.CaptivePortalDetected = false
	} else {
		result.CaptivePortalDetected = true

		// Try to get portal information
		if portalInfo := d.extractPortalInfo(resp); portalInfo != nil {
			result.PortalInfo = portalInfo
		}
	}

	// Additional heuristics for captive portal detection
	if !result.CaptivePortalDetected {
		// Check for common captive portal indicators
		if d.hasPortalIndicators(resp) {
			result.CaptivePortalDetected = true
		}
	}

	return result, nil
}

// performHTTPTest performs the actual HTTP test
func (d *Detector) performHTTPTest(opts *DetectorOptions) (*http.Response, error) {
	// Create request
	req, err := http.NewRequest("GET", opts.TestURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("User-Agent", opts.UserAgent)
	req.Header.Set("Cache-Control", "no-cache")
	req.Header.Set("Pragma", "no-cache")

	// Perform request
	return d.client.Do(req)
}

// checkDNS performs DNS resolution check
func (d *Detector) checkDNS(testURL string) (*DNSResult, error) {
	// Parse URL to get hostname
	u, err := url.Parse(testURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse URL: %w", err)
	}

	host := u.Hostname()
	if host == "" {
		return nil, fmt.Errorf("no hostname in URL")
	}

	// Resolve DNS
	start := time.Now()
	ips, err := d.dnsClient.LookupIPAddr(context.Background(), host)
	duration := time.Since(start)

	if err != nil {
		return nil, fmt.Errorf("DNS resolution failed: %w", err)
	}

	// Convert IPs to strings
	var ipStrings []string
	for _, ip := range ips {
		ipStrings = append(ipStrings, ip.IP.String())
	}

	// Check for DNS hijacking (simple heuristic)
	hijacked := d.isDNSHijacked(host, ipStrings)

	return &DNSResult{
		IPs:      ipStrings,
		Hijacked: hijacked,
		Duration: duration,
	}, nil
}

// isDNSHijacked checks if DNS appears to be hijacked
func (d *Detector) isDNSHijacked(hostname string, ips []string) bool {
	// Known good IPs for common test endpoints
	knownGoodIPs := map[string][]string{
		"clients3.google.com": {
			"142.250.191.14", "172.217.164.14", "216.58.194.14",
		},
		"detectportal.firefox.com": {
			"34.117.118.64", "35.186.224.25",
		},
		"www.msftconnecttest.com": {
			"13.107.4.52", "204.79.197.200",
		},
	}

	if goodIPs, exists := knownGoodIPs[hostname]; exists {
		// Check if any returned IP matches known good IPs
		for _, returnedIP := range ips {
			for _, goodIP := range goodIPs {
				if returnedIP == goodIP {
					return false // Not hijacked
				}
			}
		}

		// If none match, likely hijacked
		return true
	}

	// For unknown hostnames, check for obvious hijacking
	for _, ip := range ips {
		// Check for common captive portal IP ranges
		if d.isLikelyPortalIP(ip) {
			return true
		}
	}

	return false
}

// isLikelyPortalIP checks if an IP is likely from a captive portal
func (d *Detector) isLikelyPortalIP(ip string) bool {
	parsedIP := net.ParseIP(ip)
	if parsedIP == nil {
		return false
	}

	// Common captive portal IP ranges
	portalRanges := []string{
		"192.168.1.1/32", // Common router IP
		"10.0.0.1/32",    // Common router IP
		"172.16.0.1/32",  // Common router IP
		"192.168.0.1/32", // Common router IP
		"1.1.1.1/32",     // Sometimes used by portals
	}

	for _, cidr := range portalRanges {
		_, network, err := net.ParseCIDR(cidr)
		if err != nil {
			continue
		}
		if network.Contains(parsedIP) {
			return true
		}
	}

	return false
}

// extractPortalInfo extracts information about the captive portal
func (d *Detector) extractPortalInfo(resp *http.Response) *PortalInfo {
	// Only extract info from HTML responses
	contentType := resp.Header.Get("Content-Type")
	if !strings.Contains(strings.ToLower(contentType), "text/html") {
		return nil
	}

	// Read response body (limit to 64KB)
	body, err := io.ReadAll(io.LimitReader(resp.Body, 64*1024))
	if err != nil {
		return nil
	}

	bodyStr := string(body)

	portalInfo := &PortalInfo{
		URL: resp.Request.URL.String(),
	}

	// Extract title
	titleRe := regexp.MustCompile(`(?i)<title[^>]*>(.*?)</title>`)
	if matches := titleRe.FindStringSubmatch(bodyStr); len(matches) > 1 {
		portalInfo.Title = strings.TrimSpace(matches[1])
	}

	// Check for login requirements
	loginIndicators := []string{
		"login", "sign in", "authenticate", "username", "password",
		"credentials", "access code", "authorization",
	}

	bodyLower := strings.ToLower(bodyStr)
	for _, indicator := range loginIndicators {
		if strings.Contains(bodyLower, indicator) {
			portalInfo.LoginRequired = true
			break
		}
	}

	// Try to identify provider
	if strings.Contains(bodyLower, "starbucks") {
		portalInfo.Provider = "Starbucks"
	} else if strings.Contains(bodyLower, "mcdonalds") {
		portalInfo.Provider = "McDonald's"
	} else if strings.Contains(bodyLower, "airport") {
		portalInfo.Provider = "Airport WiFi"
	} else if strings.Contains(bodyLower, "hotel") {
		portalInfo.Provider = "Hotel WiFi"
	}

	return portalInfo
}

// hasPortalIndicators checks for additional captive portal indicators
func (d *Detector) hasPortalIndicators(resp *http.Response) bool {
	// Check headers for portal indicators
	headers := []string{
		"Location", "Refresh", "X-Portal-URL", "X-Captive-Portal",
	}

	for _, header := range headers {
		if resp.Header.Get(header) != "" {
			return true
		}
	}

	// Check for redirect to known portal URLs
	location := resp.Header.Get("Location")
	if location != "" {
		portalIndicators := []string{
			"portal", "captive", "login", "auth", "access",
			"wifi", "hotspot", "gateway",
		}

		locationLower := strings.ToLower(location)
		for _, indicator := range portalIndicators {
			if strings.Contains(locationLower, indicator) {
				return true
			}
		}
	}

	return false
}
