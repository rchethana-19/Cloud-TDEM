"""
Metrics routes
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from app.api.schemas.response import MetricsResponse
from app.core.security import auth_adapter, User
from app.integrations.crypto_adapter import get_crypto_adapter
from app.integrations.storage_adapter import get_metadata_store
from app.core.logging import get_logger
from datetime import datetime, timezone

logger = get_logger("metrics_route")

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Dependency to get current authenticated user"""
    user = await auth_adapter.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@router.get("", response_model=MetricsResponse)
async def get_metrics(
    current_user: User = Depends(get_current_user),
):
    """
    Get system metrics.
    
    Returns:
        Performance metrics from crypto engine and backend
    """
    try:
        crypto = get_crypto_adapter()
        metadata_store = get_metadata_store()
        
        # Get crypto metrics
        crypto_metrics = await crypto.get_metrics()
        
        # Count files
        user_files = await metadata_store.get_by_user(current_user.user_id)
        
        now = datetime.now(timezone.utc)
        active_count = 0
        expired_count = 0
        
        for f in user_files:
            if now >= f.expires_at:
                expired_count += 1
            else:
                active_count += 1
        
        return MetricsResponse(
            encryption_time_ms=crypto_metrics.get("encryption_time_ms", 0.0),
            decryption_time_ms=crypto_metrics.get("decryption_time_ms", 0.0),
            request_count=len(user_files),
            failure_count=0,
            ai_decision_count=0,
            files_active=active_count,
            files_expired=expired_count,
        )
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")
