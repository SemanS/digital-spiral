import asyncio
from datetime import UTC, datetime
from typing import Any

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


async def _create_issue(client: AsyncClient, summary: str, assignee: str | None = None) -> dict:
    fields: dict[str, Any] = {
        "project": {"key": "DEV"},
        "summary": summary,
        "issuetype": {"id": "10001"},
    }
    if assignee:
        fields["assignee"] = {"accountId": assignee}
    resp = await client.post(
        "/rest/api/3/issue",
        json={"fields": fields},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    return resp.json()


async def _wait_tick():
    await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_post_search_equivalent_to_get(client):
    await _create_issue(client, "JQL equality test")
    jql = "project = DEV"

    get_resp = await client.get(
        "/rest/api/3/search",
        params={"jql": jql},
        headers=AUTH_HEADERS,
    )
    get_resp.raise_for_status()
    post_resp = await client.post(
        "/rest/api/3/search",
        json={"jql": jql},
        headers=AUTH_HEADERS,
    )
    post_resp.raise_for_status()

    get_keys = [issue["key"] for issue in get_resp.json()["issues"]]
    post_keys = [issue["key"] for issue in post_resp.json()["issues"]]
    assert get_keys == post_keys


@pytest.mark.asyncio
async def test_order_by_updated_desc_default(client):
    first = await _create_issue(client, "Order default first")
    await _wait_tick()
    second = await _create_issue(client, "Order default second")

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    issues = resp.json()["issues"]
    positions = {issue["key"]: idx for idx, issue in enumerate(issues)}
    assert positions[second["key"]] < positions[first["key"]]


@pytest.mark.asyncio
async def test_order_by_updated_asc(client):
    first = await _create_issue(client, "Order asc first")
    await _wait_tick()
    second = await _create_issue(client, "Order asc second")

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV ORDER BY updated ASC"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    issues = resp.json()["issues"]
    positions = {issue["key"]: idx for idx, issue in enumerate(issues)}
    assert positions[first["key"]] < positions[second["key"]]


@pytest.mark.asyncio
async def test_filter_updated_gte(client):
    first = await _create_issue(client, "Updated filter first")
    issue1 = await client.get(
        f"/rest/api/3/issue/{first['key']}",
        headers=AUTH_HEADERS,
    )
    issue1.raise_for_status()
    threshold = issue1.json()["fields"]["updated"]
    await _wait_tick()
    second = await _create_issue(client, "Updated filter second")

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": f"project = DEV AND updated >= '{threshold}'"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    keys = {issue["key"] for issue in resp.json()["issues"]}
    assert second["key"] in keys
    assert first["key"] not in keys


@pytest.mark.asyncio
async def test_filter_created_gte(client):
    first = await _create_issue(client, "Created filter first")
    await _wait_tick()
    second = await _create_issue(client, "Created filter second")
    issue2 = await client.get(
        f"/rest/api/3/issue/{second['key']}",
        headers=AUTH_HEADERS,
    )
    issue2.raise_for_status()
    threshold = issue2.json()["fields"]["created"]

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": f"project = DEV AND created >= '{threshold}'"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    keys = {issue["key"] for issue in resp.json()["issues"]}
    assert second["key"] in keys
    assert first["key"] not in keys


@pytest.mark.asyncio
async def test_current_user_in_assignee_and_reporter(client):
    myself = await client.get("/rest/api/3/myself", headers=AUTH_HEADERS)
    myself.raise_for_status()
    account_id = myself.json()["accountId"]

    created = await _create_issue(
        client,
        "Current user filters",
        assignee=account_id,
    )

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV AND reporter = currentUser()"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    keys = {issue["key"] for issue in resp.json()["issues"]}
    assert created["key"] in keys

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV AND assignee = currentUser()"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    keys = {issue["key"] for issue in resp.json()["issues"]}
    assert created["key"] in keys


@pytest.mark.asyncio
async def test_fields_and_expand_subset(client):
    issue = await _create_issue(client, "Fields expand test")
    await client.post(
        f"/rest/api/3/issue/{issue['key']}/comment",
        json={"body": "note"},
        headers=AUTH_HEADERS,
    )

    resp = await client.get(
        "/rest/api/3/search",
        params={
            "jql": "project = DEV",
            "fields": "summary,status",
            "expand": "changelog",
        },
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    issues = resp.json()["issues"]
    payload = next(item for item in issues if item["key"] == issue["key"])
    assert set(payload["fields"].keys()) == {"summary", "status"}
    assert "changelog" in payload
    assert set(payload["changelog"].keys()) >= {"startAt", "histories"}
