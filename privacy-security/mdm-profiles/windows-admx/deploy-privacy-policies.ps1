# PowerShell Script for Privacy Policy Deployment
# Run as Administrator: Set-ExecutionPolicy Bypass -Scope Process; .\deploy-privacy-policies.ps1

param(
    [switch]$Chrome,
    [switch]$Firefox,
    [switch]$All,
    [switch]$Validate,
    [string]$ProxyUrl = "http://proxy.local/proxy.pac"
)

Write-Host "=== Privacy Policy Deployment Script ===" -ForegroundColor Green
Write-Host "Deploying browser privacy policies for Windows environment" -ForegroundColor Yellow

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Deploy-ChromePolicies {
    Write-Host "Deploying Chrome privacy policies..." -ForegroundColor Cyan
    
    $chromeRegPath = "HKLM:\SOFTWARE\Policies\Google\Chrome"
    
    # Create Chrome policy registry structure
    if (-not (Test-Path $chromeRegPath)) {
        New-Item -Path $chromeRegPath -Force | Out-Null
    }
    
    # Core privacy settings
    Set-ItemProperty -Path $chromeRegPath -Name "DnsOverHttpsMode" -Value "secure" -Type String
    Set-ItemProperty -Path $chromeRegPath -Name "DnsOverHttpsTemplates" -Value "https://dns.quad9.net/dns-query" -Type String
    Set-ItemProperty -Path $chromeRegPath -Name "BrowserSignin" -Value 0 -Type DWORD
    Set-ItemProperty -Path $chromeRegPath -Name "MetricsReportingEnabled" -Value 0 -Type DWORD
    Set-ItemProperty -Path $chromeRegPath -Name "WebRtcIPHandlingPolicy" -Value "DisableNonProxiedUdp" -Type String
    Set-ItemProperty -Path $chromeRegPath -Name "WebRtcUdpPortRange" -Value "0-0" -Type String
    Set-ItemProperty -Path $chromeRegPath -Name "AcceptLanguages" -Value "en-US,en" -Type String
    Set-ItemProperty -Path $chromeRegPath -Name "UserAgentReduction" -Value 1 -Type DWORD
    Set-ItemProperty -Path $chromeRegPath -Name "BlockThirdPartyCookies" -Value 1 -Type DWORD
    Set-ItemProperty -Path $chromeRegPath -Name "DefaultGeolocationSetting" -Value 2 -Type DWORD
    Set-ItemProperty -Path $chromeRegPath -Name "AudioCaptureAllowed" -Value 0 -Type DWORD
    Set-ItemProperty -Path $chromeRegPath -Name "VideoCaptureAllowed" -Value 0 -Type DWORD
    
    # Proxy settings
    $proxyPath = "$chromeRegPath\ProxySettings"
    if (-not (Test-Path $proxyPath)) {
        New-Item -Path $proxyPath -Force | Out-Null
    }
    Set-ItemProperty -Path $proxyPath -Name "ProxyMode" -Value "pac_script" -Type String
    Set-ItemProperty -Path $proxyPath -Name "ProxyPacUrl" -Value $ProxyUrl -Type String
    
    # Homepage settings
    Set-ItemProperty -Path $chromeRegPath -Name "HomepageLocation" -Value "about:blank" -Type String
    Set-ItemProperty -Path $chromeRegPath -Name "NewTabPageLocation" -Value "about:blank" -Type String
    
    Write-Host "Chrome policies deployed successfully" -ForegroundColor Green
}

function Deploy-FirefoxPolicies {
    Write-Host "Deploying Firefox privacy policies..." -ForegroundColor Cyan
    
    $firefoxPath = "${env:ProgramFiles}\Mozilla Firefox\distribution"
    
    if (-not (Test-Path $firefoxPath)) {
        Write-Warning "Firefox installation not found. Creating directory..."
        New-Item -Path $firefoxPath -ItemType Directory -Force | Out-Null
    }
    
    $policiesJson = @{
        policies = @{
            DisableTelemetry = $true
            AppAutoUpdate = $false
            DNSOverHTTPS = @{
                Enabled = $true
                ProviderURL = "https://dns.quad9.net/dns-query"
                Locked = $true
            }
            Preferences = @{
                "privacy.resistFingerprinting" = @{ Value = $true; Status = "locked" }
                "intl.accept_languages" = @{ Value = "en-US, en"; Status = "locked" }
                "general.useragent.override" = @{ Value = ""; Status = "locked" }
                "media.peerconnection.enabled" = @{ Value = $false; Status = "locked" }
                "network.trr.mode" = @{ Value = 3; Status = "locked" }
                "network.proxy.autoconfig_url" = @{ Value = $ProxyUrl; Status = "locked" }
                "network.proxy.type" = @{ Value = 2; Status = "locked" }
                "privacy.trackingprotection.enabled" = @{ Value = $true; Status = "locked" }
                "geo.enabled" = @{ Value = $false; Status = "locked" }
                "media.navigator.enabled" = @{ Value = $false; Status = "locked" }
                "toolkit.telemetry.enabled" = @{ Value = $false; Status = "locked" }
                "datareporting.healthreport.uploadEnabled" = @{ Value = $false; Status = "locked" }
            }
        }
    }
    
    $jsonContent = $policiesJson | ConvertTo-Json -Depth 10
    $policiesFile = "$firefoxPath\policies.json"
    
    $jsonContent | Out-File -FilePath $policiesFile -Encoding UTF8 -Force
    
    Write-Host "Firefox policies deployed successfully" -ForegroundColor Green
}

function Validate-Deployment {
    Write-Host "Validating privacy policy deployment..." -ForegroundColor Cyan
    
    $validation = @{
        Chrome = @{
            DoH = $false
            Proxy = $false
            WebRTC = $false
            Language = $false
        }
        Firefox = @{
            PolicyFile = $false
        }
    }
    
    # Validate Chrome
    $chromeRegPath = "HKLM:\SOFTWARE\Policies\Google\Chrome"
    if (Test-Path $chromeRegPath) {
        try {
            $dohMode = Get-ItemProperty -Path $chromeRegPath -Name "DnsOverHttpsMode" -ErrorAction SilentlyContinue
            $validation.Chrome.DoH = ($dohMode.DnsOverHttpsMode -eq "secure")
            
            $proxyMode = Get-ItemProperty -Path "$chromeRegPath\ProxySettings" -Name "ProxyMode" -ErrorAction SilentlyContinue
            $validation.Chrome.Proxy = ($proxyMode.ProxyMode -eq "pac_script")
            
            $webrtc = Get-ItemProperty -Path $chromeRegPath -Name "WebRtcIPHandlingPolicy" -ErrorAction SilentlyContinue
            $validation.Chrome.WebRTC = ($webrtc.WebRtcIPHandlingPolicy -eq "DisableNonProxiedUdp")
            
            $lang = Get-ItemProperty -Path $chromeRegPath -Name "AcceptLanguages" -ErrorAction SilentlyContinue
            $validation.Chrome.Language = ($lang.AcceptLanguages -eq "en-US,en")
        }
        catch {
            Write-Warning "Error validating Chrome policies: $($_.Exception.Message)"
        }
    }
    
    # Validate Firefox
    $firefoxPoliciesFile = "${env:ProgramFiles}\Mozilla Firefox\distribution\policies.json"
    $validation.Firefox.PolicyFile = Test-Path $firefoxPoliciesFile
    
    # Display results
    Write-Host "`n=== Validation Results ===" -ForegroundColor Yellow
    Write-Host "Chrome DoH: $(if($validation.Chrome.DoH){'✓ PASS'}else{'✗ FAIL'})" -ForegroundColor $(if($validation.Chrome.DoH){'Green'}else{'Red'})
    Write-Host "Chrome Proxy: $(if($validation.Chrome.Proxy){'✓ PASS'}else{'✗ FAIL'})" -ForegroundColor $(if($validation.Chrome.Proxy){'Green'}else{'Red'})
    Write-Host "Chrome WebRTC: $(if($validation.Chrome.WebRTC){'✓ PASS'}else{'✗ FAIL'})" -ForegroundColor $(if($validation.Chrome.WebRTC){'Green'}else{'Red'})
    Write-Host "Chrome Language: $(if($validation.Chrome.Language){'✓ PASS'}else{'✗ FAIL'})" -ForegroundColor $(if($validation.Chrome.Language){'Green'}else{'Red'})
    Write-Host "Firefox Policies: $(if($validation.Firefox.PolicyFile){'✓ PASS'}else{'✗ FAIL'})" -ForegroundColor $(if($validation.Firefox.PolicyFile){'Green'}else{'Red'})
    
    return $validation
}

function Test-ProxyConnectivity {
    param([string]$ProxyPacUrl)
    
    Write-Host "Testing proxy PAC connectivity..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri $ProxyPacUrl -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Proxy PAC file accessible" -ForegroundColor Green
            
            # Basic PAC file validation
            if ($response.Content -match "FindProxyForURL") {
                Write-Host "✓ PAC file contains FindProxyForURL function" -ForegroundColor Green
            } else {
                Write-Warning "PAC file may be malformed - no FindProxyForURL function found"
            }
        }
    }
    catch {
        Write-Error "✗ Failed to access proxy PAC file: $($_.Exception.Message)"
    }
}

# Main execution
if (-not (Test-AdminRights)) {
    Write-Error "This script requires administrator privileges. Please run as administrator."
    exit 1
}

Write-Host "Proxy PAC URL: $ProxyUrl" -ForegroundColor Magenta

if ($Validate) {
    Validate-Deployment
    Test-ProxyConnectivity -ProxyPacUrl $ProxyUrl
}
elseif ($Chrome) {
    Deploy-ChromePolicies
    Write-Host "Chrome deployment completed. Restart Chrome to apply changes." -ForegroundColor Yellow
}
elseif ($Firefox) {
    Deploy-FirefoxPolicies  
    Write-Host "Firefox deployment completed. Restart Firefox to apply changes." -ForegroundColor Yellow
}
elseif ($All) {
    Deploy-ChromePolicies
    Deploy-FirefoxPolicies
    Write-Host "All browser policies deployed. Restart browsers to apply changes." -ForegroundColor Yellow
    
    # Auto-validate after deployment
    Start-Sleep -Seconds 2
    Validate-Deployment | Out-Null
    Test-ProxyConnectivity -ProxyPacUrl $ProxyUrl
}
else {
    Write-Host "Usage: .\deploy-privacy-policies.ps1 [-Chrome] [-Firefox] [-All] [-Validate] [-ProxyUrl <url>]" -ForegroundColor Yellow
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\deploy-privacy-policies.ps1 -All" -ForegroundColor White
    Write-Host "  .\deploy-privacy-policies.ps1 -Chrome -ProxyUrl 'http://corporate.proxy:8080/proxy.pac'" -ForegroundColor White
    Write-Host "  .\deploy-privacy-policies.ps1 -Validate" -ForegroundColor White
}

Write-Host "`nPrivacy policy deployment script completed." -ForegroundColor Green