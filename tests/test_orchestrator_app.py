from __future__ import annotations

import hashlib
import importlib
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

import orchestrator.app as orchestrator_module


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
    monkeypatch.setenv("ORCHESTRATOR_BASE_URL", "http://orchestrator:7010")
    monkeypatch.setenv("AUTO_REGISTER_WEBHOOK", "1")
    module = importlib.reload(orchestrator_module)
    adapter = DummyAdapter()
    original_adapter = module.adapter
    module.adapter = adapter
    module.LEDGER.clear()
    module.SUGGESTIONS.clear()
    with TestClient(module.app) as client:
        yield client, module, adapter
    module.adapter = original_adapter
    module.LEDGER.clear()
    module.SUGGESTIONS.clear()


def test_startup_registers_webhook(orchestrator_test_app):
    _, module, adapter = orchestrator_test_app
    assert adapter.webhooks
    registration = adapter.webhooks[0]
    assert registration["url"].endswith("/webhooks/jira")
    assert set(registration["events"]) == set(module.WEBHOOK_EVENTS)
    assert registration["jql"] == module.WEBHOOK_JQL


def test_ingest_saves_suggestions(orchestrator_test_app):
    client, module, _ = orchestrator_test_app
    issue = {"key": "SUP-1", "fields": {"summary": "Potrebujeme info"}}
    response = client.post("/v1/jira/ingest", json={"issue": issue})
    assert response.status_code == 200
    suggestion = response.json()
    assert module.SUGGESTIONS["SUP-1"]["actions"] == suggestion["actions"]
    lookup = client.get("/v1/suggestions/SUP-1")
    assert lookup.status_code == 200
    assert lookup.json()["playbook_id"] == "jira-default"


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
    assert module.SUGGESTIONS["SUP-2"]["actions"]


def test_apply_executes_full_plan(orchestrator_test_app):
    client, module, adapter = orchestrator_test_app
    adapter.issue_payloads["SUP-3"] = {"key": "SUP-3", "fields": {"summary": "Potrebujem podporu", "labels": []}}
    issue = {"key": "SUP-3", "fields": {"summary": "Potrebujem podporu"}}
    ingest_response = client.post("/v1/jira/ingest", json={"issue": issue})
    draft = ingest_response.json()["draft_reply_adf"]
    apply_payload = {
        "issueKey": "SUP-3",
        "accepted_action_ids": ["reply-1", "transition-1", "label-1"],
        "draft_reply_adf": draft,
        "playbook_id": "jira-default",
    }
    apply_response = client.post("/v1/jira/apply", json=apply_payload)
    assert apply_response.status_code == 200
    assert adapter.comments and adapter.comments[0][0] == "SUP-3"
    assert adapter.transition_calls and adapter.transition_calls[0][0] == "SUP-3"
    assert adapter.updated_fields and adapter.updated_fields[0][1]["labels"] == ["needs-info"]
    assert module.LEDGER["SUP-3"]["credit"] > 0
