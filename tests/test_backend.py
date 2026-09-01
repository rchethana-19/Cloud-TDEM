"""
Tests for TDEM backend
Comprehensive test suite covering all workflows
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from httpx import AsyncClient

from app.main import app
from app.core.security import User
from app.integrations.storage_adapter import LocalObjectStore, LocalMetadataStore, FileMetadata
from app.services.file_service import FileService
from app.services.audit_service import AuditService


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def test_user():
    """Create test user"""
    return User(
        user_id="test_user_001",
        name="Test User",
        email="test@example.com"
    )


@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_file_data():
    """Create test file data"""
    return b"This is a test file content for encryption testing."


@pytest.fixture
def test_metadata(test_user, test_file_data):
    """Create test metadata"""
    now = datetime.now(timezone.utc)
    return FileMetadata(
        file_id="test_file_001",
        user_id=test_user.user_id,
        filename="test.txt",
        file_size=len(test_file_data),
        content_type="text/plain",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        status="ACTIVE",
        integrity_status="VERIFIED",
        encryption_status="ENCRYPTED",
        crypto_metadata={
            "ciphertext": b"encrypted_data",
            "nonce": b"nonce_value",
            "auth_tag": b"auth_tag_value",
            "salt": b"salt_value",
            "database_fragment": b"fdb_value",
            "encryption_window": 100,
        }
    )


# ============================================================
# STORAGE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_local_object_store_store_and_retrieve(test_file_data, tmp_path):
    """Test storing and retrieving objects"""
    store = LocalObjectStore(base_path=str(tmp_path))
    file_id = "test_file_001"
    
    # Store
    success = await store.store(file_id, test_file_data, {})
    assert success
    
    # Retrieve
    retrieved = await store.retrieve(file_id)
    assert retrieved == test_file_data
    
    # Exists
    exists = await store.exists(file_id)
    assert exists


@pytest.mark.asyncio
async def test_local_metadata_store_save_and_get(test_metadata, tmp_path):
    """Test saving and retrieving metadata"""
    store = LocalMetadataStore(base_path=str(tmp_path))
    
    # Save
    success = await store.save(test_metadata)
    assert success
    
    # Get
    retrieved = await store.get(test_metadata.file_id)
    assert retrieved is not None
    assert retrieved.file_id == test_metadata.file_id
    assert retrieved.user_id == test_metadata.user_id


@pytest.mark.asyncio
async def test_local_metadata_store_get_by_user(test_metadata, tmp_path):
    """Test getting files by user"""
    store = LocalMetadataStore(base_path=str(tmp_path))
    
    # Save
    await store.save(test_metadata)
    
    # Get by user
    files = await store.get_by_user(test_metadata.user_id)
    assert len(files) > 0
    assert files[0].file_id == test_metadata.file_id


@pytest.mark.asyncio
async def test_local_metadata_store_delete(test_metadata, tmp_path):
    """Test deleting metadata"""
    store = LocalMetadataStore(base_path=str(tmp_path))
    
    # Save
    await store.save(test_metadata)
    
    # Delete
    success = await store.delete(test_metadata.file_id)
    assert success
    
    # Verify deleted
    retrieved = await store.get(test_metadata.file_id)
    assert retrieved is None


# ============================================================
# AUDIT SERVICE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_audit_service_log_event(tmp_path):
    """Test audit event logging"""
    audit = AuditService()
    audit.audit_path = Path(tmp_path) / "audit"
    audit.audit_path.mkdir(exist_ok=True)
    audit._rotate_log()
    
    # Log event
    success = await audit.log_event(
        action="TEST_ACTION",
        result="SUCCESS",
        user_id="test_user",
        file_id="test_file",
        risk_score=0.3,
        ai_decision="ALLOW",
    )
    assert success
    
    # Retrieve event
    events = await audit.get_audit_log(limit=10, user_id="test_user")
    assert len(events) > 0
    assert events[0]["action"] == "TEST_ACTION"


# ============================================================
# HEALTH CHECK TESTS
# ============================================================

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "environment" in data


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


# ============================================================
# INTEGRATION TESTS
# ============================================================

@pytest.mark.asyncio
async def test_ingest_without_auth_fails(client, test_file_data):
    """Test that ingest without auth fails"""
    response = await client.post(
        "/api/v1/files/ingest",
        files={"file": ("test.txt", test_file_data)},
        params={"expiry_minutes": 60},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_files_without_auth_fails(client):
    """Test that list without auth fails"""
    response = await client.get("/api/v1/files")
    assert response.status_code == 401


# ============================================================
# METADATA TESTS
# ============================================================

@pytest.mark.asyncio
async def test_file_metadata_to_dict():
    """Test FileMetadata serialization"""
    now = datetime.now(timezone.utc)
    metadata = FileMetadata(
        file_id="test_file",
        user_id="test_user",
        filename="test.txt",
        file_size=100,
        content_type="text/plain",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        status="ACTIVE",
        integrity_status="VERIFIED",
        encryption_status="ENCRYPTED",
    )
    
    data = metadata.to_dict()
    assert data["file_id"] == "test_file"
    assert data["user_id"] == "test_user"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_file_metadata_from_dict():
    """Test FileMetadata deserialization"""
    now = datetime.now(timezone.utc)
    data = {
        "file_id": "test_file",
        "user_id": "test_user",
        "filename": "test.txt",
        "file_size": 100,
        "content_type": "text/plain",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "status": "ACTIVE",
        "integrity_status": "VERIFIED",
        "encryption_status": "ENCRYPTED",
    }
    
    metadata = FileMetadata.from_dict(data)
    assert metadata.file_id == "test_file"
    assert metadata.user_id == "test_user"
    assert metadata.file_size == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
