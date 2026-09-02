"""
File management service for TDEM backend
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from app.core.logging import get_logger
from app.integrations.crypto_adapter import get_crypto_adapter
from app.integrations.ai_adapter import get_ai_adapter
from app.integrations.storage_adapter import (
    get_object_store,
    get_metadata_store,
    FileMetadata,
)

logger = get_logger("file_service")


class FileService:
    """Service for file operations"""
    
    def __init__(self):
        self.crypto = get_crypto_adapter()
        self.ai = get_ai_adapter()
        self.object_store = get_object_store()
        self.metadata_store = get_metadata_store()
    
    async def ingest_file(
        self,
        user_id: str,
        filename: str,
        file_data: bytes,
        content_type: str,
        expiry_minutes: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Ingest and encrypt a file.
        
        Workflow:
        1. Validate user
        2. Validate expiry
        3. Encrypt file using Crypto Engine
        4. Store encrypted object
        5. Store metadata
        6. Return safe response
        
        Args:
            user_id: Owner user ID
            filename: Original filename
            file_data: File content
            content_type: MIME type
            expiry_minutes: Minutes until expiry
        
        Returns:
            Safe file metadata, or None on failure
        """
        try:
            # Validate inputs
            if not filename or not file_data:
                logger.warning(f"Invalid input: filename or file_data empty")
                return None
            
            if expiry_minutes <= 0 or expiry_minutes > 10080:  # Max 7 days
                logger.warning(f"Invalid expiry: {expiry_minutes} minutes")
                return None
            
            # Generate file ID
            file_id = str(uuid.uuid4())
            
            # Calculate expiry
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=expiry_minutes)
            
            # Encrypt file using Crypto Engine
            logger.debug(f"Encrypting file {file_id} for user {user_id}")
            encrypted_package = await self.crypto.encrypt_data(user_id, file_data)
            
            if not encrypted_package:
                logger.error(f"Encryption failed for {file_id}")
                return None
            
            # Calculate integrity hash and include it in the encrypted payload metadata
            integrity_hash = await self.crypto.calculate_integrity(file_data)
            encrypted_package["integrity_hash"] = integrity_hash

            serialized_encrypted = json.dumps(
                FileMetadata._encode_jsonable(encrypted_package),
                separators=(",", ":"),
            ).encode("utf-8")
            
            # Store encrypted object bytes, never the raw plaintext
            if not await self.object_store.store(file_id, serialized_encrypted, encrypted_package):
                logger.error(f"Failed to store object {file_id}")
                return None
            
            # Create and store metadata
            metadata = FileMetadata(
                file_id=file_id,
                user_id=user_id,
                filename=filename,
                file_size=len(file_data),
                content_type=content_type,
                created_at=now,
                expires_at=expires_at,
                status="ACTIVE",
                integrity_status="VERIFIED",
                encryption_status="ENCRYPTED",
                crypto_metadata=encrypted_package,
            )
            
            if not await self.metadata_store.save(metadata):
                logger.error(f"Failed to store metadata for {file_id}")
                # Clean up encrypted object
                await self.object_store.delete(file_id)
                return None
            
            logger.info(f"File ingested: {file_id} (user: {user_id}, expires: {expires_at})")
            
            # Return safe response (no secrets)
            return {
                "file_id": file_id,
                "filename": filename,
                "file_size": len(file_data),
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "status": "ACTIVE",
                "integrity_status": "VERIFIED",
                "encryption_status": "ENCRYPTED",
            }
        
        except Exception as e:
            logger.error(f"Ingest failed: {e}")
            return None
    
    async def retrieve_file(
        self,
        user_id: str,
        file_id: str,
        request_data: Dict[str, Any],
    ) -> Optional[bytes]:
        """
        Retrieve and decrypt a file.
        
        Workflow:
        1. Authenticate user
        2. Check ownership
        3. Load metadata
        4. Check expiry (backend authoritative)
        5. AI risk evaluation
        6. If denied -> stop
        7. Retrieve encrypted object
        8. Decrypt using Crypto Engine
        9. Verify integrity
        10. Update access time
        11. Return file
        
        Args:
            user_id: Requesting user ID
            file_id: File to retrieve
            request_data: Request context for AI evaluation
        
        Returns:
            File content, or None on failure
        """
        try:
            # Get metadata
            metadata = await self.metadata_store.get(file_id)
            
            if not metadata:
                logger.warning(f"File not found: {file_id}")
                return None
            
            # Check ownership
            if metadata.user_id != user_id:
                logger.warning(f"Ownership check failed: {user_id} != {metadata.user_id}")
                return None
            
            # Check expiry (backend authoritative)
            now = datetime.now(timezone.utc)
            if now >= metadata.expires_at:
                logger.warning(f"File expired: {file_id}")
                metadata.status = "EXPIRED"
                await self.metadata_store.update(metadata)
                return None
            
            # AI risk evaluation
            ai_result = await self.ai.evaluate_access_request(user_id, file_id, request_data)
            risk_score = ai_result.get("risk_score", 0.5)
            decision = ai_result.get("decision", "DENY")
            
            logger.info(f"AI evaluation for {file_id}: {decision} (score: {risk_score})")
            
            # If AI denies, stop here
            if decision == "DENY":
                logger.warning(f"Access denied by AI: {file_id}")
                return None
            
            # Retrieve encrypted object from object storage and decrypt the stored payload
            encrypted_blob = await self.object_store.retrieve(file_id)
            
            if not encrypted_blob:
                logger.error(f"Encrypted object not found: {file_id}")
                return None

            try:
                encrypted_data = FileMetadata._decode_jsonable(
                    json.loads(encrypted_blob.decode("utf-8"))
                )
            except (ValueError, UnicodeDecodeError, TypeError) as exc:
                logger.error(f"Encrypted object payload is invalid for {file_id}: {exc}")
                return None
            
            # Decrypt using the encrypted payload from the object store, not the metadata alone
            crypto_metadata = encrypted_data if isinstance(encrypted_data, dict) else metadata.crypto_metadata
            plaintext = await self.crypto.decrypt_data(user_id, crypto_metadata)
            
            if not plaintext:
                logger.error(f"Decryption failed: {file_id}")
                return None
            
            # Verify integrity
            stored_hash = crypto_metadata.get("integrity_hash")
            if stored_hash:
                is_valid = await self.crypto.verify_integrity(plaintext, stored_hash)
                if not is_valid:
                    logger.error(f"Integrity verification failed: {file_id}")
                    metadata.integrity_status = "FAILED"
                    await self.metadata_store.update(metadata)
                    return None
            
            # Update access time
            metadata.last_accessed_at = now
            await self.metadata_store.update(metadata)
            
            logger.info(f"File retrieved: {file_id}")
            return plaintext
        
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return None
    
    async def refresh_file(
        self,
        user_id: str,
        file_id: str,
        request_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh file encryption and expiry.
        
        Workflow:
        1. Authenticate user
        2. Check ownership
        3. Load metadata
        4. AI evaluation
        5. Validate new expiry
        6. Use Crypto Engine lifecycle
        7. Update metadata
        8. Return updated expiry
        
        Args:
            user_id: Owner user ID
            file_id: File to refresh
            request_data: Request context for AI evaluation
        
        Returns:
            Updated metadata, or None on failure
        """
        try:
            # Get metadata
            metadata = await self.metadata_store.get(file_id)
            
            if not metadata:
                logger.warning(f"File not found: {file_id}")
                return None
            
            # Check ownership
            if metadata.user_id != user_id:
                logger.warning(f"Ownership check failed: {user_id} != {metadata.user_id}")
                return None
            
            # AI evaluation
            ai_result = await self.ai.evaluate_access_request(user_id, file_id, request_data)
            decision = ai_result.get("decision", "DENY")
            
            if decision == "DENY":
                logger.warning(f"Refresh denied by AI: {file_id}")
                return None
            
            # Refresh crypto key
            now = datetime.now(timezone.utc)
            crypto_metadata = metadata.crypto_metadata
            
            refreshed_metadata = await self.crypto.refresh_encryption(
                user_id,
                crypto_metadata
            )
            
            if not refreshed_metadata:
                logger.error(f"Crypto refresh failed: {file_id}")
                return None
            
            # Extend expiry by original duration
            original_expiry = metadata.expires_at
            created = metadata.created_at
            original_duration = original_expiry - created
            new_expiry = now + original_duration
            
            # Update metadata
            metadata.expires_at = new_expiry
            metadata.last_refreshed_at = now
            metadata.crypto_metadata = refreshed_metadata
            metadata.status = "ACTIVE"
            
            if not await self.metadata_store.update(metadata):
                logger.error(f"Metadata update failed: {file_id}")
                return None
            
            logger.info(f"File refreshed: {file_id}, new expiry: {new_expiry}")
            
            return {
                "file_id": file_id,
                "expires_at": new_expiry.isoformat(),
                "status": "ACTIVE",
            }
        
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return None
    
    async def delete_file(
        self,
        user_id: str,
        file_id: str,
    ) -> bool:
        """
        Delete a file.
        
        Workflow:
        1. Authenticate user
        2. Check ownership
        3. Delete encrypted object
        4. Delete metadata
        
        Args:
            user_id: Owner user ID
            file_id: File to delete
        
        Returns:
            True on success, False on failure
        """
        try:
            # Get metadata
            metadata = await self.metadata_store.get(file_id)
            
            if not metadata:
                logger.warning(f"File not found: {file_id}")
                return False
            
            # Check ownership
            if metadata.user_id != user_id:
                logger.warning(f"Ownership check failed: {user_id} != {metadata.user_id}")
                return False
            
            # Delete encrypted object
            await self.object_store.delete(file_id)
            
            # Delete metadata
            if not await self.metadata_store.delete(file_id):
                logger.error(f"Metadata deletion failed: {file_id}")
                return False
            
            logger.info(f"File deleted: {file_id}")
            return True
        
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            return False
    
    async def get_file_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all files for a user.
        
        Returns safe metadata (no secrets).
        """
        try:
            metadata_list = await self.metadata_store.get_by_user(user_id)
            
            files = []
            now = datetime.now(timezone.utc)
            
            for metadata in metadata_list:
                # Update status based on expiry
                if now >= metadata.expires_at:
                    metadata.status = "EXPIRED"
                elif (metadata.expires_at - now).total_seconds() < 3600:  # 1 hour
                    metadata.status = "EXPIRING_SOON"
                else:
                    metadata.status = "ACTIVE"
                
                await self.metadata_store.update(metadata)
                
                files.append({
                    "file_id": metadata.file_id,
                    "filename": metadata.filename,
                    "status": metadata.status,
                    "created_at": metadata.created_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat(),
                    "last_accessed_at": metadata.last_accessed_at.isoformat() if metadata.last_accessed_at else None,
                    "last_refreshed_at": metadata.last_refreshed_at.isoformat() if metadata.last_refreshed_at else None,
                })
            
            return files
        
        except Exception as e:
            logger.error(f"Failed to get file list: {e}")
            return []
    
    async def get_file_details(self, user_id: str, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get safe details for a file.
        """
        try:
            metadata = await self.metadata_store.get(file_id)
            
            if not metadata or metadata.user_id != user_id:
                return None
            
            # Update status based on expiry
            now = datetime.now(timezone.utc)
            if now >= metadata.expires_at:
                metadata.status = "EXPIRED"
            elif (metadata.expires_at - now).total_seconds() < 3600:
                metadata.status = "EXPIRING_SOON"
            else:
                metadata.status = "ACTIVE"
            
            await self.metadata_store.update(metadata)
            
            return {
                "file_id": metadata.file_id,
                "filename": metadata.filename,
                "file_size": metadata.file_size,
                "status": metadata.status,
                "created_at": metadata.created_at.isoformat(),
                "expires_at": metadata.expires_at.isoformat(),
                "integrity_status": metadata.integrity_status,
                "encryption_status": metadata.encryption_status,
                "last_accessed_at": metadata.last_accessed_at.isoformat() if metadata.last_accessed_at else None,
                "last_refreshed_at": metadata.last_refreshed_at.isoformat() if metadata.last_refreshed_at else None,
            }
        
        except Exception as e:
            logger.error(f"Failed to get file details: {e}")
            return None


# Singleton instance
_file_service = None


def get_file_service() -> FileService:
    """Get file service instance (singleton)"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
