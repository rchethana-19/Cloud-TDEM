from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Protocol
from uuid import uuid4


class CryptoAdapter(Protocol):
    def encrypt(self, identity: str, plaintext: bytes, kseed: bytes) -> dict[str, Any]: ...
    def decrypt(self, identity: str, encrypted: dict[str, Any], kseed: bytes) -> bytes: ...
    def refresh(self, identity: str, encrypted: dict[str, Any], kseed: bytes) -> dict[str, Any]: ...


class RiskAdapter(Protocol):
    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]: ...


class ObjectStore(Protocol):
    def put(self, key: str, value: dict[str, Any]) -> None: ...
    def get(self, key: str) -> dict[str, Any]: ...
    def delete(self, key: str) -> None: ...


class MetadataStore(Protocol):
    def put(self, value: dict[str, Any]) -> None: ...
    def get(self, file_id: str) -> dict[str, Any] | None: ...
    def list_for_user(self, user_id: str) -> list[dict[str, Any]]: ...
    def delete(self, file_id: str) -> None: ...


@dataclass
class InMemoryObjectStore:
    values: dict[str, dict[str, Any]] = field(default_factory=dict)

    def put(self, key: str, value: dict[str, Any]) -> None:
        self.values[key] = value

    def get(self, key: str) -> dict[str, Any]:
        if key not in self.values:
            raise KeyError(key)
        return self.values[key]

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


@dataclass
class InMemoryMetadataStore:
    values: dict[str, dict[str, Any]] = field(default_factory=dict)

    def put(self, value: dict[str, Any]) -> None:
        self.values[value["file_id"]] = value

    def get(self, file_id: str) -> dict[str, Any] | None:
        return self.values.get(file_id)

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return [value for value in self.values.values() if value["user_id"] == user_id]

    def delete(self, file_id: str) -> None:
        self.values.pop(file_id, None)


@dataclass
class AuditLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def write(self, action: str, user_id: str, file_id: str | None, result: str, **details: Any) -> None:
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": str(uuid4()),
            "action": action,
            "user_id": user_id,
            "file_id": file_id,
            "result": result,
            **details,
        })


class VaultError(Exception):
    status_code = 400


class NotFoundError(VaultError):
    status_code = 404


class ForbiddenError(VaultError):
    status_code = 403


class ExpiredError(VaultError):
    status_code = 410


class RiskDeniedError(VaultError):
    status_code = 403


@dataclass
class VaultService:
    crypto: CryptoAdapter
    risk: RiskAdapter
    objects: ObjectStore
    metadata: MetadataStore
    audit: AuditLog
    kseed: bytes

    def ingest(self, user_id: str, filename: str, plaintext: bytes, expires_at: datetime) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        if expires_at <= now:
            raise VaultError("expires_at must be in the future")
        file_id = str(uuid4())
        encrypted = self.crypto.encrypt(user_id, plaintext, self.kseed)
        record = {
            "file_id": file_id,
            "user_id": user_id,
            "filename": filename,
            "file_size": len(plaintext),
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "ACTIVE",
            "integrity_hash": sha256(plaintext).hexdigest(),
        }
        self.objects.put(self._object_key(user_id, file_id), encrypted)
        self.metadata.put(record)
        self.audit.write("UPLOAD_SUCCESS", user_id, file_id, "success")
        return record

    def retrieve(self, user_id: str, file_id: str, context: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
        record = self._owned_record(user_id, file_id)
        if datetime.fromisoformat(record["expires_at"]) <= datetime.now(timezone.utc):
            record["status"] = "EXPIRED"
            self.metadata.put(record)
            self.audit.write("RETRIEVE_EXPIRED", user_id, file_id, "rejected")
            raise ExpiredError("file has expired")
        risk = self.risk.evaluate({**context, "file_sensitivity": context.get("file_sensitivity", "Medium")})
        if risk.get("decision") != "ALLOW":
            self.audit.write("RETRIEVE_DENIED", user_id, file_id, "rejected", risk_score=risk.get("risk_score"), decision=risk.get("decision"))
            raise RiskDeniedError("access denied by risk policy")
        plaintext = self.crypto.decrypt(user_id, self.objects.get(self._object_key(user_id, file_id)), self.kseed)
        if sha256(plaintext).hexdigest() != record["integrity_hash"]:
            self.audit.write("INTEGRITY_FAILURE", user_id, file_id, "failed")
            raise VaultError("integrity verification failed")
        record["last_accessed_at"] = datetime.now(timezone.utc).isoformat()
        self.metadata.put(record)
        self.audit.write("RETRIEVE_ALLOWED", user_id, file_id, "success", risk_score=risk.get("risk_score"))
        return record, plaintext

    def refresh(self, user_id: str, file_id: str, expires_at: datetime, context: dict[str, Any]) -> dict[str, Any]:
        record = self._owned_record(user_id, file_id)
        if expires_at <= datetime.now(timezone.utc):
            raise VaultError("expires_at must be in the future")
        risk = self.risk.evaluate(context)
        if risk.get("decision") != "ALLOW":
            self.audit.write("REFRESH_FAILED", user_id, file_id, "rejected", risk_score=risk.get("risk_score"))
            raise RiskDeniedError("refresh denied by risk policy")
        object_key = self._object_key(user_id, file_id)
        updated = self.crypto.refresh(user_id, self.objects.get(object_key), self.kseed)
        self.objects.put(object_key, updated)
        record["expires_at"] = expires_at.isoformat()
        record["last_refreshed_at"] = datetime.now(timezone.utc).isoformat()
        record["status"] = "ACTIVE"
        self.metadata.put(record)
        self.audit.write("REFRESH_SUCCESS", user_id, file_id, "success")
        return record

    def _owned_record(self, user_id: str, file_id: str) -> dict[str, Any]:
        record = self.metadata.get(file_id)
        if record is None:
            raise NotFoundError("file not found")
        if record["user_id"] != user_id:
            raise ForbiddenError("file does not belong to the authenticated user")
        return record

    @staticmethod
    def _object_key(user_id: str, file_id: str) -> str:
        return f"users/{user_id}/{file_id}/encrypted-data"
