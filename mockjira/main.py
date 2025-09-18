"""CLI entrypoint for running the mock Jira server."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from .app import create_app
from .store import InMemoryStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mock Jira Cloud server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host interface to bind the server"
    )
    parser.add_argument(
        "--port", type=int, default=9000, help="TCP port to bind the server"
    )
    parser.add_argument(
        "--log-level", default="info", help="Log level passed to Uvicorn"
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Start with an empty store instead of the default seed data",
    )
    parser.add_argument(
        "--seed-file",
        help="Path to a seed JSON file to preload",
        default=None,
    )
    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.seed_file:
        store = InMemoryStore()
    elif args.no_seed:
        store = InMemoryStore()
    else:
        store = InMemoryStore.with_seed_data()

    if args.seed_file:
        seed_path = Path(args.seed_file)
        with seed_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        store.load_from_json(payload)

    app = create_app(store)

    config = uvicorn.Config(
        app, host=args.host, port=args.port, log_level=args.log_level
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    run()
