"""
Pydantic schemas for TDEM API
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# FILE SCHEMAS
# ============================================================

class FileIngestRequest(BaseModel):
    """Request to ingest a file"""
    filename: str = Field(..., min_length=1, description="Original filename")
    expiry_minutes: int = Field(..., gt=0, le=10080, description="Minutes until expiry (max 7 days)")


class FileResponse(BaseModel):
    """Safe file metadata response"""
    file_id: str
    filename: str
    file_size: int
    created_at: str
    expires_at: str
    status: str
    integrity_status: str
    encryption_status: str


class FileListResponse(BaseModel):
    """File in list response"""
    file_id: str
    filename: str
    status: str
    created_at: str
    expires_at: str
    last_accessed_at: Optional[str] = None
    last_refreshed_at: Optional[str] = None


class FileDetailsResponse(BaseModel):
    """Detailed file information"""
    file_id: str
    filename: str
    file_size: int
    status: str
    created_at: str
    expires_at: str
    integrity_status: str
    encryption_status: str
    last_accessed_at: Optional[str] = None
    last_refreshed_at: Optional[str] = None


class FileRefreshRequest(BaseModel):
    """Request to refresh file encryption"""
    pass  # Can be extended for future parameters


class FileRefreshResponse(BaseModel):
    """Response from file refresh"""
    file_id: str
    expires_at: str
    status: str


class FileDeleteResponse(BaseModel):
    """Response from file deletion"""
    success: bool
    message: str


# ============================================================
# RETRIEVAL SCHEMAS
# ============================================================

class FileRetrievalRequest(BaseModel):
    """Request to retrieve a file with risk context"""
    file_id: str = Field(..., description="File ID to retrieve")
    
    # AI risk assessment context
    login_hour: Optional[int] = Field(0, ge=0, le=23, description="Hour of login")
    trusted_device: Optional[int] = Field(0, ge=0, le=1, description="Is trusted device (0/1)")
    country: Optional[str] = Field("Unknown", description="User country")
    ip_reputation: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="IP reputation score")
    vpn_detected: Optional[int] = Field(0, ge=0, le=1, description="VPN detected (0/1)")
    failed_login_attempts: Optional[int] = Field(0, ge=0, description="Failed login attempts")
    browser: Optional[str] = Field("Unknown", description="Browser name")
    access_frequency: Optional[int] = Field(1, ge=0, description="Access frequency")
    file_sensitivity: Optional[str] = Field("Medium", description="File sensitivity level")
    refresh_frequency: Optional[int] = Field(0, ge=0, description="Refresh frequency")


# ============================================================
# AUDIT SCHEMAS
# ============================================================

class AuditLogEntry(BaseModel):
    """Audit log entry"""
    timestamp: str
    action: str
    result: str
    user_id: Optional[str] = None
    file_id: Optional[str] = None
    risk_score: Optional[float] = None
    ai_decision: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# ============================================================
# SECURITY/RISK SCHEMAS
# ============================================================

class RiskAssessment(BaseModel):
    """Risk assessment from AI engine"""
    status: str
    risk_score: float
    decision: str
    reasons: List[str] = []
    model: str
    timestamp: Optional[str] = None


# ============================================================
# ERROR SCHEMAS
# ============================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: str


# ============================================================
# HEALTH SCHEMAS
# ============================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    crypto_available: bool
    ai_available: bool
    storage_available: bool


# ============================================================
# METRICS SCHEMAS
# ============================================================

class MetricsResponse(BaseModel):
    """Metrics response"""
    encryption_time_ms: float = 0.0
    decryption_time_ms: float = 0.0
    request_count: int = 0
    failure_count: int = 0
    ai_decision_count: int = 0
    files_active: int = 0
    files_expired: int = 0
