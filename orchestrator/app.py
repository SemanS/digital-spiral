from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Literal, Tuple

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from rapidfuzz.distance import Levenshtein

from clients.python.jira_adapter import JiraAdapter

from . import credit
from .metrics import estimate_savings

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "http://localhost:9000")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "mock-token")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret")
ORCH_SECRET = os.getenv("ORCH_SECRET", "forge-dev-secret")
FORGE_ALLOWLIST = {
    host.strip()
    for host in os.getenv("FORGE_ALLOWLIST", "").split(",")
    if host.strip()
}
AUTO_REGISTER_WEBHOOK = os.getenv("AUTO_REGISTER_WEBHOOK", "1").lower() not in {
    "0",
    "false",
    "no",
}
ORCHESTRATOR_BASE_URL = os.getenv("ORCHESTRATOR_BASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    if ORCHESTRATOR_BASE_URL:
        WEBHOOK_URL = f"{ORCHESTRATOR_BASE_URL.rstrip('/')}/webhooks/jira"
    else:
        WEBHOOK_URL = "http://localhost:7010/webhooks/jira"
WEBHOOK_JQL = os.getenv("WEBHOOK_JQL", "project = SUP")
_webhook_events_env = os.getenv(
    "WEBHOOK_EVENTS", "jira:issue_created,jira:issue_updated"
)
WEBHOOK_EVENTS = [
    event.strip()
    for event in _webhook_events_env.split(",")
    if event.strip()
]
if not WEBHOOK_EVENTS:
    WEBHOOK_EVENTS = ["jira:issue_created"]

logger = logging.getLogger("digital_spiral.orchestrator")

adapter = JiraAdapter(JIRA_BASE_URL, JIRA_TOKEN)

# --- in-memory "ledger" ---
LEDGER: dict[str, Dict[str, Any]] = {}  # key -> metrics
SUGGESTIONS: dict[str, Dict[str, Any]] = {}
APPLY_RESULTS: dict[str, Dict[str, Any]] = {}

DEFAULT_ESTIMATED_SAVINGS_SECONDS = int(os.getenv("DEFAULT_ESTIMATED_SAVINGS", "180"))


# --- Pydantic DTOs ---
class ApplyAction(BaseModel):
    id: str
    kind: Literal["comment", "transition", "set-labels", "link"]
    explain: Optional[str] = None
    body_adf: Optional[Dict[str, Any]] = None
    transitionId: Optional[str] = None
    transitionName: Optional[str] = None
    labels: Optional[List[str]] = None
    mode: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None


class ApplyIn(BaseModel):
    issueKey: str
    action: ApplyAction


app = FastAPI(title="Digital Spiral Orchestrator (Jira MVP)")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _client_hosts(request: Request) -> List[str]:
    hosts: List[str] = []
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        hosts.extend([segment.strip() for segment in forwarded.split(",") if segment.strip()])
    if request.client and request.client.host:
        hosts.append(request.client.host)
    return hosts


def ensure_authorized(request: Request) -> Optional[str]:
    secret = request.headers.get("x-ds-secret")
    if not secret or not hmac.compare_digest(secret, ORCH_SECRET):
        raise HTTPException(401, "Unauthorized")
    if FORGE_ALLOWLIST:
        hosts = _client_hosts(request)
        if not any(host in FORGE_ALLOWLIST for host in hosts):
            raise HTTPException(403, "Forbidden")
    tenant = request.headers.get("x-ds-tenant")
    return tenant if tenant else None


def resolve_actor(request: Request) -> Dict[str, Any]:
    header = (request.headers.get("x-ds-actor") or "").strip()
    actor_type = "human"
    actor_id = "unknown"
    if header:
        if ":" in header:
            candidate_type, candidate_id = header.split(":", 1)
            if candidate_id:
                actor_type = candidate_type
                actor_id = candidate_id
        elif "." in header and header.split(".", 1)[0] in {"human", "ai", "tool"}:
            actor_type, actor_id = header.split(".", 1)
        else:
            actor_id = header
    actor = {
        "type": actor_type.strip().lower() or "human",
        "id": actor_id.strip() or "unknown",
    }
    display = request.headers.get("x-ds-actor-display")
    if display:
        actor["display"] = display.strip()
    return actor


def parse_since(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - FastAPI handles HTTPException
        raise HTTPException(400, "Invalid since parameter") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed


def record_tenant(issue_key: str, tenant: Optional[str]) -> None:
    if not tenant:
        return
    entry = LEDGER.setdefault(issue_key, {"issueKey": issue_key, "history": []})
    tenants = entry.setdefault("tenants", [])
    if tenant not in tenants:
        tenants.append(tenant)


def lookup_suggestion(issue_key: str, action_id: str) -> Optional[Dict[str, Any]]:
    suggestion = SUGGESTIONS.get(issue_key)
    if not suggestion:
        return None
    for proposal in suggestion.get("proposals", []):
        if proposal.get("id") == action_id:
            return proposal
    return None


async def ensure_webhook_registered() -> None:
    if not AUTO_REGISTER_WEBHOOK:
        logger.info("Webhook auto-registration disabled")
        return
    if not WEBHOOK_URL:
        logger.warning("Webhook URL is not configured; skipping registration")
        return
    try:
        existing = await asyncio.to_thread(adapter.list_webhooks)
    except Exception as exc:  # pragma: no cover - network failures are logged only
        logger.warning("Failed to list webhooks: %s", exc)
        return
    target_events = set(WEBHOOK_EVENTS)
    for registration in existing:
        if (
            registration.get("url") == WEBHOOK_URL
            and registration.get("jql") == WEBHOOK_JQL
            and set(registration.get("events") or []) == target_events
        ):
            logger.info("Webhook already registered for %s", WEBHOOK_URL)
            return
    try:
        await asyncio.to_thread(
            adapter.register_webhook,
            WEBHOOK_URL,
            WEBHOOK_JQL,
            events=list(target_events),
            secret=WEBHOOK_SECRET,
        )
        logger.info("Registered webhook target %s", WEBHOOK_URL)
    except Exception as exc:  # pragma: no cover - network failures are logged only
        logger.error("Failed to register webhook %s: %s", WEBHOOK_URL, exc)


@app.on_event("startup")
async def startup_event() -> None:  # pragma: no cover - exercised in integration tests
    await ensure_webhook_registered()


def adf_from_text(text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    }
                ],
            }
        ],
    }


def adf_to_plain_text(node: Any) -> str:
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(filter(None, (adf_to_plain_text(child) for child in node)))
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "text":
            return str(node.get("text") or "")
        if "content" in node:
            return adf_to_plain_text(node.get("content"))
    return ""


def compute_quality(draft_text: str, final_text: str) -> float:
    if not draft_text:
        return 1.0
    dist = Levenshtein.distance(draft_text, final_text)
    ratio = 1.0 - dist / max(1, len(draft_text))
    # bucket
    return 1.0 if ratio > 0.9 else 0.5 if ratio > 0.6 else 0.0


def verify_signature(headers: dict, body: bytes):
    sig = headers.get("x-mockjira-signature")
    if not sig:
        raise HTTPException(400, "Missing signature")
    alg, _, hexd = sig.partition("=")
    if alg != "sha256":
        raise HTTPException(400, "Unsupported signature alg")
    # v2: sha256(secret + body)
    expected = hashlib.sha256(WEBHOOK_SECRET.encode("utf-8") + body).hexdigest()
    if not hmac.compare_digest(hexd, expected):
        raise HTTPException(401, "Bad signature")


# -------- Webhook receiver (mock Jira -> orchestrator) --------
@app.post("/webhooks/jira")
async def jira_webhook(request: Request):
    body = await request.body()
    try:
        verify_signature(request.headers, body)
    except HTTPException as exc:
        raise exc
    payload = await request.json()
    key = payload.get("issue", {}).get("key") or payload.get("issueKey")
    LEDGER.setdefault(key or "unknown", {"issueKey": key or "unknown", "history": []}).update(
        {"last_event": payload, "last_event_at": time.time()}
    )
    if not key:
        return {"ok": True}
    try:
        issue_payload = await asyncio.to_thread(adapter.get_issue, key)
    except Exception as exc:  # pragma: no cover - network failures are logged only
        logger.error("Failed to fetch issue %s from Jira: %s", key, exc)
        raise HTTPException(502, "Failed to fetch issue payload") from exc
    response = ingest_issue(key, issue_payload)
    return {"ok": True, "proposals": response}


def ingest_issue(issue_key: str, issue_payload: Dict[str, Any], tenant: Optional[str] = None) -> Dict[str, Any]:
    fields = issue_payload.get("fields", {})
    summary = str(fields.get("summary") or "(no summary)")
    comment_text = (
        f"Ahoj! V tickete {issue_key} sa píše: \"{summary}\". "
        "Prosím doplň posledné logy a verziu aplikácie, aby sme vedeli pokračovať."
    )
    proposals: List[Dict[str, Any]] = [
        {
            "id": "add-comment-1",
            "kind": "comment",
            "body_adf": adf_from_text(comment_text),
            "explain": "Navrhovaná odpoveď pre zákazníka na základe summary ticketu.",
        }
    ]

    transitions = adapter.list_transitions(issue_key)
    if transitions:
        target = transitions[0]
        proposals.append(
            {
                "id": f"transition-{target['id']}",
                "kind": "transition",
                "transitionId": target["id"],
                "transitionName": target.get("name"),
                "explain": f"Posun na {target.get('name') or target['id']} pre okamžité riešenie.",
            }
        )

    labels = [label for label in fields.get("labels") or [] if isinstance(label, str)]
    needs_label = "needs-info"
    if needs_label not in labels:
        merged_labels = sorted({*labels, needs_label})
        proposals.append(
            {
                "id": f"label-{needs_label}",
                "kind": "set-labels",
                "labels": merged_labels,
                "mode": "merge",
                "explain": "Pridá label needs-info na signalizáciu čakajúcej odpovede.",
            }
        )

    for proposal in proposals:
        proposal["estimatedSeconds"] = estimate_savings(proposal.get("kind", ""))
    estimated_total = sum(int(proposal.get("estimatedSeconds") or 0) for proposal in proposals)
    estimated = {"seconds": estimated_total or DEFAULT_ESTIMATED_SAVINGS_SECONDS}
    response = {"issueKey": issue_key, "proposals": proposals, "estimated_savings": estimated}
    SUGGESTIONS[issue_key] = response
    entry = LEDGER.setdefault(issue_key, {"issueKey": issue_key, "history": []})
    entry["last_ingest_at"] = time.time()
    entry["estimated_savings"] = estimated
    entry["draft_text"] = comment_text
    record_tenant(issue_key, tenant)
    return response


def _resolve_transition_id(issue_key: str, action: ApplyAction) -> str:
    transition_id = action.transitionId
    if transition_id:
        return transition_id
    suggestion = lookup_suggestion(issue_key, action.id)
    if suggestion and suggestion.get("transitionId"):
        return str(suggestion["transitionId"])
    raise HTTPException(400, "Missing transitionId for transition action")


def _resolve_labels(issue_key: str, action: ApplyAction) -> Tuple[List[str], str]:
    labels = action.labels
    mode = (action.mode or "merge").lower()
    suggestion = lookup_suggestion(issue_key, action.id)
    if not labels and suggestion:
        labels = suggestion.get("labels")
        if suggestion.get("mode"):
            mode = str(suggestion.get("mode")).lower()
    if not labels:
        raise HTTPException(400, "Missing labels for set-labels action")
    return [str(label) for label in labels], mode


def perform_apply(
    issue_key: str, action: ApplyAction, tenant: Optional[str], actor: Dict[str, Any]
) -> Dict[str, Any]:
    record_tenant(issue_key, tenant)
    started = time.perf_counter()
    applied_detail: Dict[str, Any] = {"id": action.id, "kind": action.kind}
    final_text = ""
    quality = 1.0
    suggestion = lookup_suggestion(issue_key, action.id)

    if action.kind == "comment":
        body = action.body_adf
        if body is None:
            body = suggestion.get("body_adf") if suggestion else None
        if body is None:
            raise HTTPException(400, "Missing body_adf for comment action")
        adapter.add_comment(issue_key, body)
        final_text = adf_to_plain_text(body)
        draft_text = LEDGER.get(issue_key, {}).get("draft_text", "")
        quality = compute_quality(draft_text, final_text)
    elif action.kind == "transition":
        transition_id = _resolve_transition_id(issue_key, action)
        adapter.transition_issue(issue_key, transition_id)
        applied_detail["transitionId"] = transition_id
    elif action.kind == "set-labels":
        labels, mode = _resolve_labels(issue_key, action)
        try:
            issue_payload = adapter.get_issue(issue_key)
        except Exception as exc:
            raise HTTPException(502, f"Failed to load issue {issue_key}: {exc}") from exc
        existing = [
            label
            for label in issue_payload.get("fields", {}).get("labels") or []
            if isinstance(label, str)
        ]
        if mode == "replace":
            new_labels = list(dict.fromkeys(labels))
        else:
            new_labels = list(dict.fromkeys(existing + labels))
        adapter.update_issue_fields(issue_key, {"labels": new_labels})
        applied_detail["labels"] = new_labels
        applied_detail["mode"] = mode
    elif action.kind == "link":
        raise HTTPException(400, "Link actions are not implemented yet")
    else:  # pragma: no cover - guarded by ApplyAction model
        raise HTTPException(400, f"Unsupported action kind {action.kind}")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    credit_seconds = estimate_savings(action.kind, {"proposal": suggestion} if suggestion else None)
    entry = LEDGER.setdefault(issue_key, {"issueKey": issue_key, "history": []})
    history = entry.setdefault("history", [])
    record = {
        "action_id": action.id,
        "kind": action.kind,
        "applied_at": time.time(),
        "apply_ms": elapsed_ms,
        "credit_seconds": credit_seconds,
    }
    if action.kind == "comment":
        record["quality"] = quality
        record["text"] = final_text
        entry["last_comment_quality"] = quality
        entry["last_comment_text"] = final_text
    history.append(record)
    entry["total_credit_seconds"] = float(entry.get("total_credit_seconds", 0.0)) + credit_seconds
    entry["applications"] = int(entry.get("applications", 0)) + 1
    entry["last_apply_at"] = record["applied_at"]
    entry["last_action"] = record
    proposal_context: Dict[str, Any] = {}
    if suggestion:
        proposal_context.update({k: v for k, v in suggestion.items() if k not in {"explain"}})
    proposal_context.update(action.model_dump(exclude_none=True))
    if applied_detail.get("labels"):
        proposal_context["labels"] = applied_detail["labels"]
    if applied_detail.get("transitionId"):
        proposal_context["transitionId"] = applied_detail["transitionId"]
    event = credit.build_apply_event(
        issue_key,
        proposal_context,
        actor,
        {"secondsSaved": credit_seconds, "quality": quality, "text": final_text},
    )
    record["credit_event_id"] = event.id
    credit_snapshot = {
        "secondsSaved": event.impact.secondsSaved,
        "quality": event.impact.quality,
        "splits": [
            {"id": split.id, "weight": split.weight}
            for split in event.attribution.split
        ],
        "reason": event.attribution.reason,
        "eventId": event.id,
        "hash": event.hash,
    }
    entry.setdefault("credit_events", []).append(event.model_dump(mode="json"))
    entry["last_credit_event"] = credit_snapshot
    record_tenant(issue_key, tenant)
    return {
        "ok": True,
        "applied": applied_detail,
        "credit": credit_snapshot,
        "ledger": entry,
    }


# -------- Ingest: create proposals --------
@app.get("/v1/jira/ingest")
def ingest(request: Request, issueKey: str = Query(..., alias="issueKey")):
    tenant = ensure_authorized(request)
    try:
        issue_payload = adapter.get_issue(issueKey)
    except Exception as exc:
        raise HTTPException(502, f"Failed to load issue {issueKey}: {exc}") from exc
    return ingest_issue(issueKey, issue_payload, tenant=tenant)


# -------- Apply: execute selected action --------
@app.post("/v1/jira/apply")
def apply(request: Request, payload: ApplyIn):
    tenant = ensure_authorized(request)
    actor = resolve_actor(request)
    idem_key = request.headers.get("idempotency-key")
    if not idem_key:
        raise HTTPException(400, "Missing Idempotency-Key")
    if idem_key in APPLY_RESULTS:
        return APPLY_RESULTS[idem_key]
    result = perform_apply(payload.issueKey, payload.action, tenant, actor)
    APPLY_RESULTS[idem_key] = result
    return result


# -------- Ledger read --------
@app.get("/v1/ledger")
def get_ledger(issueKey: str = Query(..., alias="issueKey")):
    return LEDGER.get(issueKey, {"issueKey": issueKey, "history": []})


@app.get("/v1/credit/summary")
def credit_summary_endpoint(
    since: Optional[str] = Query(None), limit: int = Query(10, ge=1, le=50)
):
    return credit.summary(since=parse_since(since), limit=limit)


@app.get("/v1/credit/agent/{id}")
def credit_agent_endpoint(
    id: str, since: Optional[str] = Query(None), limit: int = Query(20, ge=0, le=100)
):
    return credit.agent_summary(id, since=parse_since(since), limit=limit)


@app.get("/v1/credit/issue/{key}")
def credit_issue_endpoint(
    key: str, since: Optional[str] = Query(None), limit: int = Query(5, ge=0, le=50)
):
    return credit.issue_summary(key, since=parse_since(since), limit=limit)


@app.get("/v1/credit/chain")
def credit_chain_endpoint(limit: int = Query(100, ge=1, le=500)):
    return credit.credit_chain(limit=limit)


# -------- Tiny UI --------
@app.get("/ui", response_class=HTMLResponse)
def ui():
    rows = []
    for key, entry in sorted(LEDGER.items()):
        total = entry.get("total_credit_seconds", 0.0)
        last = entry.get("last_action", {})
        rows.append(
            "<tr>"
            f"<td>{key}</td>"
            f"<td>{total:.0f}s</td>"
            f"<td>{last.get('kind', '-')}</td>"
            f"<td>{last.get('apply_ms', 0)} ms</td>"
            "</tr>"
        )
    body = f"""
    <html><body>
      <h2>Digital Spiral — Ledger</h2>
      <table border=1 cellpadding=6>
        <tr><th>Issue</th><th>Credit</th><th>Last action</th><th>Latency</th></tr>
        {''.join(rows)}
      </table>
    </body></html>
    """
    return body
