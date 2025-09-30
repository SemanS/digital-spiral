from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

_BASELINES = {
    "comment": 30,
    "transition": 45,
    "set-labels": 20,
    "link": 25,
}

DEFAULT_SEED_PATH = Path(os.getenv("SEED_DATA_PATH", "artifacts/forge_demo_seed.json"))


def estimate_seconds(action: str, context: Mapping[str, Any] | None = None) -> int:
    """Estimate seconds saved for a given action type."""

    base = _BASELINES.get(action, 30)
    bundle = 1
    if context:
        bundle = int(context.get("bundle_size", 1)) or 1
    return max(int(base * bundle), 0)


def estimate_savings(action_kind: str, context: Mapping[str, Any] | None = None) -> int:
    """Backward compatible wrapper for older callers."""

    return estimate_seconds(action_kind, context)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rank = (len(values) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    weight = rank - lower
    return float(values[lower] * (1 - weight) + values[upper] * weight)


def _window_events(tenant_id: str, days: int, now: datetime | None = None) -> list[int]:
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=days)
    values: list[int] = []
    from . import credit

    for event in credit.all_events(tenant_id):
        if event.ts >= cutoff:
            values.append(int(event.impact.secondsSaved))
    return values


def seconds_saved_window(tenant_id: str, window_days: int) -> dict[str, Any]:
    """Return descriptive statistics for a rolling window."""

    if window_days <= 0:
        return {
            "windowDays": window_days,
            "count": 0,
            "totalSeconds": 0.0,
            "avgSeconds": 0.0,
            "p50Seconds": 0.0,
            "p90Seconds": 0.0,
        }
    values = sorted(_window_events(tenant_id, window_days))
    total = float(sum(values))
    count = len(values)
    avg = float(total / count) if count else 0.0
    return {
        "windowDays": window_days,
        "count": count,
        "totalSeconds": total,
        "avgSeconds": avg,
        "p50Seconds": float(_percentile(values, 0.5)),
        "p90Seconds": float(_percentile(values, 0.9)),
    }


def seconds_saved_summary(tenant_id: str, windows: Iterable[int] = (7, 30)) -> dict[str, Any]:
    """Return summary statistics for the provided windows (in days)."""

    summaries: dict[str, Any] = {}
    for window in windows:
        summaries[f"{window}d"] = seconds_saved_window(tenant_id, window)
    return {"windows": summaries}


@dataclass
class IssueBaseline:
    issue_key: str
    created: datetime
    first_response: datetime | None
    resolved: datetime | None

    @property
    def frt_seconds(self) -> float | None:
        if not self.first_response:
            return None
        return max((self.first_response - self.created).total_seconds(), 0.0)

    @property
    def ttr_seconds(self) -> float | None:
        if not self.resolved:
            return None
        return max((self.resolved - self.created).total_seconds(), 0.0)


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return None


def _load_seed_payload(path: Path = DEFAULT_SEED_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _baseline_from_seed(seed: dict[str, Any]) -> list[IssueBaseline]:
    baselines: list[IssueBaseline] = []
    for raw_issue in seed.get("issues", []):
        key = str(raw_issue.get("key")) if raw_issue.get("key") else None
        created = _parse_datetime(raw_issue.get("created"))
        if not key or not created:
            continue
        comments = raw_issue.get("comments") or []
        first_comment_ts = None
        for comment in sorted(comments, key=lambda item: item.get("created") or ""):
            ts = _parse_datetime(comment.get("created"))
            if ts is not None:
                first_comment_ts = ts
                break
        resolved_ts = None
        for change in raw_issue.get("changelog", []):
            if not isinstance(change, dict):
                continue
            items = change.get("items") or []
            for item in items:
                if item.get("field") == "status" and str(item.get("to")) == "4":
                    resolved_candidate = _parse_datetime(change.get("created"))
                    if resolved_candidate is not None:
                        resolved_ts = resolved_candidate
        baselines.append(
            IssueBaseline(
                issue_key=key,
                created=created,
                first_response=first_comment_ts,
                resolved=resolved_ts,
            )
        )
    return baselines


def _apply_seconds_by_issue(tenant_id: str) -> dict[str, float]:
    totals: dict[str, float] = {}
    from . import credit

    for event in credit.all_events(tenant_id):
        totals[event.issueKey] = totals.get(event.issueKey, 0.0) + float(event.impact.secondsSaved)
    return totals


def _summary(values: Iterable[float]) -> dict[str, Any]:
    materialised = sorted(float(value) for value in values if value is not None)
    if not materialised:
        return {"count": 0, "meanSeconds": 0.0, "p50Seconds": 0.0, "p90Seconds": 0.0}
    return {
        "count": len(materialised),
        "meanSeconds": float(statistics.mean(materialised)),
        "p50Seconds": float(_percentile(materialised, 0.5)),
        "p90Seconds": float(_percentile(materialised, 0.9)),
    }


def ttr_frt_baseline(tenant_id: str, seed_path: Path | None = None) -> dict[str, Any]:
    """Compare baseline ticket/response times with ledger improvements."""

    seed_payload = _load_seed_payload(seed_path or DEFAULT_SEED_PATH)
    baselines = _baseline_from_seed(seed_payload)
    apply_totals = _apply_seconds_by_issue(tenant_id)

    ttr_baseline = []
    ttr_with_apply = []
    frt_baseline = []
    frt_with_apply = []
    for item in baselines:
        saved = apply_totals.get(item.issue_key, 0.0)
        if item.ttr_seconds is not None:
            ttr_baseline.append(item.ttr_seconds)
            ttr_with_apply.append(max(item.ttr_seconds - saved, 0.0))
        if item.frt_seconds is not None:
            frt_baseline.append(item.frt_seconds)
            frt_with_apply.append(max(item.frt_seconds - saved, 0.0))

    return {
        "baseline": {
            "ttr": _summary(ttr_baseline),
            "frt": _summary(frt_baseline),
        },
        "withApply": {
            "ttr": _summary(ttr_with_apply),
            "frt": _summary(frt_with_apply),
        },
    }


def top_contributors(tenant_id: str, window_days: int = 30) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    since = now - timedelta(days=window_days)
    from . import credit

    summary = credit.summary(tenant_id, since=since)
    return [
        {
            "id": contributor.id,
            "secondsSaved": contributor.secondsSaved,
            "share": contributor.share,
            "events": contributor.events,
        }
        for contributor in summary.topContributors
    ]


def throughput(tenant_id: str, window_days: int = 7, now: datetime | None = None) -> dict[str, Any]:
    """Return apply throughput metrics for the specified window."""

    if window_days <= 0:
        return {"windowDays": window_days, "count": 0, "appliesPerDay": 0.0}
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=window_days)
    from . import credit

    apply_events = [
        event
        for event in credit.all_events(tenant_id)
        if event.ts >= cutoff and str(event.action or "").startswith("apply")
    ]
    count = len(apply_events)
    per_day = float(count) / float(window_days) if window_days else 0.0
    return {"windowDays": window_days, "count": count, "appliesPerDay": per_day}
