from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from clients.python.jira_adapter import JiraAdapter


def _auth_headers(secret: str, body: bytes, *, idem: str | None = None) -> dict[str, str]:
    signature = hashlib.sha256(secret.encode("utf-8") + body).hexdigest()
    headers = {
        "Authorization": "Bearer e2e-token",
        "X-Forge-Signature": f"sha256={signature}",
        "X-DS-Actor": "human.tester",
        "Content-Type": "application/json",
    }
    if idem:
        headers["Idempotency-Key"] = idem
    return headers


def test_apply_creates_credit_event(monkeypatch, tmp_path: Path, live_server: str) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    secret = "integration-secret"

    monkeypatch.setenv("JIRA_BASE_URL", live_server)
    monkeypatch.setenv("JIRA_TOKEN", "mock-token")
    monkeypatch.setenv("FORGE_SHARED_SECRET", secret)
    monkeypatch.setenv("ORCHESTRATOR_TOKEN", "e2e-token")
    monkeypatch.setenv("CREDIT_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("AUTO_REGISTER_WEBHOOK", "0")
    monkeypatch.setenv("FORGE_ALLOWLIST", "")

    credit = importlib.import_module("orchestrator.credit")
    importlib.reload(credit)
    app_module = importlib.import_module("orchestrator.app")
    importlib.reload(app_module)

    adapter = JiraAdapter(live_server, "mock-token")
    created = adapter.create_issue("DEV", "10001", "Credit flow", fields={"summary": "Credit flow"})
    issue_key = created["key"]

    with TestClient(app_module.app) as client:
        ingest_resp = client.get(
            f"/v1/jira/ingest?issueKey={issue_key}", headers=_auth_headers(secret, b"")
        )
        assert ingest_resp.status_code == 200
        proposals = ingest_resp.json().get("proposals", [])
        assert proposals, "expected at least one proposal"
        comment = next((item for item in proposals if item.get("kind") == "comment"), None)
        assert comment is not None, "comment proposal expected"

        apply_body = json.dumps({"issueKey": issue_key, "action": comment}).encode("utf-8")
        apply_resp = client.post(
            "/v1/jira/apply",
            data=apply_body,
            headers=_auth_headers(secret, apply_body, idem="test-key"),
        )
        assert apply_resp.status_code == 200
        payload = apply_resp.json()
        assert payload.get("ok") is True
        credit_block = payload.get("credit")
        assert credit_block and credit_block.get("impact", {}).get("secondsSaved")
        attributions = credit_block.get("attributions", [])
        assert attributions, "attributions expected"
        assert abs(sum(item.get("weight", 0.0) for item in attributions) - 1.0) < 1e-6

        repeat_resp = client.post(
            "/v1/jira/apply",
            data=apply_body,
            headers=_auth_headers(secret, apply_body, idem="test-key"),
        )
        assert repeat_resp.status_code == 200
        assert repeat_resp.json()["credit"]["id"] == credit_block["id"]

        summary_resp = client.get(
            f"/v1/credit/issue/{issue_key}", headers=_auth_headers(secret, b"")
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary.get("total_seconds") >= credit_block["impact"]["secondsSaved"]
        assert summary.get("events"), "expected recent events recorded"

        top_resp = client.get(
            "/v1/credit/agents/top?window=30d", headers=_auth_headers(secret, b"")
        )
        assert top_resp.status_code == 200
        top_agents = top_resp.json()
        assert isinstance(top_agents, list)
        assert any(item.get("agent_id") for item in top_agents)

        seconds_resp = client.get(
            "/v1/metrics/seconds-saved?window=7d", headers=_auth_headers(secret, b"")
        )
        assert seconds_resp.status_code == 200
        seconds_payload = seconds_resp.json()
        assert seconds_payload.get("windowDays") == 7

        throughput_resp = client.get(
            "/v1/metrics/throughput?window=7d", headers=_auth_headers(secret, b"")
        )
        assert throughput_resp.status_code == 200
        throughput_payload = throughput_resp.json()
        assert throughput_payload.get("windowDays") == 7
        assert throughput_payload.get("count") >= 1

    ledger_contents = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert ledger_contents, "ledger should contain at least one event"
