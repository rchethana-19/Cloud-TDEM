from datetime import datetime, timedelta, timezone

import pytest

from app.services.vault import (
    AuditLog,
    ExpiredError,
    ForbiddenError,
    InMemoryMetadataStore,
    InMemoryObjectStore,
    RiskDeniedError,
    VaultService,
)


class FakeCrypto:
    def encrypt(self, identity, plaintext, kseed):
        return {"payload": plaintext}

    def decrypt(self, identity, encrypted, kseed):
        return encrypted["payload"]

    def refresh(self, identity, encrypted, kseed):
        return encrypted


class FakeRisk:
    def __init__(self, decision="ALLOW"):
        self.decision = decision
        self.calls = []

    def evaluate(self, context):
        self.calls.append(context)
        return {"decision": self.decision, "risk_score": 0.9 if self.decision == "DENY" else 0.1}


def make_service(risk=None):
    return VaultService(FakeCrypto(), risk or FakeRisk(), InMemoryObjectStore(), InMemoryMetadataStore(), AuditLog(), b"seed")


def expiry(hours=1):
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def test_ingest_and_retrieve_verifies_risk_before_crypto():
    risk = FakeRisk()
    service = make_service(risk)
    record = service.ingest("user-a", "note.txt", b"secret", expiry())

    returned, plaintext = service.retrieve("user-a", record["file_id"], {"trusted_device": True})

    assert returned["filename"] == "note.txt"
    assert plaintext == b"secret"
    assert risk.calls == [{"trusted_device": True, "file_sensitivity": "Medium"}]


def test_denied_risk_blocks_retrieval():
    service = make_service(FakeRisk("DENY"))
    record = service.ingest("user-a", "note.txt", b"secret", expiry())

    with pytest.raises(RiskDeniedError):
        service.retrieve("user-a", record["file_id"], {})


def test_expiry_blocks_before_risk():
    risk = FakeRisk()
    service = make_service(risk)
    record = service.ingest("user-a", "note.txt", b"secret", expiry())
    stored = service.metadata.get(record["file_id"])
    stored["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    service.metadata.put(stored)

    with pytest.raises(ExpiredError):
        service.retrieve("user-a", record["file_id"], {})
    assert risk.calls == []


def test_owner_is_required():
    service = make_service()
    record = service.ingest("user-a", "note.txt", b"secret", expiry())

    with pytest.raises(ForbiddenError):
        service.retrieve("user-b", record["file_id"], {})
