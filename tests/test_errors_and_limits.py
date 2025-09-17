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
async def test_400_error_shape_on_bad_jql(client):
    resp = await client.get(
        "/rest/api/3/search",
        params={"jql": "text ~ 'foo'"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 400
    payload = resp.json()
    assert payload["errorMessages"] == ["Error in JQL"]
    assert "jql" in payload["errors"]
    assert payload["errors"]["jql"].startswith("Unsupported JQL clause")


@pytest.mark.asyncio
async def test_409_on_illegal_transition(client):
    resp = await client.post(
        "/rest/api/3/issue/DEV-1/transitions",
        json={"transition": {"id": "999"}},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 409
    payload = resp.json()
    assert payload["errorMessages"] == ["Transition not allowed"]
    assert payload["errors"]["transition.id"] == "Invalid transition"


@pytest.mark.asyncio
async def test_429_retry_after_and_headers(client):
    resp = await client.get(
        "/rest/api/3/project",
        headers={**AUTH_HEADERS, "X-Force-429": "1"},
    )
    assert resp.status_code == 429
    payload = resp.json()
    assert payload["errorMessages"] == ["Simulated rate limit"]
    assert payload["errors"] == {}
    assert resp.headers.get("Retry-After") == "1"
