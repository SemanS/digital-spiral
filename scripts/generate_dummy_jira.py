#!/usr/bin/env python3
"""Generate deterministic seed data for the mock Jira server."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mockjira.fixtures.generator import GenConfig, generate_seed_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate mock Jira seed data")
    parser.add_argument(
        "--out",
        default="artifacts/seed.json",
        help="Output path for the generated seed JSON",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for generation")
    parser.add_argument("--days", type=int, default=120, help="History horizon in days")
    parser.add_argument(
        "--software-projects",
        dest="software_projects",
        type=int,
        default=1,
        help="Number of software projects to generate",
    )
    parser.add_argument(
        "--servicedesk-projects",
        dest="servicedesk_projects",
        type=int,
        default=1,
        help="Number of service desk projects to generate",
    )
    parser.add_argument(
        "--issues-per-project",
        dest="issues_per_project",
        type=int,
        default=80,
        help="Average number of issues to create per project",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = GenConfig(
        seed=args.seed,
        days=args.days,
        software_projects=args.software_projects,
        servicedesk_projects=args.servicedesk_projects,
        issues_per_project=args.issues_per_project,
    )
    payload = generate_seed_json(cfg)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Seed saved to {output_path}")


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
