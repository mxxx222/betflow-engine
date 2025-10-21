"""
FAP Security Core
Authentication, encryption, and GDPR compliance utilities
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# AES encryption for sensitive data
class DataEncryption:
    """GDPR-compliant data encryption for audit data"""
    
    def __init__(self):
        self.key = settings.database_encrypt_key.encode()
        self.fernet = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data: str) -> bytes:
        """Encrypt sensitive audit data (SSID, MAC addresses, etc.)"""
        return self.fernet.encrypt(data.encode())
    
    def decrypt_sensitive_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive audit data"""
        return self.fernet.decrypt(encrypted_data).decode()
    
    def hash_for_anonymization(self, data: str) -> str:
        """Create anonymized hash for GDPR compliance"""
        return hashlib.sha256(f"{data}{self.key}".encode()).hexdigest()[:16]


# Authentication utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password for storage"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_audit_session_id() -> str:
    """Generate secure session ID for audit sessions"""
    return secrets.token_urlsafe(32)


class GDPRCompliance:
    """GDPR compliance utilities for Finnish market"""
    
    @staticmethod
    def is_personal_data(data_type: str) -> bool:
        """Check if data type contains personal information"""
        personal_data_types = [
            "ssid_with_name",  # SSID that might contain personal names
            "mac_address",     # MAC addresses can be personal data
            "bluetooth_name",  # Bluetooth device names
            "location_data",   # GPS coordinates
            "ip_address",      # IP addresses in some contexts
        ]
        return data_type in personal_data_types
    
    @staticmethod
    def anonymize_data(original_data: str, data_type: str) -> str:
        """Anonymize personal data according to GDPR"""
        if not GDPRCompliance.is_personal_data(data_type):
            return original_data
        
        # Create anonymized version
        encryption = DataEncryption()
        return f"ANON_{encryption.hash_for_anonymization(original_data)}"
    
    @staticmethod
    def log_data_processing(user_id: str, data_type: str, purpose: str):
        """Log data processing for GDPR audit trail"""
        logger.info(f"GDPR_LOG: User {user_id} processed {data_type} for {purpose}")


# Finnish Traficom compliance
class TraficomCompliance:
    """Traficom (Finnish Communications Regulatory Authority) compliance"""
    
    @staticmethod
    def is_frequency_allowed(frequency_mhz: float) -> bool:
        """Check if frequency is allowed for testing in Finland"""
        # ISM bands allowed for testing
        allowed_bands = [
            (433.05, 434.79),   # 70cm band
            (868.0, 868.6),     # SRD band 1
            (869.4, 869.65),    # SRD band 2
            (2400, 2483.5),     # 2.4GHz ISM
        ]
        
        return any(start <= frequency_mhz <= end for start, end in allowed_bands)
    
    @staticmethod
    def get_compliance_note() -> str:
        """Get compliance notice for reports"""
        return (
            "Tämä auditointi on suoritettu Trafficomin määräysten mukaisesti. "
            "Testaus on rajattu sallittuihin taajuuksiin ja tehty kirjallisen "
            "sopimuksen perusteella."
        )