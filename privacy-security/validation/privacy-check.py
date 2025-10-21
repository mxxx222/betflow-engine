#!/usr/bin/env python3
"""
Privacy Configuration Validation Script
Validates browser privacy settings and network configuration
Version: 1.0.0 - Production Ready
"""

import json
import platform
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class PrivacyValidator:
    def __init__(self):
        self.results = {
            'proxy': {'status': 'unknown', 'details': []},
            'dns': {'status': 'unknown', 'details': []},
            'browser_firefox': {'status': 'unknown', 'details': []},
            'browser_chrome': {'status': 'unknown', 'details': []},
            'network': {'status': 'unknown', 'details': []},
            'webrtc': {'status': 'unknown', 'details': []},
            'timezone': {'status': 'unknown', 'details': []},
            'language': {'status': 'unknown', 'details': []},
            'user_agent': {'status': 'unknown', 'details': []}
        }
        self.session = requests.Session()
        self.session.timeout = 10

    def print_header(self, text):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

    def print_status(self, check_name, status, details=""):
        if status == 'pass':
            icon = f"{Colors.GREEN}✓{Colors.END}"
            color = Colors.GREEN
        elif status == 'warning':
            icon = f"{Colors.YELLOW}⚠{Colors.END}"
            color = Colors.YELLOW
        elif status == 'fail':
            icon = f"{Colors.RED}✗{Colors.END}"
            color = Colors.RED
        else:
            icon = f"{Colors.MAGENTA}?{Colors.END}"
            color = Colors.MAGENTA

        print(f"{icon} {color}{check_name:<30}{Colors.END} {details}")

    def validate_proxy_connectivity(self):
        """Test proxy PAC file accessibility"""
        self.print_header("PROXY CONNECTIVITY TEST")
        
        proxy_urls = [
            "http://proxy.local/proxy.pac",
            "https://proxy.local/proxy.pac",
            "http://corporate.proxy/proxy.pac"
        ]
        
        proxy_accessible = False
        working_url = None
        
        for url in proxy_urls:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200 and "FindProxyForURL" in response.text:
                    proxy_accessible = True
                    working_url = url
                    self.print_status("Proxy PAC accessible", "pass", working_url)
                    self.results['proxy']['status'] = 'pass'
                    self.results['proxy']['details'].append(f"PAC file accessible at {url}")
                    break
            except Exception as e:
                continue
        
        if not proxy_accessible:
            self.print_status("Proxy PAC accessible", "fail", "No PAC file found")
            self.results['proxy']['status'] = 'fail'
            self.results['proxy']['details'].append("PAC file not accessible")

    def validate_dns_over_https(self):
        """Validate DNS over HTTPS configuration"""
        self.print_header("DNS OVER HTTPS VALIDATION")
        
        # Test DNS resolution timing (DoH should be slower than regular DNS)
        try:
            # Test Quad9 DoH endpoint
            doh_test_url = "https://dns.quad9.net/dns-query"
            response = self.session.get(doh_test_url, timeout=5)
            
            if response.status_code == 200:
                self.print_status("Quad9 DoH endpoint", "pass", "Accessible")
                self.results['dns']['status'] = 'pass'
                self.results['dns']['details'].append("Quad9 DoH endpoint accessible")
            else:
                self.print_status("Quad9 DoH endpoint", "warning", f"HTTP {response.status_code}")
                self.results['dns']['status'] = 'warning'
                
        except Exception as e:
            self.print_status("Quad9 DoH endpoint", "fail", str(e))
            self.results['dns']['status'] = 'fail'
            self.results['dns']['details'].append(f"DoH endpoint error: {e}")

        # Check system DNS configuration
        if platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(['scutil', '--dns'], capture_output=True, text=True)
                if "dns.quad9.net" in result.stdout:
                    self.print_status("System DNS config", "pass", "Quad9 configured")
                else:
                    self.print_status("System DNS config", "warning", "Quad9 not in system DNS")
            except:
                self.print_status("System DNS config", "unknown", "Could not check")

    def validate_browser_headers(self):
        """Test browser header normalization"""
        self.print_header("BROWSER HEADER VALIDATION")
        
        test_urls = [
            "https://httpbin.org/headers",
            "https://www.deviceinfo.me/json"  # Alternative if httpbin is blocked
        ]
        
        for url in test_urls:
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract headers
                    headers = data.get('headers', {})
                    user_agent = headers.get('User-Agent', '')
                    accept_language = headers.get('Accept-Language', '')
                    
                    # Validate User-Agent
                    if 'Mozilla/5.0' in user_agent:
                        if len(user_agent) < 150:  # Reduced UA should be shorter
                            self.print_status("User-Agent reduced", "pass", f"Length: {len(user_agent)}")
                            self.results['user_agent']['status'] = 'pass'
                        else:
                            self.print_status("User-Agent reduced", "warning", f"Length: {len(user_agent)} (may not be reduced)")
                            self.results['user_agent']['status'] = 'warning'
                    else:
                        self.print_status("User-Agent format", "fail", "Invalid UA format")
                        self.results['user_agent']['status'] = 'fail'
                    
                    # Validate Accept-Language
                    if 'en-US' in accept_language and accept_language.startswith('en-US'):
                        self.print_status("Accept-Language", "pass", accept_language)
                        self.results['language']['status'] = 'pass'
                    else:
                        self.print_status("Accept-Language", "warning", accept_language)
                        self.results['language']['status'] = 'warning'
                    
                    break
                    
            except Exception as e:
                continue
        
        if self.results['user_agent']['status'] == 'unknown':
            self.print_status("Header validation", "fail", "Could not test headers")

    def validate_webrtc_leaks(self):
        """Simulate WebRTC leak detection"""
        self.print_header("WEBRTC LEAK SIMULATION")
        
        # Since we can't directly test WebRTC from Python, we provide guidance
        webrtc_test_sites = [
            "https://browserleaks.com/webrtc",
            "https://ipleak.net/",
            "https://whatismyipaddress.com/webrtc-leak"
        ]
        
        self.print_status("WebRTC test sites", "pass", "Manual testing required")
        print(f"{Colors.YELLOW}Manual WebRTC testing required at:{Colors.END}")
        for site in webrtc_test_sites:
            print(f"  • {site}")
        
        print(f"\n{Colors.CYAN}Expected results:{Colors.END}")
        print(f"  • No local IP addresses revealed")
        print(f"  • Only proxy IP should be visible")
        print(f"  • UDP connections should be blocked")
        
        self.results['webrtc']['status'] = 'manual'
        self.results['webrtc']['details'].append("Manual testing required")

    def validate_timezone_spoofing(self):
        """Check timezone handling"""
        self.print_header("TIMEZONE VALIDATION")
        
        # Check system timezone
        try:
            import datetime
            local_tz = datetime.datetime.now().astimezone().tzinfo
            utc_offset = local_tz.utcoffset(None)
            
            if utc_offset.total_seconds() == 0:
                self.print_status("System timezone", "pass", "UTC")
                self.results['timezone']['status'] = 'pass'
            else:
                hours_offset = utc_offset.total_seconds() / 3600
                self.print_status("System timezone", "warning", f"UTC{hours_offset:+.0f}")
                self.results['timezone']['status'] = 'warning'
                self.results['timezone']['details'].append(f"System TZ is not UTC (offset: {hours_offset:+.0f}h)")
            
            # Firefox RFP should force UTC regardless of system timezone
            print(f"\n{Colors.CYAN}Note: Firefox with ResistFingerprinting should report UTC regardless of system timezone{Colors.END}")
            
        except Exception as e:
            self.print_status("Timezone check", "unknown", str(e))
            self.results['timezone']['status'] = 'unknown'

    def validate_network_fingerprinting(self):
        """Check for network-based fingerprinting resistance"""
        self.print_header("NETWORK FINGERPRINTING")
        
        try:
            # Test external IP consistency
            ip_services = [
                "https://httpbin.org/ip",
                "https://api.ipify.org?format=json"
            ]
            
            ips = []
            for service in ip_services:
                try:
                    response = self.session.get(service, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        ip = data.get('origin', data.get('ip', 'unknown')).split(',')[0].strip()
                        ips.append(ip)
                except:
                    continue
            
            if len(set(ips)) == 1 and len(ips) > 1:
                self.print_status("IP consistency", "pass", f"All services show: {ips[0]}")
                self.results['network']['status'] = 'pass'
            elif len(ips) == 0:
                self.print_status("IP detection", "fail", "Could not determine external IP")
                self.results['network']['status'] = 'fail'
            else:
                self.print_status("IP consistency", "warning", f"Multiple IPs detected: {set(ips)}")
                self.results['network']['status'] = 'warning'
                
        except Exception as e:
            self.print_status("Network fingerprinting", "unknown", str(e))
            self.results['network']['status'] = 'unknown'

    def check_firefox_policies(self):
        """Check Firefox policy file existence and validity"""
        self.print_header("FIREFOX POLICY VALIDATION")
        
        system = platform.system()
        policy_paths = []
        
        if system == "Darwin":  # macOS
            policy_paths = [
                "/Applications/Firefox.app/Contents/Resources/distribution/policies.json",
                "/usr/local/firefox/distribution/policies.json"
            ]
        elif system == "Windows":
            policy_paths = [
                "C:\\Program Files\\Mozilla Firefox\\distribution\\policies.json",
                "C:\\Program Files (x86)\\Mozilla Firefox\\distribution\\policies.json"
            ]
        elif system == "Linux":
            policy_paths = [
                "/usr/lib/firefox/distribution/policies.json",
                "/opt/firefox/distribution/policies.json",
                "/usr/local/firefox/distribution/policies.json"
            ]
        
        policy_found = False
        for path in policy_paths:
            try:
                with open(path, 'r') as f:
                    policies = json.load(f)
                    
                policy_found = True
                self.print_status("Firefox policies file", "pass", path)
                
                # Validate key policies
                prefs = policies.get('policies', {}).get('Preferences', {})
                
                # Check Resist Fingerprinting
                rfp = prefs.get('privacy.resistFingerprinting', {})
                if rfp.get('Value') is True:
                    self.print_status("ResistFingerprinting", "pass", "Enabled")
                else:
                    self.print_status("ResistFingerprinting", "fail", "Not enabled")
                
                # Check DoH
                doh_enabled = policies.get('policies', {}).get('DNSOverHTTPS', {}).get('Enabled')
                if doh_enabled:
                    self.print_status("Firefox DoH", "pass", "Enabled")
                else:
                    self.print_status("Firefox DoH", "warning", "Not configured")
                
                # Check WebRTC
                webrtc = prefs.get('media.peerconnection.enabled', {})
                if webrtc.get('Value') is False:
                    self.print_status("WebRTC disabled", "pass", "Disabled")
                else:
                    self.print_status("WebRTC disabled", "warning", "Still enabled")
                
                self.results['browser_firefox']['status'] = 'pass'
                break
                
            except FileNotFoundError:
                continue
            except json.JSONDecodeError as e:
                self.print_status("Firefox policies", "fail", f"Invalid JSON: {e}")
                self.results['browser_firefox']['status'] = 'fail'
                break
            except Exception as e:
                self.print_status("Firefox policies", "unknown", str(e))
                self.results['browser_firefox']['status'] = 'unknown'
                break
        
        if not policy_found:
            self.print_status("Firefox policies", "fail", "No policy file found")
            self.results['browser_firefox']['status'] = 'fail'

    def generate_summary_report(self):
        """Generate summary report"""
        self.print_header("VALIDATION SUMMARY")
        
        total_checks = len(self.results)
        passed = sum(1 for r in self.results.values() if r['status'] == 'pass')
        warnings = sum(1 for r in self.results.values() if r['status'] == 'warning')
        failed = sum(1 for r in self.results.values() if r['status'] == 'fail')
        unknown = sum(1 for r in self.results.values() if r['status'] == 'unknown')
        
        print(f"Total Checks: {total_checks}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {warnings}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"{Colors.MAGENTA}Unknown: {unknown}{Colors.END}")
        
        overall_score = (passed * 100 + warnings * 50) / (total_checks * 100) * 100
        
        if overall_score >= 80:
            score_color = Colors.GREEN
            status = "EXCELLENT"
        elif overall_score >= 60:
            score_color = Colors.YELLOW
            status = "GOOD"
        else:
            score_color = Colors.RED
            status = "NEEDS IMPROVEMENT"
        
        print(f"\n{Colors.BOLD}Overall Privacy Score: {score_color}{overall_score:.1f}% ({status}){Colors.END}")
        
        # Recommendations
        if failed > 0 or warnings > 0:
            print(f"\n{Colors.BOLD}Recommendations:{Colors.END}")
            
            if self.results['proxy']['status'] == 'fail':
                print(f"• {Colors.RED}Deploy proxy PAC file at http://proxy.local/proxy.pac{Colors.END}")
            
            if self.results['browser_firefox']['status'] == 'fail':
                print(f"• {Colors.RED}Install Firefox policy file in distribution/ directory{Colors.END}")
            
            if self.results['dns']['status'] in ['fail', 'warning']:
                print(f"• {Colors.YELLOW}Configure DNS-over-HTTPS with Quad9{Colors.END}")
            
            if self.results['webrtc']['status'] == 'manual':
                print(f"• {Colors.CYAN}Manually test WebRTC leak protection{Colors.END}")

    def run_full_validation(self):
        """Run complete privacy validation suite"""
        print(f"{Colors.BOLD}{Colors.MAGENTA}")
        print("🛡️  Privacy Configuration Validation")
        print("=====================================")
        print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"{Colors.END}")
        
        # Run all validation tests
        self.validate_proxy_connectivity()
        self.validate_dns_over_https()
        self.validate_browser_headers()
        self.check_firefox_policies()
        self.validate_webrtc_leaks()
        self.validate_timezone_spoofing()
        self.validate_network_fingerprinting()
        
        # Generate summary
        self.generate_summary_report()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"privacy_validation_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': f"{platform.system()} {platform.release()}",
                'results': self.results
            }, f, indent=2)
        
        print(f"\n{Colors.CYAN}Detailed results saved to: {report_file}{Colors.END}")

if __name__ == "__main__":
    validator = PrivacyValidator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick validation mode
        validator.validate_proxy_connectivity()
        validator.validate_browser_headers()
    else:
        # Full validation
        validator.run_full_validation()