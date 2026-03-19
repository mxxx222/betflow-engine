# ZeroTrace - Raspberry Pi 4 Asennusohje 🇫🇮

## 🎯 Nopea Aloitus

Tämä on yksinkertainen 6-vaiheinen ohje Raspberry Pi 4 ZeroTrace-asennukseen ilman näyttöä.

---

## ✅ Vaihe 1: Lataa Tarvittavat Tiedostot Mac Miniisi

### Lataa ohjelmat:

1. **Raspberry Pi Imager** (Maksuton)

   - Avaa selain: https://www.raspberrypi.com/software/
   - Lataa Mac-versio
   - Asenna normaaliin tapaan

2. **Parrot OS Raspberry Pi -image**
   - Avaa: https://parrotsec.org/download/
   - Valitse: "Parrot Home" → "Raspberry Pi"
   - Lataa uusin versio (iso-tiedosto)

---

## ✅ Vaihe 2: Flashaa microSD-Kortti

1. **Työnnä microSD-kortti** Mac Miniin
2. **Avaa Raspberry Pi Imager**
3. **Valitse OS**:
   - Klikkaa "Use custom"
   - Valitse lataamasi Parrot OS -image
4. **Valitse Storage**: Valitse microSD-korttisi
5. **Aseta ADVANCED-asetukset** (⚙️-ikoni oikealla alhaalla):

   ```
   Hostname: zerotrace-pi
   Enable SSH: ✅ (päälle)
   Username: parrot
   Password: [ASETA VAHVA SALASANA!]
   Wi-Fi SSID: [Verkkosi nimi]
   Wi-Fi Password: [Verkkosi salasana]
   Country: FI (Finland)
   Timezone: Europe/Helsinki
   ```

6. **Klikkaa "Write"** ja odota (5-10 minuuttia)
7. **Kun valmis, irrota turvallisesti** microSD-kortti

---

## ✅ Vaihe 3: Käynnistä Raspberry Pi 4

1. **Työnnä microSD-kortti** Pi 4:ään
2. **Kytke USB-C virtalähde** Pi:iin
3. **Odota 2-3 minuuttia** bootin loppuun

**Merkit:**

- Punainen LED: Virta OK
- Vihreä LED: Blinkkaa (normaalia)

---

## ✅ Vaihe 4: Yhdistä SSH:lla Mac Ministä

Avaa **Terminal** Macissasi:

```bash
# Kokeile mDNS:n kautta (helpoin):
ssh parrot@zerotrace-pi.local

# Jos ei toimi, etsi IP-osoite:
nmap -sn 192.168.1.0/24 | grep -i raspberry

# Yhdistä IP-osoitteella:
ssh parrot@192.168.1.XXX
```

**Ensimmäinen login:**

- Username: `parrot`
- Password: [sen jonka asetit Imagerissa]

---

## ✅ Vaihe 5: VAIHDA SALASANA VÄLITTÖMÄSTI!

```bash
# Vaihda salasana:
passwd
# Anna nykyinen salasana
# Anna uusi vahva salasana (2x)
```

---

## ✅ Vaihe 6: Asenna ZeroTrace

Kopioi ZeroTrace-tiedostot Pi:lle. Sinulla on kaksi vaihtoehtoa:

### **Vaihtoehto A: Siirrä USB:lla**

```bash
# 1. Kytke USB-muistitikku Macissasi (sisältää zerotrace/)
# 2. Kopioi tiedostot Pi:hin
scp -r /path/to/zerotrace parrot@zerotrace-pi.local:/home/parrot/

# 3. SSH Pi:hin
ssh parrot@zerotrace-pi.local

# 4. Mene zerotrace-hakemistoon
cd zerotrace
```

### **Vaihtoehto B: Lataa GitHubista (jos on)**

```bash
# SSH Pi:hin
ssh parrot@zerotrace-pi.local

# Lataa ZeroTrace:
git clone [REPO-URL] zerotrace
cd zerotrace
```

### **Aja asennusscriptit:**

```bash
# 1. Perusasetukset (pakollinen)
sudo ./scripts/10_post_boot.sh

# 2. Verkkoasetukset (pakollinen)
sudo ./scripts/20_network_setup.sh

# 3. Privacy-työkalut (pakollinen)
sudo ./scripts/30_privacy_stack.sh

# 4. Vaihtoehtoiset työkalut (valinnainen)
# Muokkaa .env: INSTALL_TOOLS=true
sudo ./scripts/40_tools_optional.sh

# 5. Log-hygiene (suositeltava)
sudo ./scripts/50_logs_hygiene.sh

# 6. Tarkista että kaikki toimii
./verify/health_summary.sh
```

---

## 🎉 Valmis!

Jos `health_summary.sh` näyttää **PASS** kaikille testeille, ZeroTrace on asennettu onnistuneesti!

### **Käyttö:**

```bash
# Käytä Tor-proxyja kaikissa yhteyksissä:
proxychains curl https://example.com
proxychains firefox-esr

# Tarkista Tor-toiminta:
./verify/check_tor.sh

# Tarkista terveys:
./verify/health_summary.sh
```

---

## 🆘 Ongelmatilanteet

### **SSH ei toimi:**

- Tarkista että Pi saa virtaa (punainen LED)
- Vihreä LED blinkkaa
- Tarkista routerissa että Pi on verkossa
- Kokeile IP-osoitetta suoraan

### **Wi-Fi ei toimi:**

- Tarkista salasana Imagerissa
- Kokeile Ethernet-kaapelia
- Kytke väliaikaisesti HDMI-näyttö debuggausta varten

### **Scriptit eivät aja:**

```bash
# Tarkista että ovat executable:
chmod +x scripts/*.sh
chmod +x verify/*.sh
```

---

## 📞 Tietoa

- Kaikki scriptit on idempotenttejä (voit ajaa monta kertaa)
- Noudata paikallisia lakeja Tor-käytössä
- Käytä vain vastuullisesti
- Säännölliset päivitykset: `sudo proxychains apt update && sudo proxychains apt upgrade`

**Onnea asennukseen!** 🚀🔒








