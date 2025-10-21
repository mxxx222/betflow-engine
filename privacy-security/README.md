# 🛡️ Privacy & Security Rollout Package

**Kompakti "valmis-nyt" paketti metadata-vuotojen minimointiin**

> Minimoi UA-/kieli-/aikavyöhyke- ja verkkometadatan vuodot heterogeenisessä (Win/macOS/iOS/Android) ympäristössä. Kaikki on offline-rollout-kelpoista ilman lisäselvityksiä.

---

## 🎯 Tavoitteet

- **🌍 Yhtenäinen UA-string**: Reduced User-Agent kaikilla alustoilla
- **🗣️ Kieli normalisoitu**: en-US kaikkialla
- **⏰ Aikavyöhyke**: UTC (Firefox RFP) / kontrolloitu (Chrome)
- **🌐 WebRTC-suojaus**: Ei IP-vuotoja, UDP estetty
- **🔒 DoH pakotettu**: Quad9 DNS-over-HTTPS
- **📡 Telemetry OFF**: Ei seurantaa

---

## 📁 Pakettirakenne

```
privacy-security/
├── 📄 README.md                    # Tämä dokumentti
├── 📁 browser-policies/            # Selaimen hallintapolitiikat
│   ├── firefox-esr-policies.json
│   └── chrome-policies.json
├── 📁 proxy-configs/               # Proxy ja verkko
│   ├── proxy.pac
│   └── nginx-privacy.conf
├── 📁 mdm-profiles/                # Mobile Device Management
│   ├── windows-admx/
│   ├── macos-ios-profiles/
│   └── android-enterprise/
├── 📁 validation/                  # Testaus ja validointi
│   └── privacy-check.py
└── 📄 ROLLOUT-CHECKLIST.md        # Kenttäoperaatio ohjeistus
```

---

## 🚀 Pikaohje (30 sekuntia)

### 1. Proxy ensin

```bash
# Julkaise proxy.pac
sudo cp proxy-configs/proxy.pac /var/www/html/
curl http://proxy.local/proxy.pac  # Testaa saavutettavuus
```

### 2. Firefox ESR

```bash
# Windows
copy browser-policies/firefox-esr-policies.json "C:\Program Files\Mozilla Firefox\distribution\policies.json"

# macOS
sudo cp browser-policies/firefox-esr-policies.json "/Applications/Firefox.app/Contents/Resources/distribution/policies.json"
```

### 3. Chrome/Chromium

```bash
# Ota käyttöön browser-policies/chrome-policies.json
# Windows: GPO / Registry
# macOS: Managed Preferences
# Linux: /etc/chromium/policies/managed/
```

### 4. Validoi

```bash
python validation/privacy-check.py
# Testaa: browserleaks.com/webrtc, deviceinfo.me
```

---

## 🔧 Tekniset detaljit

### Firefox ESR - Resistance Fingerprinting (RFP)

- **privacy.resistFingerprinting=true** → yhtenäistää UA, kieli, TZ=UTC
- **DoH pakotettu** → Quad9 (network.trr.mode=3)
- **WebRTC estetty** → media.peerconnection.enabled=false
- **Proxy PAC pakotettu** → network.proxy.type=2

### Chromium/Chrome - Policy Based

- **UserAgentReduction=true** → supistaa UA-kentä
- **DnsOverHttpsMode=secure** → DoH pakollinen
- **WebRtcIPHandlingPolicy** → EstäUDP-vuodot
- **ProxySettings** → PAC-pakko

### Proxy PAC Logic

```javascript
function FindProxyForURL(url, host) {
  // Sisäverkot suoraan
  if (isPlainHostName(host) || shExpMatch(host, "*.local")) return "DIRECT";
  // Muu liikenne proxyn kautta
  return "PROXY proxy.local:3128";
}
```

---

## 📱 Mobile Support

### Android

- **Firefox/Mull**: about:config tai Enterprise policies
- **Cromite/Brave**: DoH + WebRTC "proxy only"

### iOS

- **Configuration Profiles**: DoH (Quad9) + Safari (kieli en-US)
- **Firefox Focus**: "Send usage data" OFF, "Block WebRTC" ON

---

## ✅ Rollout Checklist

### Pre-deployment

- [ ] **Proxy PAC** saavutettavissa: `curl http://proxy.local/proxy.pac`
- [ ] **Policies** valmiina: Firefox (distribution/) + Chrome (managed/)
- [ ] **Mobile profiles** jaettavissa (MDM/Configurator)

### Deployment

- [ ] **Desktop policies** aktivoitu ja testattu
- [ ] **Mobile profiles** asennettu ja vahvistettu
- [ ] **Proxy reitit** toimivat (sisäverkot DIRECT, ulkoverkot PROXY)

### Validation

- [ ] **DoH toimii**: https://1.1.1.1/help → DoH=Yes
- [ ] **UA yhtenäinen**: deviceinfo.me → Reduced UA
- [ ] **Kieli normalisoitu**: Accept-Language=en-US
- [ ] **WebRTC estetty**: browserleaks.com/webrtc → Ei paikallisia IP:itä
- [ ] **Aikavyöhyke**: Firefox → UTC, Chrome → dokumentoitu poikkeama
- [ ] **Telemetry OFF**: Ei seurantayhteyksiä

### Post-deployment

- [ ] **Regressio-testit**: Sisäiset sovellukset toimivat
- [ ] **Poikkeuslistat**: Intranet + videoneuvottelu-URL:t
- [ ] **Audit-lokit**: Ennen/jälkeen kuvakaappaukset
- [ ] **Versionumerot**: Dokumentoitu ja arkistoitu

---

## ⚠️ Huomioitavat poikkeamat

### Aikavyöhyke-käsittely

- **✅ Firefox ESR (RFP)**: Spoilaa TZ → UTC (paras suoja)
- **⚠️ Chromium**: Ei luotettavaa cross-OS TZ-spooffia
  - **Suositus**: Firefox ESR kriittisiin työtehtäviin
  - **Chromium**: Vain proxyn takaa (UA+kieli normalisoitu, WebRTC UDP OFF)

### WebRTC Enterprise-käyttö

Jos videoneuvottelua tarvitaan:

```javascript
// proxy.pac - videoneuvottelu poikkeukset
if (shExpMatch(host, "*teams.microsoft.com") || shExpMatch(host, "*zoom.us")) {
  return "DIRECT"; // WebRTC suora yhteys
}
```

### Sisäverkon sovellukset

Testaa erityisesti:

- SharePoint / Office 365
- Sisäiset web-sovellukset
- SSO/SAML-kirjautuminen
- Printtisivut ja tiedostolataukset

---

## 🔍 Validointi & Testaus

### Automaattinen tarkistus

```bash
# Aja privacy-check.py
python validation/privacy-check.py --full

# Odotettavat tulokset:
# ✅ DoH: Quad9
# ✅ UA: Reduced/Consistent
# ✅ Lang: en-US
# ✅ WebRTC: Blocked/Proxied
# ✅ TZ: UTC (Firefox) / Controlled (Chrome)
```

### Manuaaliset testisivut

1. **https://browserleaks.com/webrtc** → Ei paikallisia IP:itä
2. **https://deviceinfo.me** → UA reduced, Accept-Language en-US
3. **https://1.1.1.1/help** → DoH enabled
4. **about:networking#dns** (Firefox) → TRR-only
5. **chrome://net-internals/#dns** (Chrome) → DoH active

---

## 📞 Tuki & Ongelmatilanteet

### Yleisimmät ongelmat

**Proxy PAC ei toimi**

```bash
# Tarkista saavutettavuus
curl -v http://proxy.local/proxy.pac
# Tarkista syntax
spidermonkey proxy.pac  # tai node proxy-pac-test.js
```

**Firefox policies ei aktivoidu**

```bash
# Tarkista polku ja oikeudet
ls -la "/Applications/Firefox.app/Contents/Resources/distribution/"
# Restart Firefox kokonaan
```

**Chrome policies ei toimi**

```bash
# Chrome://policy tarkistus
# Windows: gpedit.msc → Computer Config → Admin Templates → Google Chrome
# macOS: sudo profiles show -type configuration
```

**DoH ei aktivoidu**

- Varmista että proxy sallii 443/tcp → dns.quad9.net
- Testaa TRR-bypass: Firefox about:config → network.trr.bootstrapAddr

---

**Yhteenveto**: Tämä paketti tarjoaa production-ready privacy-suojauksen joka toimii offline ja scales yrityskäyttöön. Kaikki konfiguraatiot on testattu Windows 10/11, macOS 12+, iOS 15+ ja Android 10+ ympäristöissä.

**Päivitetty**: 24. syyskuuta 2025  
**Versio**: 1.0.0  
**Tila**: 🟢 Production Ready
