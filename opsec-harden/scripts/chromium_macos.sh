#!/bin/bash

# Chromium macOS Hardening Script
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
log_info "Applying Chromium hardening on macOS..."

# Chromium directories
CHROMIUM_APP="/Applications/Chromium.app"
CHROMIUM_PROFILE_DIR="$HOME/Library/Application Support/Chromium"
CHROMIUM_POLICIES_DIR="/Library/Managed Preferences"

# Check if Chromium is installed
if [[ ! -d "$CHROMIUM_APP" ]]; then
    log_error "Chromium not found. Please install Chromium first."
    exit 1
fi

# Stop Chromium if running
if pgrep -f "Chromium" > /dev/null; then
    log_warn "Stopping Chromium..."
    pkill -f "Chromium" || true
    sleep 3
fi

# Create profile directory if it doesn't exist
mkdir -p "$CHROMIUM_PROFILE_DIR/Default"

# Generate managed policies from config
generate_policies() {
    local config_json="$1"
    local output_file="$2"
    
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)
policies = config.get('policies', {})

# Base policy structure
managed_config = {
    'ExtensionInstallBlacklist': policies.get('ExtensionInstallBlacklist', []),
    'ExtensionInstallWhitelist': policies.get('ExtensionInstallWhitelist', []),
    'BrowserSignin': policies.get('BrowserSignin', 0),
    'SyncDisabled': policies.get('SyncDisabled', True),
    'PasswordManagerEnabled': policies.get('PasswordManagerEnabled', False),
    'AutofillAddressEnabled': policies.get('AutofillAddressEnabled', False),
    'AutofillCreditCardEnabled': policies.get('AutofillCreditCardEnabled', False),
    'SafeBrowsingEnabled': policies.get('SafeBrowsingEnabled', True),
    'MetricsReportingEnabled': policies.get('MetricsReportingEnabled', False),
    'SearchSuggestEnabled': policies.get('SearchSuggestEnabled', False),
    'NetworkPredictionOptions': policies.get('NetworkPredictionOptions', 2),
    'DefaultGeolocationSetting': policies.get('DefaultGeolocationSetting', 2),
    'DefaultNotificationsSetting': policies.get('DefaultNotificationsSetting', 2),
    'DefaultMediaStreamSetting': policies.get('DefaultMediaStreamSetting', 2),
    'BlockThirdPartyCookies': policies.get('BlockThirdPartyCookies', True),
    'HomepageLocation': policies.get('HomepageLocation', 'about:blank'),
    'RestoreOnStartup': policies.get('RestoreOnStartup', 5),
    'RestoreOnStartupURLs': policies.get('RestoreOnStartupURLs', ['about:blank']),
    'TranslateEnabled': policies.get('TranslateEnabled', False),
    'SpellCheckServiceEnabled': policies.get('SpellCheckServiceEnabled', False),
    'DeveloperToolsAvailability': policies.get('DeveloperToolsAvailability', 2),
    'ComponentUpdatesEnabled': policies.get('ComponentUpdatesEnabled', False)
}

print(json.dumps(managed_config, indent=2))
" > "$output_file"
}

# Generate Chromium preferences
generate_preferences() {
    local config_json="$1"
    local output_file="$2"
    
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)

# Base preferences structure
prefs = {
    'profile': {
        'default_content_setting_values': {
            'geolocation': 2,
            'notifications': 2,
            'media_stream': 2,
            'media_stream_mic': 2,
            'media_stream_camera': 2,
            'plugins': 2,
            'popups': 2,
            'automatic_downloads': 2,
            'mixed_script': 2
        },
        'content_settings': {
            'exceptions': {
                'plugins': {},
                'popups': {},
                'geolocation': {},
                'notifications': {},
                'media_stream': {}
            }
        },
        'password_manager_enabled': False,
        'managed_user_id': ''
    },
    'sync': {
        'suppress_start': True
    },
    'browser': {
        'check_default_browser': False,
        'show_home_button': False
    },
    'bookmark_bar': {
        'show_on_all_tabs': False
    },
    'net': {
        'network_prediction_options': 2
    },
    'search': {
        'suggest_enabled': False
    },
    'alternate_error_pages': {
        'enabled': False
    },
    'safebrowsing': {
        'enabled': True,
        'extended_reporting_enabled': False
    },
    'spellcheck': {
        'dictionaries': [],
        'dictionary': '',
        'use_spelling_service': False
    },
    'translate': {
        'enabled': False
    },
    'extensions': {
        'alerts': {
            'initialized': True
        },
        'chrome_url_overrides': {},
        'commands': {},
        'external_uninstall_url': '',
        'install_deny_list': ['*'],
        'install_allow_list': []
    }
}

# Add DNS over HTTPS configuration
dns = config.get('dns', {})
if dns.get('doh_enabled'):
    servers = dns.get('servers', [])
    prefs['dns_over_https'] = {
        'mode': 'secure',
        'templates': servers
    }

# Add user agent override
ua = config.get('user_agent', {})
if ua.get('enabled') and ua.get('value'):
    prefs['profile']['user_agent'] = ua['value']

print(json.dumps(prefs, indent=2))
" > "$output_file"
}

# Generate command line flags
generate_flags() {
    local config_json="$1"
    local output_file="$2"
    
    echo "$config_json" | python3 -c "
import json, sys
config = json.load(sys.stdin)
flags = config.get('flags', {})

flag_list = []
for flag, value in flags.items():
    if isinstance(value, bool):
        if value:
            flag_list.append(f'--{flag}')
    else:
        flag_list.append(f'--{flag}={value}')

# Add DNS over HTTPS flags
dns = config.get('dns', {})
if dns.get('doh_enabled'):
    servers = dns.get('servers', [])
    if servers:
        flag_list.append(f'--enable-features=DnsOverHttps')
        flag_list.append(f'--dns-over-https-servers={servers[0]}')

print(' '.join(flag_list))
" > "$output_file"
}

# Apply hardening configuration
apply_hardening() {
    local preferences_file="$CHROMIUM_PROFILE_DIR/Default/Preferences"
    local flags_file="$CHROMIUM_PROFILE_DIR/chrome_flags"
    local policies_file="/tmp/chromium_policies.json"
    
    log_info "Generating Chromium configuration..."
    
    # Generate preferences
    generate_preferences "$config" "$preferences_file.new"
    
    # Backup existing preferences
    if [[ -f "$preferences_file" ]]; then
        cp "$preferences_file" "$preferences_file.backup.$(date +%s)"
        log_info "Backed up existing preferences"
    fi
    
    # Install new preferences
    mv "$preferences_file.new" "$preferences_file"
    chmod 644 "$preferences_file"
    log_info "Installed hardened preferences"
    
    # Generate command line flags
    generate_flags "$config" "$flags_file"
    log_info "Generated command line flags"
    
    # Generate policies for enterprise deployment
    generate_policies "$config" "$policies_file"
    log_info "Generated enterprise policies"
    
    # Clear cache and session data
    log_info "Clearing Chromium cache and session data..."
    rm -rf "$CHROMIUM_PROFILE_DIR/Default/Cache" 2>/dev/null || true
    rm -rf "$CHROMIUM_PROFILE_DIR/Default/Code Cache" 2>/dev/null || true
    rm -rf "$CHROMIUM_PROFILE_DIR/Default/GPUCache" 2>/dev/null || true
    rm -rf "$CHROMIUM_PROFILE_DIR/Default/Service Worker" 2>/dev/null || true
    rm -rf "$CHROMIUM_PROFILE_DIR/Default/Session Storage" 2>/dev/null || true
    rm -rf "$CHROMIUM_PROFILE_DIR/ShaderCache" 2>/dev/null || true
    
    # Configure macOS-specific security
    configure_macos_security "$policies_file"
}

# Configure macOS-specific security settings
configure_macos_security() {
    local policies_file="$1"
    
    log_info "Applying macOS-specific security settings..."
    
    # Install managed policies (requires admin)
    local managed_policies="$CHROMIUM_POLICIES_DIR/org.chromium.Chromium.plist"
    
    if sudo -n true 2>/dev/null; then
        log_info "Installing managed policies (requires admin privileges)..."
        
        # Convert JSON to plist and install
        python3 -c "
import json, plistlib, sys
with open('$policies_file') as f:
    policies = json.load(f)
with open('/tmp/chromium_managed.plist', 'wb') as f:
    plistlib.dump(policies, f)
" 2>/dev/null || log_warn "Could not convert policies to plist format"
        
        sudo cp "/tmp/chromium_managed.plist" "$managed_policies" 2>/dev/null || {
            log_warn "Could not install managed policies (requires admin privileges)"
        }
        
        # Set proper permissions
        sudo chmod 644 "$managed_policies" 2>/dev/null || true
        
        # Clean up
        rm -f "/tmp/chromium_managed.plist"
        
    else
        log_warn "Admin privileges not available - managed policies not installed"
        log_info "To install enterprise policies manually:"
        log_info "1. Run: sudo mkdir -p '$CHROMIUM_POLICIES_DIR'"
        log_info "2. Convert policies JSON to plist and place in: $managed_policies"
    fi
    
    # Disable Chromium auto-update
    defaults write org.chromium.Chromium SUEnableAutomaticChecks -bool false 2>/dev/null || true
    defaults write org.chromium.Chromium SUAutomaticallyUpdate -bool false 2>/dev/null || true
    
    # Configure quarantine settings
    xattr -d com.apple.quarantine "$CHROMIUM_APP" 2>/dev/null || true
    
    log_info "macOS security settings applied"
}

# Install recommended extensions
install_extensions() {
    log_info "Recommended extensions (install manually):"
    
    echo "$config" | python3 -c "
import json, sys
config = json.load(sys.stdin)
extensions = config.get('extensions', {}).get('required', [])
for ext in extensions:
    print(f'  - {ext[\"name\"]} (ID: {ext[\"id\"]})')
    print(f'    chrome-extension://{ext[\"id\"]}/')
"
}

# Create launcher script with flags
create_launcher() {
    local launcher_script="$HOME/bin/chromium-hardened"
    local flags_file="$CHROMIUM_PROFILE_DIR/chrome_flags"
    
    log_info "Creating hardened Chromium launcher..."
    
    # Create bin directory if it doesn't exist
    mkdir -p "$HOME/bin"
    
    # Read flags
    local flags=""
    if [[ -f "$flags_file" ]]; then
        flags=$(cat "$flags_file")
    fi
    
    # Create launcher script
    cat > "$launcher_script" << EOF
#!/bin/bash
# OpSec-Harden Chromium Launcher
# Auto-generated - DO NOT EDIT MANUALLY

exec "$CHROMIUM_APP/Contents/MacOS/Chromium" $flags "\$@"
EOF
    
    chmod +x "$launcher_script"
    log_info "Launcher created: $launcher_script"
    log_info "Use this launcher to start hardened Chromium"
}

# Main execution
main() {
    log_info "Starting Chromium hardening process..."
    
    # Apply hardening configuration
    apply_hardening
    
    # Create launcher script
    create_launcher
    
    # Show extension recommendations
    install_extensions
    
    log_info "✅ Chromium hardening completed successfully!"
    log_info "Use the hardened launcher: $HOME/bin/chromium-hardened"
    log_info "Or start normally - hardened preferences will be applied"
    log_info "Note: Some enterprise policies require admin privileges"
}

# Run main function
main "$@"