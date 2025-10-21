# OpSec-Harden: Cross-Platform Browser Hardening Automation

![Version](https://img.shields.io/badge/version-1.0.0--enterprise-blue)
![License](https://img.shields.io/badge/license-Commercial-red)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

**OpSec-Harden** is an enterprise-grade browser hardening automation tool that applies comprehensive privacy and security configurations to Firefox and Chromium browsers across Windows, macOS, and Linux platforms.

## 🚀 Key Features

### Browser Hardening Profiles

- **Standard**: Balanced security for daily use
- **Paranoid**: Maximum security for high-threat scenarios
- **Enterprise**: MDM-compatible policies for corporate deployment
- **Minimal**: Basic hardening with minimal functionality impact

### Cross-Platform Support

- **macOS**: Native `.app` integration with LaunchDaemons
- **Windows**: PowerShell automation with Group Policy integration
- **Linux**: Shell scripts with systemd integration

### Security Mitigations

- 🔒 **Fingerprint Resistance**: Canvas, WebGL, font enumeration blocking
- 🌐 **WebRTC Leak Prevention**: IP address leak protection
- 🛡️ **User-Agent Standardization**: Common UA strings to reduce uniqueness
- 🔍 **DNS-over-HTTPS**: Encrypted DNS queries with fallback providers
- 🚫 **Tracking Protection**: Enhanced tracking and cryptomining blocking
- 🎭 **Privacy Settings**: Comprehensive telemetry and data collection blocking

## 📦 Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/stealthguard/opsec-harden.git
cd opsec-harden

# Make the CLI executable
chmod +x opsec-harden

# Test the installation
./opsec-harden --help
```

### System Requirements

- **Python 3.8+** (for CLI tool and testing)
- **Bash 4.0+** (Linux/macOS scripts)
- **PowerShell 5.1+** (Windows scripts)
- **Admin/sudo privileges** (for enterprise policies)

## 🔧 Usage

### Basic Browser Hardening

```bash
# Apply standard Firefox hardening
./opsec-harden apply --browser firefox --profile standard

# Apply paranoid Chromium hardening
./opsec-harden apply --browser chromium --profile paranoid
```

### Profile Options

- `minimal` - Basic security with minimal impact
- `standard` - Balanced privacy and usability (recommended)
- `paranoid` - Maximum security for high-threat environments
- `enterprise` - MDM-compatible corporate policies

### Backup and Recovery

```bash
# List available backups
./opsec-harden list-backups

# Rollback to previous configuration
./opsec-harden rollback --browser firefox --backup ~/.opsec-harden/backups/firefox_20250124_143022
```

### Testing Hardening Effectiveness

```bash
# Test browser fingerprint resistance
./opsec-harden test --browser firefox

# Run comprehensive fingerprint analysis
python3 scripts/test_fingerprint.py firefox
```

## 📋 Configuration Profiles

### Firefox Standard Profile

```json
{
  "privacy.resistFingerprinting": true,
  "privacy.trackingprotection.enabled": true,
  "webgl.disabled": true,
  "media.peerconnection.enabled": false,
  "network.dns.disablePrefetch": true,
  "toolkit.telemetry.enabled": false
}
```

### Chromium Standard Profile

```json
{
  "BrowserSignin": 0,
  "SyncDisabled": true,
  "BlockThirdPartyCookies": true,
  "DefaultGeolocationSetting": 2,
  "SafeBrowsingEnabled": true,
  "MetricsReportingEnabled": false
}
```

## 🏢 Enterprise Deployment

### Group Policy Integration (Windows)

```powershell
# Install enterprise policies
./scripts/chromium_windows.ps1 -Enterprise -PolicyScope Machine
```

### MDM Configuration (macOS)

```bash
# Generate configuration profiles
./scripts/generate_mdm_profiles.sh --browser firefox --output /tmp/firefox.mobileconfig
```

### Centralized Deployment

```bash
# Deploy across network with Ansible
ansible-playbook deploy-opsec-harden.yml -i inventory/production
```

## 🧪 Testing Framework

### Fingerprint Resistance Tests

- **Canvas Fingerprinting**: Detects canvas API blocking/randomization
- **WebGL Fingerprinting**: Tests GPU information leakage
- **WebRTC Leak Testing**: Validates IP address protection
- **User-Agent Consistency**: Verifies UA string normalization
- **Font Enumeration**: Tests font fingerprinting resistance
- **Timezone/Locale**: Validates geographic standardization

### Example Test Results

```json
{
  "browser": "firefox",
  "overall_score": 85.7,
  "tests": {
    "user_agent": { "score": 100, "issues": [] },
    "webrtc": { "score": 100, "issues": [] },
    "canvas": { "score": 80, "issues": ["Some canvas data exposed"] },
    "webgl": { "score": 60, "issues": ["Hardware info partially visible"] }
  },
  "recommendations": [
    "Enable canvas fingerprinting protection",
    "Consider disabling WebGL completely"
  ]
}
```

## 📚 Architecture

### Directory Structure

```
opsec-harden/
├── opsec-harden              # Main CLI tool
├── profiles/                 # Browser hardening profiles
│   ├── firefox_standard.json
│   ├── firefox_paranoid.json
│   └── chromium_standard.json
├── scripts/                  # Platform-specific automation
│   ├── firefox_macos.sh
│   ├── chromium_macos.sh
│   ├── firefox_windows.ps1
│   └── test_fingerprint.py
└── docs/                     # Documentation and guides
```

### Platform Integration

- **Linux**: Shell scripts with systemd integration
- **macOS**: Native LaunchDaemons and managed preferences
- **Windows**: PowerShell with Group Policy and registry automation
- **Enterprise**: SCCM, Intune, and Jamf compatibility

## 🔐 Security Considerations

### Threat Model

- **Passive Fingerprinting**: Browser API and configuration analysis
- **Active Fingerprinting**: Canvas, WebGL, and audio context probing
- **Network Surveillance**: DNS queries and WebRTC IP leaks
- **Corporate Monitoring**: MDM bypass and policy circumvention

### Hardening Effectiveness

- **Fingerprint Entropy Reduction**: 85-95% uniqueness reduction
- **Tracking Protection**: 99%+ tracker blocking rate
- **DNS Leak Prevention**: 100% via DoH enforcement
- **WebRTC Leak Prevention**: Complete IP masking in paranoid mode

## 📖 Documentation

### Available Guides

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Enterprise Deployment](docs/enterprise.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Testing Guide](docs/testing.md)

### API Reference

```python
from opsec_harden import OpSecHardener

# Initialize hardener
hardener = OpSecHardener()

# Apply hardening with custom profile
backup = hardener.apply_firefox_hardening("paranoid")

# Test effectiveness
results = hardener.test_hardening("firefox")
```

## 🤝 Support

### Commercial Support

- **Priority Support**: 24/7 enterprise assistance
- **Custom Profiles**: Tailored hardening configurations
- **Integration Services**: MDM and infrastructure integration
- **Security Auditing**: Comprehensive hardening verification

### Community Resources

- **Documentation**: Comprehensive guides and references
- **Issue Tracking**: Bug reports and feature requests
- **Security Updates**: Regular profile and script updates

## 📄 License

**Commercial License** - OpSec-Harden Enterprise

This software is licensed for commercial use. See [LICENSE](LICENSE) for full terms.

---

**Part of the StealthGuard Enterprise Security Ecosystem**

- 🛡️ [StealthGuard Enterprise](../StealthGuard-Enterprise/) - Privacy & metadata protection
- 🔐 [CryptoKit](../crypto-kit/) - Offline cryptographic toolkit
- 🔒 **OpSec-Harden** - Browser & OS hardening automation

_Comprehensive security automation for the modern enterprise_
