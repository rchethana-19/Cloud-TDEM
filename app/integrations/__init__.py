"""
Integration modules for TDEM backend
"""

from app.integrations.crypto_adapter import get_crypto_adapter, CryptoAdapter
from app.integrations.ai_adapter import get_ai_adapter, AIAdapter
from app.integrations.storage_adapter import (
    get_object_store,
    get_metadata_store,
    ObjectStore,
    MetadataStore,
    FileMetadata,
)

__all__ = [
    "get_crypto_adapter",
    "CryptoAdapter",
    "get_ai_adapter",
    "AIAdapter",
    "get_object_store",
    "get_metadata_store",
    "ObjectStore",
    "MetadataStore",
    "FileMetadata",
]
