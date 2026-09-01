"""
API routes
"""

from app.api.routes.health import router as health_router
from app.api.routes.files import router as files_router
from app.api.routes.audit import router as audit_router
from app.api.routes.metrics import router as metrics_router

__all__ = [
    "health_router",
    "files_router",
    "audit_router",
    "metrics_router",
]
