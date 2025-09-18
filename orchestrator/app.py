from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from rapidfuzz.distance import Levenshtein

from clients.python.jira_adapter import JiraAdapter

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "http://localhost:9000")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "mock-token")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret")
SIGNATURE_VERSION = int(os.getenv("SIGNATURE_VERSION", "2"))
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
LEDGER: dict[str, dict] = {}  # key -> metrics
SUGGESTIONS: dict[str, dict[str, Any]] = {}


# --- Pydantic DTOs ---
class IngestIn(BaseModel):
    issue: Dict[str, Any]


class ApplyIn(BaseModel):
    issueKey: str
    accepted_action_ids: List[str]
    playbook_id: str | None = None
    draft_reply_adf: Dict[str, Any] | None = None


app = FastAPI(title="Digital Spiral Orchestrator (Jira MVP)")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
    except HTTPException as e:
        raise e
    payload = await request.json()
    # store last event per issue (for demo)
    key = payload.get("issue", {}).get("key") or payload.get("issueKey")
    LEDGER.setdefault(key or "unknown", {}).update({"last_event": payload})
    if not key:
        return {"ok": True}
    try:
        issue_payload = await asyncio.to_thread(adapter.get_issue, key)
    except Exception as exc:
        logger.error("Failed to fetch issue %s from Jira: %s", key, exc)
        raise HTTPException(502, "Failed to fetch issue payload") from exc
    suggestion = ingest(IngestIn(issue=issue_payload))
    LEDGER.setdefault(key, {})
    LEDGER[key]["last_ingest"] = time.time()
    return {"ok": True, "suggestion": suggestion}


# -------- Ingest: create draft + plan --------
@app.post("/v1/jira/ingest")
def ingest(i: IngestIn):
    issue = i.issue
    key = issue["key"]
    fields = issue.get("fields", {})
    summary = fields.get("summary") or "(no summary)"
    # draft heuristic
    if "password" in summary.lower():
        draft = (
            "Ahoj! Tu je postup na reset hesla: 1) Otvor ... 2) Klikni ... 3) Over ...\n"
            "Daj vedieť, či pomohlo."
        )
        actions = [
            {"id": "reply-1", "type": "reply", "public": True, "body_adf": adf_from_text(draft)},
            {"id": "transition-1", "type": "transition", "to": "In Progress"},
        ]
        planned_label = None
    else:
        draft = (
            "Ahoj! Pozreli sme sa na ticket: "
            f"{summary}. Prosím pošli verziu aplikácie a posledné logy."
        )
        planned_label = "needs-info"
        actions = [
            {"id": "reply-1", "type": "reply", "public": True, "body_adf": adf_from_text(draft)},
            {"id": "label-1", "type": "add_label", "value": "needs-info"},
        ]
    LEDGER.setdefault(key, {})
    LEDGER[key]["draft_text"] = draft
    LEDGER[key]["baseline_seconds"] = LEDGER[key].get("baseline_seconds", 120)
    if planned_label:
        LEDGER[key]["planned_label"] = planned_label
    suggestion = {
        "playbook_id": "jira-default",
        "draft_reply_adf": adf_from_text(draft),
        "actions": actions,
        "explanations": ["Heuristika na základe summary", "Jednoklikové kroky pre agenta"],
    }
    SUGGESTIONS[key] = suggestion
    return suggestion


# -------- Suggestions read --------
@app.get("/v1/suggestions/{issue_key}")
def get_suggestion(issue_key: str):
    suggestion = SUGGESTIONS.get(issue_key)
    if suggestion is None:
        raise HTTPException(404, "Suggestion not found")
    return suggestion


# -------- Apply: execute plan via adapter + write ledger --------
@app.post("/v1/jira/apply")
def apply(a: ApplyIn):
    key = a.issueKey
    start = time.time()
    applied = []

    # 1) reply
    if "reply-1" in a.accepted_action_ids and a.draft_reply_adf:
        adapter.add_comment(key, a.draft_reply_adf)
        applied.append({"id": "reply-1", "ok": True})

    # 2) simple transition (ak je v pláne)
    if "transition-1" in a.accepted_action_ids:
        trs = adapter.list_transitions(key)
        # pick first transition for demo
        if trs:
            adapter.transition_issue(key, trs[0]["id"])
            applied.append({"id": "transition-1", "ok": True})

    # 3) label (demoverzia: update issue fields)
    if "label-1" in a.accepted_action_ids:
        planned_label = LEDGER.get(key, {}).get("planned_label", "needs-info")
        try:
            issue_payload = adapter.get_issue(key)
        except Exception as exc:
            raise HTTPException(502, f"Failed to load issue {key}: {exc}") from exc
        labels = list(issue_payload.get("fields", {}).get("labels") or [])
        if planned_label and planned_label not in labels:
            labels.append(planned_label)
        try:
            adapter.update_issue_fields(key, {"labels": labels})
        except Exception as exc:
            raise HTTPException(502, f"Failed to update labels for {key}: {exc}") from exc
        applied.append({"id": "label-1", "ok": True, "labels": labels})

    # ledger
    elapsed = max(time.time() - start, 1.0)
    baseline = float(LEDGER.get(key, {}).get("baseline_seconds", 120))
    draft_text = LEDGER.get(key, {}).get("draft_text", "")
    final_text = draft_text  # v MVP predpokladáme Apply bez editácie
    quality = compute_quality(draft_text, final_text)
    credit = min(1.0, elapsed / max(1.0, baseline)) * quality

    LEDGER.setdefault(key, {})
    LEDGER[key].update(
        {
            "last_apply": time.time(),
            "delta_seconds": elapsed,
            "quality": quality,
            "credit": credit,
        }
    )
    return {"applied": applied, "ledger_entry": LEDGER[key]}


# -------- Ledger read --------
@app.get("/v1/ledger/{issue_key}")
def get_ledger(issue_key: str):
    return LEDGER.get(issue_key, {})


# -------- Tiny UI --------
@app.get("/ui", response_class=HTMLResponse)
def ui():
    rows = []
    for k, v in LEDGER.items():
        ds = float(v.get("delta_seconds", 0.0))
        base = int(float(v.get("baseline_seconds", 120)))
        qual = v.get("quality", 1.0)
        cred = v.get("credit", 0.0)
        rows.append(
            f"<tr><td>{k}</td><td>{ds:.1f}s/{base}s</td><td>{qual:.2f}</td><td>{cred:.2f}</td></tr>"
        )
    body = f"""
    <html><body>
      <h2>Digital Spiral — Ledger</h2>
      <table border=1 cellpadding=6>
        <tr><th>Issue</th><th>ΔT / Baseline</th><th>Quality</th><th>Credit</th></tr>
        {''.join(rows)}
      </table>
    </body></html>
    """
    return body
