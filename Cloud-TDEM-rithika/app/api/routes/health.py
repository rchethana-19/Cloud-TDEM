"""
Health check route
"""

from fastapi import APIRouter
from app.api.schemas.response import HealthResponse
from app.core.config import settings
from app.integrations.crypto_adapter import get_crypto_adapter
from app.integrations.ai_adapter import get_ai_adapter
from app.integrations.storage_adapter import get_object_store, get_metadata_store
from app.core.logging import get_logger

logger = get_logger("health_route")

router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status and availability of components
    """
    
    # Check crypto adapter
    crypto = get_crypto_adapter()
    try:
        crypto_available = crypto is not None
    except Exception as e:
        logger.error(f"Crypto check failed: {e}")
        crypto_available = False
    
    # Check AI adapter
    ai = get_ai_adapter()
    try:
        ai_available = ai is not None
    except Exception as e:
        logger.error(f"AI check failed: {e}")
        ai_available = False
    
    # Check storage
    try:
        object_store = get_object_store()
        metadata_store = get_metadata_store()
        storage_available = True
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        storage_available = False
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
        crypto_available=crypto_available,
        ai_available=ai_available,
        storage_available=storage_available,
    )
