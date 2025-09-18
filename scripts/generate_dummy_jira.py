#!/usr/bin/env python3
"""Generate deterministic seed data for the mock Jira server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mockjira.fixtures.generator import GenConfig, generate_seed_json


def _load_config(path: str | None) -> tuple[dict[str, object] | None, dict[str, object]]:
    """Return optional seed payload or generator kwargs from a config file."""

    if not path:
        return None, {}

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if "seed_data" in data:
        seed_data = data["seed_data"]
        if not isinstance(seed_data, dict):  # pragma: no cover - config validation
            raise ValueError("seed_data must be an object containing store state")
        return seed_data, {}

    generator_cfg = data.get("generator", data)
    if not isinstance(generator_cfg, dict):  # pragma: no cover - config validation
        raise ValueError("generator config must be a JSON object")

    known_fields = set(GenConfig.__annotations__.keys())
    cfg_kwargs: dict[str, object] = {
        key: generator_cfg[key]
        for key in known_fields
        if key in generator_cfg
    }
    return None, cfg_kwargs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate mock Jira seed data")
    parser.add_argument(
        "--out",
        default="artifacts/seed.json",
        help="Output path for the generated seed JSON",
    )
    parser.add_argument(
        "--config",
        help="Path to JSON config containing generator options or explicit seed data",
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

    seed_payload, cfg_overrides = _load_config(args.config)

    if seed_payload is None:
        cfg = GenConfig(
            seed=int(cfg_overrides.get("seed", args.seed)),
            days=int(cfg_overrides.get("days", args.days)),
            software_projects=int(
                cfg_overrides.get("software_projects", args.software_projects)
            ),
            servicedesk_projects=int(
                cfg_overrides.get("servicedesk_projects", args.servicedesk_projects)
            ),
            issues_per_project=int(
                cfg_overrides.get("issues_per_project", args.issues_per_project)
            ),
            boards_per_sw_project=int(
                cfg_overrides.get("boards_per_sw_project", GenConfig.boards_per_sw_project)
            ),
            sprints_per_board=int(
                cfg_overrides.get("sprints_per_board", GenConfig.sprints_per_board)
            ),
            sprint_length_days=int(
                cfg_overrides.get("sprint_length_days", GenConfig.sprint_length_days)
            ),
            comments_per_issue_avg=float(
                cfg_overrides.get(
                    "comments_per_issue_avg", GenConfig.comments_per_issue_avg
                )
            ),
            transition_rate=float(
                cfg_overrides.get("transition_rate", GenConfig.transition_rate)
            ),
            link_probability=float(
                cfg_overrides.get("link_probability", GenConfig.link_probability)
            ),
            assignee_churn_prob=float(
                cfg_overrides.get("assignee_churn_prob", GenConfig.assignee_churn_prob)
            ),
        )
        payload = generate_seed_json(cfg)
    else:
        payload = seed_payload

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Seed saved to {output_path}")


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
