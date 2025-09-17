from __future__ import annotations

import threading
import time

import pytest
import requests
import uvicorn

from mockjira.app import create_app
from mockjira.store import InMemoryStore


@pytest.fixture()
def live_server() -> str:
    """Run the mock Jira server in the background for integration tests."""

    store = InMemoryStore.with_seed_data()
    app = create_app(store)
    config = uvicorn.Config(app, host="127.0.0.1", port=9000, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    url = "http://127.0.0.1:9000/_mock/health"
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=0.25)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:  # pragma: no cover - guard for flaky environments
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("Mock Jira server failed to start")

    yield "http://127.0.0.1:9000"

    server.should_exit = True
    thread.join(timeout=5)
