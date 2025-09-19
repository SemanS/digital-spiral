"""Credit ledger operations backed by the SQL database."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import db
from .models import (
    AgentCreditSummary,
    Attribution,
    CreditEvent,
    CreditSummary,
    Impact,
    IssueCreditSummary,
    ContributorSummary,
)

LEDGER_PATH = Path(os.getenv("CREDIT_LEDGER_PATH", "artifacts/credit-ledger.jsonl"))
AUTOMATION_AGENT_ID = os.getenv("DEFAULT_AUTOMATION_AGENT", "ai.summarizer")
DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "demo")
HALF_LIFE_DAYS = 14.0
_DECAY_LAMBDA = math.log(2.0) / HALF_LIFE_DAYS


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


def _ensure_attributions(attributions: Iterable[Attribution | Mapping[str, Any]] | None) -> List[Attribution]:
    if not attributions:
        return []
    normalized = [Attribution.model_validate(item) for item in attributions]
    total_weight = sum(float(item.weight) for item in normalized)
    if normalized and not math.isclose(total_weight, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("Attribution weights must sum to 1.0")
    return normalized


def _record_to_event(record: db.CreditEventRecord) -> CreditEvent:
    impact = Impact(seconds_saved=int(record.seconds_saved), quality=record.impact_quality)
    actor_payload = dict(record.actor_payload or {})
    if "type" not in actor_payload:
        prefix = (record.actor_id or "human.unknown").split(".", 1)[0]
        actor_payload.setdefault("type", prefix or "human")
    if "id" not in actor_payload:
        actor_payload["id"] = (record.actor_id.split(".", 1)[1] if "." in record.actor_id else record.actor_id)
    return CreditEvent(
        id=record.event_id,
        ts=(record.event_ts or record.created_at).astimezone(UTC),
        issueKey=record.issue_key,
        actor=actor_payload,
        action=record.action_kind,
        inputs=dict(record.inputs or {}),
        impact=impact,
        attributions=[Attribution.model_validate(item) for item in record.attributions or []],
        parents=list(record.parents or []),
        prevHash=record.prev_hash,
        hash=record.hash,
        attributionReason=record.attribution_reason,
        metadata=dict(record.metadata_payload or {}),
    )


def _persist_json(event: CreditEvent) -> None:
    if not LEDGER_PATH:
        return
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        json.dump(event.model_dump(mode="json", by_alias=True), handle, ensure_ascii=False)
        handle.write("\n")


def reset_ledger(path: str | Path | None = None, *, truncate: bool = True) -> None:
    """Clear persisted ledger artifacts (and database) for testing purposes."""

    global LEDGER_PATH
    ledger_path = Path(path) if path else LEDGER_PATH
    LEDGER_PATH = ledger_path
    if truncate and ledger_path.exists():
        ledger_path.unlink()
    db.init_models()
    with db.session_scope() as session:
        try:
            session.query(db.CreditEventRecord).delete()
            session.query(db.ApplyActionRecord).delete()
        except Exception:  # pragma: no cover - tables may not exist yet
            session.rollback()


def load_ledger(path: str | Path | None = None) -> None:
    """Compatibility shim kept for legacy call-sites."""

    return None


def append_event(
    tenant_id: str,
    *,
    issue_key: str,
    action: str,
    actor: Mapping[str, Any],
    impact: Impact | Mapping[str, Any],
    attributions: Iterable[Attribution | Mapping[str, Any]] | None = None,
    parents: Iterable[str] | None = None,
    inputs: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    idempotency_key: str | None = None,
    attribution_reason: str | None = None,
    session: Session | None = None,
) -> CreditEvent:
    if not tenant_id:
        raise ValueError("tenant_id is required")
    normalized_actor = dict(actor or {})
    normalized_actor.setdefault("type", str(normalized_actor.get("type") or "human").strip().lower() or "human")
    normalized_actor.setdefault("id", str(normalized_actor.get("id") or "unknown").strip() or "unknown")
    normalized_actor.setdefault("display", actor.get("display"))

    event_impact = Impact.model_validate(impact)
    event_attributions = _ensure_attributions(attributions)
    parents_list = [str(value) for value in parents or []]
    metadata_dict = dict(metadata or {})
    inputs_dict = dict(inputs or {})

    now = datetime.now(UTC)
    payload = {
        "issueKey": issue_key,
        "action": action,
        "actor": normalized_actor,
        "impact": event_impact,
        "attributions": event_attributions,
        "parents": parents_list,
        "metadata": metadata_dict,
        "inputs": inputs_dict,
        "attributionReason": attribution_reason,
        "ts": now,
    }
    payload.setdefault("id", f"evt_{int(time.time() * 1000)}")

    digest_payload = dict(payload)
    digest_payload.pop("ts", None)
    payload_hash = hashlib.sha256(_canon(digest_payload)).hexdigest()

    def _store(active_session: Session) -> CreditEvent:
        if idempotency_key:
            existing = get_credit_event_by_idempotency(active_session, tenant_id, idempotency_key)
            if existing is not None:
                if existing.payload_hash != payload_hash:
                    raise ValueError("Idempotency payload mismatch")
                return _record_to_event(existing)

        prev = db.last_event_for_tenant(active_session, tenant_id)
        prev_hash = prev.hash if prev else None

        event_model = CreditEvent.model_validate(dict(payload))
        event_model.prevHash = prev_hash
        base_for_hash = event_model.model_dump(mode="json", by_alias=True)
        base_for_hash.pop("hash", None)
        canon = _canon(base_for_hash)
        prev_bytes = (prev_hash or "").encode("utf-8")
        event_hash = hashlib.sha256(prev_bytes + canon).hexdigest()
        event_model.hash = event_hash

        record = db.CreditEventRecord(
            tenant_id=tenant_id,
            issue_key=issue_key,
            action_kind=action,
            seconds_saved=int(event_model.impact.secondsSaved),
            impact_quality=event_model.impact.quality,
            actor_id=actor_agent_id(normalized_actor),
            actor_payload=normalized_actor,
            inputs=inputs_dict,
            attributions=[item.model_dump(mode="json", by_alias=True) for item in event_attributions],
            parents=parents_list,
            metadata_payload=metadata_dict,
            attribution_reason=attribution_reason,
            hash=event_hash,
            prev_hash=prev_hash,
            payload_hash=payload_hash,
            idempotency_key=idempotency_key or f"evt-{event_hash}",
            event_ts=event_model.ts,
            created_at=now,
        )
        active_session.add(record)
        db.upsert_agent(
            active_session,
            tenant_id,
            actor_agent_id(normalized_actor),
            kind=str(normalized_actor.get("type") or "human"),
            display_name=str(normalized_actor.get("display") or "") or None,
        )
        for attribution in event_attributions:
            agent_kind = attribution.agentId.split(".", 1)[0]
            db.upsert_agent(
                active_session,
                tenant_id,
                attribution.agentId,
                kind=agent_kind or "human",
            )
        active_session.flush()
        stored_event = _record_to_event(record)
        _persist_json(stored_event)
        return stored_event

    if session is not None:
        return _store(session)

    with db.session_scope() as scoped:
        return _store(scoped)


def get_credit_event_by_idempotency(session: Session, tenant_id: str, idempotency_key: str) -> Optional[db.CreditEventRecord]:
    if not idempotency_key:
        return None
    stmt = (
        select(db.CreditEventRecord)
        .where(
            db.CreditEventRecord.tenant_id == tenant_id,
            db.CreditEventRecord.idempotency_key == idempotency_key,
        )
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


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


def _aggregate_contributors(events: Iterable[CreditEvent]) -> Dict[str, Dict[str, float]]:
    totals: Dict[str, Dict[str, float]] = {}
    for event in events:
        impact_seconds = event.impact.secondsSaved
        for attribution in event.attributions:
            bucket = totals.setdefault(attribution.agentId, {"seconds": 0.0, "events": 0.0})
            bucket["seconds"] += impact_seconds * float(attribution.weight)
            bucket["events"] += 1.0
    return totals


def _decayed_score(events: Sequence[CreditEvent], agent_id: str, *, now: Optional[datetime] = None) -> float:
    if not events:
        return 0.0
    now = now or datetime.now(UTC)
    score = 0.0
    for event in events:
        seconds = float(event.impact.secondsSaved)
        age_days = max((now - event.ts).total_seconds(), 0.0) / 86400.0
        weight = math.exp(-_DECAY_LAMBDA * age_days)
        credit_share = 0.0
        for attribution in event.attributions:
            if attribution.agentId == agent_id:
                credit_share = float(attribution.weight)
                break
        score += seconds * credit_share * weight
    return score


def _events_for_tenant(tenant_id: str, *, since: Optional[datetime] = None) -> List[CreditEvent]:
    with db.session_scope() as session:
        records = db.list_credit_events(session, tenant_id, since=since)
        return [_record_to_event(record) for record in records]


def all_events(tenant_id: str, *, since: Optional[datetime] = None) -> List[CreditEvent]:
    return _events_for_tenant(tenant_id, since=since)


def events_for_issue(tenant_id: str, issue_key: str) -> List[CreditEvent]:
    with db.session_scope() as session:
        records = db.list_credit_events(session, tenant_id, issue_key=issue_key)
        return [_record_to_event(record) for record in records]


def issue_summary(tenant_id: str, issue_key: str, since: Optional[datetime] = None, limit: int = 5) -> IssueCreditSummary:
    events = events_for_issue(tenant_id, issue_key)
    total_seconds = sum(event.impact.secondsSaved for event in events)
    recent = list(reversed(events[-limit:])) if limit else list(reversed(events))
    window_events = [event for event in events if since is None or event.ts >= since]
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


def credit_chain(tenant_id: str, limit: int = 100) -> List[CreditEvent]:
    if limit <= 0:
        return []
    with db.session_scope() as session:
        records = db.list_credit_events(session, tenant_id, order_desc=True, limit=limit)
        return list(reversed([_record_to_event(record) for record in records]))


def summary(tenant_id: str, since: Optional[datetime] = None, limit: int = 10) -> CreditSummary:
    events = _events_for_tenant(tenant_id, since=since)
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


def agent_summary(
    tenant_id: str,
    agent_id: str,
    *,
    since: Optional[datetime] = None,
    limit: int = 20,
    now: Optional[datetime] = None,
) -> AgentCreditSummary:
    events = _events_for_tenant(tenant_id, since=since)
    matching = [
        event
        for event in events
        if any(attribution.agentId == agent_id for attribution in event.attributions)
    ]
    recent = list(reversed(matching[-limit:])) if limit else list(reversed(matching))
    score = _decayed_score(matching, agent_id, now=now)
    total_seconds = sum(
        event.impact.secondsSaved
        * next(
            (float(attribution.weight) for attribution in event.attributions if attribution.agentId == agent_id),
            0.0,
        )
        for event in matching
    )
    return AgentCreditSummary(
        agentId=agent_id,
        totalSecondsSaved=total_seconds,
        score=score,
        events=recent,
    )


def top_agents(tenant_id: str, window_days: int, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if window_days <= 0:
        return []
    pivot = datetime.now(UTC) - timedelta(days=window_days)
    events = _events_for_tenant(tenant_id, since=pivot)
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


def rollup_for_issue(tenant_id: str, issue_key: str, since: Optional[datetime] = None, limit: int = 5) -> IssueCreditSummary:
    return issue_summary(tenant_id, issue_key, since=since, limit=limit)


def rollup_for_agent(
    tenant_id: str,
    agent_id: str,
    since: Optional[datetime] = None,
    limit: int = 20,
) -> AgentCreditSummary:
    return agent_summary(tenant_id, agent_id, since=since, limit=limit)


def ewma_score(tenant_id: str, agent_id: str, now: Optional[datetime] = None) -> float:
    events = _events_for_tenant(tenant_id)
    relevant = [event for event in events if any(att.agentId == agent_id for att in event.attributions)]
    return _decayed_score(relevant, agent_id, now=now)


def build_apply_event(
    issue_key: str,
    proposal: Mapping[str, Any],
    actor: Mapping[str, Any],
    execution_result: Mapping[str, Any],
    *,
    tenant_id: str | None = None,
    parents: Iterable[str] | None = None,
    idempotency_key: str | None = None,
) -> CreditEvent:
    tenant = tenant_id or DEFAULT_TENANT_ID
    if not tenant:
        raise ValueError("tenant_id is required for build_apply_event")
    seconds_value = execution_result.get("secondsSaved") or execution_result.get("seconds")
    seconds = int(seconds_value) if seconds_value is not None else 0
    quality = execution_result.get("quality")
    impact = Impact(seconds_saved=seconds, quality=quality)
    shares, reason = tip_credit(issue_key, proposal, actor, execution_result)
    inputs = {
        "proposalId": proposal.get("id"),
        "kind": proposal.get("kind"),
    }
    for field in ("from", "to", "labels", "transitionId"):
        if field in proposal:
            inputs[field] = proposal[field]
    return append_event(
        tenant,
        issue_key=issue_key,
        action=f"apply.{proposal.get('kind')}",
        actor=actor,
        impact=impact,
        attributions=shares,
        parents=parents,
        inputs=inputs,
        metadata={"execution": execution_result},
        idempotency_key=idempotency_key,
        attribution_reason=reason,
    )


__all__ = [
    "AgentCreditSummary",
    "Attribution",
    "ContributorSummary",
    "CreditEvent",
    "CreditSummary",
    "Impact",
    "IssueCreditSummary",
    "all_events",
    "actor_agent_id",
    "agent_summary",
    "append_event",
    "build_apply_event",
    "credit_chain",
    "events_for_issue",
    "ewma_score",
    "issue_summary",
    "rollup_for_agent",
    "rollup_for_issue",
    "summary",
    "tip_credit",
    "top_agents",
]
