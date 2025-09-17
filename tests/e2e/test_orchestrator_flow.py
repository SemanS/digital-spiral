from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from clients.python.jira_adapter import JiraAdapter
from examples import orchestrator_demo


async def wait_for_deliveries() -> None:
    await asyncio.sleep(1.0)


def test_orchestrator_flow(monkeypatch, live_server: str, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []

    class DummyResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code

    class DummyClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover
            return None

        async def post(self, url: str, content: bytes | None = None, headers: dict | None = None):
            calls.append({"url": url, "content": content, "headers": headers})
            return DummyResponse(200)

    monkeypatch.setattr("mockjira.store.httpx.AsyncClient", DummyClient)
    monkeypatch.setenv("JIRA_BASE_URL", live_server)
    monkeypatch.setenv("JIRA_TOKEN", "mock-token")
    monkeypatch.setenv("MOCKJIRA_LEDGER_PATH", str(tmp_path / "ledger.csv"))
    monkeypatch.setenv("MOCKJIRA_WEBHOOK_URL", "http://listener")

    result = orchestrator_demo.main()

    asyncio.run(wait_for_deliveries())

    ledger_path = Path(result["ledger"])
    assert ledger_path.exists()
    content = ledger_path.read_text().strip().splitlines()
    assert len(content) >= 2

    adapter = JiraAdapter(live_server, "mock-token")
    key = result["issue"]["key"]
    issue = adapter.get_issue(key)
    assert issue["fields"]["comment"]["total"] >= 1

    assert calls, "expected webhook delivery attempts"
