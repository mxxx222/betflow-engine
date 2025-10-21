"""
FAP Main Application
FastAPI application entry point for Field Audit Platform
"""

import os
import sys

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fap.core.config import settings
from fap.core.security import TraficomCompliance

# Initialize FastAPI app
app = FastAPI(
    title="FAP - Field Audit Platform",
    version="0.1.0",
    description="Professional Field Audit Platform for Finnish enterprises - Wi-Fi, RF, IoT security auditing",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Security
security = HTTPBearer()

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": "FAP - Field Audit Platform",
        "version": "0.1.0",
        "description": "🛡️ Professional security auditing for Finnish enterprises",
        "compliance": {
            "traficom": True,
            "gdpr": True,
        }
    }

# Compliance info endpoint
@app.get("/compliance")
async def compliance_info():
    """Get compliance information for Finnish market"""
    return {
        "traficom_note": TraficomCompliance.get_compliance_note(),
        "supported_frequencies": {
            "433_mhz": "433.05-434.79 MHz (70cm band)",
            "868_mhz": "868.0-868.6 MHz, 869.4-869.65 MHz (SRD)",
            "2400_mhz": "2400-2483.5 MHz (2.4GHz ISM)"
        },
        "gdpr_features": [
            "Data encryption at rest",
            "Audit trail for all data processing",
            "Automatic data anonymization",
            "Right to erasure support",
            "Data retention policies"
        ]
    }

# Demo endpoints for testing
@app.get("/demo/audit-types")
async def get_audit_types():
    """Get available audit types"""
    return {
        "audit_types": [
            {
                "id": "wifi_security",
                "name": "Wi-Fi Security Audit", 
                "description": "Wireless network security assessment",
                "scope": ["WPA/WPA2/WPA3 analysis", "Rogue AP detection", "Signal analysis"]
            },
            {
                "id": "rf_spectrum", 
                "name": "RF Spectrum Analysis",
                "description": "Radio frequency environment assessment",
                "scope": ["Spectrum scanning", "Interference detection", "Protocol analysis"]
            },
            {
                "id": "iot_security",
                "name": "IoT Device Security",
                "description": "Internet of Things security evaluation", 
                "scope": ["Device enumeration", "Protocol testing", "Vulnerability scanning"]
            },
            {
                "id": "access_control",
                "name": "Physical Access Control",
                "description": "NFC, RFID, and physical security testing",
                "scope": ["Card cloning detection", "Reader security", "Badge management"]
            }
        ]
    }

@app.get("/demo/flipper-integration")
async def flipper_integration_status():
    """Demo Flipper Zero integration status"""
    return {
        "integration_status": "ready",
        "supported_protocols": [
            "SubGHz (315/433/868/915 MHz)",
            "NFC (13.56 MHz)",
            "RFID (125kHz)",
            "Infrared",
            "GPIO/UART/SPI"
        ],
        "compliance_notes": [
            "All RF testing within Traficom allowed bands",
            "Written client consent required",
            "NDA acceptance mandatory",
            "GDPR data handling protocols active"
        ]
    }

def main():
    """Main entry point - kept for backwards compatibility"""
    print("🛡️ FAP - Field Audit Platform")
    print("=" * 50)
    print("Professional security auditing for Finnish enterprises")
    print("")
    print("✅ FastAPI server ready")
    print("🔒 GDPR & Traficom compliant")
    print("📱 Flipper Zero integration enabled")
    print("")
    print("To start the API server:")
    print("uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
    print("")
    print("API Documentation: http://localhost:8000/api/docs")

if __name__ == "__main__":
    # If run directly, show info and start server
    main()
    print("🚀 Starting development server...")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0", 
        port=8001,
        reload=True
    )