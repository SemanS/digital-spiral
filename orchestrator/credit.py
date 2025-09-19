from __future__ import annotations

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .metrics import estimate_savings
from .models import (
    AgentCreditSummary,
    Attribution,
    CreditEvent,
    CreditSummary,
    ContributorSummary,
    Impact,
    IssueCreditSummary,
)

LEDGER_PATH = Path(os.getenv("CREDIT_LEDGER_PATH", "artifacts/credit-ledger.jsonl"))
AUTOMATION_AGENT_ID = os.getenv("DEFAULT_AUTOMATION_AGENT", "ai.summarizer")
HALF_LIFE_DAYS = 14.0
_DECAY_LAMBDA = math.log(2.0) / HALF_LIFE_DAYS

_LEDGER: List[CreditEvent] = []
_INDEX_BY_ID: Dict[str, CreditEvent] = {}
_INDEX_BY_ISSUE: Dict[str, List[CreditEvent]] = {}
_INDEX_BY_ACTOR: Dict[str, List[CreditEvent]] = {}
_PREV_HASH: Optional[str] = None
_CURRENT_LEDGER_PATH: Path = LEDGER_PATH
_IDEMPOTENCY_CACHE: Dict[str, Tuple[str, str]] = {}


def _actor_label(actor: Mapping[str, Any]) -> str:
    actor_type = str(actor.get("type") or "human").strip().lower()
    actor_id = str(actor.get("id") or "unknown").strip() or "unknown"
    return f"{actor_type}.{actor_id}"


def actor_agent_id(actor: Mapping[str, Any]) -> str:
    """Return the canonical agent identifier for an actor mapping."""

    return _actor_label(actor)


def _normalize(obj: Any) -> Any:
    if isinstance(obj, CreditEvent):
        return _normalize(obj.model_dump(mode="json", by_alias=True))
    if isinstance(obj, Attribution):
        return _normalize(obj.model_dump(mode="json", by_alias=True))
    if isinstance(obj, Impact):
        return _normalize(obj.model_dump(mode="json", by_alias=True))
    if hasattr(obj, "model_dump"):
        return _normalize(obj.model_dump())
    if isinstance(obj, dict):
        return {str(key): _normalize(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_normalize(item) for item in obj]
    if isinstance(obj, datetime):
        return obj.astimezone(UTC).isoformat()
    return obj


def _canon(obj: Any) -> bytes:
    return json.dumps(_normalize(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _register_event(event: CreditEvent) -> None:
    _LEDGER.append(event)
    _INDEX_BY_ID[event.id] = event
    _INDEX_BY_ISSUE.setdefault(event.issueKey, []).append(event)
    for attribution in event.attributions:
        _INDEX_BY_ACTOR.setdefault(attribution.agentId, []).append(event)


def _persist_event(event: CreditEvent) -> None:
    _CURRENT_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _CURRENT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        json.dump(event.model_dump(mode="json", by_alias=True), handle, ensure_ascii=False)
        handle.write("\n")


def reset_ledger(path: str | Path | None = None, *, truncate: bool = True) -> None:
    """Reset in-memory indexes and optionally truncate the ledger file."""

    global _LEDGER, _INDEX_BY_ID, _INDEX_BY_ISSUE, _INDEX_BY_ACTOR, _PREV_HASH, _CURRENT_LEDGER_PATH, _IDEMPOTENCY_CACHE
    _LEDGER = []
    _INDEX_BY_ID = {}
    _INDEX_BY_ISSUE = {}
    _INDEX_BY_ACTOR = {}
    _PREV_HASH = None
    _IDEMPOTENCY_CACHE = {}
    if path is not None:
        _CURRENT_LEDGER_PATH = Path(path)
    if truncate and _CURRENT_LEDGER_PATH.exists():
        _CURRENT_LEDGER_PATH.unlink()


def load_ledger(path: str | Path | None = None) -> None:
    """Load existing JSONL ledger into memory."""

    global _PREV_HASH, _CURRENT_LEDGER_PATH
    if path is not None:
        _CURRENT_LEDGER_PATH = Path(path)
    if not _CURRENT_LEDGER_PATH.exists():
        _CURRENT_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        return
    reset_ledger(_CURRENT_LEDGER_PATH, truncate=False)
    with _CURRENT_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            event = CreditEvent.model_validate(payload)
            _register_event(event)
            _PREV_HASH = event.hash


def _ensure_attributions(attributions: Iterable[Attribution | Mapping[str, Any]] | None) -> List[Attribution]:
    if not attributions:
        return []
    normalized = [Attribution.model_validate(item) for item in attributions]
    total_weight = sum(float(item.weight) for item in normalized)
    if normalized and not math.isclose(total_weight, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("Attribution weights must sum to 1.0")
    return normalized


def append_event(
    payload: Mapping[str, Any] | None = None,
    /,
    *,
    issue_key: str | None = None,
    action: str | None = None,
    actor: Mapping[str, Any] | None = None,
    impact: Impact | Mapping[str, Any] | None = None,
    attributions: Iterable[Attribution | Mapping[str, Any]] | None = None,
    parents: Iterable[str] | None = None,
    inputs: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    id: str | None = None,
    ts: datetime | str | None = None,
    idempotency_key: str | None = None,
    attribution_reason: str | None = None,
) -> CreditEvent:
    """Append a new credit event and persist it to the ledger."""

    global _PREV_HASH
    now = datetime.now(UTC)
    payload_dict: Dict[str, Any] = dict(payload or {})
    if issue_key is not None:
        payload_dict.setdefault("issueKey", issue_key)
    if action is not None:
        payload_dict.setdefault("action", action)
    if actor is not None:
        payload_dict.setdefault("actor", dict(actor))
    if impact is not None:
        payload_dict.setdefault("impact", impact)
    legacy_attribution = payload_dict.pop("attribution", None)
    if attributions is not None:
        payload_dict.setdefault("attributions", list(attributions))
    elif legacy_attribution is not None and "attributions" not in payload_dict:
        if isinstance(legacy_attribution, Mapping):
            splits = legacy_attribution.get("split")
            if splits:
                payload_dict["attributions"] = list(splits)
            reason = legacy_attribution.get("reason")
            if reason and "attributionReason" not in payload_dict:
                payload_dict["attributionReason"] = reason
    if parents is not None:
        payload_dict.setdefault("parents", list(parents))
    if inputs is not None:
        payload_dict.setdefault("inputs", dict(inputs))
    if metadata is not None:
        payload_dict.setdefault("metadata", dict(metadata))
    if id is not None:
        payload_dict.setdefault("id", id)
    if ts is not None:
        payload_dict.setdefault("ts", ts)
    if attribution_reason is not None:
        payload_dict.setdefault("attributionReason", attribution_reason)

    if "issueKey" not in payload_dict or not payload_dict["issueKey"]:
        raise ValueError("issue_key is required")
    if "action" not in payload_dict or not payload_dict["action"]:
        raise ValueError("action is required")

    payload_dict.setdefault("id", f"evt_{int(time.time() * 1000)}")
    ts_value = payload_dict.get("ts")
    if ts_value is None:
        payload_dict["ts"] = now
    elif isinstance(ts_value, str):
        payload_dict["ts"] = datetime.fromisoformat(ts_value)
    elif isinstance(ts_value, datetime):
        payload_dict["ts"] = ts_value.astimezone(UTC)
    else:  # pragma: no cover - defensive guard
        raise TypeError("Unsupported ts value")

    actor_payload = payload_dict.get("actor") or {}
    normalized_actor = dict(actor_payload) if isinstance(actor_payload, Mapping) else {}
    normalized_actor.setdefault("type", "human")
    normalized_actor.setdefault("id", "unknown")
    normalized_actor["type"] = str(normalized_actor.get("type") or "human").strip().lower() or "human"
    normalized_actor["id"] = str(normalized_actor.get("id") or "unknown").strip() or "unknown"
    payload_dict["actor"] = normalized_actor

    payload_dict.setdefault("parents", [])
    payload_dict["parents"] = [str(value) for value in payload_dict.get("parents", [])]

    impact_model = payload_dict.get("impact")
    if isinstance(impact_model, Impact):
        payload_dict["impact"] = impact_model
    else:
        payload_dict["impact"] = Impact.model_validate(impact_model or {"secondsSaved": 0})

    payload_dict["attributions"] = _ensure_attributions(payload_dict.get("attributions"))
    payload_dict.setdefault("metadata", {})
    payload_dict.setdefault("attributionReason", payload_dict.get("attributionReason"))

    digest_payload = dict(payload_dict)
    digest_payload.pop("id", None)
    digest_payload.pop("ts", None)
    digest_payload.pop("prevHash", None)
    digest_payload.pop("hash", None)
    payload_digest = hashlib.sha256(_canon(digest_payload)).hexdigest()
    if idempotency_key:
        cached = _IDEMPOTENCY_CACHE.get(idempotency_key)
        if cached:
            cached_id, cached_digest = cached
            if cached_digest != payload_digest:
                raise ValueError("Idempotency payload mismatch")
            existing_event = _INDEX_BY_ID.get(cached_id)
            if existing_event is not None:
                return existing_event

    payload_dict.setdefault("prevHash", _PREV_HASH)
    event_model = CreditEvent.model_validate(payload_dict)
    base_for_hash = event_model.model_dump(mode="json", by_alias=True)
    base_for_hash.pop("hash", None)
    canon = _canon(base_for_hash)
    prev_bytes = (event_model.prevHash or "").encode("utf-8")
    event_hash = hashlib.sha256(prev_bytes + canon).hexdigest()
    event_model.hash = event_hash
    _register_event(event_model)
    _PREV_HASH = event_hash
    _persist_event(event_model)
    if idempotency_key:
        _IDEMPOTENCY_CACHE[idempotency_key] = (event_model.id, payload_digest)
    return event_model


def tip_credit(
    issue_key: str,
    proposal: Mapping[str, Any] | None,
    actor: Mapping[str, Any],
    execution_result: Mapping[str, Any] | None = None,
) -> Tuple[List[Attribution], Optional[str]]:
    """Heuristic split of credit between automation and human."""

    actor_id = actor_agent_id(actor)
    shares = _ensure_attributions(
        [
            Attribution(agent_id=AUTOMATION_AGENT_ID, weight=0.5),
            Attribution(agent_id=actor_id, weight=0.5),
        ]
    )
    reason = "AI návrh + ľudské schválenie"
    return shares, reason


def _events_since(events: Iterable[CreditEvent], since: Optional[datetime]) -> List[CreditEvent]:
    if since is None:
        return list(events)
    return [event for event in events if event.ts >= since]


def _aggregate_contributors(events: Iterable[CreditEvent]) -> Dict[str, Dict[str, float]]:
    totals: Dict[str, Dict[str, float]] = {}
    for event in events:
        impact_seconds = event.impact.secondsSaved
        for attribution in event.attributions:
            bucket = totals.setdefault(attribution.agentId, {"seconds": 0.0, "events": 0.0})
            bucket["seconds"] += impact_seconds * float(attribution.weight)
            bucket["events"] += 1.0
    return totals


def _events_within_window(window_days: int, *, now: Optional[datetime] = None) -> List[CreditEvent]:
    if window_days <= 0:
        return []
    snapshot = list(_LEDGER)
    if not snapshot:
        return []
    pivot = (now or datetime.now(UTC)) - timedelta(days=window_days)
    return [event for event in snapshot if event.ts >= pivot]


def issue_summary(issue_key: str, since: Optional[datetime] = None, limit: int = 5) -> IssueCreditSummary:
    events = list(_INDEX_BY_ISSUE.get(issue_key, []))
    total_seconds = sum(event.impact.secondsSaved for event in events)
    recent = list(reversed(events[-limit:])) if limit else list(reversed(events))
    window_events = _events_since(events, since)
    window_seconds = sum(event.impact.secondsSaved for event in window_events)
    contributors_raw = _aggregate_contributors(events)
    contributors_total = sum(item["seconds"] for item in contributors_raw.values()) or 1.0
    contributors = [
        ContributorSummary(
            id=actor_id,
            secondsSaved=item["seconds"],
            share=item["seconds"] / contributors_total if contributors_total else 0.0,
            events=int(item["events"]),
        )
        for actor_id, item in sorted(
            contributors_raw.items(), key=lambda pair: pair[1]["seconds"], reverse=True
        )
    ]
    return IssueCreditSummary(
        issueKey=issue_key,
        totalSecondsSaved=total_seconds,
        windowSecondsSaved=window_seconds if since else None,
        windowStart=since,
        contributors=contributors,
        recentEvents=recent,
    )


def _decayed_score(events: Iterable[CreditEvent], actor_id: str, now: Optional[datetime] = None) -> float:
    now = now or datetime.now(UTC)
    score_sum = 0.0
    weight_sum = 0.0
    for event in events:
        split_weight = next(
            (split.weight for split in event.attributions if split.agentId == actor_id),
            0.0,
        )
        if split_weight <= 0:
            continue
        age_days = max((now - event.ts).total_seconds() / 86400.0, 0.0)
        weight = math.exp(-_DECAY_LAMBDA * age_days)
        seconds = event.impact.secondsSaved * split_weight
        quality = event.impact.quality if event.impact.quality is not None else 1.0
        score_sum += seconds * quality * weight
        weight_sum += weight
    if weight_sum <= 0:
        return 0.0
    return score_sum / weight_sum


def agent_summary(agent_id: str, since: Optional[datetime] = None, limit: int = 20) -> AgentCreditSummary:
    events = _INDEX_BY_ACTOR.get(agent_id, [])
    window_events = _events_since(events, since)
    total_seconds = sum(
        event.impact.secondsSaved
        * next((split.weight for split in event.attributions if split.agentId == agent_id), 0.0)
        for event in window_events
    )
    score = _decayed_score(events, agent_id)
    recent = list(reversed(events[-limit:])) if limit else list(reversed(events))
    return AgentCreditSummary(
        agentId=agent_id,
        totalSecondsSaved=total_seconds,
        score=score,
        events=recent,
    )


def summary(since: Optional[datetime] = None, limit: int = 10) -> CreditSummary:
    events = _events_since(_LEDGER, since)
    total_seconds = sum(event.impact.secondsSaved for event in events)
    contributors_raw = _aggregate_contributors(events)
    total_contrib = sum(item["seconds"] for item in contributors_raw.values()) or 1.0
    contributors = [
        ContributorSummary(
            id=actor_id,
            secondsSaved=item["seconds"],
            share=item["seconds"] / total_contrib if total_contrib else 0.0,
            events=int(item["events"]),
        )
        for actor_id, item in sorted(
            contributors_raw.items(), key=lambda pair: pair[1]["seconds"], reverse=True
        )[:limit]
    ]
    return CreditSummary(
        since=since,
        totalSecondsSaved=total_seconds,
        eventCount=len(events),
        topContributors=contributors,
    )


def credit_chain(limit: int = 100) -> List[CreditEvent]:
    if limit <= 0:
        return []
    return list(reversed(_LEDGER[-limit:]))


def all_events() -> List[CreditEvent]:
    """Return a snapshot copy of all credit events."""

    return list(_LEDGER)


def events_for_issue(issue_key: str) -> List[CreditEvent]:
    """Return all recorded events for an issue key."""

    return list(_INDEX_BY_ISSUE.get(issue_key, []))


def top_agents(window_days: int, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return aggregate contribution per agent for the given window."""

    if window_days <= 0:
        return []
    events = _events_within_window(window_days)
    totals = _aggregate_contributors(events)
    ordered = sorted(totals.items(), key=lambda item: item[1]["seconds"], reverse=True)
    payload: List[Dict[str, Any]] = []
    for agent_id, bucket in ordered:
        payload.append(
            {
                "agent_id": agent_id,
                "seconds": float(bucket["seconds"]),
                "events": int(bucket["events"]),
            }
        )
    if limit is not None and limit >= 0:
        return payload[:limit]
    return payload


def rollup_for_issue(issue_key: str, since: Optional[datetime] = None, limit: int = 5) -> IssueCreditSummary:
    """Alias for :func:`issue_summary` to match orchestration terminology."""

    return issue_summary(issue_key, since=since, limit=limit)


def rollup_for_agent(agent_id: str, since: Optional[datetime] = None, limit: int = 20) -> AgentCreditSummary:
    """Alias for :func:`agent_summary` used by API endpoints."""

    return agent_summary(agent_id, since=since, limit=limit)


def ewma_score(agent_id: str, now: Optional[datetime] = None) -> float:
    """Expose the exponentially weighted moving average score for an agent."""

    events = _INDEX_BY_ACTOR.get(agent_id, [])
    return _decayed_score(events, agent_id, now=now)


def build_apply_event(
    issue_key: str,
    proposal: Mapping[str, Any],
    actor: Mapping[str, Any],
    execution_result: Mapping[str, Any],
    *,
    parents: Iterable[str] | None = None,
    idempotency_key: str | None = None,
) -> CreditEvent:
    quality = execution_result.get("quality")
    seconds_value = execution_result.get("secondsSaved") or execution_result.get("seconds")
    seconds = int(seconds_value) if seconds_value is not None else estimate_savings(str(proposal.get("kind")))
    shares, reason = tip_credit(issue_key, proposal, actor, execution_result)
    inputs = {
        "proposalId": proposal.get("id"),
        "kind": proposal.get("kind"),
    }
    for field in ("from", "to", "labels", "transitionId"):
        if field in proposal:
            inputs[field] = proposal[field]
    return append_event(
        issue_key=issue_key,
        action=f"apply.{proposal.get('kind')}",
        actor=actor,
        inputs=inputs,
        impact={"secondsSaved": seconds, "quality": quality},
        attributions=shares,
        parents=list(parents or []),
        idempotency_key=idempotency_key,
        attribution_reason=reason,
    )


# Load ledger data on module import so API endpoints can serve summaries.
load_ledger()
