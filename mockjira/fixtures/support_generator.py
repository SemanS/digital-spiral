"""Enhanced generator for AI Support Copilot with realistic support scenarios."""

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
from .support_templates import (
    SUPPORT_TEAM,
    CUSTOMERS,
    ALL_SCENARIOS,
    FOLLOWUP_COMMENTS,
    AGENT_RESPONSES,
    RESOLUTION_COMMENTS,
    SUPPORT_SPRINT_GOALS,
)


@dataclass(slots=True)
class SupportGenConfig:
    """Configuration for AI Support Copilot seed data generator."""
    
    seed: int = 42
    days: int = 180  # 6 months of history
    support_projects: int = 1
    dev_projects: int = 1
    tickets_per_month: int = 40  # ~2 tickets per day
    boards_per_project: int = 1
    sprints_per_board: int = 12  # 6 months of 2-week sprints
    sprint_length_days: int = 14
    avg_comments_per_ticket: float = 4.5
    resolution_rate: float = 0.85  # 85% of tickets get resolved
    escalation_rate: float = 0.15  # 15% get escalated
    reassignment_rate: float = 0.25  # 25% get reassigned


def generate_support_store(cfg: SupportGenConfig) -> InMemoryStore:
    """Create an InMemoryStore with realistic support data."""
    
    rng = random.Random(cfg.seed)
    store = InMemoryStore()
    _reset_store(store)
    change_counter = itertools.count(1)
    
    # Seed users (support team + customers)
    _seed_support_users(store)
    
    # Seed projects
    _seed_support_projects(store, cfg)
    
    # Seed boards and sprints
    _seed_support_boards_sprints(store, cfg, rng)
    
    # Seed realistic support tickets
    _seed_support_tickets(store, cfg, rng, change_counter)
    
    # Register mock tokens
    _register_tokens(store)
    
    return store


def _reset_store(store: InMemoryStore) -> None:
    """Reset store to clean state."""
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


def _seed_support_users(store: InMemoryStore) -> None:
    """Seed support team and customer users."""
    
    # Add support team
    for account_id, display_name, email, role in SUPPORT_TEAM:
        store.users[account_id] = User(account_id, display_name, email)
    
    # Add customers
    for account_id, display_name, email in CUSTOMERS:
        store.users[account_id] = User(account_id, display_name, email)


def _seed_support_projects(store: InMemoryStore, cfg: SupportGenConfig) -> None:
    """Seed support and development projects."""
    
    lead_support = "sarah.johnson"
    lead_dev = "mike.chen"
    
    # Support projects
    for idx in range(cfg.support_projects):
        key = "SUP" if cfg.support_projects == 1 else f"SUP{idx + 1}"
        store.projects[key] = Project(
            id=str(11000 + idx),
            key=key,
            name=f"Customer Support {idx + 1}",
            project_type="service_desk",
            lead_account_id=lead_support,
        )
    
    # Development projects (for escalations)
    for idx in range(cfg.dev_projects):
        key = "DEV" if cfg.dev_projects == 1 else f"DEV{idx + 1}"
        store.projects[key] = Project(
            id=str(10000 + idx),
            key=key,
            name=f"Engineering {idx + 1}",
            project_type="software",
            lead_account_id=lead_dev,
        )


def _seed_support_boards_sprints(
    store: InMemoryStore, 
    cfg: SupportGenConfig, 
    rng: random.Random
) -> None:
    """Seed boards and sprints with realistic goals."""
    
    now = datetime.now(UTC)
    start = now - timedelta(days=cfg.days)
    board_id = 1
    
    for project in store.projects.values():
        if project.project_type != "service_desk":
            continue
            
        for _ in range(cfg.boards_per_project):
            board = Board(
                id=board_id,
                name=f"{project.key} Support Board",
                type="kanban",  # Support teams typically use Kanban
                project_key=project.key,
            )
            store.boards[board_id] = board
            
            # Create sprints (even for Kanban, for reporting purposes)
            for offset in range(cfg.sprints_per_board):
                sprint_start = start + timedelta(days=offset * cfg.sprint_length_days)
                sprint_end = sprint_start + timedelta(days=cfg.sprint_length_days)
                state = _sprint_state(sprint_start, sprint_end, now)
                
                sprint = Sprint(
                    id=store.next_sprint_id,
                    board_id=board.id,
                    name=f"Support Sprint {offset + 1}",
                    state=state,
                    start_date=sprint_start,
                    end_date=sprint_end,
                    goal=rng.choice(SUPPORT_SPRINT_GOALS),
                )
                store.sprints[sprint.id] = sprint
                store.next_sprint_id += 1
            
            board_id += 1


def _sprint_state(start: datetime, end: datetime, now: datetime) -> str:
    """Determine sprint state based on dates."""
    if end < now:
        return "closed"
    if start <= now <= end:
        return "active"
    return "future"


def _seed_support_tickets(
    store: InMemoryStore,
    cfg: SupportGenConfig,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    """Seed realistic support tickets with full lifecycle."""
    
    now = datetime.now(UTC)
    earliest = now - timedelta(days=cfg.days)
    
    # Get support team and customer IDs
    support_team = [uid for uid, _, _, _ in SUPPORT_TEAM]
    customers = [uid for uid, _, _ in CUSTOMERS]
    
    # Calculate total tickets
    months = cfg.days / 30
    total_tickets = int(cfg.tickets_per_month * months)
    
    # Get support project
    support_projects = [p for p in store.projects.values() if p.project_type == "service_desk"]
    if not support_projects:
        return
    
    project = support_projects[0]
    
    # Create tickets based on scenarios
    for ticket_idx in range(total_tickets):
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
        labels = scenario.get("labels", [])
        
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
            sprint_id=None,  # Support tickets don't always have sprints
        )
        
        issue.created = created
        issue.updated = created
        issue.priority_id = _priority_to_id(priority)
        
        # Add comment thread
        _add_support_comments(issue, store, scenario, rng, reporter, assignee, support_team)
        
        # Maybe reassign
        if rng.random() < cfg.reassignment_rate:
            _reassign_ticket(issue, store, rng, support_team, change_counter)
        
        # Maybe resolve
        if rng.random() < cfg.resolution_rate:
            _resolve_ticket(issue, store, rng, change_counter)
        
        store.issues[issue.key] = issue


def _adf(text: str) -> dict:
    """Convert plain text to ADF format."""
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


def _priority_to_id(priority: str) -> str:
    """Convert priority name to ID."""
    mapping = {
        "Critical": "1",
        "High": "2",
        "Medium": "3",
        "Low": "4",
    }
    return mapping.get(priority, "3")


def _add_support_comments(
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


def _reassign_ticket(
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


def _resolve_ticket(
    issue: Issue,
    store: InMemoryStore,
    rng: random.Random,
    change_counter: Iterator[int],
) -> None:
    """Resolve ticket and add resolution comment."""
    
    resolution_time = issue.updated + timedelta(hours=rng.randint(2, 48))
    
    # Add resolution comment
    resolution_text = rng.choice(RESOLUTION_COMMENTS)
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


def _register_tokens(store: InMemoryStore) -> None:
    """Register mock authentication tokens."""
    store.tokens["mock-token"] = "sarah.johnson"
    store.tokens["support-token"] = "mike.chen"

