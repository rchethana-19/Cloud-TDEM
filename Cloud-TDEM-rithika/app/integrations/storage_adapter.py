"""
Storage abstractions for TDEM backend
Defines interfaces for object storage and metadata persistence
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import base64
import json
import os
import uuid
from pathlib import Path
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("storage")


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class FileMetadata:
    """File metadata storage structure"""
    file_id: str
    user_id: str
    filename: str
    file_size: int
    content_type: str
    created_at: datetime
    expires_at: datetime
    status: str  # ACTIVE, EXPIRING_SOON, EXPIRED
    integrity_status: str  # VERIFIED, UNVERIFIED, FAILED
    encryption_status: str  # ENCRYPTED
    last_accessed_at: Optional[datetime] = None
    last_refreshed_at: Optional[datetime] = None
    crypto_metadata: Optional[Dict[str, Any]] = None  # Stored crypto state
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary while preserving byte-based crypto metadata."""
        return {
            "file_id": self.file_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "integrity_status": self.integrity_status,
            "encryption_status": self.encryption_status,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "last_refreshed_at": self.last_refreshed_at.isoformat() if self.last_refreshed_at else None,
            "crypto_metadata": self._encode_jsonable(self.crypto_metadata),
        }

    @staticmethod
    def _encode_jsonable(value: Any) -> Any:
        """Convert bytes to a JSON-safe form."""
        if isinstance(value, dict):
            return {key: FileMetadata._encode_jsonable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [FileMetadata._encode_jsonable(item) for item in value]
        if isinstance(value, tuple):
            return [FileMetadata._encode_jsonable(item) for item in value]
        if isinstance(value, bytes):
            return {"__bytes__": base64.b64encode(value).decode("ascii")}
        return value

    @staticmethod
    def _decode_jsonable(value: Any) -> Any:
        """Restore bytes from JSON-safe metadata."""
        if isinstance(value, dict):
            if "__bytes__" in value and len(value) == 1:
                return base64.b64decode(value["__bytes__"])
            return {key: FileMetadata._decode_jsonable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [FileMetadata._decode_jsonable(item) for item in value]
        return value
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "FileMetadata":
        """Create from dictionary"""
        return FileMetadata(
            file_id=data["file_id"],
            user_id=data["user_id"],
            filename=data["filename"],
            file_size=data["file_size"],
            content_type=data.get("content_type", "application/octet-stream"),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            status=data.get("status", "ACTIVE"),
            integrity_status=data.get("integrity_status", "UNVERIFIED"),
            encryption_status=data.get("encryption_status", "ENCRYPTED"),
            last_accessed_at=datetime.fromisoformat(data["last_accessed_at"]) if data.get("last_accessed_at") else None,
            last_refreshed_at=datetime.fromisoformat(data["last_refreshed_at"]) if data.get("last_refreshed_at") else None,
            crypto_metadata=FileMetadata._decode_jsonable(data.get("crypto_metadata")),
        )


# ============================================================
# ABSTRACT INTERFACES
# ============================================================

class ObjectStore(ABC):
    """Abstract interface for encrypted object storage"""
    
    @abstractmethod
    async def store(self, file_id: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        """Store encrypted object"""
        pass
    
    @abstractmethod
    async def retrieve(self, file_id: str) -> Optional[bytes]:
        """Retrieve encrypted object"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Delete encrypted object"""
        pass
    
    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """Check if object exists"""
        pass


class MetadataStore(ABC):
    """Abstract interface for metadata persistence"""
    
    @abstractmethod
    async def save(self, metadata: FileMetadata) -> bool:
        """Save file metadata"""
        pass
    
    @abstractmethod
    async def get(self, file_id: str) -> Optional[FileMetadata]:
        """Retrieve file metadata"""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[FileMetadata]:
        """Get all files for a user"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Delete file metadata"""
        pass
    
    @abstractmethod
    async def update(self, metadata: FileMetadata) -> bool:
        """Update file metadata"""
        pass


# ============================================================
# LOCAL IMPLEMENTATIONS
# ============================================================

class LocalObjectStore(ObjectStore):
    """Local filesystem-based object storage"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalObjectStore initialized at {self.base_path}")
    
    def _get_object_path(self, file_id: str) -> Path:
        """Get the file path for a given file ID"""
        return self.base_path / f"{file_id}.enc"
    
    async def store(self, file_id: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        """Store encrypted object"""
        try:
            path = self._get_object_path(file_id)
            path.write_bytes(data)
            logger.debug(f"Stored object {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store object {file_id}: {e}")
            return False
    
    async def retrieve(self, file_id: str) -> Optional[bytes]:
        """Retrieve encrypted object"""
        try:
            path = self._get_object_path(file_id)
            if not path.exists():
                logger.warning(f"Object not found: {file_id}")
                return None
            
            data = path.read_bytes()
            logger.debug(f"Retrieved object {file_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to retrieve object {file_id}: {e}")
            return None
    
    async def delete(self, file_id: str) -> bool:
        """Delete encrypted object"""
        try:
            path = self._get_object_path(file_id)
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted object {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object {file_id}: {e}")
            return False
    
    async def exists(self, file_id: str) -> bool:
        """Check if object exists"""
        return self._get_object_path(file_id).exists()


class LocalMetadataStore(MetadataStore):
    """Local JSON file-based metadata storage"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.METADATA_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalMetadataStore initialized at {self.base_path}")
    
    def _get_metadata_path(self, file_id: str) -> Path:
        """Get the metadata file path for a given file ID"""
        return self.base_path / f"{file_id}.json"
    
    def _get_user_index_path(self, user_id: str) -> Path:
        """Get the user index file path"""
        return self.base_path / f"index_{user_id}.json"
    
    async def save(self, metadata: FileMetadata) -> bool:
        """Save file metadata"""
        try:
            path = self._get_metadata_path(metadata.file_id)
            data = metadata.to_dict()
            path.write_text(json.dumps(data, indent=2))
            
            # Update user index
            await self._update_user_index(metadata.user_id, metadata.file_id, add=True)
            
            logger.debug(f"Saved metadata for {metadata.file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False
    
    async def get(self, file_id: str) -> Optional[FileMetadata]:
        """Retrieve file metadata"""
        try:
            path = self._get_metadata_path(file_id)
            if not path.exists():
                return None
            
            data = json.loads(path.read_text())
            return FileMetadata.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to get metadata for {file_id}: {e}")
            return None
    
    async def get_by_user(self, user_id: str) -> List[FileMetadata]:
        """Get all files for a user"""
        try:
            index_path = self._get_user_index_path(user_id)
            if not index_path.exists():
                return []
            
            file_ids = json.loads(index_path.read_text()).get("files", [])
            
            metadata_list = []
            for file_id in file_ids:
                meta = await self.get(file_id)
                if meta:
                    metadata_list.append(meta)
            
            return metadata_list
        except Exception as e:
            logger.error(f"Failed to get files for user {user_id}: {e}")
            return []
    
    async def delete(self, file_id: str) -> bool:
        """Delete file metadata"""
        try:
            # Get metadata to find user
            meta = await self.get(file_id)
            
            # Delete metadata file
            path = self._get_metadata_path(file_id)
            if path.exists():
                path.unlink()
            
            # Update user index
            if meta:
                await self._update_user_index(meta.user_id, file_id, add=False)
            
            logger.debug(f"Deleted metadata for {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete metadata for {file_id}: {e}")
            return False
    
    async def update(self, metadata: FileMetadata) -> bool:
        """Update file metadata"""
        try:
            path = self._get_metadata_path(metadata.file_id)
            data = metadata.to_dict()
            path.write_text(json.dumps(data, indent=2))
            logger.debug(f"Updated metadata for {metadata.file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False
    
    async def _update_user_index(self, user_id: str, file_id: str, add: bool) -> bool:
        """Update user file index"""
        try:
            index_path = self._get_user_index_path(user_id)
            
            if index_path.exists():
                index = json.loads(index_path.read_text())
            else:
                index = {"files": []}
            
            if add and file_id not in index["files"]:
                index["files"].append(file_id)
            elif not add and file_id in index["files"]:
                index["files"].remove(file_id)
            
            index_path.write_text(json.dumps(index, indent=2))
            return True
        except Exception as e:
            logger.error(f"Failed to update user index for {user_id}: {e}")
            return False


# ============================================================
# FACTORY FUNCTIONS
# ============================================================

def get_object_store() -> ObjectStore:
    """Get object store instance"""
    return LocalObjectStore()


def get_metadata_store() -> MetadataStore:
    """Get metadata store instance"""
    return LocalMetadataStore()
