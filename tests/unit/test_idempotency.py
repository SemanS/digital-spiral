import hashlib
import importlib
import json
from pathlib import Path
from fastapi.testclient import TestClient

from clients.python.jira_adapter import JiraAdapter


def _headers(secret: str, body: bytes, *, idem: str | None = None, include_signature: bool = True) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": "Bearer unit-token",
        "Content-Type": "application/json",
        "X-DS-Actor": "human.tester",
    }
    if include_signature:
        digest = hashlib.sha256(secret.encode("utf-8") + body).hexdigest()
        headers["X-Forge-Signature"] = f"sha256={digest}"
    if idem:
        headers["Idempotency-Key"] = idem
    return headers


def _setup_app(monkeypatch, tmp_path: Path, live_server: str):
    ledger_path = tmp_path / "ledger.jsonl"
    secret = "unit-secret"
    monkeypatch.setenv("JIRA_BASE_URL", live_server)
    monkeypatch.setenv("JIRA_TOKEN", "mock-token")
    monkeypatch.setenv("FORGE_SHARED_SECRET", secret)
    monkeypatch.setenv("ORCHESTRATOR_TOKEN", "unit-token")
    monkeypatch.setenv("CREDIT_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("AUTO_REGISTER_WEBHOOK", "0")
    monkeypatch.setenv("FORGE_ALLOWLIST", "")

    credit = importlib.import_module("orchestrator.credit")
    importlib.reload(credit)
    app_module = importlib.import_module("orchestrator.app")
    importlib.reload(app_module)
    return secret, app_module


def _create_comment_proposal(app_module, secret: str, issue_key: str) -> dict:
    with TestClient(app_module.app) as client:
        ingest_resp = client.get(
            f"/v1/jira/ingest?issueKey={issue_key}", headers=_headers(secret, b"")
        )
        assert ingest_resp.status_code == 200
        proposals = ingest_resp.json().get("proposals", [])
        assert proposals, "expected proposals for issue"
        comment = next((item for item in proposals if item.get("kind") == "comment"), None)
        assert comment is not None, "expected comment proposal"
        return comment


def test_missing_signature_returns_401(monkeypatch, tmp_path: Path, live_server: str) -> None:
    secret, app_module = _setup_app(monkeypatch, tmp_path, live_server)

    adapter = JiraAdapter(live_server, "mock-token")
    issue = adapter.create_issue("DEV", "10001", "Signature test", fields={"summary": "Sig"})
    issue_key = issue["key"]
    comment = _create_comment_proposal(app_module, secret, issue_key)

    body = json.dumps({"issueKey": issue_key, "action": comment}).encode("utf-8")
    with TestClient(app_module.app) as client:
        resp = client.post(
            "/v1/jira/apply",
            data=body,
            headers=_headers(secret, body, idem="sig-test", include_signature=False),
        )
    assert resp.status_code == 401


def test_idempotency_conflict(monkeypatch, tmp_path: Path, live_server: str) -> None:
    secret, app_module = _setup_app(monkeypatch, tmp_path, live_server)

    adapter = JiraAdapter(live_server, "mock-token")
    issue = adapter.create_issue("DEV", "10001", "Idempotency test", fields={"summary": "Idem"})
    issue_key = issue["key"]
    comment = _create_comment_proposal(app_module, secret, issue_key)

    idem_key = "conflict-key"
    body_one = json.dumps({
        "issueKey": issue_key,
        "action": comment,
        "context": {"source": "unit"},
    }).encode("utf-8")
    body_two = json.dumps({
        "issueKey": issue_key,
        "action": comment,
        "context": {"source": "unit", "attempt": 2},
    }).encode("utf-8")

    with TestClient(app_module.app) as client:
        first = client.post(
            "/v1/jira/apply",
            data=body_one,
            headers=_headers(secret, body_one, idem=idem_key),
        )
        assert first.status_code == 200

        second = client.post(
            "/v1/jira/apply",
            data=body_two,
            headers=_headers(secret, body_two, idem=idem_key),
        )
        assert second.status_code == 409
