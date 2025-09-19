#!/usr/bin/env python3
"""Generate deterministic seed data for the mock Jira server."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mockjira.fixtures.generator import GenConfig, generate_seed_json
from orchestrator import credit
from orchestrator.metrics import estimate_savings


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


def _parse_timestamp(value: object, fallback: datetime) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return fallback
    return fallback


def _generate_credit_history(
    payload: dict[str, object], ledger_path: Path, seed: int
) -> int:
    issues = payload.get("issues") or []
    if not isinstance(issues, list) or not issues:
        credit.reset_ledger(ledger_path, truncate=True)
        return 0
    credit.reset_ledger(ledger_path, truncate=True)
    rng = random.Random(seed)
    now = datetime.now(UTC)
    users = [
        str(user.get("account_id"))
        for user in payload.get("users", [])
        if isinstance(user, dict) and user.get("account_id")
    ]
    if not users:
        users = ["alice", "bob", "carol", "dave"]
    candidates = [
        issue
        for issue in issues
        if isinstance(issue, dict) and issue.get("key")
    ]
    if not candidates:
        return 0
    sample_size = min(len(candidates), 150)
    selected = rng.sample(candidates, sample_size)
    events_created = 0
    for issue in selected:
        issue_key = str(issue.get("key"))
        base_time = _parse_timestamp(issue.get("updated") or issue.get("created"), now)
        event_time = base_time + timedelta(hours=rng.randint(-8, 0))
        assignee = str(issue.get("assignee_id") or issue.get("assigneeId") or rng.choice(users))
        reporter = str(issue.get("reporter_id") or issue.get("reporterId") or rng.choice(users))
        seconds = max(estimate_savings("comment") + rng.randint(-30, 60), 45)
        quality = round(rng.uniform(0.7, 0.95), 2)
        credit.append_event(
            {
                "ts": event_time,
                "issueKey": issue_key,
                "actor": {"type": "human", "id": assignee},
                "action": "seed.apply.comment",
                "inputs": {"proposalId": "seed-comment", "kind": "comment"},
                "impact": {"secondsSaved": seconds, "quality": quality},
                "attribution": {
                    "split": [
                        {"id": f"human.{assignee}", "weight": 0.6},
                        {"id": f"human.{reporter}", "weight": 0.2},
                        {"id": "ai.summarizer", "weight": 0.2},
                    ],
                    "reason": "Synthetic history seeding",
                },
            }
        )
        events_created += 1
        if rng.random() < 0.35:
            solver = rng.choice(users)
            handoff_seconds = max(int(seconds * rng.uniform(0.6, 0.9)), 30)
            handoff_quality = round(rng.uniform(0.65, 0.9), 2)
            credit.append_event(
                {
                    "ts": event_time + timedelta(hours=rng.randint(1, 24)),
                    "issueKey": issue_key,
                    "actor": {"type": "human", "id": solver},
                    "action": "seed.handoff.complete",
                    "inputs": {"proposalId": "seed-handoff", "kind": "handoff"},
                    "impact": {"secondsSaved": handoff_seconds, "quality": handoff_quality},
                    "attribution": {
                        "split": [
                            {"id": f"human.{solver}", "weight": 0.8},
                            {"id": f"human.{assignee}", "weight": 0.2},
                        ],
                        "reason": "Synthetic handoff completion",
                    },
                }
            )
            events_created += 1
    return events_created


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
    parser.add_argument(
        "--credit-ledger",
        dest="credit_ledger",
        default="artifacts/credit-ledger.jsonl",
        help="Path to JSONL ledger with generated credit events",
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
    credit_seed = int(cfg_overrides.get("seed", args.seed))

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
        credit_seed = cfg.seed
    else:
        payload = seed_payload

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Seed saved to {output_path}")

    ledger_path = Path(args.credit_ledger)
    try:
        events = _generate_credit_history(payload, ledger_path, credit_seed)
        print(f"Credit ledger saved to {ledger_path} ({events} events)")
    except Exception as exc:  # pragma: no cover - diagnostic output only
        print(f"Failed to generate credit ledger: {exc}", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
