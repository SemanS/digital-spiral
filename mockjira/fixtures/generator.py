"""Deterministic data generator for the mock Jira store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import itertools
import random
from typing import Iterator

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from ..store import (
    Board,
    Comment,
    InMemoryStore,
    Issue,
    Project,
    Sprint,
    User,
)
from .templates import (
    COMMENT_TEMPLATES,
    REQUEST_DESCRIPTIONS,
    REQUEST_SUMMARIES,
    SPRINT_GOALS,
    SUMMARY_TOPICS,
)

# Try to import support templates if available
try:
    from .support_templates import (
        SUPPORT_TEAM,
        CUSTOMERS,
        ALL_SCENARIOS,
        FOLLOWUP_COMMENTS,
        AGENT_RESPONSES,
        RESOLUTION_COMMENTS,
        SUPPORT_SPRINT_GOALS,
    )
    HAS_SUPPORT_TEMPLATES = True
except ImportError:
    HAS_SUPPORT_TEMPLATES = False
    SUPPORT_TEAM = []
    CUSTOMERS = []
    ALL_SCENARIOS = []
    FOLLOWUP_COMMENTS = []
    AGENT_RESPONSES = []
    RESOLUTION_COMMENTS = []
    SUPPORT_SPRINT_GOALS = []


@dataclass(slots=True)
class GenConfig:
    """Configuration for the seed data generator."""

    seed: int = 42
    days: int = 120
    software_projects: int = 1
    servicedesk_projects: int = 1
    issues_per_project: int = 80
    boards_per_sw_project: int = 1
    sprints_per_board: int = 8
    sprint_length_days: int = 14
    comments_per_issue_avg: float = 2.0
    transition_rate: float = 0.75
    link_probability: float = 0.15
    assignee_churn_prob: float = 0.25
    use_support_templates: bool = False  # Use realistic support scenarios


def generate_store(cfg: GenConfig) -> InMemoryStore:
    """Create an :class:`InMemoryStore` populated with synthetic data."""

    rng = random.Random(cfg.seed)
    store = InMemoryStore()
    _reset_state(store)
    change_counter = itertools.count(1)

    _seed_users(store, cfg.use_support_templates)
    _seed_projects(store, cfg)
    _seed_boards_sprints(store, cfg, rng)

    if cfg.use_support_templates and HAS_SUPPORT_TEMPLATES:
        _seed_support_issues(store, cfg, rng, change_counter)
    else:
        _seed_issues_with_history(store, cfg, rng, change_counter)
        _seed_service_requests(store)

    _maybe_seed_issue_links(store, cfg, rng)
    _register_mock_tokens(store)
    return store


def generate_seed_json(cfg: GenConfig) -> dict[str, object]:
    """Return a serialisable representation of generated data."""

    store = generate_store(cfg)
    return store.export_seed()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _reset_state(store: InMemoryStore) -> None:
    store.users.clear()
    store.projects.clear()
    store.boards.clear()
    store.sprints.clear()
    store.issues.clear()
    store.issue_counter.clear()
    store.service_requests.clear()
    store.tokens.clear()
    store.webhooks.clear()
    store.deliveries = []
    store.webhook_logs = []
    store.next_issue_id = 10000
    store.next_comment_id = 20000
    store.next_request_id = 30000
    store.next_webhook_id = 40000
    store.next_sprint_id = 1
    store.next_link_id = 60000


def _seed_users(store: InMemoryStore, use_support_templates: bool = False) -> None:
    if use_support_templates and HAS_SUPPORT_TEMPLATES:
        # Use support team + customers
        for account_id, display_name, email, _ in SUPPORT_TEAM:
            store.users[account_id] = User(account_id, display_name, email)
        for account_id, display_name, email in CUSTOMERS:
            store.users[account_id] = User(account_id, display_name, email)
    else:
        # Use default users
        primary = [
            ("alice", "Alice Smith", "alice@example.com"),
            ("bob", "Bob Jones", "bob@example.com"),
            ("carol", "Carol Brown", "carol@example.com"),
            ("dave", "Dave Novak", "dave@example.com"),
            ("eva", "Eva Král", "eva@example.com"),
        ]
        for account_id, display_name, email in primary:
            store.users[account_id] = User(account_id, display_name, email)
        for idx in range(1, 4):
            account_id = f"junior{idx}"
            store.users[account_id] = User(
                account_id,
                f"Junior Engineer {idx}",
                f"{account_id}@example.com",
            )


def _seed_projects(store: InMemoryStore, cfg: GenConfig) -> None:
    lead_dev = "alice" if "alice" in store.users else next(iter(store.users))
    lead_support = "bob" if "bob" in store.users else lead_dev
    for idx in range(cfg.software_projects):
        key = "DEV" if cfg.software_projects == 1 else f"DEV{idx + 1}"
        store.projects[key] = Project(
            id=str(10000 + idx),
            key=key,
            name=f"Development {idx + 1}",
            project_type="software",
            lead_account_id=lead_dev,
        )
    for idx in range(cfg.servicedesk_projects):
        key = f"SUP{idx + 1}"
        store.projects[key] = Project(
            id=str(11000 + idx),
            key=key,
            name=f"Support {idx + 1}",
            project_type="service_desk",
            lead_account_id=lead_support,
        )


def _seed_boards_sprints(store: InMemoryStore, cfg: GenConfig, rng: random.Random) -> None:
    now = datetime.now(UTC)
    start = now - timedelta(days=cfg.days)
    board_id = 1
    for project in store.projects.values():
        if project.project_type != "software":
            continue
        for _ in range(cfg.boards_per_sw_project):
            board = Board(
                id=board_id,
                name=f"{project.key} Scrum {board_id}",
                type="scrum",
                project_key=project.key,
            )
            store.boards[board_id] = board
            for offset in range(cfg.sprints_per_board):
                sprint_start = start + timedelta(days=offset * cfg.sprint_length_days)
                sprint_end = sprint_start + timedelta(days=cfg.sprint_length_days)
                state = _sprint_state(sprint_start, sprint_end, now)
                sprint = Sprint(
                    id=store.next_sprint_id,
                    board_id=board.id,
                    name=f"Sprint {offset + 1}",
                    state=state,
                    start_date=sprint_start,
                    end_date=sprint_end,
                    goal=rng.choice(SPRINT_GOALS),
                )
                store.sprints[sprint.id] = sprint
                store.next_sprint_id += 1
            board_id += 1


def _sprint_state(start: datetime, end: datetime, now: datetime) -> str:
    if end < now:
        return "closed"
    if start <= now <= end:
        return "active"
    return "future"


def _seed_issues_with_history(
    store: InMemoryStore,
    cfg: GenConfig,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    user_ids = list(store.users.keys())
    if not user_ids:
        return
    issue_type_choices = ["10000", "10001", "10002"]
    label_pool = ["backend", "frontend", "infra", "needs-info", "p1", "p2", "regression"]
    now = datetime.now(UTC)
    earliest = now - timedelta(days=cfg.days)
    for project in store.projects.values():
        for _ in range(cfg.issues_per_project):
            created = earliest + timedelta(
                days=rng.randint(0, max(cfg.days, 1)),
                hours=rng.randint(0, 8),
                minutes=rng.randint(0, 50),
            )
            reporter = rng.choice(user_ids)
            assignee = rng.choice(user_ids)
            if project.project_type == "software":
                issue_type = rng.choice(issue_type_choices)
                summary = _random_summary(rng)
                description = _adf("Auto-generated by Digital Spiral")
            else:
                issue_type = "10003"
                summary = rng.choice(REQUEST_SUMMARIES)
                description = _adf(rng.choice(REQUEST_DESCRIPTIONS))
            sprint_id = _pick_sprint_for_project(store, project.key, rng)
            issue = store._create_issue(
                project_key=project.key,
                issue_type_id=issue_type,
                summary=summary,
                description=description,
                reporter_id=reporter,
                assignee_id=assignee,
                status_id="1",
                labels=rng.sample(label_pool, k=rng.randint(0, 2)),
                sprint_id=sprint_id,
            )
            issue.created = created
            issue.updated = created
            issue.description = description

            _add_comments(issue, store, cfg, rng)
            _maybe_add_transitions(issue, store, cfg, rng, change_counter)
            _maybe_add_assignee_change(issue, store, cfg, rng, change_counter)

            store.issues[issue.key] = issue


def _add_comments(
    issue: Issue, store: InMemoryStore, cfg: GenConfig, rng: random.Random
) -> None:
    expected = max(0, int(rng.gauss(cfg.comments_per_issue_avg, 1)))
    for _ in range(expected):
        comment_time = issue.created + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 8))
        author = rng.choice(list(store.users.keys()))
        comment = Comment(
            id=str(store.next_comment_id),
            author_id=author,
            body=_adf(rng.choice(COMMENT_TEMPLATES)),
            created=comment_time,
        )
        store.next_comment_id += 1
        issue.comments.append(comment)
        issue.updated = max(issue.updated, comment_time)


def _maybe_add_transitions(
    issue: Issue,
    store: InMemoryStore,
    cfg: GenConfig,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    if rng.random() >= cfg.transition_rate:
        return
    to_in_progress = issue.created + timedelta(days=rng.randint(0, 5))
    _apply_transition_history(store, issue, "3", to_in_progress, rng, change_counter)
    if rng.random() < 0.7:
        to_done = to_in_progress + timedelta(days=rng.randint(1, 10))
        _apply_transition_history(store, issue, "4", to_done, rng, change_counter)


def _maybe_add_assignee_change(
    issue: Issue,
    store: InMemoryStore,
    cfg: GenConfig,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    if rng.random() >= cfg.assignee_churn_prob:
        return
    user_ids = list(store.users.keys())
    if len(user_ids) < 2:
        return
    when = issue.created + timedelta(days=rng.randint(0, 7))
    previous = issue.assignee_id
    replacement = rng.choice(user_ids)
    if replacement == previous:
        replacement = user_ids[(user_ids.index(replacement) + 1) % len(user_ids)]
    issue.assignee_id = replacement
    issue.updated = max(issue.updated, when)
    _record_change(
        issue,
        store,
        change_counter,
        when,
        field="assignee",
        from_value=previous,
        to_value=replacement,
        author=replacement,
    )


def _apply_transition_history(
    store: InMemoryStore,
    issue: Issue,
    to_status_id: str,
    at: datetime,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    previous = issue.status_id
    issue.status_id = to_status_id
    issue.updated = max(issue.updated, at)
    _record_change(
        issue,
        store,
        change_counter,
        at,
        field="status",
        from_value=previous,
        to_value=to_status_id,
        author=issue.assignee_id or rng.choice(list(store.users.keys())),
    )


def _record_change(
    issue: Issue,
    store: InMemoryStore,
    change_counter: Iterator[int],
    when: datetime,
    *,
    field: str,
    from_value: str | None,
    to_value: str | None,
    author: str | None,
) -> None:
    if field == "status":
        from_string = store.statuses.get(str(from_value)).name if from_value else None
        to_string = store.statuses.get(str(to_value)).name if to_value else None
    elif field == "assignee":
        from_user = store.users.get(str(from_value)) if from_value else None
        to_user = store.users.get(str(to_value)) if to_value else None
        from_string = from_user.display_name if from_user else None
        to_string = to_user.display_name if to_user else None
    else:  # pragma: no cover - defensive, currently unused
        from_string = from_value
        to_string = to_value
    issue.changelog.append(
        {
            "id": str(next(change_counter)),
            "created": when.isoformat(),
            "author": author,
            "items": [
                {
                    "field": field,
                    "from": from_value,
                    "fromString": from_string,
                    "to": to_value,
                    "toString": to_string,
                }
            ],
        }
    )


def _random_summary(rng: random.Random) -> str:
    return rng.choice(SUMMARY_TOPICS)


def _adf(text: str) -> dict[str, object]:
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


def _pick_sprint_for_project(
    store: InMemoryStore, project_key: str, rng: random.Random
) -> int | None:
    boards = [board for board in store.boards.values() if board.project_key == project_key]
    if not boards or rng.random() < 0.35:
        return None
    board = rng.choice(boards)
    sprints = [sprint for sprint in store.sprints.values() if sprint.board_id == board.id]
    if not sprints:
        return None
    return rng.choice(sprints).id


def _seed_service_requests(store: InMemoryStore) -> None:
    for issue in list(store.issues.values()):
        if issue.project_key.startswith("SUP"):
            store._ensure_service_request(issue)


def _maybe_seed_issue_links(store: InMemoryStore, cfg: GenConfig, rng: random.Random) -> None:
    keys = list(store.issues.keys())
    if len(keys) < 2:
        return
    seen: set[tuple[str, str]] = set()
    for key in keys:
        if rng.random() >= cfg.link_probability:
            continue
        other = rng.choice(keys)
        if other == key or (key, other) in seen or (other, key) in seen:
            continue
        seen.add((key, other))
        _attach_link(store, key, other, rng)


def _attach_link(store: InMemoryStore, left_key: str, right_key: str, rng: random.Random) -> None:
    left = store.issues.get(left_key)
    right = store.issues.get(right_key)
    if not left or not right:
        return
    link_type = rng.choice(["relates", "blocks"])
    if link_type == "blocks":
        type_payload = {
            "name": "Blocks",
            "outward": "blocks",
            "inward": "is blocked by",
        }
    else:
        type_payload = {
            "name": "Relates",
            "outward": "relates to",
            "inward": "relates to",
        }
    link_id = str(store.next_link_id)
    store.next_link_id += 1
    left.links.append(
        {
            "id": link_id,
            "type": type_payload,
            "outwardIssue": {
                "id": right.id,
                "key": right.key,
                "fields": {"summary": right.summary},
            },
        }
    )
    right.links.append(
        {
            "id": link_id,
            "type": type_payload,
            "inwardIssue": {
                "id": left.id,
                "key": left.key,
                "fields": {"summary": left.summary},
            },
        }
    )
    timestamp = max(left.updated, right.updated)
    left.updated = timestamp
    right.updated = timestamp


def _register_mock_tokens(store: InMemoryStore) -> None:
    if store.users:
        preferred = "alice" if "alice" in store.users else next(iter(store.users))
        store.tokens["mock-token"] = preferred
        # Support tokens
        if "sarah.johnson" in store.users:
            store.tokens["support-token"] = "sarah.johnson"
    else:  # pragma: no cover - generator always creates users
        store.tokens["mock-token"] = "mock-user"


def _seed_support_issues(
    store: InMemoryStore,
    cfg: GenConfig,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    """Seed realistic support tickets using support templates."""

    if not HAS_SUPPORT_TEMPLATES or not ALL_SCENARIOS:
        # Fallback to default generation
        _seed_issues_with_history(store, cfg, rng, change_counter)
        return

    now = datetime.now(UTC)
    earliest = now - timedelta(days=cfg.days)

    # Get support team and customer IDs
    support_team = [uid for uid, _, _, _ in SUPPORT_TEAM]
    customers = [uid for uid, _, _ in CUSTOMERS]

    if not support_team or not customers:
        # Fallback if templates not properly loaded
        _seed_issues_with_history(store, cfg, rng, change_counter)
        return

    # Get support project
    support_projects = [p for p in store.projects.values() if p.project_type == "service_desk"]
    if not support_projects:
        return

    project = support_projects[0]

    # Create tickets based on scenarios
    for ticket_idx in range(cfg.issues_per_project):
        # Pick a random scenario
        scenario = rng.choice(ALL_SCENARIOS)

        # Random creation time
        created = earliest + timedelta(
            days=rng.randint(0, cfg.days),
            hours=rng.randint(8, 18),  # Business hours
            minutes=rng.randint(0, 59),
        )

        # Pick reporter (customer) and assignee (support team)
        reporter = rng.choice(customers)
        assignee = rng.choice(support_team)

        # Determine priority and labels
        priority = scenario.get("priority", "Medium")
        labels = list(scenario.get("labels", []))

        # Create issue
        issue = store._create_issue(
            project_key=project.key,
            issue_type_id="10003",  # Service Request
            summary=scenario["summary"],
            description=_adf(scenario["description"]),
            reporter_id=reporter,
            assignee_id=assignee,
            status_id="1",  # Open
            labels=labels,
            sprint_id=None,
        )

        issue.created = created
        issue.updated = created
        issue.priority_id = _priority_to_id(priority)

        # Add comment thread
        _add_scenario_comments(issue, store, scenario, rng, reporter, assignee, support_team)

        # Maybe reassign
        if rng.random() < cfg.assignee_churn_prob:
            _reassign_support_ticket(issue, store, rng, support_team, change_counter)

        # Maybe resolve
        if rng.random() < cfg.transition_rate:
            _resolve_support_ticket(issue, store, rng, change_counter)

        store.issues[issue.key] = issue


def _priority_to_id(priority: str) -> str:
    """Convert priority name to ID."""
    mapping = {
        "Critical": "1",
        "High": "2",
        "Medium": "3",
        "Low": "4",
    }
    return mapping.get(priority, "3")


def _add_scenario_comments(
    issue: Issue,
    store: InMemoryStore,
    scenario: dict,
    rng: random.Random,
    reporter: str,
    assignee: str,
    support_team: list[str],
) -> None:
    """Add realistic comment thread from scenario."""

    comments = scenario.get("comments", [])
    current_time = issue.created

    for idx, comment_text in enumerate(comments):
        # Alternate between customer and support
        is_customer_comment = (idx % 2 == 0)
        author = reporter if is_customer_comment else rng.choice(support_team)

        # Add realistic time delays
        if idx == 0:
            delay = timedelta(minutes=rng.randint(5, 30))  # First response
        else:
            delay = timedelta(hours=rng.randint(1, 8))  # Subsequent responses

        current_time += delay

        comment = Comment(
            id=str(store.next_comment_id),
            author_id=author,
            body=_adf(comment_text),
            created=current_time,
        )
        store.next_comment_id += 1
        issue.comments.append(comment)
        issue.updated = current_time


def _reassign_support_ticket(
    issue: Issue,
    store: InMemoryStore,
    rng: random.Random,
    support_team: list[str],
    change_counter: Iterator[int],
) -> None:
    """Reassign ticket to another support agent."""

    previous = issue.assignee_id
    new_assignee = rng.choice([a for a in support_team if a != previous])

    when = issue.updated + timedelta(hours=rng.randint(1, 4))
    issue.assignee_id = new_assignee
    issue.updated = when


def _resolve_support_ticket(
    issue: Issue,
    store: InMemoryStore,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    """Resolve ticket and add resolution comment."""

    resolution_time = issue.updated + timedelta(hours=rng.randint(2, 48))

    # Add resolution comment
    if HAS_SUPPORT_TEMPLATES and RESOLUTION_COMMENTS:
        resolution_text = rng.choice(RESOLUTION_COMMENTS)
    else:
        resolution_text = "Issue resolved. Closing ticket."

    comment = Comment(
        id=str(store.next_comment_id),
        author_id=issue.assignee_id or "sarah.johnson",
        body=_adf(resolution_text),
        created=resolution_time,
    )
    store.next_comment_id += 1
    issue.comments.append(comment)

    # Transition to Done
    issue.status_id = "4"  # Done
    issue.updated = resolution_time

    # Record transition in changelog
    _apply_transition_history(
        store,
        issue,
        "4",
        resolution_time,
        rng,
        change_counter,
    )


__all__ = ["GenConfig", "generate_store", "generate_seed_json"]
