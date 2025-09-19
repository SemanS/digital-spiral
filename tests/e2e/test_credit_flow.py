from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from clients.python.jira_adapter import JiraAdapter


def _auth_headers(secret: str) -> dict[str, str]:
    return {
        "X-DS-Secret": secret,
        "X-DS-Actor": "human.tester",
        "Idempotency-Key": "test-key",
        "Content-Type": "application/json",
    }


def test_apply_creates_credit_event(monkeypatch, tmp_path: Path, live_server: str) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    secret = "integration-secret"

    monkeypatch.setenv("JIRA_BASE_URL", live_server)
    monkeypatch.setenv("JIRA_TOKEN", "mock-token")
    monkeypatch.setenv("FORGE_SHARED_SECRET", secret)
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
            f"/v1/jira/ingest?issueKey={issue_key}", headers={"X-DS-Secret": secret}
        )
        assert ingest_resp.status_code == 200
        proposals = ingest_resp.json().get("proposals", [])
        assert proposals, "expected at least one proposal"
        comment = next((item for item in proposals if item.get("kind") == "comment"), None)
        assert comment is not None, "comment proposal expected"

        apply_resp = client.post(
            "/v1/jira/apply",
            json={"issueKey": issue_key, "action": comment},
            headers=_auth_headers(secret),
        )
        assert apply_resp.status_code == 200
        payload = apply_resp.json()
        assert payload.get("ok") is True
        credit_block = payload.get("credit")
        assert credit_block and credit_block.get("secondsSaved")
        splits = credit_block.get("splits", [])
        assert len(splits) >= 1
        assert abs(sum(split.get("weight", 0.0) for split in splits) - 1.0) < 1e-6

        summary_resp = client.get(
            f"/v1/credit/issue/{issue_key}", headers={"X-DS-Secret": secret}
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary.get("totalSecondsSaved") >= credit_block["secondsSaved"]
        assert summary.get("recentEvents"), "expected recent events recorded"

    ledger_contents = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert ledger_contents, "ledger should contain at least one event"
