"""
FAP Database Models
SQLAlchemy models for audit data, sessions, and compliance
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        LargeBinary, String, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class RiskLevel(str, Enum):
    """Risk levels for audit findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    INFO = "info"


class AuditStatus(str, Enum):
    """Audit session status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    """FAP users (auditors)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # NDA acceptance tracking
    nda_accepted_at = Column(DateTime(timezone=True))
    nda_version = Column(String)
    
    # Azure AD integration fields
    azure_id = Column(String, unique=True, nullable=True)
    
    # Relationships
    audit_sessions = relationship("AuditSession", back_populates="auditor")


class Client(Base):
    """Audit clients"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    business_id = Column(String, unique=True)  # Y-tunnus
    contact_email = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    address = Column(Text)
    
    # Contract and compliance
    contract_signed_at = Column(DateTime(timezone=True))
    gdpr_consent = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    audit_sessions = relationship("AuditSession", back_populates="client")


class AuditSession(Base):
    """Audit sessions - main audit container"""
    __tablename__ = "audit_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # Public session identifier
    
    # Basic info
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default=AuditStatus.PLANNED)
    
    # Relationships
    auditor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    auditor = relationship("User", back_populates="audit_sessions")
    client = relationship("Client", back_populates="audit_sessions")
    
    # Scope definition
    scope_wifi = Column(Boolean, default=False)
    scope_rf = Column(Boolean, default=False)
    scope_iot = Column(Boolean, default=False)
    scope_nfc = Column(Boolean, default=False)
    scope_bluetooth = Column(Boolean, default=False)
    scope_zigbee = Column(Boolean, default=False)
    scope_other = Column(Text)  # Other specified systems
    
    # Timing
    planned_start = Column(DateTime(timezone=True))
    planned_end = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    findings = relationship("Finding", back_populates="session")
    audit_logs = relationship("AuditLog", back_populates="session")


class Finding(Base):
    """Individual audit findings"""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("audit_sessions.id"), nullable=False)
    
    # Finding details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(String, nullable=False)  # RiskLevel enum
    category = Column(String, nullable=False)  # wifi, rf, iot, etc.
    
    # Technical details (encrypted if personal data)
    technical_details = Column(LargeBinary)  # Encrypted JSON
    evidence_data = Column(LargeBinary)  # Encrypted evidence
    
    # Recommendations
    recommendation = Column(Text, nullable=False)
    remediation_effort = Column(String)  # Easy, Medium, Hard
    
    # Compliance flags
    gdpr_relevant = Column(Boolean, default=False)
    traficom_relevant = Column(Boolean, default=False)
    
    # Status tracking
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    retest_required = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("AuditSession", back_populates="findings")


class AuditLog(Base):
    """Audit trail - logs all activities"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("audit_sessions.id"), nullable=False)
    
    # Log details
    action = Column(String, nullable=False)  # scan_wifi, test_rf, etc.
    details = Column(Text)
    user_agent = Column(String)  # Device/software used
    
    # Data classification
    contains_personal_data = Column(Boolean, default=False)
    data_encrypted = Column(Boolean, default=False)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("AuditSession", back_populates="audit_logs")


class DeviceIntegration(Base):
    """Device integration logs (ESP32, Flipper, etc.)"""
    __tablename__ = "device_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("audit_sessions.id"), nullable=False)
    
    # Device info
    device_type = Column(String, nullable=False)  # flipper, esp32, evil_crow
    device_id = Column(String, nullable=False)
    firmware_version = Column(String)
    
    # Data received
    raw_data = Column(LargeBinary)  # Encrypted device data
    processed_data = Column(LargeBinary)  # Encrypted processed results
    
    # Metadata
    frequency_mhz = Column(Float)  # For RF data
    protocol = Column(String)  # wifi, zigbee, etc.
    traficom_compliant = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("audit_sessions.id"), nullable=False)
    
    # Report metadata
    report_type = Column(String, nullable=False)  # pdf, docx, json
    filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)  # SHA-256 for integrity
    
    # Report content (encrypted)
    content = Column(LargeBinary, nullable=False)
    
    # Access control
    client_access_expires = Column(DateTime(timezone=True))
    download_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())