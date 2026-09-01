"""
Crypto Engine Adapter
Integrates the actual TDEM Crypto Engine into the backend
"""

from typing import Optional, Dict, Any
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("crypto_adapter")

# Import actual crypto implementations
try:
    from crypto_engine.service import (
        encrypt_data as crypto_encrypt_data,
        retrieve_data as crypto_retrieve_data,
        refresh_key as crypto_refresh_key,
        get_current_time_window
    )
    from crypto_engine.file_service import (
        encrypt_file,
        decrypt_file
    )
    from crypto_engine.integrity import calculate_hash, verify_hash
    from crypto_engine.expiry import is_expired
    from crypto_engine.metrics import get_metrics as crypto_get_metrics
    
    CRYPTO_AVAILABLE = True
    logger.info("Crypto Engine successfully imported")
except ImportError as e:
    logger.warning(f"Crypto Engine import failed: {e}")
    CRYPTO_AVAILABLE = False


class CryptoAdapter:
    """Adapter for integrating the TDEM Crypto Engine"""
    
    def __init__(self):
        self.kseed = settings.CRYPTO_KSEED.encode() if isinstance(settings.CRYPTO_KSEED, str) else settings.CRYPTO_KSEED
        logger.info("CryptoAdapter initialized")
    
    async def encrypt_data(
        self,
        identity: str,
        plaintext: bytes,
    ) -> Optional[Dict[str, Any]]:
        """
        Encrypt data using the crypto engine.
        
        Args:
            identity: User identity
            plaintext: Data to encrypt
        
        Returns:
            Encrypted package with metadata, or None on failure
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Crypto Engine not available")
            return None
        
        try:
            encrypted_package = crypto_encrypt_data(identity, plaintext, self.kseed)
            logger.debug(f"Data encrypted for identity: {identity}")
            return encrypted_package
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    async def decrypt_data(
        self,
        identity: str,
        encrypted_data: Dict[str, Any],
    ) -> Optional[bytes]:
        """
        Decrypt data using the crypto engine.
        
        Args:
            identity: User identity
            encrypted_data: Encrypted package from encryption
        
        Returns:
            Decrypted plaintext, or None on failure
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Crypto Engine not available")
            return None
        
        try:
            plaintext = crypto_retrieve_data(identity, encrypted_data, self.kseed)
            logger.debug(f"Data decrypted for identity: {identity}")
            return plaintext
        except ValueError as e:
            # Temporal window expired or other validation error
            logger.warning(f"Decryption validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    async def refresh_encryption(
        self,
        identity: str,
        encrypted_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh the temporal component of encryption.
        
        Args:
            identity: User identity
            encrypted_data: Current encrypted package
        
        Returns:
            Updated encrypted package, or None on failure
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Crypto Engine not available")
            return None
        
        try:
            refreshed = crypto_refresh_key(identity, encrypted_data, self.kseed)
            logger.debug(f"Encryption refreshed for identity: {identity}")
            return refreshed
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return None
    
    async def calculate_integrity(self, data: bytes) -> str:
        """
        Calculate integrity hash for data.
        
        Args:
            data: Data to hash
        
        Returns:
            Hex string of hash
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Crypto Engine not available")
            return ""
        
        try:
            hash_value = calculate_hash(data)
            return hash_value.hex()
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return ""
    
    async def verify_integrity(self, data: bytes, expected_hash: str) -> bool:
        """
        Verify data integrity against hash.
        
        Args:
            data: Data to verify
            expected_hash: Expected hash (hex string)
        
        Returns:
            True if valid, False otherwise
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Crypto Engine not available")
            return False
        
        try:
            calculated_hash = await self.calculate_integrity(data)
            return calculated_hash == expected_hash
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    async def is_expired(self, encrypted_data: Dict[str, Any]) -> bool:
        """
        Check if encrypted data has expired.
        
        Args:
            encrypted_data: Encrypted package
        
        Returns:
            True if expired, False otherwise
        """
        if not CRYPTO_AVAILABLE:
            logger.error("Crypto Engine not available")
            return True
        
        try:
            current_window = get_current_time_window()
            stored_window = encrypted_data.get("encryption_window")
            
            if stored_window is None:
                logger.warning("No encryption window in data")
                return True
            
            # Data is expired if temporal window has changed
            is_exp = current_window != stored_window
            
            if is_exp:
                logger.debug(f"Data expired: current_window={current_window}, stored_window={stored_window}")
            
            return is_exp
        except Exception as e:
            logger.error(f"Expiry check failed: {e}")
            return True
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get crypto engine performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        if not CRYPTO_AVAILABLE:
            return {"status": "unavailable"}
        
        try:
            metrics = crypto_get_metrics()
            return metrics
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"error": str(e)}


# Singleton instance
_crypto_adapter = None


def get_crypto_adapter() -> CryptoAdapter:
    """Get crypto adapter instance (singleton)"""
    global _crypto_adapter
    if _crypto_adapter is None:
        _crypto_adapter = CryptoAdapter()
    return _crypto_adapter
