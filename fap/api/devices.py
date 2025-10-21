"""
FAP Device Integration API
ESP32, Flipper Zero, and other device integrations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class DeviceData(BaseModel):
    device_type: str  # "flipper", "esp32", "evil_crow"
    device_id: str
    firmware_version: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime
    frequency_mhz: Optional[float] = None
    protocol: Optional[str] = None

class FlipperScanResult(BaseModel):
    scan_type: str  # "wifi", "subghz", "nfc", "rfid"
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class DeviceStatus(BaseModel):
    device_id: str
    status: str  # "online", "offline", "scanning"
    last_seen: datetime
    battery_level: Optional[int] = None

# Demo device data
demo_devices = [
    {
        "device_id": "flipper_001",
        "device_type": "flipper",
        "status": "online",
        "last_seen": datetime.now().isoformat(),
        "firmware_version": "0.98.3",
        "battery_level": 87
    },
    {
        "device_id": "esp32_wifi_001", 
        "device_type": "esp32",
        "status": "scanning",
        "last_seen": datetime.now().isoformat(),
        "firmware_version": "2.1.0",
        "battery_level": None
    }
]

@router.get("/status")
async def get_device_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get status of all connected devices"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "devices": demo_devices,
        "total_devices": len(demo_devices),
        "online_devices": sum(1 for d in demo_devices if d["status"] == "online")
    }

@router.post("/data")
async def receive_device_data(
    data: DeviceData,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Receive data from field devices (ESP32, Flipper, etc.)"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Validate frequency for Traficom compliance
    if data.frequency_mhz:
        from fap.core.security import TraficomCompliance
        if not TraficomCompliance.is_frequency_allowed(data.frequency_mhz):
            raise HTTPException(
                status_code=400,
                detail=f"Frequency {data.frequency_mhz} MHz not allowed by Traficom"
            )
    
    # Process and store data (demo)
    processed_data = {
        "device_id": data.device_id,
        "received_at": datetime.now().isoformat(),
        "data_points": len(data.data),
        "compliance_check": "passed",
        "stored": True
    }
    
    return {
        "status": "data_received",
        "processing_result": processed_data,
        "message": "Data vastaanotettu ja tallennettu turvallisesti"
    }

@router.get("/flipper/{device_id}/scan")
async def start_flipper_scan(
    device_id: str,
    scan_type: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Start scan on Flipper Zero device"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Demo scan results
    demo_results = {
        "wifi": {
            "networks": [
                {"ssid": "ANON_1A2B3C", "encryption": "WPA2", "signal": -45, "channel": 6},
                {"ssid": "ANON_4D5E6F", "encryption": "Open", "signal": -67, "channel": 11},
                {"ssid": "ANON_7G8H9I", "encryption": "WPA3", "signal": -52, "channel": 1}
            ],
            "scan_duration": 30,
            "networks_found": 3
        },
        "subghz": {
            "signals": [
                {"frequency": 433.92, "protocol": "Unknown", "rssi": -42},
                {"frequency": 868.35, "protocol": "OOK", "rssi": -55}
            ],
            "scan_duration": 60,
            "signals_found": 2
        },
        "nfc": {
            "cards": [
                {"type": "MIFARE Classic", "uid": "ANON_NFC_001", "sectors": 16}
            ],
            "scan_duration": 10,
            "cards_found": 1
        }
    }
    
    if scan_type not in demo_results:
        raise HTTPException(status_code=400, detail="Invalid scan type")
    
    return {
        "status": "scan_completed",
        "device_id": device_id,
        "scan_type": scan_type,
        "results": demo_results[scan_type],
        "gdpr_note": "Kaikki tunnistettavat tiedot anonymisoitu",
        "traficom_compliance": "Skannaus suoritettu sallituilla taajuuksilla"
    }

@router.post("/esp32/{device_id}/configure")
async def configure_esp32(
    device_id: str,
    config: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Configure ESP32 device for specific audit tasks"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "status": "device_configured",
        "device_id": device_id,
        "configuration": config,
        "message": f"ESP32 {device_id} konfiguroitu onnistuneesti"
    }

@router.get("/protocols")
async def get_supported_protocols():
    """Get list of supported protocols and compliance information"""
    return {
        "protocols": {
            "wifi": {
                "standards": ["802.11a/b/g/n/ac/ax"],
                "encryption": ["Open", "WEP", "WPA", "WPA2", "WPA3"],
                "compliance": "Traficom compliant scanning"
            },
            "subghz": {
                "frequencies": ["433.05-434.79 MHz", "868.0-868.6 MHz", "869.4-869.65 MHz"],
                "modulation": ["ASK/OOK", "2-FSK", "4-FSK", "MSK"],
                "compliance": "Licensed band scanning with client permission"
            },
            "zigbee": {
                "channels": ["11-26 (2.4 GHz)"],
                "protocols": ["Zigbee 1.2", "Zigbee 3.0"],
                "compliance": "ISM band, client network only"
            },
            "bluetooth": {
                "versions": ["Classic", "BLE 4.0-5.x"],
                "scanning": ["Advertisement", "Service Discovery"],
                "compliance": "Passive scanning, no pairing"
            },
            "nfc": {
                "frequencies": ["13.56 MHz"],
                "protocols": ["ISO14443 A/B", "ISO15693", "FeliCa"],
                "compliance": "Close proximity scanning only"
            }
        },
        "compliance_notes": [
            "All scanning performed with written client consent",
            "Personal data automatically anonymized",
            "Audit trail maintained for all activities",
            "Frequency usage compliant with Traficom regulations"
        ]
    }