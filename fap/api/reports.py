"""
FAP Reports API
Report generation and document management
"""

import json
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class ReportRequest(BaseModel):
    session_id: str
    format: str  # "pdf", "docx", "json"
    include_technical_details: bool = True
    include_evidence: bool = False
    language: str = "fi"

class ReportMetadata(BaseModel):
    report_id: str
    session_id: str
    format: str
    generated_at: datetime
    expires_at: Optional[datetime] = None
    download_count: int = 0

# Demo reports data
demo_reports = [
    {
        "report_id": "RPT-2024-001",
        "session_id": "AUD-2024-001",
        "format": "pdf",
        "generated_at": "2024-01-15T18:00:00",
        "expires_at": "2024-04-15T18:00:00",
        "download_count": 2,
        "title": "Kiinteistö Oy Demo - Wi-Fi Turvallisuusraportti"
    }
]

@router.get("/")
async def list_reports(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List available reports"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "reports": demo_reports,
        "total_reports": len(demo_reports)
    }

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Generate audit report"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Demo report generation
    report_content = {
        "report_info": {
            "title": f"Turvallisuusauditointi - {request.session_id}",
            "generated_at": datetime.now().isoformat(),
            "format": request.format,
            "language": request.language
        },
        "executive_summary": {
            "fi": {
                "total_findings": 3,
                "critical_findings": 0,
                "high_findings": 1,
                "medium_findings": 2,
                "low_findings": 0,
                "overall_risk": "Keskitaso",
                "recommendations": [
                    "Päivitä Wi-Fi salaus WPA3:een",
                    "Sulje avoin vierasverkko",
                    "Toteuta verkkoliikenteen monitorointi"
                ]
            }
        },
        "findings": [
            {
                "id": 1,
                "title": "Heikko WPA2-salaus",
                "description": "Verkossa käytetään vanhentunutta WPA2-salausta",
                "risk_level": "medium",
                "category": "wifi",
                "recommendation": "Päivitä WPA3-salaukseen",
                "technical_details": {
                    "encryption": "WPA2-PSK",
                    "cipher": "TKIP/AES",
                    "vulnerabilities": ["KRACK", "Dictionary attacks"]
                } if request.include_technical_details else None
            },
            {
                "id": 2,
                "title": "Avoin vierasverkko",
                "description": "Vierasverkko ei käytä salausta",
                "risk_level": "high",
                "category": "wifi",
                "recommendation": "Ota käyttöön WPA3-salaus",
                "technical_details": {
                    "ssid": "ANON_GUEST_NET",
                    "encryption": "None",
                    "risks": ["Man-in-the-middle", "Traffic interception"]
                } if request.include_technical_details else None
            }
        ],
        "compliance": {
            "traficom": {
                "compliant": True,
                "note": "Kaikki RF-testaus suoritettu sallituilla taajuuksilla"
            },
            "gdpr": {
                "compliant": True,
                "note": "Henkilötiedot anonymisoitu, audit trail säilytetty"
            }
        },
        "methodology": {
            "tools_used": ["Flipper Zero", "ESP32", "FAP Platform"],
            "scan_duration": "8 hours",
            "scan_scope": ["Wi-Fi networks", "RF spectrum", "IoT devices"],
            "frequencies_tested": ["2.4 GHz", "5 GHz", "433 MHz", "868 MHz"]
        },
        "appendices": {
            "legal_basis": "Kirjallinen sopimus asiakkaan kanssa",
            "nda_status": "Voimassa",
            "data_retention": "7 vuotta auditoinnin valmistumisesta"
        }
    }
    
    new_report = {
        "report_id": f"RPT-2024-{len(demo_reports) + 1:03d}",
        "session_id": request.session_id,
        "format": request.format,
        "generated_at": datetime.now().isoformat(),
        "expires_at": (datetime.now().replace(month=datetime.now().month + 3)).isoformat(),
        "download_count": 0,
        "title": f"Turvallisuusraportti - {request.session_id}",
        "content": report_content
    }
    
    demo_reports.append(new_report)
    
    return {
        "status": "report_generated",
        "report": new_report,
        "message": f"Raportti generoitu onnistuneesti ({request.format.upper()})"
    }

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Download generated report"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find report
    report = next((r for r in demo_reports if r["report_id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if expired
    if report.get("expires_at"):
        expires = datetime.fromisoformat(report["expires_at"].replace("Z", "+00:00"))
        if datetime.now() > expires:
            raise HTTPException(status_code=410, detail="Report has expired")
    
    # Generate temporary file for demo
    if report["format"] == "pdf":
        content = f"FAP Turvallisuusraportti\n{report['title']}\n\nTämä on demo-raportti."
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(content)
        temp_file.close()
        
        # Increment download count
        report["download_count"] += 1
        
        return FileResponse(
            temp_file.name,
            filename=f"{report_id}.txt",
            media_type="text/plain"
        )
    
    elif report["format"] == "json":
        content = json.dumps(report.get("content", {}), indent=2, ensure_ascii=False)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
        
        report["download_count"] += 1
        
        return FileResponse(
            temp_file.name,
            filename=f"{report_id}.json",
            media_type="application/json"
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

@router.get("/{report_id}")
async def get_report_info(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get report metadata"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    report = next((r for r in demo_reports if r["report_id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete report (GDPR right to erasure)"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    global demo_reports
    demo_reports = [r for r in demo_reports if r["report_id"] != report_id]
    
    return {
        "status": "report_deleted",
        "report_id": report_id,
        "message": "Raportti poistettu pysyvästi (GDPR)"
    }

@router.get("/templates/audit-types")
async def get_report_templates():
    """Get available report templates"""
    return {
        "templates": [
            {
                "id": "wifi_security",
                "name": "Wi-Fi Turvallisuusraportti",
                "description": "Langattomien verkkojen turvallisuusarviointi",
                "sections": ["Executive Summary", "Löydökset", "Suositukset", "Tekninen liite"]
            },
            {
                "id": "iot_assessment",
                "name": "IoT Turvallisuusarviointi",
                "description": "IoT-laitteiden ja protokollien turvallisuuskatselmointis",
                "sections": ["Laitekatsaus", "Protokollianalyysi", "Haavoittuvuudet", "Korjaustoimenpiteet"]
            },
            {
                "id": "comprehensive_audit",
                "name": "Kokonaisvaltainen Turvallisuusauditointi",
                "description": "Kaikki protokollat ja järjestelmät kattava auditointi",
                "sections": ["Kokonaisarvio", "Wi-Fi", "RF/SubGHz", "IoT", "NFC/RFID", "Suositukset"]
            }
        ]
    }