# 🔧 ESP32 Auto-Diagnostics Firmware

ESP32-based automotive diagnostics and key emulation system.

## Features

- ✅ OBD-II diagnostics (ELM327 protocol)
- ✅ Key emulation (RFID, rolling codes)
- ✅ WiFi hotspot mode
- ✅ Web-based control panel
- ✅ RESTful API
- ✅ Real-time data streaming

## Hardware Requirements

- ESP32 DevKit V1 or similar
- ELM327 OBD-II adapter (Bluetooth/WiFi)
- Optional: CC1101 RF module for key emulation
- Power: 5V via USB or vehicle 12V → 5V converter

## Setup

### Installation

1. Install **PlatformIO IDE** (VSCode extension recommended)

2. Clone repository:

```bash
cd esp32
```

3. Configure settings in `config.h`:

```cpp
#define WIFI_SSID "your_ssid"
#define WIFI_PASSWORD "your_password"
#define OBD_BAUD 38400
```

4. Upload firmware:

```bash
platformio run --target upload
```

5. Monitor serial output:

```bash
platformio device monitor
```

## Usage

### WiFi Hotspot Mode

After booting, ESP32 creates WiFi AP:

- **SSID**: AutoDiagnostics
- **Password**: autodiag123
- **Web Panel**: http://192.168.4.1

### Web Interface

Access the web panel to:

- View OBD-II live data
- Read/clear DTC codes
- Monitor emissions status
- Emulate keys
- View diagnostics history

### API Endpoints

#### GET /api/status

Returns system status

#### POST /api/obd/scan

Start OBD-II scan

#### GET /api/obd/dtcs

Read DTC codes

#### POST /api/obd/clear

Clear DTC codes

#### POST /api/key/emulate

Emulate key signal

## Configuration

Edit `config.h` for custom settings:

```cpp
// WiFi Configuration
#define AP_SSID "AutoDiagnostics"
#define AP_PASSWORD "autodiag123"

// OBD-II Configuration
#define OBD_PROTOCOL PROTO_AUTO
#define OBD_BAUD_RATE 38400

// Pin Assignments
#define OBD_TX_PIN 17
#define OBD_RX_PIN 16
#define RF_CS_PIN 5
```

## Troubleshooting

**ESP32 won't connect to OBD**

- Check ELM327 adapter connection
- Verify baud rate (38400 or 9600)
- Try different protocol

**WiFi not working**

- Check WiFi SSID/password
- Verify ESP32 antenna connection
- Try different channel

**Key emulation issues**

- Verify RF module wiring
- Check frequency settings
- Calibrate RF module

## Development

### Project Structure

```
esp32/
├── src/
│   ├── main.cpp           # Main firmware code
│   ├── obd_handler.cpp    # OBD-II communication
│   ├── key_emulator.cpp   # RF key emulation
│   ├── web_server.cpp     # Web interface
│   └── wifi_manager.cpp   # WiFi management
├── lib/                   # Custom libraries
├── config.h               # Configuration file
└── platformio.ini         # PlatformIO config
```

### Building

```bash
platformio run
```

### Uploading

```bash
platformio run -t upload
```

### Serial Monitor

```bash
platformio device monitor
```

## License

MIT License








