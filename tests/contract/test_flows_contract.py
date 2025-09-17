from __future__ import annotations

import pytest
import requests

pytest.importorskip("openapi_core")

from .openapi_validator import load_openapi, validate_response

PLATFORM = load_openapi("schemas/jira-platform.v3.json")
SOFTWARE = load_openapi("schemas/jira-software.v3.json")
JSM = load_openapi("schemas/jsm.v3.json")


def _json(response: requests.Response):
    content_type = response.headers.get("content-type", "").lower()
    if content_type.startswith("application/json"):
        return response.json()
    return {}


def _record(parity_recorder, api: str, path: str, response, errors) -> None:
    request_method = getattr(getattr(response, "request", None), "method", "")
    if request_method:
        request_method = request_method.upper()
    parity_recorder(
        api=api,
        method=request_method or "",
        path=path,
        status=response.status_code,
        detail=[str(err) for err in errors],
    )


def test_issue_crud_workflow(base_url, auth_header, parity_recorder):
    with requests.Session() as session:
        session.headers.update(auth_header)

        payload = {
            "fields": {
                "summary": "Contract test issue",
                "issuetype": {"id": "10001"},
                "project": {"key": "DEV"},
                "description": {"type": "doc", "version": 1, "content": []},
            }
        }
        create = session.post(f"{base_url}/rest/api/3/issue", json=payload)
        create_data = _json(create)
        create_errors = validate_response(PLATFORM, create, "/rest/api/3/issue")
        _record(parity_recorder, "platform", "/rest/api/3/issue", create, create_errors)
        assert not create_errors, f"create issue schema errors: {create_errors}"

        issue_key = create_data["key"]

        get_issue = session.get(f"{base_url}/rest/api/3/issue/{issue_key}")
        issue_data = _json(get_issue)
        issue_errors = validate_response(
            PLATFORM, get_issue, "/rest/api/3/issue/{issueIdOrKey}"
        )
        _record(parity_recorder, "platform", "/rest/api/3/issue/{issueIdOrKey}", get_issue, issue_errors)
        assert not issue_errors, f"get issue schema errors: {issue_errors}"

        transitions = session.get(f"{base_url}/rest/api/3/issue/{issue_key}/transitions")
        transitions_data = _json(transitions)
        transitions_errors = validate_response(
            PLATFORM,
            transitions,
            "/rest/api/3/issue/{issueIdOrKey}/transitions",
        )
        _record(
            parity_recorder,
            "platform",
            "/rest/api/3/issue/{issueIdOrKey}/transitions",
            transitions,
            transitions_errors,
        )
        assert not transitions_errors, f"list transitions errors: {transitions_errors}"

        transition_id = transitions_data["transitions"][0]["id"]
        do_transition = session.post(
            f"{base_url}/rest/api/3/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        do_transition_errors = validate_response(
            PLATFORM,
            do_transition,
            "/rest/api/3/issue/{issueIdOrKey}/transitions",
        )
        _record(
            parity_recorder,
            "platform",
            "/rest/api/3/issue/{issueIdOrKey}/transitions",
            do_transition,
            do_transition_errors,
        )
        assert not do_transition_errors, f"do transition schema errors: {do_transition_errors}"

        search = session.post(
            f"{base_url}/rest/api/3/search", json={"jql": f'key = "{issue_key}"'}
        )
        search_data = _json(search)
        search_errors = validate_response(PLATFORM, search, "/rest/api/3/search")
        _record(parity_recorder, "platform", "/rest/api/3/search", search, search_errors)
        assert not search_errors, f"search schema errors: {search_errors}"


def test_jsm_request_flow(base_url, auth_header, parity_recorder):
    with requests.Session() as session:
        session.headers.update(auth_header)

        create = session.post(
            f"{base_url}/rest/servicedeskapi/request",
            json={
                "serviceDeskId": "1",
                "requestTypeId": "1",
                "requestFieldValues": [
                    {"fieldId": "summary", "value": "Contract test request"}
                ],
            },
        )
        create_data = _json(create)
        create_errors = validate_response(JSM, create, "/rest/servicedeskapi/request")
        _record(parity_recorder, "jsm", "/rest/servicedeskapi/request", create, create_errors)
        assert not create_errors, f"jsm create request errors: {create_errors}"

        request_id = create_data["issueId"]
        get_request = session.get(
            f"{base_url}/rest/servicedeskapi/request/{request_id}"
        )
        request_data = _json(get_request)
        request_errors = validate_response(
            JSM, get_request, "/rest/servicedeskapi/request/{issueIdOrKey}"
        )
        _record(
            parity_recorder,
            "jsm",
            "/rest/servicedeskapi/request/{issueIdOrKey}",
            get_request,
            request_errors,
        )
        assert not request_errors, f"jsm get request errors: {request_errors}"


def test_agile_board_flow(base_url, auth_header, parity_recorder):
    with requests.Session() as session:
        session.headers.update(auth_header)

        boards = session.get(f"{base_url}/rest/agile/1.0/board")
        boards_data = _json(boards)
        boards_errors = validate_response(SOFTWARE, boards, "/rest/agile/1.0/board")
        _record(parity_recorder, "software", "/rest/agile/1.0/board", boards, boards_errors)
        assert not boards_errors, f"list boards schema errors: {boards_errors}"

        board_id = boards_data["values"][0]["id"]
        sprints = session.get(f"{base_url}/rest/agile/1.0/board/{board_id}/sprint")
        sprints_data = _json(sprints)
        sprints_errors = validate_response(
            SOFTWARE, sprints, "/rest/agile/1.0/board/{boardId}/sprint"
        )
        _record(
            parity_recorder,
            "software",
            "/rest/agile/1.0/board/{boardId}/sprint",
            sprints,
            sprints_errors,
        )
        assert not sprints_errors, f"list sprints schema errors: {sprints_errors}"
