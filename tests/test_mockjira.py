import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from mockjira.app import create_app
from mockjira.store import InMemoryStore

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
