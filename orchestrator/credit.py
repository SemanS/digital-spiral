from __future__ import annotations

import hashlib
import json
import math
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .metrics import estimate_savings
from .models import (
    AgentCreditSummary,
    Attribution,
    CreditEvent,
    CreditSplit,
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


def _actor_label(actor: Mapping[str, Any]) -> str:
    actor_type = str(actor.get("type") or "human").strip().lower()
    actor_id = str(actor.get("id") or "unknown").strip() or "unknown"
    return f"{actor_type}.{actor_id}"


def _normalize(obj: Any) -> Any:
    if isinstance(obj, CreditEvent):
        return _normalize(obj.model_dump())
    if isinstance(obj, Attribution):
        return _normalize(obj.model_dump())
    if isinstance(obj, CreditSplit):
        return _normalize(obj.model_dump())
    if isinstance(obj, Impact):
        return _normalize(obj.model_dump())
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
    for split in event.attribution.split:
        _INDEX_BY_ACTOR.setdefault(split.id, []).append(event)


def _persist_event(event: CreditEvent) -> None:
    _CURRENT_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _CURRENT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        json.dump(event.model_dump(mode="json"), handle, ensure_ascii=False)
        handle.write("\n")


def reset_ledger(path: str | Path | None = None, *, truncate: bool = True) -> None:
    """Reset in-memory indexes and optionally truncate the ledger file."""

    global _LEDGER, _INDEX_BY_ID, _INDEX_BY_ISSUE, _INDEX_BY_ACTOR, _PREV_HASH, _CURRENT_LEDGER_PATH
    _LEDGER = []
    _INDEX_BY_ID = {}
    _INDEX_BY_ISSUE = {}
    _INDEX_BY_ACTOR = {}
    _PREV_HASH = None
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


def _ensure_attribution(attribution: Mapping[str, Any] | Attribution | None) -> Attribution:
    if isinstance(attribution, Attribution):
        splits = [CreditSplit.model_validate(split) for split in attribution.split]
        return Attribution(split=_normalize_splits(splits), reason=attribution.reason)
    data = attribution or {}
    splits_raw = data.get("split") or []
    splits = [CreditSplit.model_validate(split) for split in splits_raw]
    reason = data.get("reason")
    return Attribution(split=_normalize_splits(splits), reason=reason)


def _normalize_splits(splits: Iterable[CreditSplit]) -> List[CreditSplit]:
    materialized = list(splits)
    if not materialized:
        return []
    totals: Dict[str, float] = {}
    for split in materialized:
        totals[split.id] = totals.get(split.id, 0.0) + float(split.weight)
    total_weight = sum(totals.values())
    if total_weight <= 0:
        total_weight = 1.0
    return [CreditSplit(id=actor_id, weight=value / total_weight) for actor_id, value in totals.items()]


def append_event(event: Mapping[str, Any]) -> CreditEvent:
    """Append a new credit event and persist it to the ledger."""

    global _PREV_HASH
    now = datetime.now(UTC)
    payload: Dict[str, Any] = dict(event)
    payload.setdefault("id", f"evt_{int(time.time() * 1000)}")
    ts_value = payload.get("ts")
    if ts_value is None:
        payload["ts"] = now
    elif isinstance(ts_value, str):
        payload["ts"] = datetime.fromisoformat(ts_value)
    elif isinstance(ts_value, datetime):
        payload["ts"] = ts_value.astimezone(UTC)
    else:
        raise TypeError("Unsupported ts value")
    actor_payload = payload.get("actor")
    if isinstance(actor_payload, Mapping):
        normalized_actor = dict(actor_payload)
    else:
        normalized_actor = {}
    normalized_actor.setdefault("type", "human")
    normalized_actor.setdefault("id", "unknown")
    normalized_actor["type"] = str(normalized_actor.get("type") or "human").lower()
    normalized_actor["id"] = str(normalized_actor.get("id") or "unknown")
    payload["actor"] = normalized_actor
    payload.setdefault("prev", _PREV_HASH)
    payload.setdefault("parents", [])
    attribution = _ensure_attribution(payload.get("attribution"))
    payload["attribution"] = attribution
    impact = payload.get("impact")
    if isinstance(impact, Impact):
        payload["impact"] = impact
    else:
        payload["impact"] = Impact.model_validate(impact or {"secondsSaved": 0})
    event_model = CreditEvent.model_validate(payload)
    base_for_hash = event_model.model_dump(mode="json")
    base_for_hash.pop("hash", None)
    canon = _canon(base_for_hash)
    prev_bytes = (_PREV_HASH or "").encode("utf-8")
    event_hash = hashlib.sha256(prev_bytes + canon).hexdigest()
    event_model.hash = event_hash
    _register_event(event_model)
    _PREV_HASH = event_hash
    _persist_event(event_model)
    return event_model


def tip_credit(
    issue_key: str,
    proposal: Mapping[str, Any] | None,
    actor: Mapping[str, Any],
    execution_result: Mapping[str, Any] | None = None,
) -> Attribution:
    """Heuristic split of credit between automation and human."""

    actor_id = _actor_label(actor)
    splits = [
        CreditSplit(id=AUTOMATION_AGENT_ID, weight=0.5),
        CreditSplit(id=actor_id, weight=0.5),
    ]
    reason = "AI návrh + ľudské schválenie"
    return Attribution(split=_normalize_splits(splits), reason=reason)


def _events_since(events: Iterable[CreditEvent], since: Optional[datetime]) -> List[CreditEvent]:
    if since is None:
        return list(events)
    return [event for event in events if event.ts >= since]


def _aggregate_contributors(events: Iterable[CreditEvent]) -> Dict[str, Dict[str, float]]:
    totals: Dict[str, Dict[str, float]] = {}
    for event in events:
        impact_seconds = event.impact.secondsSaved
        for split in event.attribution.split:
            bucket = totals.setdefault(split.id, {"seconds": 0.0, "events": 0.0})
            bucket["seconds"] += impact_seconds * float(split.weight)
            bucket["events"] += 1.0
    return totals


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
        split_weight = next((split.weight for split in event.attribution.split if split.id == actor_id), 0.0)
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
        event.impact.secondsSaved * next(
            (split.weight for split in event.attribution.split if split.id == agent_id), 0.0
        )
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
) -> CreditEvent:
    quality = execution_result.get("quality")
    seconds_value = execution_result.get("secondsSaved") or execution_result.get("seconds")
    seconds = int(seconds_value) if seconds_value is not None else estimate_savings(str(proposal.get("kind")))
    attribution = tip_credit(issue_key, proposal, actor, execution_result)
    inputs = {
        "proposalId": proposal.get("id"),
        "kind": proposal.get("kind"),
    }
    for field in ("from", "to", "labels", "transitionId"):
        if field in proposal:
            inputs[field] = proposal[field]
    event_payload = {
        "issueKey": issue_key,
        "actor": actor,
        "action": f"apply.{proposal.get('kind')}",
        "inputs": inputs,
        "impact": {"secondsSaved": seconds, "quality": quality},
        "attribution": attribution,
    }
    return append_event(event_payload)


# Load ledger data on module import so API endpoints can serve summaries.
load_ledger()
