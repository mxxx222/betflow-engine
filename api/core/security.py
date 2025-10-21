"""
Security utilities for API authentication and authorization.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt

from .database import get_db
from .config import settings
from ..models.api_keys import APIKey

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()

class SecurityManager:
    """Security manager for authentication and authorization."""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage."""
        salt = settings.API_KEY_HASH_SALT.encode()
        return hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt, 100000).hex()
    
    def verify_api_key_hash(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash."""
        return self.hash_api_key(api_key) == hashed_key

# Global security manager
security_manager = SecurityManager()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    # Get database session
    async for db in get_db():
        # Query API key from database
        result = await db.execute(
            select(APIKey).where(
                APIKey.hash == security_manager.hash_api_key(api_key),
                APIKey.revoked_at.is_(None)
            )
        )
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if key is expired
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last used timestamp
        api_key_record.last_used_at = datetime.utcnow()
        await db.commit()
        
        return api_key_record

async def get_current_user(api_key_record = Depends(verify_api_key)):
    """Get current user from API key."""
    return {
        "client": api_key_record.client,
        "scope": api_key_record.scope,
        "api_key_id": api_key_record.id
    }

def create_api_key(client: str, scope: str = "read", expires_days: int = 365) -> tuple[str, str]:
    """Create new API key."""
    # Generate random API key
    api_key = secrets.token_urlsafe(32)
    
    # Hash for storage
    hashed_key = security_manager.hash_api_key(api_key)
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    return api_key, hashed_key

def check_rate_limit(client: str, endpoint: str) -> bool:
    """Check if client has exceeded rate limit."""
    # This would integrate with Redis for actual rate limiting
    # For now, return True (no limit)
    return True

def audit_action(action: str, resource: str, client: str, details: dict = None):
    """Audit action for compliance tracking."""
    # This would write to audit_logs table
    # For now, just log
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Audit: {action} on {resource} by {client}", extra={
        "action": action,
        "resource": resource,
        "client": client,
        "details": details or {}
    })
