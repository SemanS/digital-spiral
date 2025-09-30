#!/usr/bin/env python3
"""Generate deterministic seed data for the mock Jira server."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mockjira.fixtures.generator import GenConfig, generate_seed_json

DEFAULT_CFG = GenConfig()
from orchestrator import credit
from orchestrator.metrics import estimate_savings


def _adf_text(text: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


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
    if "handoff_probability" in data:
        cfg_kwargs["handoff_probability"] = data["handoff_probability"]
    if "handoff_probability" in generator_cfg:
        cfg_kwargs["handoff_probability"] = generator_cfg["handoff_probability"]

    # Check for support templates flag
    if "use_support_templates" in data:
        cfg_kwargs["use_support_templates"] = data["use_support_templates"]
    if "use_support_templates" in generator_cfg:
        cfg_kwargs["use_support_templates"] = generator_cfg["use_support_templates"]

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


def _normalise_sprint_windows(payload: dict[str, Any], rng: random.Random) -> None:
    raw_sprints = payload.get("sprints")
    if not isinstance(raw_sprints, list):
        return
    now = datetime.now(UTC)
    grouped: dict[int, list[dict[str, Any]]] = {}
    for sprint in raw_sprints:
        if not isinstance(sprint, dict):
            continue
        try:
            board_id = int(sprint.get("board_id") or sprint.get("boardId") or 0)
        except (TypeError, ValueError):
            board_id = 0
        grouped.setdefault(board_id, []).append(sprint)
    for sprints in grouped.values():
        if not sprints:
            continue
        sprints.sort(
            key=lambda item: _parse_timestamp(item.get("start_date") or item.get("startDate"), now)
            or datetime.min.replace(tzinfo=UTC)
        )
        sample_start = _parse_timestamp(sprints[0].get("start_date") or sprints[0].get("startDate"), now)
        sample_end = _parse_timestamp(sprints[0].get("end_date") or sprints[0].get("endDate"), sample_start + timedelta(days=14))
        length_days = max(int((sample_end - sample_start).days) if sample_end and sample_start else 14, 7)
        active_candidates = [item for item in sprints if str(item.get("state", "")).lower() == "active"]
        active = active_candidates[-1] if active_candidates else sprints[-1]
        active_start = now - timedelta(days=rng.randint(1, 2))
        active_end = active_start + timedelta(days=length_days)
        active["state"] = "active"
        active["start_date"] = active_start.isoformat()
        active["end_date"] = active_end.isoformat()
        for sprint in sprints:
            if sprint is active:
                continue
            start = _parse_timestamp(sprint.get("start_date") or sprint.get("startDate"), now)
            end = _parse_timestamp(sprint.get("end_date") or sprint.get("endDate"), start + timedelta(days=length_days))
            if end and end < active_start:
                sprint["state"] = "closed"
                sprint["end_date"] = end.isoformat()
                if start:
                    sprint["start_date"] = start.isoformat()
            elif start and start > active_end:
                sprint["state"] = "future"
                sprint["start_date"] = start.isoformat()
                sprint["end_date"] = (start + timedelta(days=length_days)).isoformat()


def _next_numeric_id(items: Iterable[dict[str, Any]], field: str, default: int) -> int:
    current = default
    for item in items:
        try:
            value = int(item.get(field))
        except (TypeError, ValueError):
            continue
        current = max(current, value)
    return current + 1


def _inject_handoff_threads(payload: dict[str, Any], probability: float, rng: random.Random) -> None:
    if probability <= 0.0:
        return
    issues_raw = payload.get("issues")
    if not isinstance(issues_raw, list):
        return
    issues = [issue for issue in issues_raw if isinstance(issue, dict) and issue.get("key")]
    if not issues:
        return
    users = [
        str(user.get("account_id"))
        for user in payload.get("users", [])
        if isinstance(user, dict) and user.get("account_id")
    ]
    comment_seed = _next_numeric_id(
        (comment for issue in issues for comment in issue.get("comments", []) if isinstance(comment, dict)),
        "id",
        200000,
    )
    link_seed = _next_numeric_id(
        (link for issue in issues for link in issue.get("links", []) if isinstance(link, dict)),
        "id",
        60000,
    )
    seen_pairs: set[tuple[str, str]] = set()
    for issue in issues:
        if rng.random() >= probability:
            continue
        partner_candidates = [candidate for candidate in issues if candidate is not issue]
        if not partner_candidates:
            break
        partner = rng.choice(partner_candidates)
        pair = tuple(sorted((str(issue.get("key")), str(partner.get("key")))))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        labels = [str(label) for label in issue.get("labels", []) if isinstance(label, str)]
        if "handoff" not in labels:
            labels.append("handoff")
            issue["labels"] = labels
        base_time = _parse_timestamp(issue.get("updated") or issue.get("created"), datetime.now(UTC))
        comment_time = (base_time or datetime.now(UTC)) + timedelta(minutes=rng.randint(5, 240))
        author = issue.get("assignee_id") or issue.get("reporter_id") or (users[0] if users else "alice")
        handoff_code = f"HO-{rng.randint(1000, 9999)}"
        comment_payload = {
            "id": str(comment_seed),
            "author_id": author,
            "body": _adf_text(f"handoff-id: {handoff_code} ready for assist."),
            "created": comment_time.isoformat(),
        }
        comment_seed += 1
        issue.setdefault("comments", []).append(comment_payload)
        issue["comments"].sort(key=lambda item: item.get("created", ""))
        issue["updated"] = comment_time.isoformat()
        link_payload = {
            "id": str(link_seed),
            "type": {"name": "Relates", "outward": "relates to", "inward": "relates to"},
            "outwardIssue": {
                "id": partner.get("id"),
                "key": partner.get("key"),
                "fields": {"summary": partner.get("summary")},
            },
        }
        link_reverse = {
            "id": str(link_seed),
            "type": {"name": "Relates", "outward": "relates to", "inward": "relates to"},
            "inwardIssue": {
                "id": issue.get("id"),
                "key": issue.get("key"),
                "fields": {"summary": issue.get("summary")},
            },
        }
        link_seed += 1
        issue.setdefault("links", []).append(link_payload)
        partner.setdefault("links", []).append(link_reverse)
        partner["updated"] = comment_time.isoformat()


_PRIORITY_LABELS = [
    "priority:highest",
    "priority:high",
    "priority:medium",
    "priority:low",
]


def _strip_priority(labels: list[str]) -> list[str]:
    return [label for label in labels if not label.startswith("priority:")]


def _assign_priority_labels(
    payload: dict[str, Any], rng: random.Random, *, min_missing: int = 10, max_missing: int = 15
) -> None:
    issues_raw = payload.get("issues")
    if not isinstance(issues_raw, list) or not issues_raw:
        return
    issues = [issue for issue in issues_raw if isinstance(issue, dict)]
    if not issues:
        return

    target_missing = len(issues) // 10
    target_missing = max(min_missing, target_missing)
    target_missing = min(max_missing, target_missing, len(issues))

    def normalise_labels(issue: dict[str, Any]) -> list[str]:
        labels = [str(label) for label in issue.get("labels", []) if isinstance(label, str)]
        issue["labels"] = labels
        return labels

    def has_priority(issue: dict[str, Any]) -> bool:
        return any(label.startswith("priority:") for label in normalise_labels(issue))

    missing_ids = {id(issue) for issue in issues if not has_priority(issue)}

    if len(missing_ids) < target_missing:
        candidates = [issue for issue in issues if id(issue) not in missing_ids]
        rng.shuffle(candidates)
        needed = min(target_missing - len(missing_ids), len(candidates))
        for issue in candidates[:needed]:
            labels = normalise_labels(issue)
            issue["labels"] = _strip_priority(labels)
            missing_ids.add(id(issue))
    elif len(missing_ids) > target_missing:
        to_fix = rng.sample(list(missing_ids), len(missing_ids) - target_missing)
        fix_ids = set(to_fix)
        for issue in issues:
            if id(issue) in fix_ids:
                labels = normalise_labels(issue)
                if not any(label.startswith("priority:") for label in labels):
                    labels.append(rng.choice(_PRIORITY_LABELS))
                issue["labels"] = list(dict.fromkeys(labels))
                missing_ids.discard(id(issue))

    for issue in issues:
        labels = normalise_labels(issue)
        if id(issue) in missing_ids:
            issue["labels"] = _strip_priority(labels)
        else:
            if not any(label.startswith("priority:") for label in labels):
                labels.append(rng.choice(_PRIORITY_LABELS))
            issue["labels"] = list(dict.fromkeys(labels))


_STATUS_NAMES = {"1": "To Do", "3": "In Progress", "4": "Done"}


def _append_status_change(
    issue: dict[str, Any],
    *,
    previous: str,
    new_status: str,
    when: datetime,
    author: str,
) -> None:
    changes = issue.setdefault("changelog", [])
    change_id = _next_numeric_id((change for change in changes if isinstance(change, dict)), "id", 1)
    entry = {
        "id": str(change_id),
        "created": when.isoformat(),
        "author": author,
        "items": [
            {
                "field": "status",
                "from": previous,
                "to": new_status,
                "fromString": _STATUS_NAMES.get(previous, previous),
                "toString": _STATUS_NAMES.get(new_status, new_status),
            }
        ],
    }
    changes.append(entry)
    changes.sort(key=lambda item: item.get("created", ""))


def _mark_issue_stale(
    issue: dict[str, Any], rng: random.Random, now: datetime, *, min_age_days: int = 5
) -> None:
    created = _parse_timestamp(issue.get("created"), now - timedelta(days=30))
    previous_status = str(issue.get("status_id") or "1")
    stale_days = rng.randint(min_age_days + 1, min_age_days + 6)
    stale_ts = now - timedelta(days=stale_days)
    if created and stale_ts <= created:
        stale_ts = created + timedelta(days=min_age_days + 1)
    issue["status_id"] = "3"
    issue["updated"] = stale_ts.isoformat()
    author = str(issue.get("assignee_id") or issue.get("reporter_id") or "alice")
    if previous_status != "3":
        _append_status_change(issue, previous=previous_status, new_status="3", when=stale_ts, author=author)


def _ensure_stale_in_progress(
    payload: dict[str, Any],
    rng: random.Random,
    *,
    min_count: int = 10,
    max_count: int = 12,
    min_age_days: int = 5,
) -> None:
    issues_raw = payload.get("issues")
    if not isinstance(issues_raw, list) or not issues_raw:
        return
    issues = [issue for issue in issues_raw if isinstance(issue, dict)]
    if not issues:
        return
    now = datetime.now(UTC)
    target = max(min_count, len(issues) // 20)
    target = min(max_count, target, len(issues))

    def is_stale(issue: dict[str, Any]) -> bool:
        status_id = str(issue.get("status_id") or "")
        if status_id != "3":
            return False
        updated = _parse_timestamp(issue.get("updated"), now)
        return updated is not None and (now - updated) >= timedelta(days=min_age_days)

    stale_ids = {id(issue) for issue in issues if is_stale(issue)}

    if len(stale_ids) < target:
        candidates = [issue for issue in issues if id(issue) not in stale_ids]
        rng.shuffle(candidates)
        needed = min(target - len(stale_ids), len(candidates))
        for issue in candidates[:needed]:
            _mark_issue_stale(issue, rng, now, min_age_days=min_age_days)
            stale_ids.add(id(issue))
    elif len(stale_ids) > target:
        to_refresh = rng.sample(list(stale_ids), len(stale_ids) - target)
        refresh_ids = set(to_refresh)
        for issue in issues:
            if id(issue) in refresh_ids:
                recent = now - timedelta(days=rng.randint(0, max(min_age_days - 1, 0)))
                issue["updated"] = recent.isoformat()
                stale_ids.discard(id(issue))


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
        default=None,
        help="Average number of issues to create per project",
    )
    parser.add_argument(
        "--issues",
        type=int,
        default=150,
        help="Average number of issues to create per software project (overrides --issues-per-project)",
    )
    parser.add_argument(
        "--boards-per-sw-project",
        dest="boards_per_sw_project",
        type=int,
        default=1,
        help="Number of software boards to generate per project",
    )
    parser.add_argument(
        "--sprints-per-board",
        dest="sprints_per_board",
        type=int,
        default=None,
        help="Number of sprints to generate per software board",
    )
    parser.add_argument(
        "--sprints",
        type=int,
        default=8,
        help="Number of sprints per board (overrides --sprints-per-board)",
    )
    parser.add_argument(
        "--sprint-length-days",
        dest="sprint_length_days",
        type=int,
        default=14,
        help="Length of a sprint in days",
    )
    parser.add_argument(
        "--comments-per-issue",
        dest="comments_per_issue_avg",
        type=float,
        default=None,
        help="Average number of comments per issue",
    )
    parser.add_argument(
        "--comments",
        type=float,
        default=25.0,
        help="Average number of comments per issue (overrides --comments-per-issue)",
    )
    parser.add_argument(
        "--handoff",
        type=float,
        default=0.2,
        help="Probability of injecting a synthetic handoff thread per issue",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    seed_payload, cfg_overrides = _load_config(args.config)
    credit_seed = int(cfg_overrides.get("seed", args.seed))

    issues_per_project = cfg_overrides.get("issues_per_project")
    if issues_per_project is None:
        issues_per_project = args.issues if args.issues is not None else args.issues_per_project
    if issues_per_project is None:
        issues_per_project = DEFAULT_CFG.issues_per_project
    sprints_per_board = cfg_overrides.get("sprints_per_board")
    if sprints_per_board is None:
        sprints_per_board = args.sprints if args.sprints is not None else args.sprints_per_board
    if sprints_per_board is None:
        sprints_per_board = DEFAULT_CFG.sprints_per_board
    comments_avg = cfg_overrides.get("comments_per_issue_avg")
    if comments_avg is None:
        comments_avg = args.comments if args.comments is not None else args.comments_per_issue_avg
    if comments_avg is None:
        comments_avg = DEFAULT_CFG.comments_per_issue_avg
    boards_per_sw_project = cfg_overrides.get("boards_per_sw_project", args.boards_per_sw_project)
    handoff_probability = float(cfg_overrides.get("handoff_probability", args.handoff))

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
            issues_per_project=int(issues_per_project),
            boards_per_sw_project=int(boards_per_sw_project),
            sprints_per_board=int(sprints_per_board),
            sprint_length_days=int(
                cfg_overrides.get("sprint_length_days", DEFAULT_CFG.sprint_length_days)
            ),
            comments_per_issue_avg=float(comments_avg),
            transition_rate=float(
                cfg_overrides.get("transition_rate", DEFAULT_CFG.transition_rate)
            ),
            link_probability=float(
                cfg_overrides.get("link_probability", DEFAULT_CFG.link_probability)
            ),
            assignee_churn_prob=float(
                cfg_overrides.get("assignee_churn_prob", DEFAULT_CFG.assignee_churn_prob)
            ),
            use_support_templates=bool(
                cfg_overrides.get("use_support_templates", DEFAULT_CFG.use_support_templates)
            ),
        )
        payload = generate_seed_json(cfg)
        credit_seed = cfg.seed
    else:
        payload = seed_payload

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    post_rng = random.Random(credit_seed + 97)
    _normalise_sprint_windows(payload, post_rng)
    _inject_handoff_threads(payload, handoff_probability, post_rng)
    _assign_priority_labels(payload, post_rng)
    _ensure_stale_in_progress(payload, post_rng)
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
