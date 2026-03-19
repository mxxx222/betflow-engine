# 🐧 Raspberry Pi Auto-Diagnostics

Advanced automotive diagnostics system for Raspberry Pi with full OBD-II, CAN-bus analysis, and key emulation capabilities.

## Features

- ✅ Full OBD-II diagnostics
- ✅ CAN-bus deep scanning
- ✅ Key emulation & cloning
- ✅ Web-based dashboard
- ✅ Database logging
- ✅ Fleet management
- ✅ Automated reporting
- ✅ AI-powered failure prediction

## Hardware Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- microSD card (32GB+)
- OBD-II ELM327 adapter (USB or Bluetooth)
- Optional: CAN-bus module
- Optional: 7" Touchscreen
- Power: 5V 3A

## Installation

### 1. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git

# Install system dependencies
sudo apt install -y python3-serial python3-can can-utils
```

### 2. Clone Repository

```bash
cd raspberry-pi
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Settings

Edit `config/config.yaml`:

```yaml
obd:
  port: /dev/ttyUSB0
  baud: 38400
  protocol: AUTO

can:
  interface: can0
  bitrate: 500000

database:
  path: /var/lib/auto-diagnostics/data.db
```

### 5. Run Application

```bash
python3 app.py
```

Access web dashboard at `http://raspberry-pi-ip:5000`

## Usage

### Web Dashboard

Access the web interface for:

- Vehicle scanning
- DTC code management
- Live data monitoring
- Key emulation
- Fleet management
- Report generation

### Command Line Interface

```bash
# Scan vehicle
python3 -m auto_diagnostics.scan --vehicle-id ABC123

# Read DTCs
python3 -m auto_diagnostics.obd read_dtcs

# Clear DTCs
python3 -m auto_diagnostics.obd clear_dtcs

# Deep CAN scan
python3 -m auto_diagnostics.can scan --deep

# Emulate key
python3 -m auto_diagnostics.key emulate --key-id KEY001
```

### API Usage

#### Start Diagnostics

```bash
curl -X POST http://localhost:5000/api/v1/diagnostics/start \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "ABC123"}'
```

#### Get DTCs

```bash
curl http://localhost:5000/api/v1/diagnostics/ABC123/dtcs
```

#### Clear DTCs

```bash
curl -X POST http://localhost:5000/api/v1/diagnostics/ABC123/clear
```

## Project Structure

```
raspberry-pi/
├── app.py                    # Main application
├── config/
│   └── config.yaml          # Configuration
├── auto_diagnostics/
│   ├── __init__.py
│   ├── obd_scanner.py       # OBD-II scanner
│   ├── key_emulator.py      # Key emulation
│   ├── can_analyzer.py      # CAN-bus analyzer
│   ├── database.py          # Database handler
│   └── web_api.py           # REST API
├── web/
│   ├── templates/           # HTML templates
│   └── static/              # CSS/JS assets
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

### OBD-II Settings

Edit `config/config.yaml`:

```yaml
obd:
  port: /dev/ttyUSB0
  baud: 38400
  protocol: AUTO
  timeout: 5
```

### Database Settings

```yaml
database:
  path: /var/lib/auto-diagnostics/data.db
  backup_enabled: true
  backup_interval: 3600
```

### CAN-bus Settings

```yaml
can:
  interface: can0
  bitrate: 500000
  filters:
    - id: 0x7DF # OBD-II requests
    - id: 0x7E8 # OBD-II responses
```

## Troubleshooting

**OBD-II not detected**

```bash
# List serial devices
ls -l /dev/ttyUSB*

# Check permissions
sudo usermod -aG dialout $USER
```

**CAN-bus not working**

```bash
# Enable CAN interface
sudo ip link set can0 up type can bitrate 500000

# Check CAN status
ip link show can0
```

**Database errors**

```bash
# Fix permissions
sudo chown -R pi:pi /var/lib/auto-diagnostics
```

## Systemd Service

Create `/etc/systemd/system/auto-diagnostics.service`:

```ini
[Unit]
Description=Auto-Diagnostics Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspberry-pi
ExecStart=/home/pi/raspberry-pi/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl enable auto-diagnostics
sudo systemctl start auto-diagnostics
```

## License

MIT License








