import asyncio

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport, AsyncClient
from typing import Any

from mockjira.app import create_app
from mockjira.store import InMemoryStore
from tests.utils.webhook_sig import compute_sig_v2, get_sig_from_headers

AUTH_HEADERS = {"Authorization": "Bearer mock-token"}


@pytest.fixture()
def app():
    store = InMemoryStore.with_seed_data()
    return create_app(store)


@pytest_asyncio.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_projects_and_fields(client):
    resp = await client.get("/rest/api/3/project", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    projects = resp.json()["values"]
    assert any(project["key"] == "DEV" for project in projects)

    resp = await client.get("/rest/api/3/field", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    fields = resp.json()["values"]
    assert any(field["id"] == "summary" for field in fields)


@pytest.mark.asyncio
async def test_issue_lifecycle_and_webhook_delivery(client):
    issue_payload = {
        "fields": {
            "project": {"key": "DEV"},
            "summary": "Automated test issue",
            "description": "Created from tests",
            "issuetype": {"id": "10001"},
        }
    }
    create_resp = await client.post(
        "/rest/api/3/issue", json=issue_payload, headers=AUTH_HEADERS
    )
    assert create_resp.status_code == 201
    issue = create_resp.json()

    get_resp = await client.get(
        f"/rest/api/3/issue/{issue['key']}", headers=AUTH_HEADERS
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["fields"]["summary"] == "Automated test issue"

    search_resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV AND status = \"To Do\""},
        headers=AUTH_HEADERS,
    )
    assert search_resp.status_code == 200
    issues = [i["key"] for i in search_resp.json()["issues"]]
    assert issue["key"] in issues

    transitions_resp = await client.get(
        f"/rest/api/3/issue/{issue['key']}/transitions", headers=AUTH_HEADERS
    )
    transition_id = transitions_resp.json()["transitions"][0]["id"]
    apply_resp = await client.post(
        f"/rest/api/3/issue/{issue['key']}/transitions",
        json={"transition": {"id": transition_id}},
        headers=AUTH_HEADERS,
    )
    assert apply_resp.status_code == 200

    comment_resp = await client.post(
        f"/rest/api/3/issue/{issue['key']}/comment",
        json={"body": "Looks good"},
        headers=AUTH_HEADERS,
    )
    assert comment_resp.status_code == 201
    comments = await client.get(
        f"/rest/api/3/issue/{issue['key']}/comment", headers=AUTH_HEADERS
    )
    assert comments.status_code == 200
    assert comments.json()["total"] == 1

    deliveries_resp = await client.get(
        "/rest/api/3/_mock/webhooks/deliveries", headers=AUTH_HEADERS
    )
    deliveries = deliveries_resp.json()["values"]
    assert any(delivery["event"] == "jira:issue_created" for delivery in deliveries)


@pytest.mark.asyncio
async def test_agile_endpoints(client):
    board_resp = await client.get("/rest/agile/1.0/board", headers=AUTH_HEADERS)
    assert board_resp.status_code == 200
    boards = board_resp.json()["values"]
    assert boards

    backlog_resp = await client.get(
        "/rest/agile/1.0/board/1/backlog", headers=AUTH_HEADERS
    )
    assert backlog_resp.status_code == 200
    assert "issues" in backlog_resp.json()

    sprint_resp = await client.post(
        "/rest/agile/1.0/sprint",
        json={"originBoardId": 1, "name": "QA Sprint"},
        headers=AUTH_HEADERS,
    )
    assert sprint_resp.status_code == 201
    assert sprint_resp.json()["name"] == "QA Sprint"


@pytest.mark.asyncio
async def test_service_management_flow(client):
    create_resp = await client.post(
        "/rest/servicedeskapi/request",
        json={
            "serviceDeskId": "1",
            "requestTypeId": "100",
            "requestFieldValues": {
                "summary": "Need laptop",
                "description": "New starter hardware request",
            },
        },
        headers=AUTH_HEADERS,
    )
    assert create_resp.status_code == 201
    request_payload = create_resp.json()

    approval_resp = await client.post(
        f"/rest/servicedeskapi/request/{request_payload['id']}/approval/42",
        json={"decision": "approve"},
        headers=AUTH_HEADERS,
    )
    assert approval_resp.status_code == 200
    assert approval_resp.json()["approvals"]


@pytest.mark.asyncio
async def test_webhook_registration(client):
    register_resp = await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://localhost/dummy",
                    "events": ["jira:issue_created"],
                }
            ]
        },
        headers=AUTH_HEADERS,
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["webhookRegistrationResult"]


@pytest.mark.asyncio
async def test_rate_limit_simulation(client):
    resp = await client.get(
        "/rest/api/3/project",
        headers={**AUTH_HEADERS, "X-Force-429": "true"},
    )
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") == "1"


@pytest.mark.asyncio
async def test_post_search_equivalent_to_get(client):
    get_resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV"},
        headers=AUTH_HEADERS,
    )
    post_resp = await client.post(
        "/rest/api/3/search",
        json={"jql": "project = DEV"},
        headers=AUTH_HEADERS,
    )
    assert get_resp.status_code == post_resp.status_code == 200
    assert get_resp.json()["issues"] == post_resp.json()["issues"]


@pytest.mark.asyncio
async def test_order_by_desc(client):
    resp = await client.post(
        "/rest/api/3/search",
        json={"jql": "project = DEV ORDER BY updated DESC"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    issues = resp.json()["issues"]
    updates = [issue["fields"]["updated"] for issue in issues]
    assert updates == sorted(updates, reverse=True)


@pytest.mark.asyncio
async def test_current_user_function(client):
    resp = await client.post(
        "/rest/api/3/search",
        json={"jql": "assignee = currentUser()"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    issues = resp.json()["issues"]
    assert issues
    for issue in issues:
        assignee = issue["fields"]["assignee"]
        assert assignee is not None
        assert assignee["accountId"] == "5b10a2844c20165700ede21g"


@pytest.mark.asyncio
async def test_webhook_hmac_valid_and_retry_on_500(client, monkeypatch):
    calls: list[dict[str, Any]] = []

    class DummyResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code

    class DummyClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - cleanup
            return None

        async def post(self, url: str, content: bytes | None = None, headers: dict | None = None):
            record = {"url": url, "content": content, "headers": headers}
            calls.append(record)
            if len(calls) == 1:
                raise httpx.HTTPError("Injected failure")
            return DummyResponse(200)

    monkeypatch.setattr("mockjira.store.httpx.AsyncClient", DummyClient)

    await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://listener",
                    "events": ["jira:issue_created"],
                    "secret": "shh",
                }
            ]
        },
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Webhook"}},
        headers=AUTH_HEADERS,
    )

    await asyncio.sleep(1.0)
    assert len(calls) == 2
    alg, digest = get_sig_from_headers(calls[1]["headers"])
    assert alg == "sha256"
    expected = compute_sig_v2("shh", calls[1]["content"])
    assert digest == expected


@pytest.mark.asyncio
async def test_webhook_replay_resends_same_payload(client, monkeypatch):
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

    await client.post(
        "/rest/api/3/webhook",
        json={"webhooks": [{"url": "http://listener", "events": ["jira:issue_created"]}]},
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Webhook replay"}},
        headers=AUTH_HEADERS,
    )

    await asyncio.sleep(1.0)
    assert len(calls) == 1

    deliveries = await client.get(
        "/rest/api/3/_mock/webhooks/deliveries",
        headers=AUTH_HEADERS,
    )
    values = deliveries.json()["values"]
    delivery_id = next(item["id"] for item in values if "id" in item)

    await client.post(
        "/rest/api/3/_mock/webhooks/replay",
        params={"id": delivery_id},
        headers=AUTH_HEADERS,
    )

    await asyncio.sleep(1.0)
    assert len(calls) == 2
    assert calls[0]["content"] == calls[1]["content"]


@pytest.mark.asyncio
async def test_webhook_jitter_bounds_and_idempotency(client, monkeypatch):
    jitter_calls: list[tuple[float, float]] = []

    def fake_uniform(a: float, b: float) -> float:
        jitter_calls.append((a, b))
        return a

    monkeypatch.setattr("mockjira.store.random.uniform", fake_uniform)

    await client.post(
        "/rest/api/3/webhook",
        json={"webhooks": [{"url": "http://listener", "events": ["jira:issue_created"]}]},
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Webhook jitter"}},
        headers=AUTH_HEADERS,
    )

    await asyncio.sleep(0.3)
    assert jitter_calls
    for low, high in jitter_calls:
        assert low == 50
        assert high == 250


@pytest.mark.asyncio
async def test_issue_link_blocks_roundtrip(client):
    link_payload = {
        "type": {"name": "Blocks"},
        "outwardIssue": {"key": "DEV-1"},
        "inwardIssue": {"key": "DEV-2"},
    }
    resp = await client.post(
        "/rest/api/3/issueLink",
        json=link_payload,
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    issue = await client.get("/rest/api/3/issue/DEV-1", headers=AUTH_HEADERS)
    links = issue.json()["fields"].get("issuelinks", [])
    assert any(link.get("outwardIssue", {}).get("key") == "DEV-2" for link in links)


@pytest.mark.asyncio
async def test_customfield_text_saved_and_returned(client):
    create_resp = await client.post(
        "/rest/api/3/issue",
        json={
            "fields": {
                "project": {"key": "DEV"},
                "summary": "Custom field",
                "issuetype": {"id": "10001"},
                "customfield_12345": "Hello",
            }
        },
        headers=AUTH_HEADERS,
    )
    assert create_resp.status_code == 201
    key = create_resp.json()["key"]
    issue_resp = await client.get(f"/rest/api/3/issue/{key}", headers=AUTH_HEADERS)
    assert issue_resp.json()["fields"]["customfield_12345"] == "Hello"


@pytest.mark.asyncio
async def test_transition_appends_changelog_and_expand(client):
    create_resp = await client.post(
        "/rest/api/3/issue",
        json={
            "fields": {
                "project": {"key": "DEV"},
                "summary": "Changelog transition",
                "issuetype": {"id": "10001"},
            }
        },
        headers=AUTH_HEADERS,
    )
    key = create_resp.json()["key"]

    transitions_resp = await client.get(
        f"/rest/api/3/issue/{key}/transitions",
        headers=AUTH_HEADERS,
    )
    transition_id = transitions_resp.json()["transitions"][0]["id"]

    transition_resp = await client.post(
        f"/rest/api/3/issue/{key}/transitions",
        json={"transition": {"id": transition_id}},
        headers=AUTH_HEADERS,
    )
    assert transition_resp.status_code == 200

    issue_resp = await client.get(
        f"/rest/api/3/issue/{key}",
        params={"expand": "changelog"},
        headers=AUTH_HEADERS,
    )
    changelog = issue_resp.json().get("changelog", {})
    assert changelog.get("total", 0) >= 1
    last_history = changelog["histories"][-1]
    assert last_history["items"][0]["field"] == "status"


@pytest.mark.asyncio
async def test_health_info_and_trace(client):
    health = await client.get("/_mock/health")
    assert health.status_code == 200
    req_id = health.headers.get("x-req-id")
    assert health.json()["status"] == "ok"

    info = await client.get("/_mock/info")
    payload = info.json()
    assert "version" in payload
    assert payload["seed"]["issues"] >= 1

    trace = await client.get(f"/_mock/trace/{req_id}")
    assert trace.status_code == 200
    entries = trace.json()["entries"]
    assert entries and entries[0]["id"] == req_id
