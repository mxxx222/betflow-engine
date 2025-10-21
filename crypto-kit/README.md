# 🔧 CryptoKit - Enterprise Cryptographic Toolkit

**Offline-friendly cryptographic toolkit for StealthGuard Enterprise field operations**

## Overview

CryptoKit provides a unified command-line interface for enterprise cryptographic operations, eliminating ad-hoc security practices and reducing human error in field deployments. Built with Go for maximum portability and minimal dependencies.

## 🎯 Core Capabilities

### File Encryption & Sharing

- **Age cryptography**: Modern, secure file encryption
- **QR code generation**: Easy sharing workflows
- **Hardware key support**: YubiKey/HSM integration (planned)
- **One-time sharing**: Secure temporary file access

### Cross-Platform Disk Encryption

- **Linux**: LUKS with cryptsetup integration
- **macOS**: APFS encryption with diskutil
- **Windows**: BitLocker PowerShell wrapper
- **Unified interface**: Same commands across all platforms

### Key Lifecycle Management

- **Automated rotation**: Configurable policies (30d, 90d, 180d, 365d)
- **Vault integration**: HashiCorp Vault, Bitwarden API (planned)
- **Secure archival**: Encrypted key backup and recovery
- **Audit logging**: Compliance-ready key rotation logs

## 🚀 Quick Start

### Installation

```bash
# Build from source
git clone <repository>
cd crypto-kit
go build -o crypto-kit main.go

# Or download pre-built binary
curl -L https://releases.stealth-guard.com/crypto-kit/latest/crypto-kit-$(uname -s)-$(uname -m) -o crypto-kit
chmod +x crypto-kit
```

### Generate Keys

```bash
# Generate new age key pair
./crypto-kit keygen

# Keys saved to:
# ~/.crypto-kit/keys/public.age
# ~/.crypto-kit/keys/private.age
```

### Encrypt & Share Files

```bash
# Encrypt file for recipient
./crypto-kit share --file secret.pdf --recipient pubkey.age

# Generate QR code for easy sharing
./crypto-kit share --file report.xlsx --recipient pub.age --qr

# Decrypt received file
./crypto-kit decrypt --file secret.pdf.age --key private.age
```

### Disk Encryption

```bash
# Linux: Initialize LUKS encrypted disk
sudo ./crypto-kit disk --init --device /dev/sdb --algo XTS-AES-256

# macOS: Initialize APFS encrypted disk
sudo ./crypto-kit disk --init --device /dev/disk2 --algo AES-XTS

# Windows: Initialize BitLocker encrypted disk
./crypto-kit disk --init --device D: --algo AES-256
```

### Key Rotation

```bash
# Rotate keys every 90 days (default policy)
./crypto-kit rotate --policy 90d --backup /secure/keystore

# Force immediate rotation
./crypto-kit rotate --force --policy 30d

# Integrate with vault
./crypto-kit rotate --policy 90d --vault bitwarden
```

## 📋 Command Reference

### Global Flags

```bash
-v, --verbose    Enable verbose output
-o, --output     Specify output file or directory
-c, --config     Custom config file path
```

### Core Commands

#### `crypto-kit keygen`

Generate new age key pairs for encryption/decryption.

```bash
crypto-kit keygen [flags]

Flags:
  --force    Overwrite existing keys
```

#### `crypto-kit share`

Encrypt files for secure sharing.

```bash
crypto-kit share --file <file> --recipient <pubkey> [flags]

Flags:
  -f, --file        File to encrypt (required)
  -r, --recipient   Recipient's public key file (required)
  -o, --output      Output file path (default: <file>.age)
  --expiry         Expiration time (7d, 24h, 2w)
  --qr             Generate QR code with decrypt instructions
```

#### `crypto-kit decrypt`

Decrypt age-encrypted files.

```bash
crypto-kit decrypt --file <file> --key <privkey> [flags]

Flags:
  -f, --file    Encrypted file to decrypt (required)
  -k, --key     Private key file or 'hardware' (required)
  -o, --output  Output file path (default: remove .age extension)
```

#### `crypto-kit disk`

Cross-platform disk encryption management.

```bash
crypto-kit disk --init --device <device> [flags]

Flags:
  --device     Target device (e.g., /dev/sdb, /dev/disk2)
  --algo       Encryption algorithm (default: XTS-AES-256)
  --init       Initialize disk encryption
  --mount      Mount point for encrypted disk
  --label      Volume label (default: CryptoKit)
```

#### `crypto-kit rotate`

Automated key rotation and lifecycle management.

```bash
crypto-kit rotate [flags]

Flags:
  --policy     Rotation policy: 30d, 90d, 180d, 365d (default: 90d)
  --vault      Vault backend: vault, bitwarden
  --backup     Backup directory for old keys
  --force      Force rotation even if policy not met
```

## 🏗️ Architecture

### Security Design Principles

- **Offline-first**: No cloud dependencies for core operations
- **Minimal attack surface**: Single binary, minimal dependencies
- **Cross-platform consistency**: Unified interface across OS
- **Hardware integration**: Support for HSM/YubiKey (planned)

### Cryptographic Standards

- **File encryption**: Age (X25519, ChaCha20-Poly1305)
- **Disk encryption**: AES-XTS-256 (LUKS, APFS, BitLocker)
- **Key generation**: Cryptographically secure random number generation
- **Key storage**: OS-appropriate secure file permissions

### File Structure

```
~/.crypto-kit/
├── config/
│   ├── last_rotation      # Rotation timestamp
│   └── settings.yaml      # User configuration
├── keys/
│   ├── public.age         # Current public key
│   ├── private.age        # Current private key
│   └── backup/            # Rotated key archive
└── logs/
    └── audit.log          # Security event logging
```

## 🔒 Security Features

### Threat Model (STRIDE Analysis)

#### Spoofing

- **Threat**: Unauthorized key usage
- **Mitigation**: Hardware key PIN protection, secure key storage

#### Tampering

- **Threat**: File/key modification
- **Mitigation**: SHA-256 checksums, cryptographic signatures

#### Repudiation

- **Threat**: Denial of cryptographic actions
- **Mitigation**: Comprehensive audit logging, timestamped events

#### Information Disclosure

- **Threat**: Key/plaintext exposure
- **Mitigation**: AES-XTS disk encryption, age file encryption

#### Denial of Service

- **Threat**: Key loss, system unavailability
- **Mitigation**: Offline recovery keys, secure key backup

#### Elevation of Privilege

- **Threat**: Unauthorized access escalation
- **Mitigation**: Role-based key policies, principle of least privilege

### Compliance Features

- **Audit trails**: Complete cryptographic operation logging
- **Key rotation**: Automated lifecycle management
- **Secure storage**: OS-integrated permission systems
- **Recovery procedures**: Documented key recovery processes

## 🚀 ROI & Business Impact

### Cost Reduction

- **Training**: Single tool replaces multiple cryptographic utilities
- **Maintenance**: Automated key rotation reduces manual overhead
- **Compliance**: Built-in audit logging reduces regulatory preparation time
- **Errors**: Standardized workflows prevent ad-hoc security mistakes

### Risk Mitigation

- **Data exposure**: Consistent encryption across all field operations
- **Key compromise**: Automated rotation limits exposure window
- **Human error**: Unified interface reduces complexity-related mistakes
- **Compliance violations**: Audit-ready logging prevents regulatory issues

### Implementation Timeline

- **Week 1**: MVP deployment and initial key generation
- **Week 2**: Cross-platform disk encryption testing
- **Month 1**: Key rotation policies and vault integration
- **Month 3**: Hardware key integration (YubiKey/HSM)

## 🔧 Development

### Build Requirements

- **Go 1.21+**: Modern Go version with module support
- **CGO**: Required for some cryptographic operations
- **Cross-compilation**: Supports Linux, macOS, Windows

### Dependencies

```go
filippo.io/age                 // Age encryption library
github.com/spf13/cobra         // CLI framework
github.com/spf13/viper         // Configuration management
github.com/skip2/go-qrcode     // QR code generation
github.com/hashicorp/vault/api // HashiCorp Vault integration
golang.org/x/crypto            // Extended cryptographic primitives
```

### Testing

```bash
# Run unit tests
go test ./...

# Run integration tests (requires sudo for disk operations)
go test -tags=integration ./cmd/...

# Security audit
go mod verify
gosec ./...
```

### Building

```bash
# Local development build
go build -o crypto-kit main.go

# Cross-platform builds
GOOS=linux GOARCH=amd64 go build -o crypto-kit-linux-amd64 main.go
GOOS=darwin GOARCH=amd64 go build -o crypto-kit-darwin-amd64 main.go
GOOS=windows GOARCH=amd64 go build -o crypto-kit-windows-amd64.exe main.go

# Release build with optimizations
go build -ldflags="-s -w" -o crypto-kit main.go
```

## 📚 Integration with StealthGuard Enterprise

CryptoKit complements the StealthGuard Enterprise privacy platform:

### Privacy + Cryptography

- **Network anonymity**: StealthGuard hides traffic patterns
- **Data protection**: CryptoKit encrypts sensitive data
- **Field operations**: Unified security toolkit for remote work

### Shared Principles

- **Offline-first**: Both tools work without cloud connectivity
- **Enterprise-ready**: MDM integration and centralized management
- **Cross-platform**: Consistent experience across all devices
- **Audit compliance**: Built-in logging for regulatory requirements

### Deployment Synergy

- **Phase 1**: Deploy StealthGuard for network privacy
- **Phase 2**: Add CryptoKit for data encryption
- **Phase 3**: Integrate both tools in unified security workflow
- **Phase 4**: Scale across entire enterprise with centralized policies

## 📞 Support & Documentation

### Community

- **GitHub**: Issues, feature requests, contributions
- **Documentation**: Comprehensive guides and examples
- **Security**: Responsible disclosure process

### Enterprise Support

- **Email**: crypto-kit@stealthguard.com
- **Phone**: +1-800-STEALTH (Enterprise customers)
- **Professional Services**: Custom integration and deployment

### Training & Certification

- **Admin Training**: 2-day cryptographic operations course
- **User Training**: 4-hour end-user encryption workshop
- **Security Training**: Advanced threat modeling and key management

---

**🔐 CryptoKit - Enterprise cryptography made simple**

_Secure by design, simple by choice_

**Version**: 1.0.0-enterprise  
**License**: Commercial (included with StealthGuard Enterprise)  
**Copyright**: © 2025 StealthGuard Technologies, Inc.
