#!/usr/bin/env python3
"""
Browser Fingerprint Testing Tool
Part of OpSec-Harden Enterprise Security Toolkit

Tests browser hardening effectiveness by checking:
- User-Agent normalization
- WebRTC leak prevention
- Canvas fingerprinting resistance
- WebGL fingerprinting resistance
- Timezone/locale standardization
- DNS leak prevention
"""

import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional


class FingerprintTester:
    """Browser fingerprint resistance tester"""
    
    def __init__(self, browser: str):
        self.browser = browser.lower()
        self.results = {
            "browser": browser,
            "timestamp": int(time.time()),
            "tests": {},
            "overall_score": 0,
            "recommendations": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log test progress"""
        print(f"[{level}] {message}", file=sys.stderr)
        
    def run_all_tests(self) -> Dict:
        """Run all fingerprinting tests"""
        self.log("Starting fingerprint resistance tests...")
        
        try:
            # Test User-Agent consistency
            self._test_user_agent()
            
            # Test WebRTC leak prevention
            self._test_webrtc_leaks()
            
            # Test Canvas fingerprinting resistance
            self._test_canvas_fingerprinting()
            
            # Test WebGL fingerprinting resistance  
            self._test_webgl_fingerprinting()
            
            # Test timezone/locale standardization
            self._test_timezone_locale()
            
            # Test DNS leak prevention
            self._test_dns_leaks()
            
            # Test plugin enumeration blocking
            self._test_plugin_enumeration()
            
            # Test font enumeration blocking
            self._test_font_enumeration()
            
            # Calculate overall score
            self._calculate_score()
            
        except Exception as e:
            self.results["error"] = str(e)
            self.log(f"Testing failed: {e}", "ERROR")
            
        return self.results
    
    def _test_user_agent(self):
        """Test User-Agent string consistency"""
        self.log("Testing User-Agent consistency...")
        
        test_script = """
        const ua = navigator.userAgent;
        const results = {
            userAgent: ua,
            isFirefox: ua.includes('Firefox'),
            isChrome: ua.includes('Chrome'),
            platform: navigator.platform,
            language: navigator.language,
            languages: navigator.languages,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack
        };
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            # Check for common hardening indicators
            ua = result.get("userAgent", "")
            score = 0
            issues = []
            
            # Check for generic/common UA string
            if "Windows NT 10.0" in ua and "rv:102.0" in ua:
                score += 25
            elif "Windows NT 10.0" in ua and "Chrome/120.0.0.0" in ua:
                score += 25
            else:
                issues.append("User-Agent not standardized to common value")
            
            # Check DoNotTrack header
            if result.get("doNotTrack") in ["1", True]:
                score += 25
            else:
                issues.append("Do Not Track not enabled")
            
            # Check language standardization
            if result.get("language") == "en-US":
                score += 25
            else:
                issues.append("Language not standardized to en-US")
            
            # Check platform obfuscation
            platform = result.get("platform", "")
            if platform in ["Win32", "Linux x86_64"]:
                score += 25
            else:
                issues.append(f"Platform reveals fingerprinting info: {platform}")
            
            self.results["tests"]["user_agent"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_webrtc_leaks(self):
        """Test WebRTC IP leak prevention"""
        self.log("Testing WebRTC leak prevention...")
        
        test_script = """
        const results = {
            webrtcSupported: !!(window.RTCPeerConnection || window.webkitRTCPeerConnection),
            candidates: []
        };
        
        if (results.webrtcSupported) {
            const pc = new (window.RTCPeerConnection || window.webkitRTCPeerConnection)({
                iceServers: [{urls: "stun:stun.l.google.com:19302"}]
            });
            
            pc.createDataChannel("");
            pc.onicecandidate = (e) => {
                if (e.candidate) {
                    results.candidates.push(e.candidate.candidate);
                }
            };
            
            pc.createOffer().then((offer) => pc.setLocalDescription(offer));
            
            setTimeout(() => {
                console.log(JSON.stringify(results));
            }, 3000);
        } else {
            console.log(JSON.stringify(results));
        }
        """
        
        result = self._run_js_test(test_script, timeout=5)
        if result:
            score = 0
            issues = []
            
            if not result.get("webrtcSupported", True):
                score = 100  # Perfect - WebRTC disabled
            else:
                candidates = result.get("candidates", [])
                local_ips = [c for c in candidates if "192.168." in c or "10." in c or "172." in c]
                
                if not candidates:
                    score = 80  # Good - no candidates leaked
                elif not local_ips:
                    score = 60  # OK - no local IPs leaked
                else:
                    score = 20  # Poor - local IPs leaked
                    issues.append(f"WebRTC leaked {len(local_ips)} local IP addresses")
            
            self.results["tests"]["webrtc"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_canvas_fingerprinting(self):
        """Test Canvas fingerprinting resistance"""
        self.log("Testing Canvas fingerprinting resistance...")
        
        test_script = """
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Draw fingerprinting pattern
        ctx.textBaseline = "top";
        ctx.font = "14px Arial";
        ctx.textBaseline = "alphabetic";
        ctx.fillStyle = "#f60";
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = "#069";
        ctx.fillText("OpSec-Test 🔒", 2, 15);
        ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
        ctx.fillText("OpSec-Test 🔒", 4, 17);
        
        const hash1 = canvas.toDataURL();
        
        // Second identical draw
        const canvas2 = document.createElement('canvas');
        const ctx2 = canvas2.getContext('2d');
        ctx2.textBaseline = "top";
        ctx2.font = "14px Arial";
        ctx2.textBaseline = "alphabetic";
        ctx2.fillStyle = "#f60";
        ctx2.fillRect(125, 1, 62, 20);
        ctx2.fillStyle = "#069";
        ctx2.fillText("OpSec-Test 🔒", 2, 15);
        ctx2.fillStyle = "rgba(102, 204, 0, 0.7)";
        ctx2.fillText("OpSec-Test 🔒", 4, 17);
        
        const hash2 = canvas2.toDataURL();
        
        const results = {
            hash1: hash1.substring(0, 50) + "...",
            hash2: hash2.substring(0, 50) + "...",
            consistent: hash1 === hash2,
            isBlank: hash1.includes("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XS")
        };
        
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            score = 0
            issues = []
            
            if result.get("isBlank"):
                score = 100  # Perfect - canvas blocked/blank
            elif not result.get("consistent"):
                score = 80   # Good - randomization active
            else:
                score = 20   # Poor - consistent fingerprint
                issues.append("Canvas fingerprinting not blocked")
            
            self.results["tests"]["canvas"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_webgl_fingerprinting(self):
        """Test WebGL fingerprinting resistance"""
        self.log("Testing WebGL fingerprinting resistance...")
        
        test_script = """
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        const results = {
            webglSupported: !!gl,
            vendor: null,
            renderer: null,
            version: null,
            shadingLanguageVersion: null,
            extensions: []
        };
        
        if (gl) {
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            results.vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
            results.renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
            results.version = gl.getParameter(gl.VERSION);
            results.shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
            results.extensions = gl.getSupportedExtensions();
        }
        
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            score = 0
            issues = []
            
            if not result.get("webglSupported"):
                score = 100  # Perfect - WebGL disabled
            else:
                vendor = result.get("vendor", "")
                renderer = result.get("renderer", "")
                
                # Check for generic/masked values
                if "Google Inc." in vendor and "ANGLE" in renderer:
                    score = 60  # OK - using ANGLE (common)
                elif vendor == "Mozilla" or "Software" in renderer:
                    score = 80  # Good - software rendering
                else:
                    score = 20  # Poor - hardware info exposed
                    issues.append(f"WebGL exposes hardware info: {vendor} / {renderer}")
            
            self.results["tests"]["webgl"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_timezone_locale(self):
        """Test timezone and locale standardization"""
        self.log("Testing timezone/locale standardization...")
        
        test_script = """
        const results = {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            locale: navigator.language,
            languages: navigator.languages,
            dateFormat: new Date().toLocaleString(),
            numberFormat: (1234.56).toLocaleString(),
            timezoneOffset: new Date().getTimezoneOffset()
        };
        
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            score = 0
            issues = []
            
            # Check timezone
            tz = result.get("timezone", "")
            if tz == "UTC":
                score += 50
            else:
                issues.append(f"Timezone not standardized: {tz}")
            
            # Check locale
            locale = result.get("locale", "")
            if locale == "en-US":
                score += 50
            else:
                issues.append(f"Locale not standardized: {locale}")
            
            self.results["tests"]["timezone_locale"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_dns_leaks(self):
        """Test DNS leak prevention (simplified)"""
        self.log("Testing DNS leak prevention...")
        
        # This is a simplified test - full DNS leak testing requires external services
        test_script = """
        const results = {
            dnsOverHttps: false,
            browserDNS: "unknown"
        };
        
        // Check if DNS-over-HTTPS is likely enabled
        if (typeof chrome !== 'undefined' && chrome.dns) {
            results.browserDNS = "chrome-dns";
        }
        
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            # For now, just check if we're testing at all
            score = 50  # Neutral - would need external service to verify
            issues = ["DNS leak testing requires external verification"]
            
            self.results["tests"]["dns_leaks"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_plugin_enumeration(self):
        """Test plugin enumeration blocking"""
        self.log("Testing plugin enumeration...")
        
        test_script = """
        const results = {
            pluginsLength: navigator.plugins.length,
            plugins: Array.from(navigator.plugins).map(p => ({
                name: p.name,
                description: p.description,
                filename: p.filename
            })),
            mimeTypesLength: navigator.mimeTypes.length
        };
        
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            score = 0
            issues = []
            
            plugins_count = result.get("pluginsLength", 0)
            if plugins_count == 0:
                score = 100  # Perfect - no plugins exposed
            elif plugins_count <= 2:
                score = 60   # OK - minimal plugins
            else:
                score = 20   # Poor - many plugins exposed
                issues.append(f"Browser exposes {plugins_count} plugins")
            
            self.results["tests"]["plugins"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _test_font_enumeration(self):
        """Test font enumeration resistance"""
        self.log("Testing font enumeration...")
        
        test_script = """
        const fonts = [
            'Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Georgia',
            'Impact', 'Times New Roman', 'Trebuchet MS', 'Verdana',
            'Helvetica', 'Times', 'Courier', 'Palatino', 'Garamond'
        ];
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testString = 'OpSec Font Test';
        const testSize = '72px';
        
        const baseline = {};
        baseFonts.forEach(baseFont => {
            ctx.font = testSize + ' ' + baseFont;
            baseline[baseFont] = ctx.measureText(testString).width;
        });
        
        const detectedFonts = [];
        fonts.forEach(font => {
            baseFonts.forEach(baseFont => {
                ctx.font = testSize + ' ' + font + ', ' + baseFont;
                const matched = ctx.measureText(testString).width !== baseline[baseFont];
                if (matched) {
                    detectedFonts.push(font);
                    return;
                }
            });
        });
        
        const results = {
            fontsDetected: detectedFonts.length,
            detectedFonts: detectedFonts
        };
        
        console.log(JSON.stringify(results));
        """
        
        result = self._run_js_test(test_script)
        if result:
            score = 0
            issues = []
            
            fonts_detected = result.get("fontsDetected", 0)
            if fonts_detected <= 5:
                score = 100  # Good - minimal font detection
            elif fonts_detected <= 10:
                score = 60   # OK - some fonts detected
            else:
                score = 20   # Poor - many fonts detected
                issues.append(f"Font enumeration detected {fonts_detected} fonts")
            
            self.results["tests"]["fonts"] = {
                "score": score,
                "max_score": 100,
                "details": result,
                "issues": issues
            }
    
    def _run_js_test(self, script: str, timeout: int = 10) -> Optional[Dict]:
        """Run JavaScript test in browser"""
        try:
            # Create temporary HTML file with test script
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>OpSec-Harden Test</title></head>
            <body>
            <script>
            try {{
                {script}
            }} catch(e) {{
                console.log(JSON.stringify({{error: e.toString()}}));
            }}
            </script>
            </body>
            </html>
            """
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_file = f.name
            
            # Run browser with test file
            if self.browser == "firefox":
                cmd = ["firefox", "--headless", "--new-instance", f"file://{html_file}"]
            elif self.browser == "chromium":
                cmd = ["chromium", "--headless", "--no-sandbox", "--disable-gpu", f"file://{html_file}"]
            else:
                self.log(f"Unsupported browser: {self.browser}", "ERROR")
                return None
            
            # Capture output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            # Clean up
            Path(html_file).unlink(missing_ok=True)
            
            # Parse JSON output from console.log
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        return json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
            
            return None
            
        except subprocess.TimeoutExpired:
            self.log(f"Test timed out after {timeout}s", "WARN")
            return None
        except Exception as e:
            self.log(f"Test execution failed: {e}", "ERROR")
            return None
    
    def _calculate_score(self):
        """Calculate overall hardening score"""
        total_score = 0
        max_total = 0
        
        for test_name, test_result in self.results["tests"].items():
            total_score += test_result.get("score", 0)
            max_total += test_result.get("max_score", 100)
        
        if max_total > 0:
            self.results["overall_score"] = round((total_score / max_total) * 100, 1)
        else:
            self.results["overall_score"] = 0
        
        # Generate recommendations based on low scores
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate recommendations for improving hardening"""
        recommendations = []
        
        for test_name, test_result in self.results["tests"].items():
            score = test_result.get("score", 0)
            max_score = test_result.get("max_score", 100)
            
            if score < max_score * 0.7:  # Less than 70%
                if test_name == "user_agent":
                    recommendations.append("Enable User-Agent spoofing to common value")
                elif test_name == "webrtc":
                    recommendations.append("Disable WebRTC or enable IP leak protection")
                elif test_name == "canvas":
                    recommendations.append("Enable canvas fingerprinting protection")
                elif test_name == "webgl":
                    recommendations.append("Disable WebGL or enable fingerprinting protection")
                elif test_name == "timezone_locale":
                    recommendations.append("Standardize timezone to UTC and locale to en-US")
                elif test_name == "plugins":
                    recommendations.append("Disable or hide browser plugins")
                elif test_name == "fonts":
                    recommendations.append("Enable font fingerprinting protection")
        
        self.results["recommendations"] = recommendations

def main():
    """Main test runner"""
    if len(sys.argv) != 2:
        print("Usage: test_fingerprint.py <browser>", file=sys.stderr)
        print("Available browsers: firefox, chromium", file=sys.stderr)
        sys.exit(1)
    
    browser = sys.argv[1].lower()
    if browser in ["--help", "-h", "help"]:
        print("OpSec-Harden Fingerprint Testing Tool")
        print("Usage: test_fingerprint.py <browser>")
        print("Available browsers: firefox, chromium")
        print("\nTests browser hardening effectiveness by checking:")
        print("  - User-Agent normalization")
        print("  - WebRTC leak prevention") 
        print("  - Canvas fingerprinting resistance")
        print("  - WebGL fingerprinting resistance")
        print("  - Timezone/locale standardization")
        print("  - DNS leak prevention")
        print("  - Plugin and font enumeration blocking")
        sys.exit(0)
        
    if browser not in ["firefox", "chromium"]:
        print(f"Unsupported browser: {browser}", file=sys.stderr)
        print("Available browsers: firefox, chromium", file=sys.stderr)
        sys.exit(1)
    
    tester = FingerprintTester(browser)
    results = tester.run_all_tests()
    
    # Output results as JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()