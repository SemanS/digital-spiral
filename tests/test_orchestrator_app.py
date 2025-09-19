from __future__ import annotations

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
    with TestClient(module.app) as client:
        yield client, module, adapter
    module.adapter = original_adapter
    module.LEDGER.clear()
    module.SUGGESTIONS.clear()
    module.APPLY_RESULTS.clear()
    module.credit.reset_ledger(ledger_path, truncate=True)


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
    response = client.get(
        "/v1/jira/ingest",
        params={"issueKey": "SUP-1"},
        headers={"x-ds-secret": "unit-shared-secret"},
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
    ingest_response = client.get(
        "/v1/jira/ingest",
        params={"issueKey": "SUP-3"},
        headers={"x-ds-secret": "unit-shared-secret"},
    )
    proposals = ingest_response.json()["proposals"]
    comment_action = next(p for p in proposals if p["kind"] == "comment")
    label_action = next(p for p in proposals if p["kind"] == "set-labels")

    apply_response = client.post(
        "/v1/jira/apply",
        json={"issueKey": "SUP-3", "action": comment_action},
        headers={
            "x-ds-secret": "unit-shared-secret",
            "Idempotency-Key": f"SUP-3:{comment_action['id']}",
            "X-DS-Actor": "human.test-user",
            "X-DS-Actor-Display": "Test User",
        },
    )
    assert apply_response.status_code == 200
    result = apply_response.json()
    assert result["ok"] is True
    assert result["credit"]["secondsSaved"] > 0
    assert result["credit"]["splits"]
    assert adapter.comments and adapter.comments[0][0] == "SUP-3"

    second_call = client.post(
        "/v1/jira/apply",
        json={"issueKey": "SUP-3", "action": comment_action},
        headers={
            "x-ds-secret": "unit-shared-secret",
            "Idempotency-Key": f"SUP-3:{comment_action['id']}",
            "X-DS-Actor": "human.test-user",
        },
    )
    assert second_call.status_code == 200
    assert len(adapter.comments) == 1

    apply_labels = client.post(
        "/v1/jira/apply",
        json={"issueKey": "SUP-3", "action": label_action},
        headers={
            "x-ds-secret": "unit-shared-secret",
            "Idempotency-Key": f"SUP-3:{label_action['id']}",
            "X-DS-Actor": "human.test-user",
        },
    )
    assert apply_labels.status_code == 200
    assert adapter.updated_fields and adapter.updated_fields[0][1]["labels"]
    ledger_entry = module.LEDGER["SUP-3"]
    assert ledger_entry["total_credit_seconds"] > 0
    issue_credit = client.get(
        "/v1/credit/issue/SUP-3",
        headers={"x-ds-secret": "unit-shared-secret"},
    )
    assert issue_credit.status_code == 200
    issue_payload = issue_credit.json()
    assert issue_payload["totalSecondsSaved"] >= result["credit"]["secondsSaved"]
    chain_resp = client.get(
        "/v1/credit/chain",
        params={"limit": 5},
        headers={"x-ds-secret": "unit-shared-secret"},
    )
    assert chain_resp.status_code == 200
    chain_events = chain_resp.json()
    assert any(event["id"] == result["credit"]["eventId"] for event in chain_events)
    agent_summary = client.get(
        "/v1/credit/agent/human.test-user",
        headers={"x-ds-secret": "unit-shared-secret"},
    )
    assert agent_summary.status_code == 200
    agent_payload = agent_summary.json()
    assert agent_payload["totalSecondsSaved"] > 0
