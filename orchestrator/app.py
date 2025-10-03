from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Literal, Tuple

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rapidfuzz.distance import Levenshtein

from sqlalchemy import select

from clients.python.jira_adapter import JiraAdapter

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

from . import audit, credit, db, metrics as metrics_module
from .models import Impact

# Import Pulse API router
try:
    from . import pulse_api
    PULSE_API_AVAILABLE = True
except ImportError:
    PULSE_API_AVAILABLE = False

# Import AI Assistant API router
try:
    from . import ai_assistant_api
    AI_ASSISTANT_API_AVAILABLE = True
except ImportError:
    AI_ASSISTANT_API_AVAILABLE = False

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "http://localhost:9000")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "mock-token")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret")
FORGE_SHARED_SECRET = os.getenv("FORGE_SHARED_SECRET") or os.getenv("ORCH_SECRET", "forge-dev-secret")
FORGE_ALLOWLIST = {
    host.strip()
    for host in os.getenv("FORGE_ALLOWLIST", "").split(",")
    if host.strip()
}
ORCHESTRATOR_TOKEN = os.getenv("ORCHESTRATOR_TOKEN") or os.getenv("ORCH_TOKEN")
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

DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "demo")
DEFAULT_TENANT_SITE_ID = os.getenv("DEFAULT_TENANT_SITE_ID") or (
    f"{DEFAULT_TENANT_ID}.site" if DEFAULT_TENANT_ID else None
)
DEFAULT_TENANT_SECRET = os.getenv("DEFAULT_TENANT_SECRET") or FORGE_SHARED_SECRET

REGISTRY = CollectorRegistry()
APPLIES_TOTAL = Counter(
    "applies_total",
    "Total apply operations",
    ("tenant", "action"),
    registry=REGISTRY,
)
SECONDS_SAVED_TOTAL = Counter(
    "seconds_saved_total",
    "Seconds saved credited to tenants",
    ("tenant",),
    registry=REGISTRY,
)
APPLY_LATENCY = Histogram(
    "apply_latency_ms",
    "Latency of apply operations in milliseconds",
    ("tenant", "action"),
    registry=REGISTRY,
)
IDEMPOTENCY_CONFLICTS = Counter(
    "idempotency_conflicts_total",
    "Conflicts triggered by Idempotency-Key reuse",
    ("tenant",),
    registry=REGISTRY,
)
SIGNATURE_FAILURES = Counter(
    "signature_fail_total",
    "Forge signature verification failures",
    ("tenant",),
    registry=REGISTRY,
)

logger = logging.getLogger("digital_spiral.orchestrator")

adapter = JiraAdapter(JIRA_BASE_URL, JIRA_TOKEN)

# --- in-memory "ledger" ---
LEDGER: dict[str, Dict[str, Any]] = {}  # key -> metrics
SUGGESTIONS: dict[str, Dict[str, Any]] = {}
APPLY_RESULTS: dict[str, Dict[str, Any]] = {}
APPLY_FINGERPRINTS: dict[str, str] = {}
PII_VAULT: dict[str, List[Dict[str, Any]]] = {}

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
    proposalEventId: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


app = FastAPI(title="Digital Spiral Orchestrator (Jira MVP)")

# Include Pulse API router if available
if PULSE_API_AVAILABLE:
    app.include_router(pulse_api.router)

# Include AI Assistant API router if available
if AI_ASSISTANT_API_AVAILABLE:
    app.include_router(ai_assistant_api.router)

# Mount static files for templates
templates_static_path = Path(__file__).parent / "templates" / "static"
if templates_static_path.exists():
    app.mount("/v1/pulse/static", StaticFiles(directory=str(templates_static_path)), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event() -> None:
    db.init_models()
    if DEFAULT_TENANT_ID and DEFAULT_TENANT_SITE_ID and DEFAULT_TENANT_SECRET:
        with db.session_scope() as session:
            db.ensure_tenant(
                session,
                DEFAULT_TENANT_ID,
                site_id=DEFAULT_TENANT_SITE_ID,
                forge_shared_secret=DEFAULT_TENANT_SECRET,
            )


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    artifacts_dir = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
    probe_path = artifacts_dir / ".orch-health"
    try:
        probe_path.parent.mkdir(parents=True, exist_ok=True)
        probe_path.write_text(str(time.time()), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - failure surfaces via HTTP
        raise HTTPException(503, f"Storage check failed: {exc}") from exc
    try:
        adapter._call("GET", "/rest/api/3/project")
    except Exception as exc:  # pragma: no cover - failure surfaces via HTTP
        raise HTTPException(503, f"Jira connectivity failed: {exc}") from exc
    try:
        with db.session_scope() as session:
            session.execute(select(1))
    except Exception as exc:  # pragma: no cover - surfaces via HTTP
        raise HTTPException(503, f"Database connectivity failed: {exc}") from exc
    return {"status": "ok", "storage": "ok", "jira": "ok", "database": "ok"}


@app.get("/readyz")
def readyz() -> Dict[str, str]:
    try:
        with db.session_scope() as session:
            if DEFAULT_TENANT_ID:
                tenant = db.get_tenant(session, DEFAULT_TENANT_ID)
                if tenant is None:
                    raise HTTPException(503, "Default tenant not provisioned")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - surfaces via HTTP
        raise HTTPException(503, f"Database readiness check failed: {exc}") from exc
    if not DEFAULT_TENANT_SECRET:
        raise HTTPException(503, "Forge shared secret not configured")
    return {"status": "ok"}


@app.get("/metrics")
def metrics_endpoint() -> Response:
    payload = generate_latest(REGISTRY)
    return Response(payload, media_type=CONTENT_TYPE_LATEST)


def _client_hosts(request: Request) -> List[str]:
    hosts: List[str] = []
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        hosts.extend([segment.strip() for segment in forwarded.split(",") if segment.strip()])
    if request.client and request.client.host:
        hosts.append(request.client.host)
    return hosts


def verify_forge_signature(secret: str | None, request: Request, body: bytes) -> None:
    if not secret:
        return
    signature = request.headers.get("x-forge-signature")
    if not signature:
        raise HTTPException(401, "Missing X-Forge-Signature")
    algorithm, _, value = signature.partition("=")
    if not value:
        digest = algorithm
        algorithm = "sha256"
    else:
        digest = value
    if algorithm.lower() != "sha256":
        raise HTTPException(400, "Unsupported signature algorithm")
    expected = hashlib.sha256(secret.encode("utf-8") + body).hexdigest()
    if not hmac.compare_digest(digest, expected):
        raise HTTPException(401, "Invalid signature")


def _extract_tenant_id(request: Request) -> str:
    header = (
        request.headers.get("x-tenant-id")
        or request.headers.get("x-ds-tenant")
        or request.headers.get("x-forge-tenant-id")
    )
    if header:
        return header.strip()
    if DEFAULT_TENANT_ID:
        return DEFAULT_TENANT_ID
    raise HTTPException(400, "Missing X-Tenant-Id")


def ensure_authorized(request: Request, *, body: bytes | None = None) -> str:
    tenant = _extract_tenant_id(request)
    tenant_secret = DEFAULT_TENANT_SECRET
    with db.session_scope() as session:
        db_secret = db.get_tenant_secret(session, tenant)
        if db_secret:
            tenant_secret = db_secret

    if ORCHESTRATOR_TOKEN:
        expected = f"Bearer {ORCHESTRATOR_TOKEN}"
        provided = request.headers.get("authorization")
        if provided != expected:
            raise HTTPException(401, "Unauthorized")
    else:
        provided_secret = request.headers.get("x-ds-secret")
        if (
            not provided_secret
            or not tenant_secret
            or not hmac.compare_digest(provided_secret, tenant_secret)
        ):
            raise HTTPException(401, "Unauthorized")

    if tenant_secret:
        try:
            verify_forge_signature(tenant_secret, request, body or b"")
        except HTTPException:
            SIGNATURE_FAILURES.labels(tenant=tenant).inc()
            raise
    elif request.headers.get("x-forge-signature"):
        SIGNATURE_FAILURES.labels(tenant=tenant).inc()
        raise HTTPException(401, "Forge shared secret not configured")

    if FORGE_ALLOWLIST:
        hosts = _client_hosts(request)
        if not any(host in FORGE_ALLOWLIST for host in hosts):
            raise HTTPException(403, "Forbidden")
    return tenant


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


def parse_window_days(raw: str) -> int:
    candidate = (raw or "").strip().lower()
    if candidate.endswith("d"):
        candidate = candidate[:-1]
    try:
        days = int(candidate)
    except ValueError as exc:  # pragma: no cover - FastAPI surfaces HTTP
        raise HTTPException(400, "Invalid window parameter") from exc
    if days <= 0 or days > 365:
        raise HTTPException(400, "Window parameter out of range")
    return days


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


def record_apply_failure(
    issue_key: str, action: ApplyAction, actor: Dict[str, Any], reason: Optional[str] = None
) -> None:
    inputs: Dict[str, Any] = {"proposalId": action.id, "kind": action.kind}
    if reason:
        inputs["reason"] = reason
    credit.append_event(
        issue_key=issue_key,
        action="apply.failed",
        actor=actor,
        inputs=inputs,
        impact={"secondsSaved": 0, "quality": 0.0},
        attributions=[],
    )


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


PII_PLACEHOLDERS = {
    "email": "<REDACTED_EMAIL>",
    "phone": "<REDACTED_PHONE>",
    "card": "<REDACTED_CARD>",
    "iban": "<REDACTED_IBAN>",
    "address": "<REDACTED_ADDRESS>",
}

_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_CARD_PATTERN = re.compile(r"(?:\d[ -]?){13,19}")
_IBAN_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}(?:[\s-]?[A-Z0-9]{2,4}){3,}\b")
_ADDRESS_PATTERN = re.compile(
    r"(?:\b[A-Za-zÁ-Žá-ž]+\.?,?\s+)?\b\d{1,4}[A-Za-z]?\s+[A-Za-zÁ-Žá-ž0-9'.-]+(?:\s+(?:Street|St\\.?|Avenue|Ave\\.?|Road|Rd\\.?|Boulevard|Blvd\\.?|Lane|Ln\\.?|Drive|Dr\\.?|Court|Ct\\.?|Square|Sq\\.?|ulica|ul\\.?|námestie|nám\\.?|cesta|trieda))[^\n]*",
    re.IGNORECASE,
)


def _is_probable_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 9 <= len(digits) <= 15


def _is_probable_card(value: str) -> bool:
    digits = [int(ch) for ch in value if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            doubled = digit * 2
            if doubled > 9:
                doubled -= 9
            total += doubled
        else:
            total += digit
    return total % 10 == 0


def _is_valid_iban(value: str) -> bool:
    compact = re.sub(r"\s+", "", value).upper()
    if len(compact) < 15 or len(compact) > 34:
        return False
    if not compact[:2].isalpha() or not compact[2:4].isdigit():
        return False
    rearranged = compact[4:] + compact[:4]
    translated = []
    for char in rearranged:
        if char.isdigit():
            translated.append(char)
        elif char.isalpha():
            translated.append(str(ord(char) - 55))
        else:
            return False
    remainder = 0
    for char in "".join(translated):
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


_PII_PATTERNS: Tuple[Tuple[str, re.Pattern[str], Optional[Callable[[str], bool]]], ...] = (
    ("email", _EMAIL_PATTERN, None),
    ("card", _CARD_PATTERN, _is_probable_card),
    ("iban", _IBAN_PATTERN, _is_valid_iban),
    ("phone", _PHONE_PATTERN, _is_probable_phone),
    ("address", _ADDRESS_PATTERN, None),
)


def _as_plain_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return adf_to_plain_text(value)
    return str(value)


def _merge_text_parts(parts: Iterable[str]) -> str:
    seen: set[str] = set()
    ordered: List[str] = []
    for part in parts:
        if not part:
            continue
        candidate = part.strip()
        if not candidate:
            continue
        lower = candidate.lower()
        if lower in seen:
            continue
        seen.add(lower)
        ordered.append(candidate)
    return "\n\n".join(ordered)


def redact_pii(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    if not text:
        return "", []
    vault: List[Dict[str, Any]] = []
    counters = {key: 0 for key in PII_PLACEHOLDERS}
    redacted = text

    def apply_pattern(pattern: re.Pattern[str], category: str, validator: Optional[Callable[[str], bool]]) -> None:
        nonlocal redacted

        def _replacement(match: re.Match[str]) -> str:
            value = match.group(0)
            if validator and not validator(value):
                return value
            for existing in vault:
                if existing["type"] == category and existing["value"] == value:
                    return existing["placeholder"]
            counters[category] += 1
            base = PII_PLACEHOLDERS[category]
            if base.endswith(">"):
                placeholder = f"{base[:-1]}_{counters[category]}>"
            else:
                placeholder = f"{base}_{counters[category]}"
            vault.append(
                {
                    "type": category,
                    "value": value,
                    "hash": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    "placeholder": placeholder,
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return placeholder

        redacted = pattern.sub(_replacement, redacted)

    for category, pattern, validator in _PII_PATTERNS:
        apply_pattern(pattern, category, validator)

    return redacted, vault


_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "bug_report": [
        "bug",
        "error",
        "crash",
        "exception",
        "fail",
        "problem",
        "stack trace",
        "traceback",
        "nefunguje",
        "nejde",
    ],
    "incident": [
        "outage",
        "incident",
        "impact",
        "downtime",
        "production",
        "critical",
        "p0",
        "p1",
    ],
    "access_request": [
        "access",
        "permission",
        "login",
        "account",
        "pristup",
        "role",
        "credentials",
    ],
    "billing": [
        "invoice",
        "billing",
        "payment",
        "refund",
        "charge",
        "platba",
        "faktura",
    ],
    "question": [
        "how",
        "can i",
        "could you",
        "where",
        "ako",
        "kde",
        "?",
    ],
    "feedback": [
        "feature",
        "improvement",
        "enhancement",
        "suggestion",
        "feedback",
        "navrh",
    ],
}

_DEFAULT_INTENT = "general_support"
_URGENCY_MARKERS = {"urgent", "asap", "critical", "severe", "blokuje", "blocker"}


def classify_intent(summary: str, body: str) -> Dict[str, Any]:
    text = f"{summary}\n{body}".lower()
    matches: Dict[str, List[str]] = {}
    for label, keywords in _INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword == "?":
                if "?" in text:
                    matches.setdefault(label, []).append("question_mark")
                continue
            if keyword in text:
                matches.setdefault(label, []).append(keyword)
    if matches:
        label, evidence = max(matches.items(), key=lambda item: len(item[1]))
        total = sum(len(values) for values in matches.values())
        confidence = len(evidence) / total if total else 1.0
    else:
        label = _DEFAULT_INTENT
        evidence = []
        confidence = 0.2
    return {
        "label": label,
        "confidence": round(min(max(confidence, 0.05), 1.0), 2),
        "evidence": evidence,
    }


def estimate_complexity(summary: str, body: str, event_type: Optional[str] = None) -> Dict[str, Any]:
    text = f"{summary}\n{body}"
    normalized = text.lower()
    word_count = len(re.findall(r"\w+", text))
    question_count = normalized.count("?")
    newline_count = text.count("\n")
    complexity_score = 0
    if word_count > 400:
        complexity_score += 3
    elif word_count > 220:
        complexity_score += 2
    elif word_count > 120:
        complexity_score += 1
    if any(marker in normalized for marker in _URGENCY_MARKERS):
        complexity_score += 2
    if question_count >= 2:
        complexity_score += 1
    if newline_count >= 5:
        complexity_score += 1
    if any(term in normalized for term in ["stacktrace", "traceback", "error code", "sqlstate", "exception"]):
        complexity_score += 1
    if event_type and "message.added" in event_type:
        complexity_score += 1
    unique_tokens = {token for token in re.findall(r"[A-Za-zÁ-Žá-ž]{3,}", normalized)}
    if len(unique_tokens) > 120:
        complexity_score += 1
    if word_count < 40:
        complexity_score = max(complexity_score - 1, 0)
    if complexity_score >= 5:
        level = "high"
    elif complexity_score >= 3:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "score": complexity_score,
        "word_count": word_count,
        "question_count": question_count,
    }


def _subtask_id(issue_key: str, suffix: str) -> str:
    base = issue_key.lower().replace("-", "_")
    digest = hashlib.sha1(f"{issue_key}:{suffix}".encode("utf-8")).hexdigest()[:8]
    return f"{base}_{suffix}_{digest}"


def generate_subtasks(
    issue_key: str,
    intent_label: str,
    complexity_level: str,
    summary: str,
    body: str,
) -> List[Dict[str, Any]]:
    subtasks: List[Dict[str, Any]] = []
    subtasks.append(
        {
            "id": _subtask_id(issue_key, "triage"),
            "title": "Prečítať ticket a určiť prioritu",
            "description": "Preskúmaj obsah a potvrď prioritu podľa dostupných informácií.",
            "status": "suggested",
            "owner": "orchestrator.triage",
            "intent": intent_label,
        }
    )
    lowered = body.lower()
    if intent_label in {"bug_report", "incident"}:
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "diagnostics"),
                "title": "Získať diagnostické údaje",
                "description": "Over posledné logy, release a kroky na reprodukciu problému.",
                "status": "suggested",
                "owner": "agent.diagnostics",
            }
        )
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "kb"),
                "title": "Skontrolovať známe incidenty",
                "description": "Porovnaj ticket s existujúcimi incidentmi alebo výpadkami v KB.",
                "status": "suggested",
                "owner": "agent.kb",
            }
        )
    elif intent_label == "access_request":
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "access"),
                "title": "Overiť oprávnenia používateľa",
                "description": "Skontroluj v IAM systéme stav účtu a požadované roly.",
                "status": "suggested",
                "owner": "agent.iam",
            }
        )
    elif intent_label == "billing":
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "billing"),
                "title": "Overiť fakturáciu",
                "description": "Vyhľadaj transakcie a porovnaj s históriou platieb zákazníka.",
                "status": "suggested",
                "owner": "agent.billing",
            }
        )
    else:
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "research"),
                "title": "Nájsť relevantné znalosti",
                "description": "Vyhľadaj podobné otázky alebo návody v znalostnej báze.",
                "status": "suggested",
                "owner": "agent.research",
            }
        )
    subtasks.append(
        {
            "id": _subtask_id(issue_key, "draft"),
            "title": "Pripraviť návrh odpovede",
            "description": "Zhrň zistenia a priprav odpoveď pre zákazníka na schválenie.",
            "status": "suggested",
            "owner": "agent.response",
        }
    )
    follow_up_needed = "log" not in lowered and intent_label in {"bug_report", "incident"}
    if follow_up_needed or intent_label in {"question", "general_support"}:
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "questions"),
                "title": "Navrhnúť doplňujúce otázky",
                "description": "Priprav otázky pre zákazníka, ktoré pomôžu urýchliť riešenie.",
                "status": "suggested",
                "owner": "agent.engagement",
            }
        )
    if complexity_level == "high":
        subtasks.append(
            {
                "id": _subtask_id(issue_key, "escalation"),
                "title": "Pripraviť eskaláciu",
                "description": "Zhromaždi všetky dôležité fakty pre prípadnú eskaláciu na L2/L3.",
                "status": "suggested",
                "owner": "agent.escalation",
            }
        )
    return subtasks


def generate_suggested_steps(
    intent_label: str,
    summary: str,
    body: str,
    complexity_level: str,
) -> Dict[str, Any]:
    keywords = [token for token in re.findall(r"[A-Za-zÁ-Žá-ž0-9]{3,}", summary)][:6]
    base_query = " ".join(keywords) or summary
    if intent_label == "bug_report":
        queries = [
            f"Incident - {base_query}",
            "Troubleshooting guide for reported error",
        ]
    elif intent_label == "incident":
        queries = [
            f"Outage status {base_query}",
            "Incident runbook",
        ]
    elif intent_label == "access_request":
        queries = [
            f"Access provisioning {base_query}",
            "IAM onboarding checklist",
        ]
    elif intent_label == "billing":
        queries = [
            f"Billing discrepancy {base_query}",
            "Refund policy",
        ]
    else:
        queries = [base_query, "Knowledge base search"]
    seen_queries: set[str] = set()
    deduped_queries: List[str] = []
    for query in queries:
        candidate = query.strip()
        if not candidate:
            continue
        lowered = candidate.lower()
        if lowered in seen_queries:
            continue
        seen_queries.add(lowered)
        deduped_queries.append(candidate)
    lowered_body = body.lower()
    follow_up_questions: List[str] = []
    if intent_label in {"bug_report", "incident"} and "log" not in lowered_body:
        follow_up_questions.append("Môžete prosím pripojiť relevantné logy alebo screenshot problému?")
    if intent_label == "access_request" and "username" not in lowered_body:
        follow_up_questions.append("Potvrdíte prihlasovacie meno a požadovanú rolu?")
    if intent_label == "billing" and "invoice" not in lowered_body:
        follow_up_questions.append("Pošlite číslo faktúry alebo obdobie fakturácie, ktorého sa problém týka.")
    if complexity_level == "high":
        follow_up_questions.append("Existuje termín alebo obchodný dopad, o ktorom by sme mali vedieť?")
    draft_response = (
        "Ahoj, ďakujeme za podnet. Identifikovali sme ho ako "
        f"{intent_label.replace('_', ' ')} a pracujeme na navrhnutých krokoch. "
        "Dáme vedieť hneď, ako budeme mať ďalšie informácie."
    )
    if intent_label in {"bug_report", "incident"}:
        draft_response += " Medzitým nám prosím pošlite všetky nové pozorovania."  # type: ignore[operator]
    return {
        "knowledge_base_queries": deduped_queries,
        "draft_response": draft_response,
        "follow_up_questions": follow_up_questions,
    }


def build_notification(
    issue_key: str,
    intent: Dict[str, Any],
    complexity: Dict[str, Any],
    subtasks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "channel": "ui.sidebar",
        "event": "suggestions.updated",
        "issueKey": issue_key,
        "intent": intent.get("label"),
        "complexity": complexity.get("level"),
        "subtaskCount": len(subtasks),
        "timestamp": time.time(),
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
    response = ingest_issue(key, issue_payload, event=payload)
    return {"ok": True, "proposals": response}


def _resolve_event_type(event: Optional[Mapping[str, Any]]) -> str:
    if not event:
        return "ticket.inspect"
    for key in ("webhookEvent", "event", "notificationEvent", "issue_event_type_name"):
        value = event.get(key) if isinstance(event, Mapping) else None
        if value:
            return str(value)
    if isinstance(event, Mapping) and event.get("comment"):
        return "message.added"
    if isinstance(event, Mapping) and event.get("issue"):
        return "ticket.updated"
    return "ticket.event"


def _extract_comment_text(event: Optional[Mapping[str, Any]]) -> str:
    if not event or not isinstance(event, Mapping):
        return ""
    comment = event.get("comment")
    if isinstance(comment, Mapping):
        for key in ("body", "bodyText", "renderedBody"):
            if key in comment:
                return _as_plain_text(comment.get(key))
    return ""


def ingest_issue(
    issue_key: str,
    issue_payload: Dict[str, Any],
    tenant: Optional[str] = None,
    *,
    event: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    fields = issue_payload.get("fields", {})
    summary = str(fields.get("summary") or "(no summary)")
    event_type = _resolve_event_type(event)
    comment_text_raw = _extract_comment_text(event)
    description_text = _as_plain_text(fields.get("description"))
    description_text = description_text or _as_plain_text(fields.get("descriptionText"))
    summary_text = summary
    body_parts = []
    initial_source = "summary"
    if comment_text_raw:
        body_parts.append(comment_text_raw)
        initial_source = "comment"
    if description_text:
        body_parts.append(description_text)
        if initial_source == "summary":
            initial_source = "description"
    if summary_text:
        body_parts.append(summary_text)
    raw_body = _merge_text_parts(body_parts)
    redacted_body, pii_hits = redact_pii(raw_body)
    PII_VAULT[issue_key] = pii_hits
    intent_info = classify_intent(summary, redacted_body)
    complexity_info = estimate_complexity(summary, redacted_body, event_type)
    subtasks = generate_subtasks(
        issue_key,
        intent_info["label"],
        complexity_info["level"],
        summary,
        redacted_body,
    )
    suggested_steps = generate_suggested_steps(
        intent_info["label"], summary, redacted_body, complexity_info["level"]
    )
    pii_summary = {
        "count": len(pii_hits),
        "types": sorted({entry["type"] for entry in pii_hits}),
    }
    analysis = {
        "intent": intent_info,
        "complexity": complexity_info,
        "initial_body": redacted_body,
        "initial_body_source": initial_source,
        "pii": pii_summary,
        "subtasks": subtasks,
        "suggested_steps": suggested_steps,
        "event": event_type,
    }
    notification = build_notification(issue_key, intent_info, complexity_info, subtasks)
    analysis["notifications"] = [notification]

    follow_up = suggested_steps.get("follow_up_questions") or []
    follow_up_line = follow_up[0] if follow_up else "Prosím doplň posledné logy alebo ďalšie detaily, aby sme vedeli pokračovať."
    comment_text = (
        f"Ahoj! Pracujeme na tickete {issue_key}. "
        f"Identifikovali sme intent {intent_info['label'].replace('_', ' ')} "
        f"(komplexita {complexity_info['level']}). {follow_up_line}"
    )
    proposals: List[Dict[str, Any]] = [
        {
            "id": "add-comment-1",
            "kind": "comment",
            "body_adf": adf_from_text(comment_text),
            "explain": "Automaticky navrhnutá odpoveď vrátane ďalších krokov.",
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
        proposal["estimatedSeconds"] = metrics_module.estimate_seconds(proposal.get("kind", ""))
    estimated_total = sum(int(proposal.get("estimatedSeconds") or 0) for proposal in proposals)
    estimated = {"seconds": estimated_total or DEFAULT_ESTIMATED_SAVINGS_SECONDS}
    response = {
        "issueKey": issue_key,
        "proposals": proposals,
        "estimated_savings": estimated,
        "analysis": analysis,
    }
    SUGGESTIONS[issue_key] = response
    entry = LEDGER.setdefault(issue_key, {"issueKey": issue_key, "history": []})
    entry["last_ingest_at"] = time.time()
    entry["estimated_savings"] = estimated
    entry["draft_text"] = comment_text
    entry["ticket"] = {
        "initial_body": redacted_body,
        "initial_body_source": initial_source,
        "intent": intent_info,
        "complexity": complexity_info,
        "subtasks": subtasks,
        "suggested_steps": suggested_steps,
        "pii_summary": pii_summary,
        "analysis_event": event_type,
        "analysis_ts": datetime.now(timezone.utc).isoformat(),
        "tenant": tenant,
    }
    entry.setdefault("notifications", []).append(notification)
    entry["last_notification"] = notification
    entry["last_analysis"] = analysis
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
    issue_key: str,
    action: ApplyAction,
    tenant: str,
    actor: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
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
    seconds_context: Dict[str, Any] = {"proposal": suggestion or {}}
    if context:
        seconds_context["context"] = context
    credit_seconds = metrics_module.estimate_seconds(action.kind, seconds_context)
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
    entry["last_actor"] = actor
    entry["last_seconds_saved"] = credit_seconds
    proposal_context: Dict[str, Any] = {}
    if suggestion:
        proposal_context.update({k: v for k, v in suggestion.items() if k not in {"explain"}})
    proposal_context.update(action.model_dump(exclude_none=True))
    if applied_detail.get("labels"):
        proposal_context["labels"] = applied_detail["labels"]
    if applied_detail.get("transitionId"):
        proposal_context["transitionId"] = applied_detail["transitionId"]
    entry["last_proposal_context"] = proposal_context
    result_payload = {
        "status": "success",
        "action": action.kind,
        "details": applied_detail,
    }
    return {
        "result": result_payload,
        "entry": entry,
        "record": record,
        "seconds_saved": credit_seconds,
        "quality": quality,
        "proposal_context": proposal_context,
        "suggestion": suggestion,
        "final_text": final_text,
    }


# -------- Ingest: create proposals --------
@app.get("/v1/jira/ingest")
async def ingest(request: Request, issueKey: str = Query(..., alias="issueKey")):
    body = await request.body()
    tenant = ensure_authorized(request, body=body)
    try:
        issue_payload = adapter.get_issue(issueKey)
    except Exception as exc:
        raise HTTPException(502, f"Failed to load issue {issueKey}: {exc}") from exc
    return ingest_issue(issueKey, issue_payload, tenant=tenant)


# -------- Apply: execute selected action --------
@app.post("/v1/jira/apply")
async def apply(request: Request, payload: ApplyIn):
    body = await request.body()
    tenant = ensure_authorized(request, body=body)
    actor = resolve_actor(request)
    idem_key = request.headers.get("idempotency-key")
    if not idem_key:
        raise HTTPException(400, "Missing Idempotency-Key")
    payload_hash = hashlib.sha256(body or b"").hexdigest()
    request_payload = payload.model_dump(mode="json", by_alias=True)
    with db.session_scope() as session:
        existing = db.get_apply_by_idempotency(session, tenant, idem_key)
        if existing:
            if existing.payload_hash != payload_hash:
                IDEMPOTENCY_CONFLICTS.labels(tenant=tenant).inc()
                raise HTTPException(409, "Idempotency-Key conflict")
            if existing.result:
                return existing.result
    try:
        apply_data = perform_apply(
            payload.issueKey,
            payload.action,
            tenant,
            actor,
            context=payload.context,
        )
    except HTTPException as exc:
        reason = str(exc.detail) if exc.detail else "HTTP error"
        record_apply_failure(payload.issueKey, payload.action, actor, reason)
        audit.log_event(
            {
                "event": "apply.failed",
                "issueKey": payload.issueKey,
                "actionId": payload.action.id,
                "actor": actor,
                "tenant": tenant,
                "reason": reason,
            }
        )
        raise
    except Exception as exc:  # pragma: no cover - defensive guard
        reason = str(exc)
        record_apply_failure(payload.issueKey, payload.action, actor, reason)
        audit.log_event(
            {
                "event": "apply.failed",
                "issueKey": payload.issueKey,
                "actionId": payload.action.id,
                "actor": actor,
                "tenant": tenant,
                "reason": reason,
            }
        )
        raise

    execution_context = {
        "secondsSaved": apply_data["seconds_saved"],
        "quality": apply_data["quality"],
        "text": apply_data["final_text"],
    }
    shares, attribution_reason = credit.tip_credit(
        payload.issueKey,
        apply_data["proposal_context"],
        actor,
        execution_context,
    )
    event_payload: Dict[str, Any]
    response_payload: Dict[str, Any]
    try:
        with db.session_scope() as session:
            event = credit.append_event(
                tenant,
                issue_key=payload.issueKey,
                action="apply",
                actor=actor,
                inputs=apply_data["proposal_context"],
                impact=Impact(
                    seconds_saved=int(apply_data["seconds_saved"]),
                    quality=apply_data["quality"],
                ),
                attributions=shares,
                parents=[payload.proposalEventId] if payload.proposalEventId else [],
                idempotency_key=idem_key,
                attribution_reason=attribution_reason,
                session=session,
            )
            event_payload = event.model_dump(mode="json", by_alias=True)
            response_payload = {
                "ok": True,
                "result": apply_data["result"],
                "credit": event_payload,
            }
            record_model = db.ApplyActionRecord(
                tenant_id=tenant,
                issue_key=payload.issueKey,
                payload=request_payload,
                result=response_payload,
                status="success",
                payload_hash=payload_hash,
                idempotency_key=idem_key,
                latency_ms=int(apply_data["record"].get("apply_ms", 0)),
            )
            session.add(record_model)
    except ValueError as exc:
        IDEMPOTENCY_CONFLICTS.labels(tenant=tenant).inc()
        raise HTTPException(409, str(exc)) from exc

    record = apply_data["record"]
    record["credit_event_id"] = event.id
    entry = apply_data["entry"]
    entry.setdefault("credit_events", []).append(event_payload)
    entry["last_credit_event"] = event_payload

    audit.log_event(
        {
            "event": "apply.success",
            "issueKey": payload.issueKey,
            "actionId": payload.action.id,
            "actor": actor,
            "tenant": tenant,
            "secondsSaved": event.impact.secondsSaved,
            "eventId": event.id,
        }
    )
    action_label = payload.action.kind
    APPLIES_TOTAL.labels(tenant=tenant, action=action_label).inc()
    APPLY_LATENCY.labels(tenant=tenant, action=action_label).observe(float(record.get("apply_ms", 0)))
    SECONDS_SAVED_TOTAL.labels(tenant=tenant).inc(float(apply_data["seconds_saved"]))
    return response_payload


# -------- Ledger read --------
@app.get("/v1/ledger")
def get_ledger(request: Request, issueKey: str = Query(..., alias="issueKey")):
    ensure_authorized(request, body=b"")
    return LEDGER.get(issueKey, {"issueKey": issueKey, "history": []})


@app.get("/v1/credit/summary")
def credit_summary_endpoint(
    request: Request,
    since: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    tenant = ensure_authorized(request, body=b"")
    return credit.summary(tenant, since=parse_since(since), limit=limit)


@app.get("/v1/credit/agent/{id}")
def credit_agent_endpoint(
    id: str,
    request: Request,
    window: str = Query("30d"),
    limit: int = Query(20, ge=0, le=100),
):
    tenant = ensure_authorized(request, body=b"")
    days = parse_window_days(window)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    summary = credit.agent_summary(tenant, id, since=since, limit=limit)
    events = [event.model_dump(mode="json", by_alias=True) for event in summary.events]
    return {
        "agent": summary.agentId,
        "window_days": days,
        "total_seconds": summary.totalSecondsSaved,
        "score": summary.score,
        "events": events,
    }


@app.get("/v1/credit/issue/{key}")
def credit_issue_endpoint(
    key: str,
    request: Request,
    since: Optional[str] = Query(None),
    limit: int = Query(20, ge=0, le=200),
):
    tenant = ensure_authorized(request, body=b"")
    since_dt = parse_since(since)
    summary = credit.issue_summary(tenant, key, since=since_dt, limit=limit)
    contributors = [
        {
            "agent_id": contributor.id,
            "seconds": contributor.secondsSaved,
            "share": contributor.share,
            "events": contributor.events,
        }
        for contributor in summary.contributors
    ]
    events = credit.events_for_issue(tenant, key)
    if limit:
        events = events[-limit:]
    events_payload = [event.model_dump(mode="json", by_alias=True) for event in reversed(events)]
    payload: Dict[str, Any] = {
        "issue": summary.issueKey,
        "total_seconds": summary.totalSecondsSaved,
        "contributors": contributors,
        "events": events_payload,
    }
    if summary.windowSecondsSaved is not None:
        payload["window_seconds"] = summary.windowSecondsSaved
    if summary.windowStart is not None:
        payload["window_start"] = summary.windowStart.isoformat()
    return payload


@app.get("/v1/credit/chain")
def credit_chain_endpoint(request: Request, limit: int = Query(100, ge=1, le=500)):
    tenant = ensure_authorized(request, body=b"")
    return credit.credit_chain(tenant, limit=limit)


@app.get("/v1/credit/agents/top")
def credit_agents_top(
    request: Request,
    window: str = Query("30d"),
    limit: int = Query(10, ge=1, le=100),
):
    tenant = ensure_authorized(request, body=b"")
    days = parse_window_days(window)
    rankings = credit.top_agents(tenant, days, limit=None)
    payload = [
        {
            "agent_id": item.get("agent_id"),
            "seconds": float(item.get("seconds", 0.0)),
            "events": int(item.get("events", 0)),
        }
        for item in rankings[:limit]
    ]
    return payload


@app.get("/v1/metrics/seconds-saved")
def metrics_seconds_saved(request: Request, window: str = Query("7d")):
    tenant = ensure_authorized(request, body=b"")
    days = parse_window_days(window)
    return metrics_module.seconds_saved_window(tenant, days)


@app.get("/v1/agents/top")
def agents_top_endpoint(
    request: Request,
    window: str = Query("30d"),
    limit: int = Query(10, ge=1, le=100),
):
    tenant = ensure_authorized(request, body=b"")
    days = parse_window_days(window)
    rankings = credit.top_agents(tenant, days, limit=None)
    total_seconds = sum(float(item.get("seconds", 0.0)) for item in rankings) or 1.0
    payload = [
        {
            "id": item.get("agent_id"),
            "secondsSaved": float(item.get("seconds", 0.0)),
            "share": float(item.get("seconds", 0.0)) / total_seconds,
            "events": int(item.get("events", 0)),
        }
        for item in rankings[:limit]
    ]
    return {"window_days": days, "contributors": payload}


@app.get("/v1/metrics/throughput")
def metrics_throughput(request: Request, window: str = Query("7d")):
    tenant = ensure_authorized(request, body=b"")
    days = parse_window_days(window)
    return metrics_module.throughput(tenant, window_days=days)


@app.get("/v1/metrics/ttr_frt_baseline")
def metrics_ttr_frt_baseline(request: Request):
    tenant = ensure_authorized(request, body=b"")
    return metrics_module.ttr_frt_baseline(tenant)


@app.get("/v1/metrics/top-contributors")
def metrics_top_contributors(request: Request, window: str = Query("30d")):
    tenant = ensure_authorized(request, body=b"")
    days = parse_window_days(window)
    contributors = metrics_module.top_contributors(tenant, window_days=days)
    return {"windowDays": days, "contributors": contributors}


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
