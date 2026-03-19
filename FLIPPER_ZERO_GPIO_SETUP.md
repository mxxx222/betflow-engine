# Flipper Zero Unleashed GPIO Setup for Van Testing

## Overview

High-ROI testing setup combining Flipper Zero (Unleashed firmware) with ESP32 Dev Kit, CC1101, and NRF24 modules for van door vulnerability testing.

## Hardware Requirements

- Flipper Zero with Unleashed firmware
- ESP32 Dev Kit C (ESP32-WROOM-32)
- CC1101 RF transceiver module
- NRF24L01+ transceiver module
- Evil Crow RF (optional for additional protocols)
- GPIO breakout board/cables
- Power supply (3.3V/5V regulated)

## GPIO Pin Mapping (Flipper Zero to Modules)

### ESP32 Dev Kit Connection

```
Flipper GPIO → ESP32 Pin → Function
GPIO 2       → GPIO 22    → SPI MISO
GPIO 3       → GPIO 21    → I2C SDA
GPIO 4       → GPIO 19    → SPI MOSI
GPIO 5       → GPIO 18    → SPI SCK
GPIO 6       → GPIO 5     → SPI CS
GPIO 7       → GPIO 23    → UART TX
GPIO 8       → GPIO 22    → UART RX
GPIO 9       → EN         → Reset control
GND          → GND        → Ground
3.3V         → 3.3V       → Power
```

### CC1101 RF Module Connection

```
Flipper GPIO → CC1101 Pin → Function
GPIO 2       → MISO       → SPI Data In
GPIO 4       → MOSI       → SPI Data Out
GPIO 5       → SCK        → SPI Clock
GPIO 6       → CSN        → Chip Select
GPIO 13      → GDO0       → Digital Output
GPIO 14      → GDO2       → Digital Output
GND          → GND        → Ground
3.3V         → VCC        → Power
```

### NRF24L01+ Module Connection

```
Flipper GPIO → NRF24 Pin  → Function
GPIO 2       → MISO       → SPI Data In
GPIO 4       → MOSI       → SPI Data Out
GPIO 5       → SCK        → SPI Clock
GPIO 6       → CSN        → Chip Select
GPIO 15      → CE         → Chip Enable
GND          → GND        → Ground
3.3V         → VCC        → Power
```

## Highest ROI Testing Setup Configuration

### Primary Setup (Flipper Zero + ESP32)

1. **Flipper Zero** (Unleashed): Main control and signal generation
2. **ESP32 Dev Kit**: Advanced processing and multi-protocol handling
3. **CC1101**: Sub-GHz frequencies (315/433/868/915MHz)
4. **NRF24**: 2.4GHz protocols (BLE, proprietary)

### Testing Workflow

1. Use Flipper Zero for initial signal capture/analysis
2. ESP32 handles brute force computations
3. CC1101 targets vehicle key fobs (433MHz)
4. NRF24 for modern BLE-enabled systems

#### Top 10 Targets per Component

**Flipper Zero (Signal Capture/Analysis):**

1. Fiat Ducato Gen3 keypad signal patterns
2. VW T4 rolling code sequences
3. Ford Transit MK6 CAN bus diagnostics
4. Peugeot Boxer EEPROM access codes
5. Citroën Jumper immobilizer frequencies
6. Mercedes Sprinter key fob modulation
7. Iveco Daily remote entry systems
8. Volkswagen Crafter central locking
9. Ford Transit Connect wireless protocols
10. Renault Master keyless entry

**ESP32 (Brute Force Computations):**

1. Fiat Ducato PIN code enumeration (4-6 digits)
2. VW T4 timing-based code prediction
3. Ford Transit cryptographic key derivation
4. Peugeot Boxer memory address calculation
5. Citroën Jumper relay attack simulation
6. Mercedes Sprinter algorithm optimization
7. Iveco Daily parallel processing tasks
8. Volkswagen Crafter hash cracking
9. Ford Transit Connect pattern analysis
10. Renault Master computational load balancing

**CC1101 (433MHz Key Fob Targets):**

1. Fiat Ducato Gen3 remote unlock signals
2. VW T4 key fob replay protection bypass
3. Ford Transit MK6 wireless keypad
4. Peugeot Boxer proximity sensors
5. Citroën Jumper backup entry system
6. Mercedes Sprinter long-range fobs
7. Iveco Daily multi-button remotes
8. Volkswagen Crafter garage door integration
9. Ford Transit Connect passive entry
10. Renault Master rolling code systems

**NRF24 (BLE & 2.4GHz Modern Systems):**

1. Fiat Ducato smartphone app integration
2. VW T4 BLE proximity unlocking
3. Ford Transit MK6 wireless diagnostics
4. Peugeot Boxer digital key systems
5. Citroën Jumper NFC/Bluetooth combo
6. Mercedes Sprinter UWB positioning
7. Iveco Daily IoT connectivity modules
8. Volkswagen Crafter cloud-based access
9. Ford Transit Connect gesture controls
10. Renault Master biometric interfaces

### Vehicle-Specific ROI Optimization

#### Fiat Ducato Gen3 (20-35s bypass)

- **Primary**: CC1101 on 433MHz for keypad bypass
- **Secondary**: ESP32 UART for direct PIN injection
- **ROI**: High - Fastest bypass time

#### VW T4 (20-40s bypass)

- **Primary**: NRF24 for rolling code analysis
- **Secondary**: ESP32 SPI for timing manipulation
- **ROI**: High - Good balance of speed/cost

#### Ford Transit MK6 (25-45s bypass)

- **Primary**: ESP32 CAN bus interface
- **Secondary**: CC1101 for wireless diagnostics
- **ROI**: Highest - OBD-II accessible

#### Peugeot Boxer (30-50s bypass)

- **Primary**: ESP32 EEPROM interface
- **Secondary**: Flipper Zero GPIO for memory dumps
- **ROI**: Medium-High - Direct hardware access

#### Citroën Jumper (30-50s bypass)

- **Primary**: CC1101 immobilizer interception
- **Secondary**: ESP32 relay attack simulation
- **ROI**: Medium - Complex but effective

#### Toyota Proace 2022-2023 (15-30s bypass)

- **Primary**: NRF24 BLE relay attack on smart key system
- **Secondary**: ESP32 for BLE pairing code prediction
- **ROI**: Highest - Fastest modern system bypass

#### Peugeot Expert 2023 (25-40s bypass)

- **Primary**: ESP32 CAN bus cryptographic bypass
- **Secondary**: CC1101 for backup key fob interception
- **ROI**: High - Modern PSA platform with known vulnerabilities

## Firmware Setup

### Flipper Zero Unleashed

```bash
# Install Unleashed firmware via web updater
# Enable GPIO in settings
# Install sub-GHz protocols for van frequencies
```

### ESP32 Configuration

```cpp
// ESP32 firmware for van testing
#define SPI_MOSI 19
#define SPI_MISO 22
#define SPI_SCK 18
#define SPI_CS 5

#define CC1101_CS 6
#define NRF24_CE 15
#define NRF24_CSN 6
```

## Power Management

- Use regulated 3.3V supply for all modules
- Flipper Zero can power ESP32 via GPIO (limited current)
- External power bank recommended for extended testing
- Monitor current draw to prevent module damage

## Testing Protocol

1. Connect modules per pin mapping
2. Flash ESP32 with van-specific firmware
3. Use Flipper Zero interface to control ESP32
4. Run automated brute force sequences
5. Log successful bypasses with timestamps

## Safety Notes

- Test only on owned vehicles
- Use Faraday cage for contained testing
- Monitor module temperatures
- Backup original vehicle configurations
