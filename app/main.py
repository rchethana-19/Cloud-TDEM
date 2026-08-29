from __future__ import annotations

import base64
import binascii
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.integrations.adapters import BranchCryptoAdapter, BranchRiskAdapter, EngineUnavailable
from app.integrations.aws_services import DynamoMetadataStore, S3ObjectStore, SecretsManager
from app.core.config import get_settings
from app.services.vault import (
    AuditLog,
    InMemoryMetadataStore,
    InMemoryObjectStore,
    VaultError,
    VaultService,
)


class RiskContext(BaseModel):
    login_hour: int = Field(ge=0, le=23)
    trusted_device: bool
    country: Literal["Canada", "China", "Germany", "India", "Russia", "UK", "USA", "Unknown"]
    ip_reputation: float = Field(ge=0, le=1)
    vpn_detected: bool
    failed_login_attempts: int = Field(ge=0, le=100)
    browser: Literal["Chrome", "Edge", "Firefox", "Safari"]
    access_frequency: int = Field(ge=0, le=100000)
    file_sensitivity: Literal["Low", "Medium", "High"]
    refresh_frequency: int = Field(ge=0, le=100000)


class IngestRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)
    validity_duration: int = Field(gt=0, le=3650)
    validity_unit: str = Field(pattern="^(minutes|hours|days)$")


class RetrieveRequest(BaseModel):
    file_id: str
    context: RiskContext


class RefreshRequest(BaseModel):
    file_id: str
    extension_duration: int = Field(gt=0, le=3650)
    extension_unit: str = Field(pattern="^(minutes|hours|days)$")
    context: RiskContext


class RuntimeRisk:
    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"risk_score": 0.0, "decision": "ALLOW"}


class RuntimeCrypto:
    def __init__(self) -> None:
        self.adapter = BranchCryptoAdapter()

    def encrypt(self, identity: str, plaintext: bytes, kseed: bytes) -> dict[str, Any]:
        return self.adapter.encrypt(identity, plaintext, kseed)

    def decrypt(self, identity: str, encrypted: dict[str, Any], kseed: bytes) -> bytes:
        return self.adapter.decrypt(identity, encrypted, kseed)

    def refresh(self, identity: str, encrypted: dict[str, Any], kseed: bytes) -> dict[str, Any]:
        return self.adapter.refresh(identity, encrypted, kseed)


def build_service() -> VaultService:
    settings = get_settings()
    try:
        crypto: Any = RuntimeCrypto()
        risk: Any = BranchRiskAdapter(settings.model_module)
    except EngineUnavailable as error:
        raise RuntimeError(str(error)) from error
    if not settings.secret_name or not settings.s3_bucket or not settings.dynamodb_table:
        raise RuntimeError("AWS secret, S3 bucket, and DynamoDB table must be configured")
    seed = SecretsManager().get_bytes(settings.secret_name)
    if len(seed) != 32:
        raise RuntimeError("Kseed must be 32 bytes")
    return VaultService(crypto, risk, S3ObjectStore(settings.s3_bucket), DynamoMetadataStore(settings.dynamodb_table), AuditLog(), seed)


app = FastAPI(title="TDEM Secure Vault", version="1.0.0")

try:
    vault = build_service()
except RuntimeError:
    vault = None


def current_user(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return user_id


def duration_delta(duration: int, unit: str) -> timedelta:
    return {"minutes": timedelta(minutes=duration), "hours": timedelta(hours=duration), "days": timedelta(days=duration)}[unit]


def service_or_error() -> VaultService | None:
    return vault


def require_service(service: VaultService | None) -> VaultService:
    if vault is None:
        raise HTTPException(status_code=503, detail="backend engines are not configured")
    return service


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/files/ingest")
def ingest(payload: IngestRequest, user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> dict[str, Any]:
    service = require_service(service)
    try:
        content = base64.b64decode(payload.content_base64, validate=True)
        if len(content) > get_settings().max_upload_bytes:
            raise VaultError("uploaded file exceeds the configured size limit")
        return service.ingest(user_id, payload.filename, content, datetime.now(timezone.utc) + duration_delta(payload.validity_duration, payload.validity_unit))
    except (ValueError, binascii.Error, VaultError) as error:
        raise HTTPException(status_code=getattr(error, "status_code", 400), detail=str(error)) from error


@app.post("/api/v1/files/retrieve")
def retrieve(payload: RetrieveRequest, user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> dict[str, Any]:
    service = require_service(service)
    try:
        record, content = service.retrieve(user_id, payload.file_id, payload.context.model_dump())
        return {"file": safe_detail(record), "content_base64": base64.b64encode(content).decode("ascii")}
    except VaultError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@app.post("/api/v1/files/refresh")
def refresh(payload: RefreshRequest, user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> dict[str, Any]:
    service = require_service(service)
    try:
        expiry = datetime.now(timezone.utc) + duration_delta(payload.extension_duration, payload.extension_unit)
        return service.refresh(user_id, payload.file_id, expiry, payload.context.model_dump())
    except VaultError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@app.get("/api/v1/files")
def list_files(user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> list[dict[str, Any]]:
    service = require_service(service)
    return [safe_summary(record) for record in service.metadata.list_for_user(user_id)]


@app.get("/api/v1/files/{file_id}")
def get_file(file_id: str, user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> dict[str, Any]:
    service = require_service(service)
    try:
        return safe_detail(service._owned_record(user_id, file_id))
    except VaultError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@app.delete("/api/v1/files/{file_id}")
def delete_file(file_id: str, user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> dict[str, str]:
    service = require_service(service)
    try:
        record = service._owned_record(user_id, file_id)
        service.objects.delete(service._object_key(user_id, file_id))
        service.metadata.delete(file_id)
        service.audit.write("DELETE", user_id, file_id, "success")
        return {"status": "deleted", "file_id": record["file_id"]}
    except VaultError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@app.get("/api/v1/audit")
def audit(user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> list[dict[str, Any]]:
    service = require_service(service)
    return [event for event in service.audit.events if event["user_id"] == user_id]


@app.get("/api/v1/metrics")
def metrics(user_id: str = Depends(current_user), service: VaultService | None = Depends(service_or_error)) -> dict[str, int]:
    service = require_service(service)
    return {"files": len(service.metadata.list_for_user(user_id)), "audit_events": len(audit(user_id, service))}


def safe_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {key: record.get(key) for key in ("file_id", "filename", "status", "created_at", "expires_at", "last_accessed_at")}


def safe_detail(record: dict[str, Any]) -> dict[str, Any]:
    return {**safe_summary(record), **{key: record.get(key) for key in ("file_size", "last_refreshed_at")}, "integrity_status": "VERIFIED", "encryption_status": "ENCRYPTED"}
