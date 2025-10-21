#!/bin/bash

# Firefox macOS Hardening Script
# Part of OpSec-Harden Enterprise Security Toolkit

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*" >&2
}

log_info() { log "${GREEN}INFO${NC}" "$@"; }
log_warn() { log "${YELLOW}WARN${NC}" "$@"; }
log_error() { log "${RED}ERROR${NC}" "$@"; }

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    log_error "This script is for macOS only"
    exit 1
fi

# Parse configuration from environment variable
if [[ -z "${OPSEC_CONFIG:-}" ]]; then
    log_error "OPSEC_CONFIG environment variable not set"
    exit 1
fi

config="$OPSEC_CONFIG"
log_info "Applying Firefox hardening on macOS..."

# Firefox profile directory
FIREFOX_PROFILE_DIR="$HOME/Library/Application Support/Firefox/Profiles"
USER_JS_TEMPLATE="/tmp/user.js.$$"

# Check if Firefox is installed
if [[ ! -d "$FIREFOX_PROFILE_DIR" ]]; then
    log_error "Firefox not found. Please install Firefox first."
    exit 1
fi

# Stop Firefox if running
if pgrep -x "firefox" > /dev/null; then
    log_warn "Stopping Firefox..."
    pkill -x "firefox" || true
    sleep 3
fi

# Find default profile or create one
find_or_create_profile() {
    local profiles_ini="$HOME/Library/Application Support/Firefox/profiles.ini"
    local profile_path=""
    
    if [[ -f "$profiles_ini" ]]; then
        # Look for default profile
        profile_path=$(awk -F= '/^Path=/ {path=$2} /^Default=1/ && path {print path; exit}' "$profiles_ini" 2>/dev/null || true)
        
        if [[ -z "$profile_path" ]]; then
            # Get first profile if no default
            profile_path=$(awk -F= '/^Path=/ {print $2; exit}' "$profiles_ini" 2>/dev/null || true)
        fi
    fi
    
    if [[ -z "$profile_path" ]] || [[ ! -d "$FIREFOX_PROFILE_DIR/$profile_path" ]]; then
        log_info "Creating new Firefox profile..."
        # Create a new profile using Firefox
        /Applications/Firefox.app/Contents/MacOS/firefox -CreateProfile "opsec-hardened" -headless >/dev/null 2>&1 &
        local firefox_pid=$!
        sleep 5
        kill $firefox_pid 2>/dev/null || true
        wait $firefox_pid 2>/dev/null || true
        
        # Find the newly created profile
        if [[ -f "$profiles_ini" ]]; then
            profile_path=$(awk -F= '/^Path=/ {print $2}' "$profiles_ini" | tail -1)
        fi
    fi
    
    if [[ -z "$profile_path" ]]; then
        log_error "Could not find or create Firefox profile"
        exit 1
    fi
    
    echo "$FIREFOX_PROFILE_DIR/$profile_path"
}

PROFILE_PATH=$(find_or_create_profile)
log_info "Using profile: $PROFILE_PATH"

# Generate user.js from config
generate_user_js() {
    local config_json="$1"
    local output_file="$2"
    
    cat > "$output_file" << 'EOF'
// OpSec-Harden Firefox Configuration
// Auto-generated on macOS
// DO NOT EDIT MANUALLY

EOF
    
    # Parse JSON and generate user.js preferences
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)
prefs = config.get('prefs', {})
for key, value in prefs.items():
    if isinstance(value, bool):
        print(f'user_pref(\"{key}\", {str(value).lower()});')
    elif isinstance(value, (int, float)):
        print(f'user_pref(\"{key}\", {value});')
    elif isinstance(value, str):
        print(f'user_pref(\"{key}\", \"{value}\");')
" >> "$output_file"
    
    # Add DNS over HTTPS configuration
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)
dns = config.get('dns', {})
if dns.get('doh_enabled'):
    url = dns.get('url', '')
    fallback = dns.get('fallback', '')
    print(f'user_pref(\"network.trr.mode\", 2);')
    print(f'user_pref(\"network.trr.uri\", \"{url}\");')
    if fallback:
        print(f'user_pref(\"network.trr.fallback-resolver\", \"{fallback}\");')
    print('user_pref(\"network.trr.bootstrapAddress\", \"1.1.1.1\");')
    print('user_pref(\"network.dns.disableIPv6\", false);')
" >> "$output_file"
    
    # Add User-Agent override
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)
ua = config.get('user_agent', {})
if ua.get('enabled') and ua.get('value'):
    print(f'user_pref(\"general.useragent.override\", \"{ua[\"value\"]}\");')
" >> "$output_file"
    
    # Add proxy configuration
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)
proxy = config.get('proxy', {})
if proxy.get('enabled'):
    proxy_type = proxy.get('type', 'http')
    host = proxy.get('host', '')
    port = proxy.get('port', 0)
    
    if proxy_type == 'socks5':
        print(f'user_pref(\"network.proxy.type\", 1);')
        print(f'user_pref(\"network.proxy.socks\", \"{host}\");')
        print(f'user_pref(\"network.proxy.socks_port\", {port});')
        print(f'user_pref(\"network.proxy.socks_version\", 5);')
        if proxy.get('dns_over_proxy'):
            print('user_pref(\"network.proxy.socks_remote_dns\", true);')
    elif proxy_type == 'http':
        print(f'user_pref(\"network.proxy.type\", 1);')
        print(f'user_pref(\"network.proxy.http\", \"{host}\");')
        print(f'user_pref(\"network.proxy.http_port\", {port});')
        print(f'user_pref(\"network.proxy.ssl\", \"{host}\");')
        print(f'user_pref(\"network.proxy.ssl_port\", {port});')
else:
    print('user_pref(\"network.proxy.type\", 0);')
" >> "$output_file"
}

# Apply hardening configuration
apply_hardening() {
    local user_js_file="$PROFILE_PATH/user.js"
    
    log_info "Generating user.js configuration..."
    generate_user_js "$config" "$USER_JS_TEMPLATE"
    
    # Backup existing user.js if it exists
    if [[ -f "$user_js_file" ]]; then
        cp "$user_js_file" "$user_js_file.backup.$(date +%s)"
        log_info "Backed up existing user.js"
    fi
    
    # Install new user.js
    cp "$USER_JS_TEMPLATE" "$user_js_file"
    log_info "Installed hardened user.js configuration"
    
    # Set appropriate permissions
    chmod 644 "$user_js_file"
    
    # Clear existing cache and session data
    log_info "Clearing Firefox cache and session data..."
    rm -rf "$PROFILE_PATH/cache2" 2>/dev/null || true
    rm -rf "$PROFILE_PATH/startupCache" 2>/dev/null || true
    rm -rf "$PROFILE_PATH/sessionstore-backups" 2>/dev/null || true
    rm -f "$PROFILE_PATH/sessionstore.jsonlz4" 2>/dev/null || true
    rm -f "$PROFILE_PATH/recovery.jsonlz4" 2>/dev/null || true
    
    # Configure macOS-specific security settings
    configure_macos_security
}

# Configure macOS-specific security settings
configure_macos_security() {
    log_info "Applying macOS-specific security settings..."
    
    # Disable Firefox auto-update via macOS preferences
    defaults write org.mozilla.firefox SUEnableAutomaticChecks -bool false 2>/dev/null || true
    defaults write org.mozilla.firefox SUAutomaticallyUpdate -bool false 2>/dev/null || true
    
    # Configure quarantine settings
    xattr -d com.apple.quarantine "/Applications/Firefox.app" 2>/dev/null || true
    
    # Set Firefox as non-privileged app
    sudo -n spctl --add --label "Firefox" --requirement "identifier \"org.mozilla.firefox\"" 2>/dev/null || true
    
    log_info "macOS security settings applied"
}

# Install recommended extensions
install_extensions() {
    log_info "Extension installation requires manual intervention"
    log_info "Please install these recommended extensions manually:"
    
    echo "$config" | python3 -c "
import json, sys
config = json.load(sys.stdin)
extensions = config.get('extensions', {}).get('recommended', [])
for ext in extensions:
    print(f'  - {ext}')
"
}

# Configure Firefox policies (macOS)
configure_policies() {
    local policies_dir="/Applications/Firefox.app/Contents/Resources/distribution"
    local policies_file="$policies_dir/policies.json"
    
    log_info "Configuring Firefox enterprise policies..."
    
    # Create policies directory if it doesn't exist
    if [[ ! -d "$policies_dir" ]]; then
        sudo mkdir -p "$policies_dir" 2>/dev/null || {
            log_warn "Cannot create policies directory (requires admin privileges)"
            return 0
        }
    fi
    
    # Generate basic policies
    sudo tee "$policies_file" > /dev/null 2>&1 << 'EOF' || {
        log_warn "Cannot write policies file (requires admin privileges)"
        return 0
    }
{
  "policies": {
    "DisableAppUpdate": true,
    "DisableFirefoxStudies": true,
    "DisableTelemetry": true,
    "DisableFirefoxAccounts": true,
    "DisablePocket": true,
    "DisableFirefoxScreenshots": true,
    "DontCheckDefaultBrowser": true,
    "NoDefaultBookmarks": true,
    "DisableSecurityBypass": {
      "InvalidCertificate": true,
      "SafeBrowsing": true
    },
    "DisableSystemAddonUpdate": true,
    "ExtensionUpdate": false,
    "SecurityDevices": {},
    "Certificates": {
      "ImportEnterpriseRoots": false,
      "Install": []
    }
  }
}
EOF

    log_info "Firefox enterprise policies configured"
}

# Main execution
main() {
    log_info "Starting Firefox hardening process..."
    
    # Apply hardening configuration
    apply_hardening
    
    # Configure policies
    configure_policies
    
    # Show extension recommendations
    install_extensions
    
    # Cleanup
    rm -f "$USER_JS_TEMPLATE"
    
    log_info "✅ Firefox hardening completed successfully!"
    log_info "Please restart Firefox to apply all changes"
    log_info "Note: Some settings may require manual extension installation"
}

# Trap to cleanup on exit
trap 'rm -f "$USER_JS_TEMPLATE"' EXIT

# Run main function
main "$@"