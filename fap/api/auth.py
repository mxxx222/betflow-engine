"""
FAP Authentication API
User authentication and authorization endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

# Pydantic models for requests/responses
class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company: str
    is_active: bool
    nda_accepted: bool

class NDAAcceptance(BaseModel):
    accepted: bool
    version: str = "1.0"

# Demo endpoints for authentication
@router.post("/login")
async def login(user_login: UserLogin):
    """User login endpoint"""
    # Demo implementation
    if user_login.email == "demo@fap.fi" and user_login.password == "demo":
        return {
            "access_token": "demo_token_123",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": "demo@fap.fi",
                "full_name": "Demo Auditoija",
                "company": "FAP Demo Oy",
                "is_active": True,
                "nda_accepted": True
            }
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@router.post("/accept-nda")
async def accept_nda(
    nda: NDAAcceptance,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Accept NDA (Non-Disclosure Agreement)"""
    # Demo implementation
    if credentials.credentials == "demo_token_123":
        return {
            "status": "nda_accepted",
            "version": nda.version,
            "accepted_at": datetime.now().isoformat(),
            "message": "Vaitiolovelvollisuus hyväksytty. Auditointitoiminnot käytettävissä."
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

@router.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user profile"""
    if credentials.credentials == "demo_token_123":
        return {
            "id": 1,
            "email": "demo@fap.fi",
            "full_name": "Demo Auditoija",
            "company": "FAP Demo Oy",
            "is_active": True,
            "nda_accepted": True,
            "nda_accepted_at": "2024-01-01T00:00:00",
            "permissions": [
                "audit:wifi",
                "audit:rf",
                "audit:iot",
                "reports:generate",
                "reports:download"
            ]
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )