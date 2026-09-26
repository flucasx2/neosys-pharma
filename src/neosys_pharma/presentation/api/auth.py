from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticationSettings:
    enabled: bool
    username: str
    password: str
    session_secret: str
    cookie_secure: bool
    session_duration_seconds: int = 8 * 60 * 60

    @classmethod
    def from_environment(cls) -> AuthenticationSettings:
        enabled = os.getenv("NEOSYS_AUTH_ENABLED", "false").lower() in {"1", "true", "yes"}
        username = os.getenv("NEOSYS_AUTH_USERNAME", "")
        password = os.getenv("NEOSYS_AUTH_PASSWORD", "")
        secret = os.getenv("NEOSYS_SESSION_SECRET", "")
        secure = os.getenv("NEOSYS_COOKIE_SECURE", "true").lower() in {"1", "true", "yes"}
        if enabled:
            if not username or not password:
                raise RuntimeError(
                    "NEOSYS_AUTH_USERNAME et NEOSYS_AUTH_PASSWORD sont obligatoires."
                )
            if len(secret) < 32:
                raise RuntimeError("NEOSYS_SESSION_SECRET doit contenir au moins 32 caractères.")
        return cls(enabled, username, password, secret, secure)

    def credentials_are_valid(self, username: str, password: str) -> bool:
        return hmac.compare_digest(username, self.username) and hmac.compare_digest(
            password, self.password
        )

    def create_session(self) -> str:
        payload = json.dumps(
            {"sub": self.username, "exp": int(time.time()) + self.session_duration_seconds},
            separators=(",", ":"),
        ).encode()
        encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
        signature = hmac.new(self.session_secret.encode(), encoded, hashlib.sha256).digest()
        return f"{encoded.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"

    def session_is_valid(self, token: str | None) -> bool:
        if not token or "." not in token:
            return False
        encoded, supplied_signature = token.split(".", 1)
        expected = hmac.new(
            self.session_secret.encode(), encoded.encode(), hashlib.sha256
        ).digest()
        try:
            signature_padding = "=" * (-len(supplied_signature) % 4)
            signature = base64.urlsafe_b64decode(supplied_signature + signature_padding)
            payload = json.loads(
                base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
            )
        except (ValueError, json.JSONDecodeError):
            return False
        return (
            hmac.compare_digest(signature, expected)
            and payload.get("sub") == self.username
            and int(payload.get("exp", 0)) >= int(time.time())
        )


def safe_destination(value: str | None) -> str:
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/encaissement"
