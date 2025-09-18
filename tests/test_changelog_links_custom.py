import asyncio
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


async def _create_issue(client: AsyncClient, summary: str, **fields: Any) -> dict:
    payload_fields = {
        "project": {"key": "DEV"},
        "summary": summary,
        "issuetype": {"id": "10001"},
    }
    payload_fields.update(fields)
    resp = await client.post(
        "/rest/api/3/issue",
        json={"fields": payload_fields},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    return resp.json()


async def _apply_transition(client: AsyncClient, key: str, name: str) -> None:
    transitions = await client.get(
        f"/rest/api/3/issue/{key}/transitions",
        headers=AUTH_HEADERS,
    )
    transitions.raise_for_status()
    data = transitions.json()["transitions"]
    target = next(item for item in data if item["to"]["name"] == name)
    resp = await client.post(
        f"/rest/api/3/issue/{key}/transitions",
        json={"transition": {"id": target["id"]}},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_create_issue_with_text_custom_field(client):
    issue = await _create_issue(
        client,
        "Custom field issue",
        customfield_12345="High priority",
    )
    assert issue["fields"]["customfield_12345"] == "High priority"

    fetched = await client.get(
        f"/rest/api/3/issue/{issue['key']}",
        headers=AUTH_HEADERS,
    )
    fetched.raise_for_status()
    assert fetched.json()["fields"]["customfield_12345"] == "High priority"


@pytest.mark.asyncio
async def test_issue_link_blocks_roundtrip(client):
    blocker = await _create_issue(client, "Blocks target")
    target = await _create_issue(client, "Is blocked")

    resp = await client.post(
        "/rest/api/3/issueLink",
        json={
            "type": {"name": "blocks"},
            "outwardIssue": {"key": blocker["key"]},
            "inwardIssue": {"key": target["key"]},
        },
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()

    blocker_data = await client.get(
        f"/rest/api/3/issue/{blocker['key']}",
        headers=AUTH_HEADERS,
    )
    blocker_links = blocker_data.json()["fields"]["issuelinks"]
    assert any(link.get("outwardIssue", {}).get("key") == target["key"] for link in blocker_links)

    target_data = await client.get(
        f"/rest/api/3/issue/{target['key']}",
        headers=AUTH_HEADERS,
    )
    target_links = target_data.json()["fields"]["issuelinks"]
    assert any(link.get("inwardIssue", {}).get("key") == blocker["key"] for link in target_links)


@pytest.mark.asyncio
async def test_transition_adds_changelog_item(client):
    issue = await _create_issue(client, "Changelog single")
    await _apply_transition(client, issue["key"], "In Progress")

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV", "expand": "changelog"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    payload = next(item for item in resp.json()["issues"] if item["key"] == issue["key"])
    histories = payload["changelog"]["histories"]
    assert len(histories) >= 1
    first = histories[-1]["items"][0]
    assert first["fromString"] == "To Do"
    assert first["toString"] == "In Progress"


@pytest.mark.asyncio
async def test_expand_changelog_values_present_and_ordered(client):
    issue = await _create_issue(client, "Changelog ordered")
    await _apply_transition(client, issue["key"], "In Progress")
    await _apply_transition(client, issue["key"], "Done")

    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "project = DEV", "expand": "changelog"},
        headers=AUTH_HEADERS,
    )
    resp.raise_for_status()
    payload = next(item for item in resp.json()["issues"] if item["key"] == issue["key"])
    changelog = payload["changelog"]
    histories = changelog["histories"]
    assert changelog["total"] == len(histories) == 2
    first, second = histories
    assert first["created"] <= second["created"]
    assert first["items"][0]["toString"] == "In Progress"
    assert second["items"][0]["toString"] == "Done"
    assert changelog["values"] == histories
