"""Helpers for verifying mock Jira webhook signatures in tests."""

from __future__ import annotations

import hashlib
from typing import Tuple


def compute_sig_v2(secret: str, body_bytes: bytes) -> str:
    """Return the sha256(secret + body) digest used by signature v2."""

    data = secret.encode("utf-8") + body_bytes
    return hashlib.sha256(data).hexdigest()


def get_sig_from_headers(headers: dict) -> Tuple[str, str]:
    """Extract the algorithm and hex digest from webhook headers."""

    raw = headers.get("X-MockJira-Signature") or ""
    alg, _, hexdigest = raw.partition("=")
    return alg, hexdigest
