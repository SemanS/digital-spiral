from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


class DummyAdapter:
    def __init__(self) -> None:
        self.webhooks: list[dict[str, Any]] = []
        self.issue_payloads: dict[str, dict[str, Any]] = {}
        self.comments: list[tuple[str, dict[str, Any]]] = []
        self.transition_calls: list[tuple[str, str]] = []
        self.updated_fields: list[tuple[str, dict[str, Any]]] = []
        self.transitions = [{"id": "11", "name": "Start"}]

    def list_webhooks(self) -> list[dict[str, Any]]:
        return list(self.webhooks)

    def register_webhook(
        self,
        url: str,
        jql: str,
        events: list[str] | None = None,
        secret: str | None = None,
    ) -> list[dict[str, Any]]:
        self.webhooks.append(
            {
                "id": str(len(self.webhooks) + 1),
                "url": url,
                "jql": jql,
                "events": list(events or []),
                "secret": secret,
            }
        )
        return [{"createdWebhookId": str(len(self.webhooks)), "failureReason": None}]

    def get_issue(self, key: str) -> dict[str, Any]:
        payload = self.issue_payloads.get(key)
        if not payload:
            payload = {"key": key, "fields": {"summary": "Auto", "labels": []}}
            self.issue_payloads[key] = payload
        return payload

    def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
        self.comments.append((key, body_adf))
        return {}

    def list_transitions(self, key: str) -> list[dict[str, Any]]:
        return list(self.transitions)

    def transition_issue(self, key: str, transition_id: str) -> dict[str, Any]:
        self.transition_calls.append((key, transition_id))
        return {}

    def update_issue_fields(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        self.updated_fields.append((key, fields))
        payload = self.issue_payloads.setdefault(
            key, {"key": key, "fields": {"summary": "", "labels": []}}
        )
        payload.setdefault("fields", {})["labels"] = list(fields.get("labels", []))
        return {}


@pytest.fixture()
def orchestrator_test_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JIRA_BASE_URL", "http://mock-jira:9000")
    monkeypatch.setenv("JIRA_TOKEN", "unit-token")
    monkeypatch.setenv("WEBHOOK_SECRET", "unit-secret")
    monkeypatch.setenv("ORCH_SECRET", "unit-shared-secret")
    monkeypatch.setenv("ORCHESTRATOR_TOKEN", "unit-orch-token")
    monkeypatch.setenv("ORCHESTRATOR_BASE_URL", "http://orchestrator:7010")
    monkeypatch.setenv("AUTO_REGISTER_WEBHOOK", "1")
    ledger_path = Path("artifacts/test-credit-ledger.jsonl")
    if ledger_path.exists():
        ledger_path.unlink()
    monkeypatch.setenv("CREDIT_LEDGER_PATH", str(ledger_path))
    orchestrator_module = importlib.import_module("orchestrator.app")
    module = importlib.reload(orchestrator_module)
    module.credit.reset_ledger(ledger_path, truncate=True)
    adapter = DummyAdapter()
    original_adapter = module.adapter
    module.adapter = adapter
    module.LEDGER.clear()
    module.SUGGESTIONS.clear()
    module.APPLY_RESULTS.clear()
    module.APPLY_FINGERPRINTS.clear()
    with TestClient(module.app) as client:
        yield client, module, adapter
    module.adapter = original_adapter
    module.LEDGER.clear()
    module.SUGGESTIONS.clear()
    module.APPLY_RESULTS.clear()
    module.APPLY_FINGERPRINTS.clear()
    module.credit.reset_ledger(ledger_path, truncate=True)


def forge_headers(
    secret: str,
    body: bytes,
    *,
    idem: str | None = None,
    actor: str | None = None,
    display: str | None = None,
) -> dict[str, str]:
    signature = hashlib.sha256(secret.encode("utf-8") + body).hexdigest()
    headers = {
        "Authorization": "Bearer unit-orch-token",
        "X-Forge-Signature": f"sha256={signature}",
    }
    if idem:
        headers["Idempotency-Key"] = idem
    if actor:
        headers["X-DS-Actor"] = actor
    if display:
        headers["X-DS-Actor-Display"] = display
    return headers


def test_startup_registers_webhook(orchestrator_test_app):
    _, module, adapter = orchestrator_test_app
    assert adapter.webhooks
    registration = adapter.webhooks[0]
    assert registration["url"].endswith("/webhooks/jira")
    assert set(registration["events"]) == set(module.WEBHOOK_EVENTS)
    assert registration["jql"] == module.WEBHOOK_JQL


def test_ingest_returns_proposals(orchestrator_test_app):
    client, module, adapter = orchestrator_test_app
    adapter.issue_payloads["SUP-1"] = {
        "key": "SUP-1",
        "fields": {"summary": "Potrebujeme info", "labels": []},
    }
    headers = forge_headers(module.FORGE_SHARED_SECRET, b"")
    response = client.get(
        "/v1/jira/ingest",
        params={"issueKey": "SUP-1"},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["issueKey"] == "SUP-1"
    assert module.SUGGESTIONS["SUP-1"]["proposals"] == payload["proposals"]
    assert any(p["kind"] == "comment" for p in payload["proposals"])
    assert all("estimatedSeconds" in proposal for proposal in payload["proposals"])
    expected_total = sum(int(proposal["estimatedSeconds"]) for proposal in payload["proposals"])
    ledger_entry = module.LEDGER["SUP-1"]
    assert ledger_entry["estimated_savings"]["seconds"] == payload["estimated_savings"]["seconds"]
    assert payload["estimated_savings"]["seconds"] == expected_total


def test_ingest_rejects_invalid_signature(orchestrator_test_app):
    client, module, _ = orchestrator_test_app
    headers = forge_headers(module.FORGE_SHARED_SECRET, b"")
    headers["X-Forge-Signature"] = "sha256=deadbeef"
    response = client.get(
        "/v1/jira/ingest",
        params={"issueKey": "SUP-unauthorized"},
        headers=headers,
    )
    assert response.status_code == 401


def test_webhook_triggers_auto_ingest(orchestrator_test_app):
    client, module, adapter = orchestrator_test_app
    adapter.issue_payloads["SUP-2"] = {"key": "SUP-2", "fields": {"summary": "Login nejde", "labels": []}}
    payload = {"issue": {"key": "SUP-2"}}
    body = json.dumps(payload).encode("utf-8")
    signature = hashlib.sha256(module.WEBHOOK_SECRET.encode("utf-8") + body).hexdigest()
    resp = client.post(
        "/webhooks/jira",
        data=body,
        headers={
            "content-type": "application/json",
            "x-mockjira-signature": f"sha256={signature}",
        },
    )
    assert resp.status_code == 200
    assert "SUP-2" in module.SUGGESTIONS
    assert module.SUGGESTIONS["SUP-2"]["proposals"]
    assert module.LEDGER["SUP-2"]["last_event"] == payload


def test_apply_executes_full_plan(orchestrator_test_app):
    client, module, adapter = orchestrator_test_app
    adapter.issue_payloads["SUP-3"] = {
        "key": "SUP-3",
        "fields": {"summary": "Potrebujem podporu", "labels": []},
    }
    ingest_headers = forge_headers(module.FORGE_SHARED_SECRET, b"")
    ingest_response = client.get(
        "/v1/jira/ingest",
        params={"issueKey": "SUP-3"},
        headers=ingest_headers,
    )
    proposals = ingest_response.json()["proposals"]
    comment_action = next(p for p in proposals if p["kind"] == "comment")
    label_action = next(p for p in proposals if p["kind"] == "set-labels")

    apply_payload = json.dumps({"issueKey": "SUP-3", "action": comment_action}).encode("utf-8")
    apply_headers = forge_headers(
        module.FORGE_SHARED_SECRET,
        apply_payload,
        idem=f"SUP-3:{comment_action['id']}",
        actor="human.test-user",
        display="Test User",
    )
    apply_headers["Content-Type"] = "application/json"
    apply_response = client.post(
        "/v1/jira/apply",
        data=apply_payload,
        headers=apply_headers,
    )
    assert apply_response.status_code == 200
    result = apply_response.json()
    assert result["ok"] is True
    assert result["result"]["status"] == "success"
    assert result["credit"]["impact"]["secondsSaved"] > 0
    assert result["credit"]["attributions"]
    assert adapter.comments and adapter.comments[0][0] == "SUP-3"
    credit_event_id = result["credit"]["id"]

    second_headers = forge_headers(
        module.FORGE_SHARED_SECRET,
        apply_payload,
        idem=f"SUP-3:{comment_action['id']}",
        actor="human.test-user",
    )
    second_headers["Content-Type"] = "application/json"
    second_call = client.post(
        "/v1/jira/apply",
        data=apply_payload,
        headers=second_headers,
    )
    assert second_call.status_code == 200
    assert second_call.json()["credit"]["id"] == credit_event_id
    assert len(adapter.comments) == 1

    labels_payload = json.dumps({"issueKey": "SUP-3", "action": label_action}).encode("utf-8")
    label_headers = forge_headers(
        module.FORGE_SHARED_SECRET,
        labels_payload,
        idem=f"SUP-3:{label_action['id']}",
        actor="human.test-user",
    )
    label_headers["Content-Type"] = "application/json"
    apply_labels = client.post(
        "/v1/jira/apply",
        data=labels_payload,
        headers=label_headers,
    )
    assert apply_labels.status_code == 200
    assert adapter.updated_fields and adapter.updated_fields[0][1]["labels"]
    ledger_entry = module.LEDGER["SUP-3"]
    assert ledger_entry["total_credit_seconds"] > 0
    credit_summary = result["credit"]
    issue_credit = client.get(
        "/v1/credit/issue/SUP-3",
        headers=forge_headers(module.FORGE_SHARED_SECRET, b""),
    )
    assert issue_credit.status_code == 200
    issue_payload = issue_credit.json()
    assert issue_payload["total_seconds"] >= credit_summary["impact"]["secondsSaved"]
    assert issue_payload["events"] and issue_payload["contributors"]
    chain_resp = client.get(
        "/v1/credit/chain",
        params={"limit": 5},
        headers=forge_headers(module.FORGE_SHARED_SECRET, b""),
    )
    assert chain_resp.status_code == 200
    chain_events = chain_resp.json()
    assert any(event["id"] == credit_event_id for event in chain_events)
    agent_summary = client.get(
        "/v1/credit/agent/human.test-user",
        headers=forge_headers(module.FORGE_SHARED_SECRET, b""),
    )
    assert agent_summary.status_code == 200
    agent_payload = agent_summary.json()
    assert agent_payload["total_seconds"] > 0


def test_agents_top_endpoint(orchestrator_test_app):
    client, module, adapter = orchestrator_test_app
    adapter.issue_payloads["SUP-4"] = {
        "key": "SUP-4",
        "fields": {"summary": "Potrebujeme prioritu", "labels": ["priority:medium"]},
    }
    ingest_headers = forge_headers(module.FORGE_SHARED_SECRET, b"")
    ingest_response = client.get(
        "/v1/jira/ingest",
        params={"issueKey": "SUP-4"},
        headers=ingest_headers,
    )
    proposals = ingest_response.json()["proposals"]
    comment_action = next(p for p in proposals if p["kind"] == "comment")
    apply_payload = json.dumps({"issueKey": "SUP-4", "action": comment_action}).encode("utf-8")
    apply_headers = forge_headers(
        module.FORGE_SHARED_SECRET,
        apply_payload,
        idem="SUP-4:comment",
        actor="human.test-user",
    )
    apply_headers["Content-Type"] = "application/json"
    apply_response = client.post(
        "/v1/jira/apply",
        data=apply_payload,
        headers=apply_headers,
    )
    assert apply_response.status_code == 200

    top_resp = client.get(
        "/v1/agents/top",
        params={"window": "30d"},
        headers=forge_headers(module.FORGE_SHARED_SECRET, b""),
    )
    assert top_resp.status_code == 200
    body = top_resp.json()
    assert body["window_days"] == 30
    assert body["contributors"], "expected at least one contributor"
