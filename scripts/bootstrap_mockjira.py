#!/usr/bin/env python3
"""Bootstrap a running mock Jira instance with declarative seed data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mockjira.fixtures.generator import GenConfig

DEFAULT_TIMEOUT = 60
DEFAULT_INTERVAL = 1.0


def _auth_header(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _wait_for_health(base_url: str, timeout: int, interval: float) -> None:
    deadline = time.monotonic() + timeout
    url = f"{base_url.rstrip('/')}/_mock/health"
    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.ok:
                return
        except requests.RequestException:
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Mock Jira at {base_url} did not become healthy within {timeout}s"
            )
        time.sleep(interval)


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_generator(config: dict[str, Any]) -> dict[str, Any] | None:
    payload = config.get("generator")
    if payload is None and all(key in GenConfig.__annotations__ for key in config.keys()):
        payload = config
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError("generator configuration must be a JSON object")
    known_fields = set(GenConfig.__annotations__.keys())
    return {key: payload[key] for key in known_fields if key in payload}


def _extract_seed_data(config: dict[str, Any], root: Path) -> dict[str, Any] | None:
    if "seed_data" in config:
        seed_data = config["seed_data"]
        if not isinstance(seed_data, dict):
            raise ValueError("seed_data must be a JSON object")
        return seed_data

    seed_file = config.get("seed_file")
    if seed_file:
        seed_path = (root / seed_file).resolve() if not Path(seed_file).is_absolute() else Path(seed_file)
        with seed_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("seed file must contain a JSON object")
        return data
    return None


def _post_json(url: str, token: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    headers.update(_auth_header(token))
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed a mock Jira instance running in Docker")
    parser.add_argument(
        "--config",
        default=os.getenv("MOCK_JIRA_SEED_CONFIG", "scripts/seed_profiles/default.json"),
        help="Path to JSON config describing generator options or explicit seed data",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("JIRA_BASE_URL", "http://localhost:9000"),
        help="Base URL of the running mock Jira instance",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("JIRA_TOKEN", ""),
        help="Bearer token used for admin endpoints (optional)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Seconds to wait for the server to become available",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="Polling interval while waiting for health endpoint",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file {config_path} not found")

    config = _load_config(config_path)
    base_dir = config_path.parent

    generator_cfg = _extract_generator(config)
    seed_data = _extract_seed_data(config, base_dir)

    if generator_cfg and seed_data:
        raise ValueError("Config may define either generator options or explicit seed data, not both")
    if not generator_cfg and not seed_data:
        raise ValueError(
            "Config must include a 'generator' section or 'seed_data'/'seed_file' payload"
        )

    base_url = args.base_url.rstrip("/")

    _wait_for_health(base_url, args.timeout, args.interval)

    if generator_cfg:
        result = _post_json(f"{base_url}/_mock/seed/generate", args.token, generator_cfg)
        mode = "generator"
    else:
        result = _post_json(f"{base_url}/_mock/seed/load", args.token, seed_data)  # type: ignore[arg-type]
        mode = "seed"

    counts = result.get("counts", {}) if isinstance(result, dict) else {}
    print(
        "Seed bootstrap complete",
        json.dumps({"mode": mode, "counts": counts}, ensure_ascii=False),
    )


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
