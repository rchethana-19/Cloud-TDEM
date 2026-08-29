from __future__ import annotations

from importlib import import_module
from typing import Any


class EngineUnavailable(RuntimeError):
    pass


class BranchCryptoAdapter:
    """Thin adapter over the existing crypto engine service API."""

    def __init__(self, module_name: str = "crypto_engine.service") -> None:
        try:
            self.engine = import_module(module_name)
        except ImportError as error:
            raise EngineUnavailable("Crypto engine is not installed on this branch") from error

    def encrypt(self, identity: str, plaintext: bytes, kseed: bytes) -> dict[str, Any]:
        return self.engine.encrypt_data(identity, plaintext, kseed)

    def decrypt(self, identity: str, encrypted: dict[str, Any], kseed: bytes) -> bytes:
        return self.engine.retrieve_data(identity, encrypted, kseed)

    def refresh(self, identity: str, encrypted: dict[str, Any], kseed: bytes) -> dict[str, Any]:
        return self.engine.refresh_key(identity, encrypted, kseed)


class BranchRiskAdapter:
    """Thin adapter over the existing AI service API."""

    def __init__(self, module_name: str = "major_project.service") -> None:
        try:
            self.engine = import_module(module_name)
        except ImportError as error:
            raise EngineUnavailable("AI engine is not installed on this branch") from error

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        return self.engine.evaluate_request(context)
