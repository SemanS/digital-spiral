from __future__ import annotations

from mcp_jira import tools


def test_mcp_tools_round_trip(live_server: str) -> None:
    issue = tools.t_jira_create_issue(
        {
            "project_key": "DEV",
            "issue_type_id": "10001",
            "summary": "MCP created issue",
            "description_adf": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Created via MCP"}],
                    }
                ],
            },
        }
    )
    key = issue["key"]

    transitions = tools.t_jira_list_transitions({"key": key})["transitions"]
    assert transitions

    tools.t_jira_transition_issue({"key": key, "transition_id": transitions[0]["id"]})

    comment = tools.t_jira_add_comment(
        {
            "key": key,
            "body_adf": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Handled by MCP"}],
                    }
                ],
            },
        }
    )
    assert comment["id"]

    search = tools.t_jira_search({"jql": f'key = "{key}"'})
    assert any(issue["key"] == key for issue in search.get("issues", []))

    request = tools.t_jsm_create_request(
        {
            "service_desk_id": "1",
            "request_type_id": "100",
            "summary": "Printer broken",
            "fields": {"description": "Needs maintenance"},
        }
    )
    assert request["issueId"]

    sprints = tools.t_agile_list_sprints({"board_id": 1})
    assert "values" in sprints

    registry_keys = set(tools.TOOL_REGISTRY)
    assert {
        "jira.create_issue",
        "jira.get_issue",
        "jira.search",
        "jira.list_transitions",
        "jira.transition_issue",
        "jira.add_comment",
        "jsm.create_request",
        "agile.list_sprints",
    }.issubset(registry_keys)
