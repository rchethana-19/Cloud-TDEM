"""
Security utilities for TDEM backend
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("security")


class User:
    """User representation"""
    
    def __init__(self, user_id: str, name: str, email: Optional[str] = None):
        self.user_id = user_id
        self.name = name
        self.email = email or f"{user_id}@tdem.local"


class AuthAdapter:
    """Authentication adapter for pluggable auth backends"""
    
    async def authenticate(self, token: Optional[str]) -> Optional[User]:
        """Authenticate user from token"""
        raise NotImplementedError
    
    async def get_current_user(self, authorization: Optional[str]) -> Optional[User]:
        """Extract user from authorization header"""
        raise NotImplementedError


class DevelopmentAuth(AuthAdapter):
    """Development authentication (no real security)"""
    
    async def authenticate(self, token: Optional[str]) -> Optional[User]:
        """In development, accept any token or use default user"""
        if settings.ENVIRONMENT != "development":
            return None
        
        return User(
            user_id=settings.DEVELOPMENT_USER_ID,
            name=settings.DEVELOPMENT_USER_NAME
        )
    
    async def get_current_user(self, authorization: Optional[str]) -> Optional[User]:
        """Extract user from authorization header"""
        if settings.ENVIRONMENT != "development":
            return None
        
        # In development, always return the development user
        return User(
            user_id=settings.DEVELOPMENT_USER_ID,
            name=settings.DEVELOPMENT_USER_NAME
        )


class JWTAuth(AuthAdapter):
    """JWT-based authentication (for future Cognito integration)"""
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"sub": user_id, "exp": expire}
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    async def authenticate(self, token: Optional[str]) -> Optional[User]:
        """Authenticate user from JWT token"""
        if not token:
            return None
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id: str = payload.get("sub")
            
            if user_id is None:
                return None
            
            return User(user_id=user_id, name=user_id)
        
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
    
    async def get_current_user(self, authorization: Optional[str]) -> Optional[User]:
        """Extract user from Bearer token in authorization header"""
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            
            return await self.authenticate(token)
        
        except ValueError:
            return None


# Initialize auth adapter based on environment
def get_auth_adapter() -> AuthAdapter:
    """Get appropriate authentication adapter"""
    if settings.ENVIRONMENT == "development":
        return DevelopmentAuth()
    else:
        return JWTAuth()


auth_adapter = get_auth_adapter()
