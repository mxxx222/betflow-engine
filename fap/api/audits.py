"""
FAP Audit Management API
Audit session creation, management, and findings
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AuditScope(BaseModel):
    wifi: bool = False
    rf: bool = False
    iot: bool = False
    nfc: bool = False
    bluetooth: bool = False
    zigbee: bool = False
    other: Optional[str] = None

class CreateAuditSession(BaseModel):
    title: str
    description: Optional[str] = None
    client_name: str
    client_business_id: str
    scope: AuditScope
    planned_start: datetime
    planned_end: datetime

class Finding(BaseModel):
    title: str
    description: str
    risk_level: RiskLevel
    category: str
    recommendation: str
    technical_details: Optional[dict] = None

class AuditSessionResponse(BaseModel):
    id: int
    session_id: str
    title: str
    description: Optional[str]
    status: str
    scope: AuditScope
    planned_start: datetime
    planned_end: datetime
    findings_count: int

# Demo data
demo_sessions = [
    {
        "id": 1,
        "session_id": "AUD-2024-001",
        "title": "Kiinteistö Oy Demo - Wi-Fi Auditointi",
        "description": "Kerrostalon langattomien verkkojen turvallisuusarviointi",
        "status": "completed",
        "scope": {
            "wifi": True,
            "rf": True,
            "iot": False,
            "nfc": False,
            "bluetooth": False,
            "zigbee": False
        },
        "planned_start": "2024-01-15T09:00:00",
        "planned_end": "2024-01-15T17:00:00",
        "findings_count": 3
    },
    {
        "id": 2,
        "session_id": "AUD-2024-002",
        "title": "Yritys Oy - IoT Turvallisuus",
        "description": "Toimiston IoT-laitteiden turvallisuuskatselmointis",
        "status": "in_progress",
        "scope": {
            "wifi": True,
            "rf": False,
            "iot": True,
            "nfc": True,
            "bluetooth": True,
            "zigbee": True
        },
        "planned_start": "2024-01-20T08:00:00",
        "planned_end": "2024-01-20T16:00:00",
        "findings_count": 1
    }
]

@router.get("/sessions")
async def get_audit_sessions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all audit sessions for current user"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"sessions": demo_sessions}

@router.post("/sessions")
async def create_audit_session(
    session_data: CreateAuditSession,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create new audit session"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    new_session = {
        "id": len(demo_sessions) + 1,
        "session_id": f"AUD-2024-{len(demo_sessions) + 1:03d}",
        "title": session_data.title,
        "description": session_data.description,
        "status": "planned",
        "scope": session_data.scope.dict(),
        "planned_start": session_data.planned_start.isoformat(),
        "planned_end": session_data.planned_end.isoformat(),
        "findings_count": 0,
        "client_name": session_data.client_name,
        "client_business_id": session_data.client_business_id
    }
    
    demo_sessions.append(new_session)
    
    return {
        "status": "created",
        "session": new_session,
        "message": "Auditointisessio luotu onnistuneesti"
    }

@router.get("/sessions/{session_id}")
async def get_audit_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific audit session details"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find session
    session = next((s for s in demo_sessions if s["session_id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add demo findings
    session["findings"] = [
        {
            "id": 1,
            "title": "Heikko WPA2-salaus",
            "description": "Verkossa käytetään vanhentunutta WPA2-salausta ilman WPA3-tukea",
            "risk_level": "medium",
            "category": "wifi",
            "recommendation": "Päivitä verkkolaitteet tukemaan WPA3-salausta",
            "created_at": "2024-01-15T10:30:00"
        },
        {
            "id": 2,
            "title": "Avoin vierasverkko",
            "description": "Vierasverkko ei käytä minkäänlaista salausta",
            "risk_level": "high",
            "category": "wifi", 
            "recommendation": "Ota käyttöön WPA3-Personal salaus vierasverkossa",
            "created_at": "2024-01-15T11:15:00"
        }
    ]
    
    return session

@router.post("/sessions/{session_id}/findings")
async def add_finding(
    session_id: str,
    finding: Finding,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Add finding to audit session"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "status": "finding_added",
        "finding_id": 123,
        "message": f"Löydös lisätty sessioon {session_id}",
        "finding": finding.dict()
    }

@router.put("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update audit session status"""
    if credentials.credentials != "demo_token_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find and update session
    for session in demo_sessions:
        if session["session_id"] == session_id:
            session["status"] = status.get("status", session["status"])
            if status.get("status") == "completed":
                session["actual_end"] = datetime.now().isoformat()
            
            return {
                "status": "updated",
                "session_id": session_id,
                "new_status": session["status"]
            }
    
    raise HTTPException(status_code=404, detail="Session not found")