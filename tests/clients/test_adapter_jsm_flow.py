from __future__ import annotations

from clients.python.jira_adapter import JiraAdapter


def test_service_management_flow(live_server: str) -> None:
    adapter = JiraAdapter(live_server, "mock-token")
    created = adapter.create_request(
        service_desk_id="1",
        request_type_id="100",
        summary="Laptop request",
        fields={"description": "Need a new laptop"},
    )
    assert created["issueId"]

    fetched = adapter.get_request(created["id"])
    assert fetched["issueId"] == created["issueId"]
    assert fetched["requestFieldValues"]["summary"] == "Laptop request"
