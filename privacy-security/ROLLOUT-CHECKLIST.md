# 📋 Privacy & Security Rollout Checklist

**Kenttäoperaatio-ohjeistus metadata-vuotojen minimointiin**

---

## 🎯 Rollout-vaiheet

### Vaihe 1: Esivalmistelu (Pre-deployment)

#### Infrastructure Readiness

- [ ] **Proxy PAC saavutettavissa**: `curl http://proxy.local/proxy.pac`

  - [ ] PAC-tiedosto sisältää `FindProxyForURL`-funktion
  - [ ] Sisäverkkoreititys toimii (_.local, _.corp → DIRECT)
  - [ ] Ulkoliikenne ohjautuu proxyn kautta
  - [ ] Backup proxy määritetty (`proxy-backup.local`)

- [ ] **DNS infrastruktuuri**:

  - [ ] Quad9 DoH-endpoint tavoitettavissa: `https://dns.quad9.net/dns-query`
  - [ ] Bootstrap DNS toimii: `9.9.9.9`
  - [ ] Firewall sallii 443/tcp → dns.quad9.net

- [ ] **Browser policy files valmiina**:
  - [ ] Firefox: `policies.json` generoitu
  - [ ] Chrome: Policy JSON/Registry valmiina
  - [ ] Mobile profiles luotu (.mobileconfig, .json)

#### Environment Testing

- [ ] **Testiympäristö validoitu**:
  - [ ] Privacy-check.py ajettu testiympäristössä
  - [ ] Kaikki kriittiset kontrollit toimivat
  - [ ] Regressio-testit suoritettu

---

### Vaihe 2: Deployment

#### Desktop Browsers

- [ ] **Firefox ESR deployment**:

  ```bash
  # Windows
  copy policies.json "C:\Program Files\Mozilla Firefox\distribution\"

  # macOS
  sudo cp policies.json "/Applications/Firefox.app/Contents/Resources/distribution/"

  # Linux
  sudo cp policies.json "/usr/lib/firefox/distribution/"
  ```

  - [ ] Policy-tiedosto paikallaan ja oikeudet oikein
  - [ ] Firefox restart tehty
  - [ ] `about:policies` näyttää aktivoidut käytännöt

- [ ] **Chrome/Chromium deployment**:

  ```bash
  # Windows Registry
  regedit /s chrome-privacy-policy.reg

  # macOS Managed Preferences
  sudo profiles install -path chrome-privacy.mobileconfig

  # Linux Policy Files
  sudo cp chrome-policies.json /etc/chromium/policies/managed/
  ```

  - [ ] Käytännöt aktivoituneet: `chrome://policy`
  - [ ] Chrome restart tehty
  - [ ] DoH ja proxy toimivat

#### Mobile Devices

- [ ] **iOS deployment**:

  - [ ] .mobileconfig-profiilit jaettu (Apple Configurator/MDM)
  - [ ] DNS over HTTPS aktivoitunut
  - [ ] Safari privacy-asetukset aktivoituneet
  - [ ] Proxy PAC toimii iOS:llä

- [ ] **Android Enterprise**:
  - [ ] Policy JSON ladattu MDM:ään
  - [ ] Firefox/Chrome managed configuration aktivoitunut
  - [ ] DNS-asetukset ohjattu Quad9:ään
  - [ ] App-rajoitukset asetettu (social media, messaging)

---

### Vaihe 3: Validation

#### Automaattinen validointi

```bash
# Aja privacy-check.py jokaisella laitteella
python privacy-check.py --full

# Odotetut tulokset:
# ✅ Proxy PAC: Accessible
# ✅ DoH: Quad9 enabled
# ✅ UA: Reduced/Consistent
# ✅ Lang: en-US
# ✅ WebRTC: Blocked/Proxied
# ✅ TZ: UTC (Firefox) / Controlled (Chrome)
```

#### Manuaaliset tarkistukset

- [ ] **WebRTC leak test**:

  - Siirry → https://browserleaks.com/webrtc
  - ✅ Ei paikallisia IP-osoitteita näkyvissä
  - ✅ Vain proxy IP näkyy
  - ✅ UDP-yhteydet estetty

- [ ] **User-Agent consistency**:

  - Siirry → https://deviceinfo.me
  - ✅ UA reduced (lyhyempi kuin normaali)
  - ✅ Accept-Language: en-US
  - ✅ Timezone: UTC (Firefox) tai kontrolloitu (Chrome)

- [ ] **DNS leak test**:
  - Siirry → https://1.1.1.1/help
  - ✅ "Using DNS over HTTPS (DoH): Yes"
  - ✅ DNS resolver: Quad9 (9.9.9.9)

#### Browser-spesifit validointi

**Firefox ESR:**

- [ ] `about:config` tarkistukset:
  - `privacy.resistFingerprinting` = true
  - `network.trr.mode` = 3 (TRR-only)
  - `intl.accept_languages` = "en-US, en"
  - `media.peerconnection.enabled` = false
- [ ] `about:networking#dns` näyttää DoH = Yes

**Chrome/Chromium:**

- [ ] `chrome://policy` tarkistukset:
  - DnsOverHttpsMode = "secure"
  - WebRtcIPHandlingPolicy = "DisableNonProxiedUdp"
  - AcceptLanguages = "en-US,en"
  - UserAgentReduction = true
- [ ] `chrome://net-internals/#dns` näyttää DoH active

---

### Vaihe 4: Post-deployment

#### Regressio-testit

- [ ] **Sisäiset sovellukset toimivat**:

  - [ ] SharePoint / Office 365
  - [ ] Sisäiset web-sovellukset
  - [ ] SSO/SAML-kirjautuminen toimii
  - [ ] Printtisivut ja lataukset onnistuvat

- [ ] **Videoneuvottelu toimii** (jos sallittu):
  - [ ] Teams: Kamera ja mikrofoni toimivat
  - [ ] Zoom: Yhteys muodostuu
  - [ ] WebEx: Ääni ja video toimivat

#### Poikkeuslistat

- [ ] **Dokumentoidut poikkeukset**:
  ```
  Intranet-sivustot:     *.corp, *.internal → DIRECT
  Videoneuvottelu:       *.teams.microsoft.com → DIRECT
  Sertifikaatit:         *.ocsp.*, *.crl.* → DIRECT
  Kriittinen Office365:  login.microsoftonline.com → DIRECT
  ```

#### Monitoring & Logging

- [ ] **Audit-lokit kerätty**:

  - [ ] Ennen-deployment kuvakaappaukset
  - [ ] Jälkeen-deployment kuvakaappaukset
  - [ ] Versionumerot dokumentoitu
  - [ ] Käyttäjäpalautteet kerätty

- [ ] **Versionhallinta**:
  - [ ] Browser-versiot kirjattu
  - [ ] Policy-versiot dokumentoitu
  - [ ] Rollback-suunnitelma valmiina

---

## 🚨 Ongelmatilanteet

### Proxy ei toimi

```bash
# Debug proxy connectivity
curl -v http://proxy.local/proxy.pac
nslookup proxy.local

# Test proxy function
spidermonkey proxy.pac  # tai node proxy-test.js
```

**Korjaus**: Tarkista DNS resolution, firewall rules, web server status

### DoH ei aktivoidu

```bash
# Test Quad9 connectivity
curl -H "accept: application/dns-json" "https://dns.quad9.net/dns-query?name=google.com&type=A"

# Check bootstrap DNS
nslookup google.com 9.9.9.9
```

**Korjaus**: Varmista 443/tcp pääsy, tarkista sertifikaatit

### Browser policies eivät aktivoidu

```bash
# Firefox debug
firefox --ProfileManager  # Luo uusi profiili testiin
cat /Applications/Firefox.app/Contents/Resources/distribution/policies.json

# Chrome debug
chrome --show-policy-status
```

**Korjaus**: Tarkista tiedostopolut, oikeudet, syntax

### WebRTC vuotaa IP:t

- [ ] Tarkista policy: `WebRtcIPHandlingPolicy` = `DisableNonProxiedUdp`
- [ ] Testaa uBlock Origin filter listoilla
- [ ] Varmista proxy PAC exceptions (videoneuvottelu)

---

## 📊 Success Metrics

### Kriittiset mittarit (100% compliance required)

- [ ] **DoH enabled**: 100% laitteista
- [ ] **Proxy active**: 100% laitteista
- [ ] **Language normalized**: 100% → "en-US"
- [ ] **WebRTC protected**: 100% (ei IP-vuotoja)

### Suorituskykymittarit

- [ ] **DNS resolution time**: < 100ms (DoH overhead hyväksyttävä)
- [ ] **Page load impact**: < 10% hidastuminen proxyn takia
- [ ] **SSL/TLS handshake**: Toimii normaalisti DoH:n kanssa

### Käyttäjäkokemusmittarit

- [ ] **Login success rate**: > 99% (SSO ei rikkoutunut)
- [ ] **Videoneuvottelu quality**: Ei heikennystä
- [ ] **Internal app performance**: Ei regressiota

---

## 🔄 Rollback Plan

### Nopea rollback (hätätilanne)

```bash
# Firefox
sudo rm /Applications/Firefox.app/Contents/Resources/distribution/policies.json

# Chrome
sudo profiles remove -identifier com.organization.privacy.profile

# Windows Registry
regedit /s chrome-policy-rollback.reg
```

### Asteittainen rollback

1. **Poista proxy-pakollisuus**: PAC → DIRECT kaikille
2. **Palauta kieli-asetukset**: en-US → käyttäjän valinta
3. **Aktivoi WebRTC**: Videoneuvotteluille
4. **Poista DoH**: Takaisin system DNS:ään

---

## ✅ Sign-off Checklist

### Technical Sign-off

- [ ] **Network Admin**: Proxy infrastructure toimii
- [ ] **Security Team**: Privacy controls validoitu
- [ ] **IT Support**: User support dokumentaatio valmis
- [ ] **QA Team**: Regressio-testit läpäisty

### Business Sign-off

- [ ] **Business Users**: Sisäiset sovellukset toimivat
- [ ] **Compliance Officer**: GDPR/regulatory requirements täytetty
- [ ] **Management**: Rollout hyväksytty production-käyttöön

### Documentation Sign-off

- [ ] **Rollout report**: Täytetty ja arkistoitu
- [ ] **Known issues**: Dokumentoitu ja workaround-ohjeet luotu
- [ ] **Monitoring plan**: Jatkuva seuranta määritelty
- [ ] **Update procedures**: Tulevien päivitysten prosessi määritelty

---

**🛡️ Privacy & Security Rollout - Mission Complete**

_Metadata leaks minimized | Compliance achieved | Users protected_

**Rollout Date**: ******\_\_\_\_******  
**Rollout Leader**: ******\_\_\_\_******  
**Technical Lead**: ******\_\_\_\_******  
**Sign-off Authority**: ******\_\_\_\_******
