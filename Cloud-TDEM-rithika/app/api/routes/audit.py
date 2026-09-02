"""
Audit log routes
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import Optional, List
from app.api.schemas.response import AuditLogEntry
from app.core.security import auth_adapter, User
from app.services.audit_service import get_audit_service
from app.core.logging import get_logger

logger = get_logger("audit_route")

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Dependency to get current authenticated user"""
    user = await auth_adapter.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@router.get("", response_model=List[AuditLogEntry])
async def get_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    file_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Get audit log entries.
    
    Parameters:
    - limit: Maximum entries to return (1-1000)
    - file_id: Filter by file ID
    
    Returns:
        List of audit log entries
    """
    try:
        audit_service = get_audit_service()
        
        # Get audit log for this user
        entries = await audit_service.get_audit_log(
            limit=limit,
            user_id=current_user.user_id,
            file_id=file_id,
        )
        
        return [AuditLogEntry(**e) for e in entries]
    
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit log")
