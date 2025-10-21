# 🔧 CryptoKit - Build & Deployment Instructions

## Prerequisites

### System Requirements

- **Go 1.21+**: Modern Go version with module support
- **Git**: Source code management
- **Make**: Build automation (optional but recommended)
- **sudo access**: Required for disk encryption operations

### Platform-Specific Requirements

#### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install golang-go git make cryptsetup

# RHEL/CentOS
sudo yum install golang git make cryptsetup-luks

# Arch Linux
sudo pacman -S go git make cryptsetup
```

#### macOS

```bash
# Using Homebrew
brew install go git make

# Xcode Command Line Tools (for system integration)
xcode-select --install
```

#### Windows

```powershell
# Using Chocolatey
choco install golang git make

# Or download manually:
# - Go: https://golang.org/dl/
# - Git: https://git-scm.com/downloads
```

## 🚀 Build Instructions

### Development Build

```bash
# Clone repository
git clone https://github.com/stealthguard/crypto-kit.git
cd crypto-kit

# Initialize Go modules
go mod tidy

# Build for current platform
go build -o crypto-kit main.go

# Test the build
./crypto-kit --version
```

### Production Build

```bash
# Build with optimizations
go build -ldflags="-s -w -X main.version=1.0.0 -X main.buildDate=$(date -u +%Y-%m-%dT%H:%M:%SZ)" -o crypto-kit main.go

# Strip debug symbols (Linux/macOS)
strip crypto-kit

# Verify build
file crypto-kit
./crypto-kit --help
```

### Cross-Platform Builds

```bash
# Linux AMD64
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o crypto-kit-linux-amd64 main.go

# Linux ARM64
GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o crypto-kit-linux-arm64 main.go

# macOS AMD64
GOOS=darwin GOARCH=amd64 go build -ldflags="-s -w" -o crypto-kit-darwin-amd64 main.go

# macOS ARM64 (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -ldflags="-s -w" -o crypto-kit-darwin-arm64 main.go

# Windows AMD64
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o crypto-kit-windows-amd64.exe main.go
```

### Build Automation (Makefile)

```makefile
# Create Makefile in project root
.PHONY: all build clean test install cross-compile

VERSION := $(shell git describe --tags --always --dirty)
BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
LDFLAGS := -s -w -X main.version=$(VERSION) -X main.buildDate=$(BUILD_DATE)

all: build

build:
	go build -ldflags="$(LDFLAGS)" -o crypto-kit main.go

clean:
	rm -f crypto-kit crypto-kit-*

test:
	go test ./...

install: build
	sudo cp crypto-kit /usr/local/bin/
	sudo chmod 755 /usr/local/bin/crypto-kit

cross-compile:
	GOOS=linux GOARCH=amd64 go build -ldflags="$(LDFLAGS)" -o crypto-kit-linux-amd64 main.go
	GOOS=darwin GOARCH=amd64 go build -ldflags="$(LDFLAGS)" -o crypto-kit-darwin-amd64 main.go
	GOOS=windows GOARCH=amd64 go build -ldflags="$(LDFLAGS)" -o crypto-kit-windows-amd64.exe main.go
```

Usage:

```bash
make build          # Build for current platform
make cross-compile  # Build for all platforms
make test          # Run test suite
make install       # Install to system
make clean         # Clean build artifacts
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html

# Run specific test
go test -run TestKeyGeneration ./tests/
```

### Integration Tests

```bash
# Run integration tests (requires sudo for disk operations)
go test -tags=integration ./tests/

# Run with verbose output
go test -v -tags=integration ./tests/

# Run specific integration test
go test -tags=integration -run TestDiskEncryptionLinux ./tests/
```

### Security Testing

```bash
# Static security analysis
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
gosec ./...

# Dependency vulnerability scan
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

# Race condition detection
go test -race ./...

# Memory leak detection
go test -memprofile=mem.prof ./...
go tool pprof mem.prof
```

## 📦 Packaging

### Debian/Ubuntu Package

```bash
# Install packaging tools
sudo apt install devscripts debhelper

# Create debian package structure
mkdir -p debian/crypto-kit/{DEBIAN,usr/local/bin,usr/share/doc/crypto-kit}

# Create control file
cat > debian/crypto-kit/DEBIAN/control << EOF
Package: crypto-kit
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: StealthGuard <support@stealthguard.com>
Description: Enterprise cryptographic toolkit
 CryptoKit provides file encryption, disk encryption,
 and key management for enterprise environments.
EOF

# Copy binary and documentation
cp crypto-kit debian/crypto-kit/usr/local/bin/
cp README.md debian/crypto-kit/usr/share/doc/crypto-kit/

# Build package
dpkg-deb --build debian/crypto-kit
```

### RPM Package (RHEL/CentOS)

```bash
# Install packaging tools
sudo yum install rpm-build rpmdevtools

# Create RPM build structure
rpmdev-setuptree

# Create spec file
cat > ~/rpmbuild/SPECS/crypto-kit.spec << EOF
Name: crypto-kit
Version: 1.0.0
Release: 1%{?dist}
Summary: Enterprise cryptographic toolkit
License: Commercial
URL: https://stealthguard.com
Source0: crypto-kit

%description
CryptoKit provides file encryption, disk encryption,
and key management for enterprise environments.

%install
mkdir -p %{buildroot}%{_bindir}
cp %{SOURCE0} %{buildroot}%{_bindir}/crypto-kit

%files
%{_bindir}/crypto-kit

%changelog
* $(date "+%a %b %d %Y") StealthGuard <support@stealthguard.com> - 1.0.0-1
- Initial release
EOF

# Build RPM
cp crypto-kit ~/rpmbuild/SOURCES/
rpmbuild -ba ~/rpmbuild/SPECS/crypto-kit.spec
```

### macOS Package

```bash
# Create macOS package structure
mkdir -p crypto-kit.pkg/{Scripts,Payload/usr/local/bin}

# Copy binary
cp crypto-kit crypto-kit.pkg/Payload/usr/local/bin/

# Create package info
cat > crypto-kit.pkg/PackageInfo << EOF
<?xml version="1.0" encoding="utf-8"?>
<pkg-info format-version="2" identifier="com.stealthguard.crypto-kit"
          version="1.0.0" install-location="/" auth="root">
    <payload installKBytes="$(du -k crypto-kit | cut -f1)" numberOfFiles="1"/>
</pkg-info>
EOF

# Build package
pkgbuild --root crypto-kit.pkg/Payload --identifier com.stealthguard.crypto-kit \
         --version 1.0.0 crypto-kit-1.0.0.pkg
```

### Windows Installer

```powershell
# Using NSIS (Nullsoft Scriptable Install System)
# Install NSIS from https://nsis.sourceforge.io/

# Create installer script (crypto-kit.nsi)
@"
!define APPNAME "CryptoKit"
!define VERSION "1.0.0"

Name "${APPNAME} ${VERSION}"
OutFile "crypto-kit-${VERSION}-setup.exe"
InstallDir "$PROGRAMFILES\StealthGuard\CryptoKit"

Section "Install"
    SetOutPath $INSTDIR
    File "crypto-kit-windows-amd64.exe"

    # Add to PATH
    ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$INSTDIR"

    # Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd
"@ > crypto-kit.nsi

# Build installer
makensis crypto-kit.nsi
```

## 🚀 Deployment

### Single Binary Deployment

```bash
# Copy to system location
sudo cp crypto-kit /usr/local/bin/
sudo chmod 755 /usr/local/bin/crypto-kit

# Verify installation
crypto-kit --version
which crypto-kit
```

### Container Deployment

```dockerfile
# Dockerfile
FROM alpine:latest

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY crypto-kit /usr/local/bin/crypto-kit
RUN chmod +x /usr/local/bin/crypto-kit

USER nobody:nobody

ENTRYPOINT ["crypto-kit"]
```

```bash
# Build container
docker build -t stealthguard/crypto-kit:1.0.0 .

# Run container
docker run -it --rm -v $(pwd):/data stealthguard/crypto-kit:1.0.0 keygen
```

### Enterprise Deployment (MDM)

```bash
# Create deployment package
mkdir -p crypto-kit-deploy/{bin,scripts,config}

# Copy binary
cp crypto-kit crypto-kit-deploy/bin/

# Create deployment script
cat > crypto-kit-deploy/scripts/install.sh << 'EOF'
#!/bin/bash
set -e

# Install binary
sudo cp bin/crypto-kit /usr/local/bin/
sudo chmod 755 /usr/local/bin/crypto-kit

# Create user config directory
mkdir -p ~/.crypto-kit/{config,keys,logs}
chmod 700 ~/.crypto-kit

# Generate initial keys if they don't exist
if [ ! -f ~/.crypto-kit/keys/private.age ]; then
    crypto-kit keygen
fi

echo "CryptoKit installation completed successfully"
EOF

chmod +x crypto-kit-deploy/scripts/install.sh

# Create package
tar czf crypto-kit-deploy.tar.gz crypto-kit-deploy/
```

### Configuration Management

#### Ansible Playbook

```yaml
---
- name: Deploy CryptoKit
  hosts: all
  become: yes
  tasks:
    - name: Download CryptoKit binary
      get_url:
        url: "https://releases.stealthguard.com/crypto-kit/1.0.0/crypto-kit-linux-amd64"
        dest: /usr/local/bin/crypto-kit
        mode: "0755"
        owner: root
        group: root

    - name: Verify installation
      command: crypto-kit --version
      register: version_output

    - name: Display version
      debug:
        msg: "Installed {{ version_output.stdout }}"
```

#### Chef Cookbook

```ruby
# recipes/default.rb
remote_file '/usr/local/bin/crypto-kit' do
  source 'https://releases.stealthguard.com/crypto-kit/1.0.0/crypto-kit-linux-amd64'
  mode '0755'
  owner 'root'
  group 'root'
  action :create
end

execute 'verify_crypto_kit' do
  command 'crypto-kit --version'
  action :run
end
```

## 📊 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/build.yml
name: Build and Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v3
        with:
          go-version: 1.21

      - name: Run tests
        run: |
          go test -v ./...
          go test -race ./...

      - name: Security scan
        run: |
          go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
          gosec ./...

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        goos: [linux, darwin, windows]
        goarch: [amd64, arm64]
        exclude:
          - goos: windows
            goarch: arm64

    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v3
        with:
          go-version: 1.21

      - name: Build
        env:
          GOOS: ${{ matrix.goos }}
          GOARCH: ${{ matrix.goarch }}
        run: |
          go build -ldflags="-s -w" -o crypto-kit-${{ matrix.goos }}-${{ matrix.goarch }}${{ matrix.goos == 'windows' && '.exe' || '' }} main.go

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: crypto-kit-${{ matrix.goos }}-${{ matrix.goarch }}
          path: crypto-kit-${{ matrix.goos }}-${{ matrix.goarch }}${{ matrix.goos == 'windows' && '.exe' || '' }}
```

### Release Automation

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v3
        with:
          go-version: 1.21

      - name: Build all platforms
        run: make cross-compile

      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

## 🔒 Security Considerations

### Build Security

- **Reproducible builds**: Use fixed Go version and dependencies
- **Supply chain security**: Verify all dependencies with checksums
- **Code signing**: Sign binaries with enterprise certificate
- **SBOM generation**: Create software bill of materials

### Deployment Security

- **Integrity verification**: Use SHA-256 checksums for all binaries
- **Secure distribution**: HTTPS-only download with certificate pinning
- **Privilege escalation**: Minimal required permissions for installation
- **Audit logging**: Log all deployment and configuration changes

---

**🔧 CryptoKit Build & Deployment Guide**

_From source to production in enterprise environments_

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Target Platforms**: Linux, macOS, Windows

**Contact**: devops@stealthguard.com  
**Build Support**: build-support@stealthguard.com
