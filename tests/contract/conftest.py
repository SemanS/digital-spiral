from __future__ import annotations

import json
import os
import pathlib
from typing import Callable, Dict, List

import pytest


class ParityRecorder:
    def __init__(self) -> None:
        self.records: List[Dict[str, object]] = []

    def record(
        self,
        *,
        api: str,
        method: str,
        path: str,
        status: int,
        detail: List[str] | None = None,
    ) -> None:
        self.records.append(
            {
                "api": api,
                "method": method,
                "path": path,
                "status": status,
                "detail": detail or [],
            }
        )


def pytest_configure(config: pytest.Config) -> None:
    config._parity_recorder = ParityRecorder()  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("MOCK_JIRA_BASE_URL", "http://localhost:9000")


@pytest.fixture(scope="session")
def auth_header() -> Dict[str, str]:
    return {"Authorization": "Bearer mock-token"}


@pytest.fixture
def parity_recorder(request: pytest.FixtureRequest) -> Callable[..., None]:
    recorder: ParityRecorder = request.config._parity_recorder  # type: ignore[attr-defined]

    def _record(**kwargs) -> None:
        recorder.record(**kwargs)

    return _record


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    recorder: ParityRecorder = session.config._parity_recorder  # type: ignore[attr-defined]
    path = pathlib.Path("artifacts")
    path.mkdir(exist_ok=True)

    payload = {
        "responses": recorder.records,
        "total_responses": len(recorder.records),
    }

    (path / "parity.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Parity Report",
        f"- Total: {payload['total_responses']}",
        f"- With schema issues: {sum(1 for item in recorder.records if item['detail'])}",
        "",
    ]
    for record in recorder.records[:200]:
        lines.append(
            f"* `{record['api']}` {record['method']} {record['path']} → {record['status']}"
        )
        for detail in record["detail"]:
            lines.append(f"  - {detail}")
    (path / "parity.md").write_text("\n".join(lines), encoding="utf-8")
