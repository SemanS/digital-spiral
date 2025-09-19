"""Simple append-only audit log with retention window."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "artifacts/audit-log.jsonl"))
RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "7"))


def _ensure_parent() -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _parse_ts(value: Any) -> datetime | None:
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    return None


def _prune(now: datetime) -> None:
    if not AUDIT_LOG_PATH.exists():
        return
    cutoff = now - timedelta(days=RETENTION_DAYS)
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    keep: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(payload.get("ts"))
        if ts is None or ts >= cutoff:
            keep.append(json.dumps(payload, ensure_ascii=False))
    if len(keep) == len(lines):
        return
    with AUDIT_LOG_PATH.open("w", encoding="utf-8") as handle:
        for entry in keep:
            handle.write(entry)
            handle.write("\n")


def log_event(event: Mapping[str, Any]) -> None:
    now = datetime.now(UTC)
    payload = dict(event)
    if "ts" not in payload:
        payload["ts"] = now.isoformat()
    _ensure_parent()
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.write("\n")
    _prune(now)
