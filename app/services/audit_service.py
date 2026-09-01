"""
Audit service for TDEM backend
Tracks important security events
"""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("audit_service")


class AuditService:
    """Service for audit logging"""
    
    # Audit event types
    UPLOAD_SUCCESS = "UPLOAD_SUCCESS"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    RETRIEVE_REQUEST = "RETRIEVE_REQUEST"
    RETRIEVE_ALLOWED = "RETRIEVE_ALLOWED"
    RETRIEVE_DENIED = "RETRIEVE_DENIED"
    RETRIEVE_EXPIRED = "RETRIEVE_EXPIRED"
    REFRESH_SUCCESS = "REFRESH_SUCCESS"
    REFRESH_FAILED = "REFRESH_FAILED"
    DELETE_SUCCESS = "DELETE_SUCCESS"
    DELETE_FAILED = "DELETE_FAILED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    AUTH_FAILURE = "AUTH_FAILURE"
    CRYPTO_FAILURE = "CRYPTO_FAILURE"
    ACCESS_DENIED_BY_AI = "ACCESS_DENIED_BY_AI"
    MFA_REQUIRED = "MFA_REQUIRED"
    
    def __init__(self):
        self.audit_path = Path(settings.METADATA_PATH) / "audit"
        self.audit_path.mkdir(parents=True, exist_ok=True)
        self.current_log = None
        self._rotate_log()
    
    def _rotate_log(self):
        """Create new audit log file for today"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        self.current_log = self.audit_path / f"audit_{date_str}.jsonl"
    
    def _ensure_current_log(self):
        """Ensure we're writing to today's log"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        new_log = self.audit_path / f"audit_{date_str}.jsonl"
        
        if new_log != self.current_log:
            self.current_log = new_log
    
    async def log_event(
        self,
        action: str,
        result: str,
        user_id: Optional[str] = None,
        file_id: Optional[str] = None,
        risk_score: Optional[float] = None,
        ai_decision: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """
        Log an audit event.
        
        Args:
            action: Action type (e.g., UPLOAD_SUCCESS)
            result: ALLOW/DENY/FAILURE/SUCCESS
            user_id: User performing action
            file_id: Affected file
            risk_score: AI risk score if available
            ai_decision: AI decision if available
            details: Additional details
            request_id: Request ID for correlation
        
        Returns:
            True if logged successfully
        """
        try:
            self._ensure_current_log()
            
            now = datetime.now(timezone.utc)
            
            event = {
                "timestamp": now.isoformat(),
                "action": action,
                "result": result,
                "user_id": user_id,
                "file_id": file_id,
                "risk_score": risk_score,
                "ai_decision": ai_decision,
                "request_id": request_id,
                "details": details or {},
            }
            
            # Write to audit log (append-only)
            with open(self.current_log, "a") as f:
                f.write(json.dumps(event) + "\n")
            
            logger.debug(f"Audit logged: {action}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    async def get_audit_log(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            limit: Maximum entries to return
            user_id: Filter by user
            file_id: Filter by file
        
        Returns:
            List of audit events
        """
        try:
            self._ensure_current_log()
            
            events = []
            
            # Read all audit files
            for log_file in sorted(self.audit_path.glob("audit_*.jsonl"), reverse=True):
                if len(events) >= limit:
                    break
                
                with open(log_file, "r") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        event = json.loads(line)
                        
                        # Apply filters
                        if user_id and event.get("user_id") != user_id:
                            continue
                        
                        if file_id and event.get("file_id") != file_id:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
            
            # Reverse to show newest first
            return list(reversed(events[:limit]))
        
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            return []
    
    async def log_upload(
        self,
        user_id: str,
        file_id: str,
        filename: str,
        success: bool,
    ):
        """Log file upload"""
        action = self.UPLOAD_SUCCESS if success else self.UPLOAD_FAILED
        await self.log_event(
            action=action,
            result="SUCCESS" if success else "FAILURE",
            user_id=user_id,
            file_id=file_id,
            details={"filename": filename},
        )
    
    async def log_retrieve_request(
        self,
        user_id: str,
        file_id: str,
        ai_decision: str,
        risk_score: float,
    ):
        """Log retrieval request"""
        if ai_decision == "DENY":
            action = self.RETRIEVE_DENIED
        elif ai_decision == "REQUIRE_MFA":
            action = self.MFA_REQUIRED
        else:
            action = self.RETRIEVE_REQUEST
        
        await self.log_event(
            action=action,
            result="REQUEST",
            user_id=user_id,
            file_id=file_id,
            risk_score=risk_score,
            ai_decision=ai_decision,
        )
    
    async def log_retrieve_success(
        self,
        user_id: str,
        file_id: str,
    ):
        """Log successful retrieval"""
        await self.log_event(
            action=self.RETRIEVE_ALLOWED,
            result="ALLOW",
            user_id=user_id,
            file_id=file_id,
        )
    
    async def log_refresh(
        self,
        user_id: str,
        file_id: str,
        success: bool,
    ):
        """Log refresh operation"""
        action = self.REFRESH_SUCCESS if success else self.REFRESH_FAILED
        await self.log_event(
            action=action,
            result="SUCCESS" if success else "FAILURE",
            user_id=user_id,
            file_id=file_id,
        )
    
    async def log_delete(
        self,
        user_id: str,
        file_id: str,
        success: bool,
    ):
        """Log file deletion"""
        action = self.DELETE_SUCCESS if success else self.DELETE_FAILED
        await self.log_event(
            action=action,
            result="SUCCESS" if success else "FAILURE",
            user_id=user_id,
            file_id=file_id,
        )
    
    async def log_integrity_failure(
        self,
        user_id: str,
        file_id: str,
    ):
        """Log integrity verification failure"""
        await self.log_event(
            action=self.INTEGRITY_FAILURE,
            result="FAILURE",
            user_id=user_id,
            file_id=file_id,
        )
    
    async def log_auth_failure(
        self,
        user_id: str,
    ):
        """Log authentication failure"""
        await self.log_event(
            action=self.AUTH_FAILURE,
            result="FAILURE",
            user_id=user_id,
        )


# Singleton instance
_audit_service = None


def get_audit_service() -> AuditService:
    """Get audit service instance (singleton)"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
