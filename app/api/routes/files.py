"""
File management routes
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Header, Query
from typing import Optional, List
from app.api.schemas.response import (
    FileResponse,
    FileListResponse,
    FileDetailsResponse,
    FileRefreshResponse,
    FileDeleteResponse,
    FileRetrievalRequest,
    ErrorResponse,
)
from app.core.security import auth_adapter, User
from app.services.file_service import get_file_service
from app.services.audit_service import get_audit_service
from app.core.logging import get_logger

logger = get_logger("files_route")

router = APIRouter(prefix="/api/v1/files", tags=["files"])


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Dependency to get current authenticated user"""
    user = await auth_adapter.get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


# ============================================================
# UPLOAD / INGEST
# ============================================================

@router.post("/ingest", response_model=FileResponse)
async def ingest_file(
    file: UploadFile = File(...),
    expiry_minutes: int = Query(..., gt=0, le=10080),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and encrypt a file.
    
    Parameters:
    - file: File to upload
    - expiry_minutes: Minutes until file expires (1-10080)
    
    Returns:
        Safe file metadata
    """
    try:
        # Read file
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Get services
        file_service = get_file_service()
        audit_service = get_audit_service()
        
        # Ingest file
        result = await file_service.ingest_file(
            user_id=current_user.user_id,
            filename=file.filename or "unknown",
            file_data=file_content,
            content_type=file.content_type or "application/octet-stream",
            expiry_minutes=expiry_minutes,
        )
        
        if not result:
            await audit_service.log_upload(
                user_id=current_user.user_id,
                file_id="unknown",
                filename=file.filename or "unknown",
                success=False,
            )
            raise HTTPException(status_code=500, detail="Upload failed")
        
        # Log success
        await audit_service.log_upload(
            user_id=current_user.user_id,
            file_id=result["file_id"],
            filename=result["filename"],
            success=True,
        )
        
        return FileResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


# ============================================================
# RETRIEVE
# ============================================================

@router.post("/retrieve")
async def retrieve_file(
    request: FileRetrievalRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve and decrypt a file.
    
    The AI engine evaluates the request context to determine
    if access should be allowed.
    
    Returns:
        File content (bytes) or error
    """
    try:
        file_service = get_file_service()
        audit_service = get_audit_service()
        
        # Prepare request data for AI evaluation
        request_data = {
            "user_id": current_user.user_id,
            "login_hour": request.login_hour or 0,
            "trusted_device": request.trusted_device or 0,
            "country": request.country or "Unknown",
            "ip_reputation": request.ip_reputation or 0.5,
            "vpn_detected": request.vpn_detected or 0,
            "failed_login_attempts": request.failed_login_attempts or 0,
            "browser": request.browser or "Unknown",
            "access_frequency": request.access_frequency or 1,
            "file_sensitivity": request.file_sensitivity or "Medium",
            "refresh_frequency": request.refresh_frequency or 0,
        }
        
        # Retrieve file
        plaintext = await file_service.retrieve_file(
            user_id=current_user.user_id,
            file_id=request.file_id,
            request_data=request_data,
        )
        
        if not plaintext:
            # Log retrieval failure
            await audit_service.log_retrieve_request(
                user_id=current_user.user_id,
                file_id=request.file_id,
                ai_decision="DENY",
                risk_score=0.5,
            )
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Log successful retrieval
        await audit_service.log_retrieve_success(
            user_id=current_user.user_id,
            file_id=request.file_id,
        )
        
        return {
            "content": plaintext,
            "file_id": request.file_id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Retrieval failed")


# ============================================================
# REFRESH
# ============================================================

@router.post("/{file_id}/refresh", response_model=FileRefreshResponse)
async def refresh_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Refresh file encryption and extend expiry.
    
    Parameters:
    - file_id: File to refresh
    
    Returns:
        Updated file metadata
    """
    try:
        file_service = get_file_service()
        audit_service = get_audit_service()
        
        # Prepare request data for AI evaluation
        request_data = {
            "user_id": current_user.user_id,
            "login_hour": 12,
            "trusted_device": 1,
            "country": "Unknown",
            "ip_reputation": 0.9,
            "vpn_detected": 0,
            "failed_login_attempts": 0,
            "browser": "Unknown",
            "access_frequency": 1,
            "file_sensitivity": "Medium",
            "refresh_frequency": 1,
        }
        
        # Refresh file
        result = await file_service.refresh_file(
            user_id=current_user.user_id,
            file_id=file_id,
            request_data=request_data,
        )
        
        if not result:
            await audit_service.log_refresh(
                user_id=current_user.user_id,
                file_id=file_id,
                success=False,
            )
            raise HTTPException(status_code=403, detail="Refresh denied")
        
        # Log success
        await audit_service.log_refresh(
            user_id=current_user.user_id,
            file_id=file_id,
            success=True,
        )
        
        return FileRefreshResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Refresh failed")


# ============================================================
# LIST FILES
# ============================================================

@router.get("", response_model=List[FileListResponse])
async def list_files(
    current_user: User = Depends(get_current_user),
):
    """
    Get all files for current user.
    
    Returns:
        List of file metadata
    """
    try:
        file_service = get_file_service()
        files = await file_service.get_file_list(current_user.user_id)
        return [FileListResponse(**f) for f in files]
    except Exception as e:
        logger.error(f"List failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


# ============================================================
# GET FILE DETAILS
# ============================================================

@router.get("/{file_id}", response_model=FileDetailsResponse)
async def get_file_details(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get details for a specific file.
    
    Parameters:
    - file_id: File to get details for
    
    Returns:
        Detailed file metadata
    """
    try:
        file_service = get_file_service()
        details = await file_service.get_file_details(
            current_user.user_id,
            file_id
        )
        
        if not details:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileDetailsResponse(**details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get details failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file details")


# ============================================================
# DELETE FILE
# ============================================================

@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a file.
    
    Parameters:
    - file_id: File to delete
    
    Returns:
        Deletion result
    """
    try:
        file_service = get_file_service()
        audit_service = get_audit_service()
        
        success = await file_service.delete_file(
            current_user.user_id,
            file_id
        )
        
        if not success:
            await audit_service.log_delete(
                user_id=current_user.user_id,
                file_id=file_id,
                success=False,
            )
            raise HTTPException(status_code=403, detail="Cannot delete file")
        
        # Log success
        await audit_service.log_delete(
            user_id=current_user.user_id,
            file_id=file_id,
            success=True,
        )
        
        return FileDeleteResponse(
            success=True,
            message="File deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")
