"""GitHub X-Hub-Signature-256 verification."""

from __future__ import annotations

import hashlib
import hmac


def sign_body(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, body: bytes, header: str | None) -> bool:
    """Return True only when the header matches the HMAC of the raw body.

    Comparison uses hmac.compare_digest. A missing secret, a missing header,
    or a header that is not sha256=... is a failure.
    """
    if not secret or not header:
        return False
    provided = header.strip()
    if not provided.startswith("sha256=") or len(provided) != len("sha256=") + 64:
        return False
    expected = sign_body(secret, body)
    return hmac.compare_digest(expected, provided)
