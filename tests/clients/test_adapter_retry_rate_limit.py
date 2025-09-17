from __future__ import annotations

from clients.python.jira_adapter import JiraAdapter


def test_retry_on_429(live_server: str) -> None:
    adapter = JiraAdapter(live_server, "mock-token")
    adapter.session.headers["X-Force-429"] = "1"
    try:
        boards = adapter.list_boards()
        assert "values" in boards
    finally:
        adapter.session.headers.pop("X-Force-429", None)
