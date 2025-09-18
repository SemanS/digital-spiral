import asyncio
import base64
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from mockjira.app import create_app
from mockjira.store import InMemoryStore
from tests.utils.webhook_sig import compute_sig_v2, get_sig_from_headers

AUTH_HEADERS = {"Authorization": "Bearer mock-token"}


class DummyResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class WebhookReceiver:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self._responses: list[int] = []

    def queue(self, status_code: int) -> None:
        self._responses.append(status_code)

    async def handle(self, url: str, content: bytes, headers: dict[str, Any]) -> DummyResponse:
        status = self._responses.pop(0) if self._responses else 200
        record = {"url": url, "content": content, "headers": headers.copy()}
        self.calls.append(record)
        return DummyResponse(status)


@pytest.fixture()
def app():
    store = InMemoryStore.with_seed_data()
    return create_app(store)


@pytest_asyncio.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture()
def webhook_receiver(monkeypatch) -> WebhookReceiver:
    receiver = WebhookReceiver()

    class DummyAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(
            self,
            url: str,
            content: bytes | None = None,
            headers: dict[str, Any] | None = None,
        ) -> DummyResponse:
            return await receiver.handle(url, content or b"", headers or {})

    monkeypatch.setattr("mockjira.store.httpx.AsyncClient", DummyAsyncClient)
    return receiver


async def _wait_for_calls(receiver: WebhookReceiver, expected: int, timeout: float = 2.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout
    while len(receiver.calls) < expected:
        if asyncio.get_event_loop().time() > deadline:
            raise AssertionError(f"expected {expected} webhook calls, got {len(receiver.calls)}")
        await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_webhook_signature_v2_ok_and_tamper_fails(client, app, webhook_receiver):
    await client.post(
        "/rest/api/3/_mock/webhooks/settings",
        json={"jitter_ms": [0, 0], "poison_prob": 0},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://receiver",
                    "events": ["jira:issue_created"],
                    "secret": "supersecret",
                }
            ]
        },
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Signed"}},
        headers=AUTH_HEADERS,
    )

    await _wait_for_calls(webhook_receiver, 1)
    call = webhook_receiver.calls[0]
    alg, digest = get_sig_from_headers(call["headers"])
    assert alg == "sha256"
    assert digest == compute_sig_v2("supersecret", call["content"])
    assert digest != compute_sig_v2("supersecret", call["content"] + b"tamper")

    deliveries = await client.get(
        "/rest/api/3/_mock/webhooks/deliveries",
        headers=AUTH_HEADERS,
    )
    delivered = next(item for item in deliveries.json()["values"] if item.get("status") == "delivered")
    assert base64.b64decode(delivered["wireBody"]) == call["content"]


@pytest.mark.asyncio
async def test_webhook_retry_on_5xx_then_success(client, webhook_receiver):
    await client.post(
        "/rest/api/3/_mock/webhooks/settings",
        json={"jitter_ms": [0, 0], "poison_prob": 0},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://receiver",
                    "events": ["jira:issue_created"],
                    "secret": "retry",
                }
            ]
        },
        headers=AUTH_HEADERS,
    )

    webhook_receiver.queue(500)
    webhook_receiver.queue(200)

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Retry"}},
        headers=AUTH_HEADERS,
    )

    await _wait_for_calls(webhook_receiver, 2)
    first, second = webhook_receiver.calls
    assert first["headers"]["X-MockJira-Event-Id"] == second["headers"]["X-MockJira-Event-Id"]
    assert first["headers"]["X-MockJira-Signature"] == second["headers"]["X-MockJira-Signature"]

    deliveries = await client.get(
        "/rest/api/3/_mock/webhooks/deliveries",
        headers=AUTH_HEADERS,
    )
    record = next(item for item in deliveries.json()["values"] if item.get("status") == "delivered")
    assert record["attempts"] == 2


@pytest.mark.asyncio
async def test_webhook_dedupe_ignores_duplicate_event_id(client, app, webhook_receiver):
    await client.post(
        "/rest/api/3/_mock/webhooks/settings",
        json={"jitter_ms": [0, 0], "poison_prob": 0},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://receiver",
                    "events": ["jira:issue_created"],
                }
            ]
        },
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Dup"}},
        headers=AUTH_HEADERS,
    )
    await _wait_for_calls(webhook_receiver, 1)

    deliveries = await client.get(
        "/rest/api/3/_mock/webhooks/deliveries",
        headers=AUTH_HEADERS,
    )
    values = deliveries.json()["values"]
    original = next(item for item in values if item.get("status") == "delivered")

    store = app.state.store
    meta = store._delivery_index[original["id"]]
    duplicate_record = {
        "id": "duplicate-test",
        "webhookId": original["webhookId"],
        "event": original["event"],
        "eventId": original["eventId"],
        "url": original["url"],
        "payload": original["payload"],
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "pending",
        "attempts": 0,
    }
    store.deliveries.append(duplicate_record)
    store._schedule_delivery(
        delivery_id="duplicate-test",
        event_type=meta["event"],
        event_id=meta["event_id"],
        url=meta["url"],
        secret=meta["secret"],
        payload=meta["payload"],
        record=duplicate_record,
        force=False,
    )

    assert duplicate_record["status"] == "duplicate"
    assert len(webhook_receiver.calls) == 1


@pytest.mark.asyncio
async def test_webhook_replay_resends_identical_wire_body(client, webhook_receiver):
    await client.post(
        "/rest/api/3/_mock/webhooks/settings",
        json={"jitter_ms": [0, 0], "poison_prob": 0},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://receiver",
                    "events": ["jira:issue_created"],
                    "secret": "replay",
                }
            ]
        },
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Replay"}},
        headers=AUTH_HEADERS,
    )
    await _wait_for_calls(webhook_receiver, 1)

    deliveries = await client.get(
        "/rest/api/3/_mock/webhooks/deliveries",
        headers=AUTH_HEADERS,
    )
    record = next(item for item in deliveries.json()["values"] if item.get("status") == "delivered")

    await client.post(
        "/rest/api/3/_mock/webhooks/replay",
        params={"id": record["id"]},
        headers=AUTH_HEADERS,
    )
    await _wait_for_calls(webhook_receiver, 2)

    first, second = webhook_receiver.calls
    assert first["content"] == second["content"]
    assert first["headers"] == second["headers"]


@pytest.mark.asyncio
async def test_structured_json_logs_include_req_id_event_id(client, webhook_receiver):
    await client.post(
        "/rest/api/3/_mock/webhooks/settings",
        json={"jitter_ms": [0, 0], "poison_prob": 0},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/rest/api/3/webhook",
        json={
            "webhooks": [
                {
                    "url": "http://receiver",
                    "events": ["jira:issue_created"],
                }
            ]
        },
        headers=AUTH_HEADERS,
    )

    await client.post(
        "/rest/api/3/issue",
        json={"fields": {"project": {"key": "DEV"}, "summary": "Logs"}},
        headers=AUTH_HEADERS,
    )
    await _wait_for_calls(webhook_receiver, 1)

    logs_resp = await client.get(
        "/rest/api/3/_mock/webhooks/logs",
        headers=AUTH_HEADERS,
    )
    logs = logs_resp.json()["values"]
    assert logs
    last = logs[-1]
    assert last["requestId"]
    assert last["eventId"]
    assert last["status"] in {"delivered", "failed", "retrying"}
    assert isinstance(last["attempt"], int)
