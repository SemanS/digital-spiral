from __future__ import annotations

from clients.python.jira_adapter import JiraAdapter


def _adf(text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ],
    }


def test_issue_flow_against_mock(live_server: str) -> None:
    adapter = JiraAdapter(live_server, "mock-token")
    created = adapter.create_issue(
        "DEV",
        "10001",
        "Contract test",
        description_adf=_adf("Contract test description"),
    )
    key = created["key"]

    issue = adapter.get_issue(key)
    assert issue["key"] == key

    transitions = adapter.list_transitions(key)
    assert transitions, "expected at least one transition"

    adapter.transition_issue(key, transitions[0]["id"])

    search = adapter.search(f'key = "{key}" ORDER BY updated DESC')
    assert any(item["key"] == key for item in search.get("issues", []))
