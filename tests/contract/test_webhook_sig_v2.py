from __future__ import annotations

import base64
import time
from typing import Any

import requests
from fastapi.testclient import TestClient

from mockjira.app import create_app
from mockjira.store import InMemoryStore
from tests.utils.webhook_sig import compute_sig_v2

AUTH = {"Authorization": "Bearer mock-token"}


def _poll_deliveries(base_url: str, session: requests.Session, timeout: float = 3.0) -> list[dict[str, Any]]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = session.get(f"{base_url}/rest/api/3/_mock/webhooks/deliveries", headers=AUTH, timeout=5)
        resp.raise_for_status()
        values = resp.json().get("values", [])
        if values:
            return values
        time.sleep(0.1)
    return []


def test_signature_v2_headers_and_digest(live_server: str) -> None:
    secret = "contract-secret"
    session = requests.Session()
    session.headers.update(AUTH)

    session.post(
        f"{live_server}/rest/api/3/_mock/webhooks/settings",
        json={"jitter_ms": [0, 0], "poison_prob": 0},
        timeout=5,
    )
    session.post(
        f"{live_server}/rest/api/3/webhook",
        json={
            "webhooks": [
                {"url": "http://listener", "events": ["jira:issue_created"], "secret": secret}
            ]
        },
        timeout=5,
    )

    session.post(
        f"{live_server}/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Signature contract"}},
        timeout=5,
    )

    deliveries = _poll_deliveries(live_server, session)
    assert deliveries, "expected webhook deliveries"
    delivered = deliveries[0]
    headers = delivered.get("headers", {})
    assert headers.get("X-MockJira-Signature-Version") == "2"
    assert "X-MockJira-Legacy-Signature" not in headers
    body = base64.b64decode(delivered.get("wireBody", ""))
    digest = compute_sig_v2(secret, body)
    sig_header = headers.get("X-MockJira-Signature", "")
    assert sig_header.startswith("sha256=")
    assert sig_header.split("=", 1)[1] == digest


def test_signature_v2_with_legacy_header(monkeypatch) -> None:
    monkeypatch.setenv("WEBHOOK_SIGNATURE_COMPAT", "1")
    monkeypatch.setenv("MOCKJIRA_WEBHOOK_JITTER_MIN", "0")
    monkeypatch.setenv("MOCKJIRA_WEBHOOK_JITTER_MAX", "0")
    store = InMemoryStore.with_seed_data()
    app = create_app(store)

    with TestClient(app) as client:
        client.post(
            "/rest/api/3/webhook",
            json={"webhooks": [{"url": "http://listener", "events": ["jira:issue_created"], "secret": "legacy"}]},
            headers=AUTH,
        )
        client.post(
            "/rest/api/3/issue",
            json={"fields": {"project": {"key": "DEV"}, "summary": "Legacy signature"}},
            headers=AUTH,
        )
        deliveries = client.get(
            "/rest/api/3/_mock/webhooks/deliveries",
            headers=AUTH,
        ).json()["values"]
    assert deliveries, "expected webhook deliveries"
    delivered = deliveries[0]
    headers = delivered.get("headers", {})
    assert headers.get("X-MockJira-Signature-Version") == "2"
    assert "X-MockJira-Legacy-Signature" in headers
