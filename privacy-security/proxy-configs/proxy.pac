// Proxy Auto-Configuration (PAC) Script
// Minimizes network metadata leaks in heterogeneous environments
// Version: 1.0.0 - Production Ready

function FindProxyForURL(url, host) {
    // Convert host to lowercase for consistent matching
    var lhost = host.toLowerCase();
    
    // === DIRECT ACCESS RULES ===
    
    // Local development and testing
    if (isPlainHostName(lhost) || 
        shExpMatch(lhost, "*.local") ||
        shExpMatch(lhost, "localhost*") ||
        shExpMatch(lhost, "127.*") ||
        shExpMatch(lhost, "10.*") ||
        shExpMatch(lhost, "172.16.*") ||
        shExpMatch(lhost, "172.17.*") ||
        shExpMatch(lhost, "172.18.*") ||
        shExpMatch(lhost, "172.19.*") ||
        shExpMatch(lhost, "172.20.*") ||
        shExpMatch(lhost, "172.21.*") ||
        shExpMatch(lhost, "172.22.*") ||
        shExpMatch(lhost, "172.23.*") ||
        shExpMatch(lhost, "172.24.*") ||
        shExpMatch(lhost, "172.25.*") ||
        shExpMatch(lhost, "172.26.*") ||
        shExpMatch(lhost, "172.27.*") ||
        shExpMatch(lhost, "172.28.*") ||
        shExpMatch(lhost, "172.29.*") ||
        shExpMatch(lhost, "172.30.*") ||
        shExpMatch(lhost, "172.31.*") ||
        shExpMatch(lhost, "192.168.*")) {
        return "DIRECT";
    }
    
    // Internal corporate domains
    if (shExpMatch(lhost, "*.corp") ||
        shExpMatch(lhost, "*.internal") ||
        shExpMatch(lhost, "*.intranet") ||
        shExpMatch(lhost, "*.company.com") ||
        shExpMatch(lhost, "*.organization.fi")) {
        return "DIRECT";
    }
    
    // === VIDEO CONFERENCING EXCEPTIONS ===
    // These services require direct WebRTC connections
    
    if (shExpMatch(lhost, "*teams.microsoft.com") ||
        shExpMatch(lhost, "*teams.microsoftonline.com") ||
        shExpMatch(lhost, "*skype.com") ||
        shExpMatch(lhost, "*zoom.us") ||
        shExpMatch(lhost, "*zoom.com") ||
        shExpMatch(lhost, "*zoomgov.com") ||
        shExpMatch(lhost, "*webex.com") ||
        shExpMatch(lhost, "*gotomeeting.com") ||
        shExpMatch(lhost, "*google.com") && url.indexOf("meet.google.com") !== -1) {
        return "DIRECT";
    }
    
    // === CRITICAL SERVICES ===
    // Services that may break with proxy interference
    
    // Certificate validation and security services
    if (shExpMatch(lhost, "*ocsp.*") ||
        shExpMatch(lhost, "*crl.*") ||
        shExpMatch(lhost, "*pki.*") ||
        shExpMatch(lhost, "*.verisign.*") ||
        shExpMatch(lhost, "*.digicert.*") ||
        shExpMatch(lhost, "*.globalsign.*")) {
        return "DIRECT";
    }
    
    // Microsoft Office 365 / Azure AD critical endpoints
    if (shExpMatch(lhost, "*login.microsoft.com") ||
        shExpMatch(lhost, "*login.microsoftonline.com") ||
        shExpMatch(lhost, "*graph.microsoft.com") ||
        shExpMatch(lhost, "*outlook.office365.com")) {
        return "DIRECT";
    }
    
    // === TIME SENSITIVE SERVICES ===
    // NTP and time synchronization
    if (shExpMatch(lhost, "*ntp.*") ||
        shExpMatch(lhost, "*time.*") ||
        url.indexOf(":123") !== -1) {
        return "DIRECT";
    }
    
    // === PROXY BYPASS FOR SPECIFIC PROTOCOLS ===
    
    // FTP traffic (if needed)
    if (url.substring(0, 4) === "ftp:") {
        return "DIRECT";
    }
    
    // === DEFAULT: PROXY ALL OTHER TRAFFIC ===
    
    // Primary proxy with fallback
    return "PROXY proxy.local:3128; PROXY proxy-backup.local:3128; DIRECT";
}

// === UTILITY FUNCTIONS ===

// Helper function for IP range checking
function isInNet(host, pattern, mask) {
    var hostIP = dnsResolve(host);
    if (!hostIP) return false;
    return isInNetEx(hostIP, pattern + "/" + mask);
}

// Debug logging (disable in production)
function debug(message) {
    // Uncomment for debugging:
    // console.log("[PAC DEBUG] " + message);
}

// Usage examples and testing:
// FindProxyForURL("http://google.com", "google.com")         → PROXY
// FindProxyForURL("http://intranet.corp", "intranet.corp")   → DIRECT  
// FindProxyForURL("https://teams.microsoft.com", "teams.microsoft.com") → DIRECT