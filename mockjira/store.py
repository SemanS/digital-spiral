"""In-memory persistence layer for the mock Jira server."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


class RateLimitError(Exception):
    """Raised when a token exceeds its allowed request budget."""

    def __init__(
        self,
        retry_after: int,
        *,
        remaining: int | None = None,
        reset_at: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        self.remaining = remaining
        self.reset_at = reset_at
        super().__init__("Rate limit exceeded")


@dataclass
class User:
    account_id: str
    display_name: str
    email: str
    time_zone: str = "UTC"

    def to_api(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "displayName": self.display_name,
            "emailAddress": self.email,
            "timeZone": self.time_zone,
            "active": True,
        }


@dataclass
class Project:
    id: str
    key: str
    name: str
    project_type: str
    lead_account_id: str

    def to_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "projectTypeKey": self.project_type,
            "lead": {
                **self.to_user_api(self.lead_account_id),
            },
        }

    def to_user_api(self, account_id: str) -> dict[str, Any]:
        return {
            "accountId": account_id,
        }


@dataclass
class IssueType:
    id: str
    name: str
    subtask: bool = False

    def to_api(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "subtask": self.subtask}


@dataclass
class StatusCategory:
    id: int
    key: str
    name: str

    def to_api(self) -> dict[str, Any]:
        return {"id": self.id, "key": self.key, "name": self.name}


@dataclass
class Status:
    id: str
    name: str
    status_category: StatusCategory

    def to_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "statusCategory": self.status_category.to_api(),
        }


@dataclass
class Transition:
    id: str
    name: str
    to_status: Status

    def to_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "to": self.to_status.to_api(),
        }


@dataclass
class Comment:
    id: str
    author_id: str
    body: dict[str, Any]
    created: datetime

    def to_api(self, author: User) -> dict[str, Any]:
        return {
            "id": self.id,
            "body": self.body,
            "author": author.to_api(),
            "created": self.created.isoformat(),
            "updated": self.created.isoformat(),
        }


@dataclass
class Sprint:
    id: int
    board_id: int
    name: str
    state: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    goal: str | None = None

    def to_api(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "originBoardId": self.board_id,
        }
        if self.start_date:
            payload["startDate"] = self.start_date.isoformat()
        if self.end_date:
            payload["endDate"] = self.end_date.isoformat()
        if self.goal:
            payload["goal"] = self.goal
        return payload


@dataclass
class Board:
    id: int
    name: str
    type: str
    project_key: str

    def to_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "location": {"projectKey": self.project_key},
        }


@dataclass
class ServiceRequest:
    id: str
    issue_key: str
    request_type_id: str
    approvals: list[dict[str, Any]] = field(default_factory=list)

    def to_api(self, issue: "Issue", store: "InMemoryStore") -> dict[str, Any]:
        return {
            "id": self.id,
            "issueId": issue.id,
            "issueKey": issue.key,
            "serviceDeskId": "1",
            "requestTypeId": self.request_type_id,
            "status": issue.status(store).to_api(),
            "requestFieldValues": {
                "summary": issue.summary,
                "description": issue.description,
            },
            "approvals": self.approvals,
        }


@dataclass
class Issue:
    id: str
    key: str
    project_key: str
    issue_type_id: str
    summary: str
    description: dict[str, Any]
    status_id: str
    reporter_id: str
    assignee_id: str | None
    labels: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    sprint_id: int | None = None
    comments: list[Comment] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)
    links: list[dict[str, Any]] = field(default_factory=list)
    changelog: list[dict[str, Any]] = field(default_factory=list)

    def project(self, store: "InMemoryStore") -> Project:
        return store.projects[self.project_key]

    def issue_type(self, store: "InMemoryStore") -> IssueType:
        return store.issue_types[self.issue_type_id]

    def status(self, store: "InMemoryStore") -> Status:
        return store.statuses[self.status_id]

    def reporter(self, store: "InMemoryStore") -> User:
        return store.users[self.reporter_id]

    def assignee(self, store: "InMemoryStore") -> User | None:
        return store.users.get(self.assignee_id) if self.assignee_id else None

    def to_api(
        self,
        store: "InMemoryStore",
        *,
        expand: set[str] | None = None,
    ) -> dict[str, Any]:
        assignee = self.assignee(store)
        reporter = self.reporter(store)
        project = self.project(store)
        fields = {
            "summary": self.summary,
            "description": self.description,
            "issuetype": self.issue_type(store).to_api(),
            "project": {
                "id": project.id,
                "key": project.key,
                "name": project.name,
                "projectTypeKey": project.project_type,
            },
            "status": self.status(store).to_api(),
            "reporter": reporter.to_api(),
            "assignee": assignee.to_api() if assignee else None,
            "labels": self.labels,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "comment": {
                "comments": [
                    c.to_api(store.users[c.author_id]) for c in self.comments
                ],
                "total": len(self.comments),
            },
        }
        if self.sprint_id:
            fields["customfield_10020"] = [self.sprint_id]
        for key, value in sorted(self.custom_fields.items()):
            fields[key] = value
        if self.links:
            fields["issuelinks"] = self.links
        payload = {
            "id": self.id,
            "key": self.key,
            "fields": fields,
        }
        changelog = self._changelog_payload(store, expand=expand)
        if changelog is not None:
            payload["changelog"] = changelog
        return payload

    def _changelog_payload(
        self, store: "InMemoryStore", *, expand: set[str] | None
    ) -> dict[str, Any] | None:
        if not expand or "changelog" not in expand:
            return None
        histories = []
        for entry in self.changelog:
            author = store.users.get(entry.get("author"))
            histories.append(
                {
                    "id": entry.get("id"),
                    "created": entry.get("created"),
                    "author": author.to_api() if author else None,
                    "items": [
                        {
                            "field": entry.get("field"),
                            "from": entry.get("from"),
                            "fromString": entry.get("fromString"),
                            "to": entry.get("to"),
                            "toString": entry.get("toString"),
                        }
                    ],
                }
            )
        return {
            "startAt": 0,
            "maxResults": len(histories),
            "total": len(histories),
            "histories": histories,
            "values": histories,
        }


@dataclass
class WebhookRegistration:
    id: str
    url: str
    events: list[str] = field(default_factory=list)
    jql: str | None = None
    secret: str | None = None
    active: bool = True


logger = logging.getLogger("mockjira.webhooks")


class InMemoryStore:
    """Central state container for the mock server."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.projects: dict[str, Project] = {}
        self.issue_types: dict[str, IssueType] = {}
        self.status_categories: dict[str, StatusCategory] = {}
        self.statuses: dict[str, Status] = {}
        self.transitions: dict[str, list[Transition]] = {}
        self.issues: dict[str, Issue] = {}
        self.issue_counter: dict[str, int] = defaultdict(int)
        self.boards: dict[int, Board] = {}
        self.sprints: dict[int, Sprint] = {}
        self.service_requests: dict[str, ServiceRequest] = {}
        self.webhooks: dict[str, WebhookRegistration] = {}
        self.deliveries: list[dict[str, Any]] = []
        self._delivery_index: dict[str, dict[str, Any]] = {}
        self._recent_delivery_keys: deque[tuple[str, str]] = deque()
        self._recent_delivery_lookup: set[tuple[str, str]] = set()
        self._recent_delivery_window = 2000
        self.tokens: dict[str, str] = {}
        self.rate_calls: dict[str, deque[tuple[datetime, int]]] = defaultdict(deque)
        self.next_issue_id = 10000
        self.next_comment_id = 20000
        self.next_request_id = 30000
        self.next_webhook_id = 40000
        self.next_sprint_id = 5000
        self.next_link_id = 60000
        jitter_min = int(os.getenv("MOCKJIRA_WEBHOOK_JITTER_MIN", "50"))
        jitter_max = int(os.getenv("MOCKJIRA_WEBHOOK_JITTER_MAX", "250"))
        if jitter_min > jitter_max:
            jitter_min, jitter_max = jitter_max, jitter_min
        self._webhook_jitter_ms: tuple[int, int] = (jitter_min, jitter_max)
        self._webhook_poison_prob: float = float(
            os.getenv("MOCKJIRA_WEBHOOK_POISON_PROB", "0.0")
        )
        self._force_429_tokens: set[str] = set()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def with_seed_data(cls) -> "InMemoryStore":
        store = cls()
        store._seed()
        return store

    # ------------------------------------------------------------------
    def _seed(self) -> None:
        self.tokens = {"mock-token": "5b10a2844c20165700ede21g"}

        self.users = {
            "5b10a2844c20165700ede21g": User(
                account_id="5b10a2844c20165700ede21g",
                display_name="Alice Johnson",
                email="alice@example.com",
            ),
            "5b10a2844c20165700ede20f": User(
                account_id="5b10a2844c20165700ede20f",
                display_name="Bob Smith",
                email="bob@example.com",
            ),
            "5b10a2844c20165700ede20e": User(
                account_id="5b10a2844c20165700ede20e",
                display_name="Carol Williams",
                email="carol@example.com",
            ),
        }

        to_do = StatusCategory(id=2, key="new", name="To Do")
        in_progress = StatusCategory(id=4, key="indeterminate", name="In Progress")
        done_cat = StatusCategory(id=3, key="done", name="Done")
        self.status_categories = {
            "todo": to_do,
            "in_progress": in_progress,
            "done": done_cat,
        }

        status_to_do = Status(id="1", name="To Do", status_category=to_do)
        status_in_progress = Status(
            id="3", name="In Progress", status_category=in_progress
        )
        status_done = Status(id="4", name="Done", status_category=done_cat)
        self.statuses = {
            status_to_do.id: status_to_do,
            status_in_progress.id: status_in_progress,
            status_done.id: status_done,
        }

        self.transitions = {
            status_to_do.id: [
                Transition(id="11", name="Start Progress", to_status=status_in_progress)
            ],
            status_in_progress.id: [
                Transition(id="21", name="Resolve", to_status=status_done),
                Transition(id="31", name="Reopen", to_status=status_to_do),
            ],
            status_done.id: [
                Transition(id="41", name="Reopen", to_status=status_in_progress)
            ],
        }

        self.projects = {
            "DEV": Project(
                id="10000",
                key="DEV",
                name="Development",
                project_type="software",
                lead_account_id="5b10a2844c20165700ede21g",
            ),
            "SUP": Project(
                id="10001",
                key="SUP",
                name="Support",
                project_type="service_desk",
                lead_account_id="5b10a2844c20165700ede20f",
            ),
        }

        self.issue_types = {
            "10000": IssueType(id="10000", name="Bug"),
            "10001": IssueType(id="10001", name="Task"),
            "10002": IssueType(id="10002", name="Story"),
            "10003": IssueType(id="10003", name="Service Request"),
        }

        self.boards = {
            1: Board(id=1, name="DEV Scrum", type="scrum", project_key="DEV"),
            2: Board(id=2, name="DEV Kanban", type="kanban", project_key="DEV"),
        }

        now = datetime.now(UTC)
        self.sprints = {
            1: Sprint(
                id=1,
                board_id=1,
                name="Sprint 1",
                state="closed",
                start_date=now - timedelta(days=21),
                end_date=now - timedelta(days=7),
                goal="Initial release",
            ),
            2: Sprint(
                id=2,
                board_id=1,
                name="Sprint 2",
                state="active",
                start_date=now - timedelta(days=6),
                end_date=now + timedelta(days=8),
                goal="Polish features",
            ),
            3: Sprint(
                id=3,
                board_id=1,
                name="Sprint 3",
                state="future",
                start_date=now + timedelta(days=9),
                end_date=now + timedelta(days=23),
            ),
        }
        self.next_sprint_id = 4

        self._create_issue(
            project_key="DEV",
            issue_type_id="10002",
            summary="User can sign up",
            description=self._adf("Implement sign-up flow"),
            reporter_id="5b10a2844c20165700ede21g",
            assignee_id="5b10a2844c20165700ede20f",
            status_id="3",
            labels=["backend"],
            sprint_id=2,
        )
        self._create_issue(
            project_key="DEV",
            issue_type_id="10000",
            summary="Fix payment bug",
            description=self._adf("Resolve gateway timeout"),
            reporter_id="5b10a2844c20165700ede20f",
            assignee_id="5b10a2844c20165700ede21g",
            status_id="1",
            labels=["urgent"],
        )
        self._create_issue(
            project_key="DEV",
            issue_type_id="10001",
            summary="Improve onboarding",
            description=self._adf("Add product tour"),
            reporter_id="5b10a2844c20165700ede21g",
            assignee_id=None,
            status_id="1",
        )
        self._create_issue(
            project_key="SUP",
            issue_type_id="10003",
            summary="Cannot login",
            description=self._adf("Customer reports login failure"),
            reporter_id="5b10a2844c20165700ede20e",
            assignee_id="5b10a2844c20165700ede20f",
            status_id="1",
        )

        for issue in self.issues.values():
            if issue.project_key == "SUP":
                self._ensure_service_request(issue)

    # ------------------------------------------------------------------
    def _create_issue(
        self,
        project_key: str,
        issue_type_id: str,
        summary: str,
        description: dict[str, Any],
        reporter_id: str,
        assignee_id: str | None,
        status_id: str,
        labels: list[str] | None = None,
        sprint_id: int | None = None,
    ) -> Issue:
        seq = self.issue_counter[project_key] + 1
        self.issue_counter[project_key] = seq
        key = f"{project_key}-{seq}"
        issue = Issue(
            id=str(self.next_issue_id),
            key=key,
            project_key=project_key,
            issue_type_id=issue_type_id,
            summary=summary,
            description=description,
            status_id=status_id,
            reporter_id=reporter_id,
            assignee_id=assignee_id,
            labels=labels or [],
            sprint_id=sprint_id,
        )
        self.next_issue_id += 1
        self.issues[key] = issue
        return issue

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _adf(self, text: str) -> dict[str, Any]:
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_valid_token(self, token: str) -> bool:
        return token in self.tokens

    def should_force_429(self, token: str) -> bool:
        if token in self._force_429_tokens:
            return False
        self._force_429_tokens.add(token)
        return True

    def register_call(self, token: str, cost: int = 1) -> None:
        limit = 100
        window = timedelta(seconds=60)
        now = datetime.now(UTC)
        bucket = self.rate_calls[token]
        while bucket and now - bucket[0][0] > window:
            bucket.popleft()
        current_cost = sum(item_cost for _, item_cost in bucket)
        if current_cost + cost > limit:
            oldest = bucket[0][0] if bucket else now
            retry_after = max(1, int((oldest + window - now).total_seconds()))
            remaining = max(0, limit - current_cost)
            reset_at = int((oldest + window).timestamp())
            raise RateLimitError(
                retry_after=retry_after,
                remaining=remaining,
                reset_at=reset_at,
            )
        bucket.append((now, cost))

    # ------------------------- Platform --------------------------------
    def list_projects(self) -> list[dict[str, Any]]:
        return [
            {
                "id": proj.id,
                "key": proj.key,
                "name": proj.name,
                "projectTypeKey": proj.project_type,
            }
            for proj in self.projects.values()
        ]

    def list_issue_types(self) -> list[dict[str, Any]]:
        return [t.to_api() for t in self.issue_types.values()]

    def list_statuses(self) -> list[dict[str, Any]]:
        return [status.to_api() for status in self.statuses.values()]

    def list_users(self, query: str | None = None) -> list[dict[str, Any]]:
        query = (query or "").lower()
        matches = [
            user.to_api()
            for user in self.users.values()
            if query in user.display_name.lower() or query in user.email.lower()
        ]
        return matches

    def fields_payload(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "summary",
                "name": "Summary",
                "schema": {"type": "string"},
                "custom": False,
            },
            {
                "id": "description",
                "name": "Description",
                "schema": {"type": "rich_text"},
                "custom": False,
            },
            {
                "id": "labels",
                "name": "Labels",
                "schema": {"type": "array", "items": "string"},
                "custom": False,
            },
        ]

    def get_issue(self, key: str) -> Issue | None:
        return self.issues.get(key)

    def create_issue(self, payload: dict[str, Any], reporter_id: str) -> Issue:
        fields = payload.get("fields", {})
        project = fields.get("project", {})
        project_key = project.get("key")
        if not project_key or project_key not in self.projects:
            raise ValueError("Invalid or missing project key")
        issue_type_id = fields.get("issuetype", {}).get("id") or "10001"
        summary = fields.get("summary", "Untitled issue")
        description = self.normalize_adf(fields.get("description", ""))
        assignee_field = fields.get("assignee") or {}
        assignee_id = assignee_field.get("accountId")
        labels = fields.get("labels", [])
        sprint_values = fields.get("customfield_10020")
        sprint_id: int | None = None
        if isinstance(sprint_values, list) and sprint_values:
            try:
                sprint_id = int(sprint_values[0])
            except (TypeError, ValueError):
                sprint_id = None
        custom_fields = {
            key: value
            for key, value in fields.items()
            if key.startswith("customfield_") and key != "customfield_10020"
        }
        issue = self._create_issue(
            project_key=project_key,
            issue_type_id=issue_type_id,
            summary=summary,
            description=description,
            reporter_id=reporter_id,
            assignee_id=assignee_id,
            status_id="1",
            labels=labels,
            sprint_id=sprint_id,
        )
        if custom_fields:
            issue.custom_fields.update(custom_fields)
        if project_key == "SUP":
            self._ensure_service_request(issue)
        self.dispatch_event(
            "jira:issue_created",
            {"issue": issue.to_api(self)},
        )
        return issue

    def update_issue(self, key: str, payload: dict[str, Any]) -> Issue:
        issue = self.issues[key]
        fields = payload.get("fields", {})
        if "summary" in fields:
            issue.summary = fields["summary"]
        if "description" in fields:
            issue.description = self.normalize_adf(fields["description"])
        if "assignee" in fields:
            assignee = fields.get("assignee")
            issue.assignee_id = assignee.get("accountId") if assignee else None
        if "labels" in fields:
            issue.labels = list(fields["labels"])
        if "customfield_10020" in fields:
            values = fields.get("customfield_10020")
            if isinstance(values, list) and values:
                try:
                    issue.sprint_id = int(values[0])
                except (TypeError, ValueError):
                    issue.sprint_id = None
            else:
                issue.sprint_id = None
        for key, value in fields.items():
            if key.startswith("customfield_") and key != "customfield_10020":
                issue.custom_fields[key] = value
        issue.updated = datetime.now(UTC)
        self.dispatch_event(
            "jira:issue_updated",
            {"issue": issue.to_api(self)},
        )
        return issue

    def create_issue_link(self, payload: dict[str, Any], actor_id: str) -> dict[str, Any]:
        type_info = payload.get("type") or {}
        type_name = str(type_info.get("name", "")).strip()
        if not type_name:
            raise ValueError("Link type name is required")
        normalised = type_name.lower()
        if normalised not in {"blocks", "relates"}:
            raise ValueError("Unsupported link type")
        type_payload = {
            "id": type_info.get("id"),
            "name": type_info.get("name", type_name.title()),
            "outward": type_info.get("outward")
            or ("blocks" if normalised == "blocks" else "relates to"),
            "inward": type_info.get("inward")
            or ("is blocked by" if normalised == "blocks" else "relates to"),
        }
        outward_key = payload.get("outwardIssue", {}).get("key")
        inward_key = payload.get("inwardIssue", {}).get("key")
        if not outward_key or not inward_key:
            raise ValueError("Both outwardIssue and inwardIssue keys are required")
        outward_issue = self.issues.get(outward_key)
        inward_issue = self.issues.get(inward_key)
        if not outward_issue or not inward_issue:
            raise ValueError("Unknown issue key")

        link_id = str(self.next_link_id)
        self.next_link_id += 1

        outward_issue.links.append(
            {
                "id": link_id,
                "type": type_payload,
                "outwardIssue": {
                    "id": inward_issue.id,
                    "key": inward_issue.key,
                    "fields": {"summary": inward_issue.summary},
                },
            }
        )
        inward_issue.links.append(
            {
                "id": link_id,
                "type": type_payload,
                "inwardIssue": {
                    "id": outward_issue.id,
                    "key": outward_issue.key,
                    "fields": {"summary": outward_issue.summary},
                },
            }
        )

        now = datetime.now(UTC)
        outward_issue.updated = now
        inward_issue.updated = now

        self.dispatch_event(
            "jira:issue_updated",
            {"issue": outward_issue.to_api(self)},
        )
        self.dispatch_event(
            "jira:issue_updated",
            {"issue": inward_issue.to_api(self)},
        )
        return {"id": link_id}

    def search_issues(
        self,
        filters: dict[str, Any],
        *,
        order_by: list[tuple[str, str]] | None = None,
        date_filters: dict[str, dict[str, Any]] | None = None,
    ) -> list[Issue]:
        results = list(self.issues.values())

        def _as_list(value: Any) -> list[Any]:
            if isinstance(value, list):
                return value
            if value is None:
                return []
            return [value]

        project = filters.get("project")
        if project:
            allowed = {str(item).upper() for item in _as_list(project)}
            results = [
                issue for issue in results if issue.project_key.upper() in allowed
            ]

        status = filters.get("status")
        if status:
            status_values = {str(item).lower() for item in _as_list(status)}
            results = [
                issue
                for issue in results
                if issue.status(self).name.lower() in status_values
            ]

        reporter = filters.get("reporter")
        if reporter:
            reporter_values = {str(item) for item in _as_list(reporter)}
            results = [
                issue for issue in results if issue.reporter_id in reporter_values
            ]

        assignee = filters.get("assignee")
        if assignee:
            assignee_values = set()
            include_unassigned = False
            for item in _as_list(assignee):
                if isinstance(item, str) and item.lower() == "unassigned":
                    include_unassigned = True
                    continue
                assignee_values.add(str(item))
            results = [
                issue
                for issue in results
                if (
                    (issue.assignee_id in assignee_values)
                    or (include_unassigned and issue.assignee_id is None)
                )
            ]

        issue_type = filters.get("issuetype") or filters.get("type")
        if issue_type:
            raw_values = {str(item).lower() for item in _as_list(issue_type)}
            results = [
                issue
                for issue in results
                if (
                    str(issue.issue_type_id).lower() in raw_values
                    or issue.issue_type(self).name.lower() in raw_values
                )
            ]

        date_filters = date_filters or {}
        updated_filter = date_filters.get("updated") or {}
        updated_gte = updated_filter.get("gte") if isinstance(updated_filter, dict) else None
        if updated_gte:
            threshold = self._parse_datetime(updated_gte)
            if threshold:
                results = [issue for issue in results if issue.updated >= threshold]

        created_filter = date_filters.get("created") or {}
        created_gte = created_filter.get("gte") if isinstance(created_filter, dict) else None
        if created_gte:
            threshold = self._parse_datetime(created_gte)
            if threshold:
                results = [issue for issue in results if issue.created >= threshold]

        ordered = sorted(results, key=lambda issue: issue.key)
        if not order_by:
            ordered.sort(key=lambda issue: issue.updated, reverse=True)
            return ordered

        for field, direction in reversed(order_by):
            reverse = direction.lower() == "desc"
            ordered.sort(
                key=lambda issue: self._order_key(issue, field),
                reverse=reverse,
            )
        return ordered

    def _order_key(self, issue: Issue, field: str):
        field = field.lower()
        if field == "updated":
            return issue.updated
        if field == "created":
            return issue.created
        if field == "priority":
            return self._priority_sort_value(issue)
        return issue.created

    def _priority_sort_value(self, issue: Issue) -> tuple[int, str]:
        raw = issue.custom_fields.get("priority")
        if isinstance(raw, dict):
            name = raw.get("name", "")
        else:
            name = str(raw or "")
        order = {
            "highest": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "lowest": 4,
        }
        rank = order.get(name.lower(), 5)
        return (rank, name)

    def get_transitions(self, issue: Issue) -> list[Transition]:
        return self.transitions.get(issue.status_id, [])

    def apply_transition(
        self, issue: Issue, transition_id: str, actor_id: str
    ) -> Issue:
        transitions = self.get_transitions(issue)
        for transition in transitions:
            if transition.id == transition_id:
                previous_status = issue.status(self)
                issue.status_id = transition.to_status.id
                now = datetime.now(UTC)
                issue.updated = now
                entry = {
                    "id": str(uuid.uuid4()),
                    "field": "status",
                    "from": previous_status.id,
                    "fromString": previous_status.name,
                    "to": transition.to_status.id,
                    "toString": transition.to_status.name,
                    "created": now.isoformat(),
                    "author": actor_id,
                }
                issue.changelog.append(entry)
                self.dispatch_event(
                    "jira:issue_updated",
                    {"issue": issue.to_api(self)},
                )
                return issue
        raise ValueError("Invalid transition")

    def add_comment(self, issue: Issue, author_id: str, body: Any) -> Comment:
        comment = Comment(
            id=str(self.next_comment_id),
            author_id=author_id,
            body=self.normalize_adf(body),
            created=datetime.now(UTC),
        )
        self.next_comment_id += 1
        issue.comments.append(comment)
        issue.updated = datetime.now(UTC)
        self.dispatch_event(
            "comment_created",
            {"issue": issue.to_api(self), "comment": comment.to_api(self.users[author_id])},
        )
        return comment

    # --------------------------- Agile ---------------------------------
    def list_boards(self) -> list[dict[str, Any]]:
        return [board.to_api() for board in self.boards.values()]

    def list_sprints(self, board_id: int) -> list[dict[str, Any]]:
        return [s.to_api() for s in self.sprints.values() if s.board_id == board_id]

    def create_sprint(self, payload: dict[str, Any]) -> Sprint:
        sprint = Sprint(
            id=self.next_sprint_id,
            board_id=payload.get("originBoardId", 1),
            name=payload.get("name", f"Sprint {self.next_sprint_id}"),
            state=payload.get("state", "future"),
            start_date=self._parse_datetime(payload.get("startDate")),
            end_date=self._parse_datetime(payload.get("endDate")),
            goal=payload.get("goal"),
        )
        self.sprints[sprint.id] = sprint
        self.next_sprint_id += 1
        return sprint

    def backlog_issues(self, board_id: int) -> list[Issue]:
        board = self.boards.get(board_id)
        if not board:
            return []
        project_key = board.project_key
        return [
            issue
            for issue in self.issues.values()
            if issue.project_key == project_key and issue.sprint_id is None
        ]

    # ------------------------ Service Desk -----------------------------
    def list_service_requests(self) -> list[dict[str, Any]]:
        payloads = []
        for req in self.service_requests.values():
            issue = self.issues[req.issue_key]
            payloads.append(req.to_api(issue, self))
        return payloads

    def create_service_request(
        self, payload: dict[str, Any], reporter_id: str
    ) -> ServiceRequest:
        field_values = payload.get("requestFieldValues", {})
        summary = "Support request"
        description = ""
        if isinstance(field_values, list):
            for item in field_values:
                if not isinstance(item, dict):
                    continue
                field_id = item.get("fieldId")
                value = item.get("value")
                if field_id == "summary":
                    summary = value or summary
                elif field_id == "description":
                    description = value or description
        elif isinstance(field_values, dict):
            summary = field_values.get("summary", summary)
            description = field_values.get("description", description)
        issue = self._create_issue(
            project_key="SUP",
            issue_type_id="10003",
            summary=summary,
            description=self.normalize_adf(description),
            reporter_id=reporter_id,
            assignee_id=None,
            status_id="1",
        )
        service_request = self._ensure_service_request(issue)
        self.dispatch_event(
            "jira:issue_created",
            {"issue": issue.to_api(self)},
        )
        return service_request

    def update_service_request(
        self, request_id: str, approval_id: str, approve: bool
    ) -> ServiceRequest:
        request = self.service_requests.get(request_id)
        if not request:
            raise ValueError("Unknown service request")
        decision = "approved" if approve else "declined"
        approval_record = {
            "id": approval_id,
            "decision": decision,
            "decider": self.users[next(iter(self.users))].to_api(),
        }
        request.approvals.append(approval_record)
        issue = self.issues[request.issue_key]
        issue.status_id = "4" if approve else "3"
        issue.updated = datetime.now(UTC)
        self.dispatch_event(
            "jira:issue_updated",
            {"issue": issue.to_api(self)},
        )
        return request

    # -------------------------- Webhooks -------------------------------
    def register_webhook(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        registrations = []
        for body in payload.get("webhooks", []):
            url = body.get("url")
            if not url:
                registrations.append(
                    {"createdWebhookId": None, "failureReason": "Missing url"}
                )
                continue
            webhook_id = str(self.next_webhook_id)
            self.next_webhook_id += 1
            registration = WebhookRegistration(
                id=webhook_id,
                url=url,
                events=body.get("events", []),
                jql=body.get("jqlFilter") or body.get("jql"),
                secret=body.get("secret"),
                active=body.get("active", True),
            )
            self.webhooks[webhook_id] = registration
            registrations.append(
                {"createdWebhookId": webhook_id, "failureReason": None}
            )
        return registrations

    def list_webhooks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": reg.id,
                "url": reg.url,
                "events": reg.events,
                "jql": reg.jql,
                "active": reg.active,
                "hasSecret": bool(reg.secret),
            }
            for reg in self.webhooks.values()
        ]

    def delete_webhook(self, webhook_id: str) -> None:
        self.webhooks.pop(webhook_id, None)

    def dispatch_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        self.deliveries.append(
            {
                "event": event_type,
                "eventId": event_id,
                "payload": payload,
                "timestamp": now.isoformat(),
            }
        )
        for registration in self.webhooks.values():
            if not registration.active or event_type not in registration.events:
                continue
            delivery_id = str(uuid.uuid4())
            record = {
                "id": delivery_id,
                "webhookId": registration.id,
                "event": event_type,
                "eventId": event_id,
                "url": registration.url,
                "payload": payload,
                "timestamp": now.isoformat(),
                "status": "pending",
                "attempts": 0,
            }
            self.deliveries.append(record)
            self._schedule_delivery(
                delivery_id=delivery_id,
                event_type=event_type,
                event_id=event_id,
                url=registration.url,
                secret=registration.secret,
                payload=payload,
                record=record,
                force=False,
            )

    def _remember_delivery_key(self, key: tuple[str, str]) -> None:
        self._recent_delivery_keys.append(key)
        self._recent_delivery_lookup.add(key)
        while len(self._recent_delivery_keys) > self._recent_delivery_window:
            expired = self._recent_delivery_keys.popleft()
            self._recent_delivery_lookup.discard(expired)

    def _schedule_delivery(
        self,
        *,
        delivery_id: str,
        event_type: str,
        event_id: str,
        url: str | None,
        secret: str | None,
        payload: dict[str, Any],
        record: dict[str, Any],
        force: bool,
    ) -> None:
        meta = {
            "delivery_id": delivery_id,
            "event": event_type,
            "event_id": event_id,
            "url": url,
            "secret": secret,
            "payload": payload,
            "record": record,
            "force": force,
        }
        self._delivery_index[delivery_id] = meta
        record["status"] = "pending"
        record["attempts"] = 0
        record.pop("completedAt", None)
        webhook_id = record.get("webhookId")
        if webhook_id:
            key = (str(webhook_id), event_id)
            if not force and key in self._recent_delivery_lookup:
                record["status"] = "duplicate"
                record["completedAt"] = datetime.now(UTC).isoformat()
                logger.info(
                    "Skip duplicate webhook delivery id=%s event=%s event_id=%s",
                    delivery_id,
                    event_type,
                    event_id,
                )
                return
            self._remember_delivery_key(key)
        logger.info(
            "Queue webhook delivery id=%s event=%s event_id=%s url=%s",
            delivery_id,
            event_type,
            event_id,
            url,
        )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._deliver_webhook(meta))
        else:
            loop.create_task(self._deliver_webhook(meta))

    async def _deliver_webhook(self, meta: dict[str, Any]) -> None:
        record = meta["record"]
        url = meta["url"]
        if not url:
            record["status"] = "skipped"
            return
        payload = meta["payload"]
        secret = meta["secret"]
        event_type = meta["event"]
        event_id = meta["event_id"]
        jitter = random.uniform(*self._webhook_jitter_ms) / 1000
        await asyncio.sleep(jitter)
        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "X-MockJira-Event-Id": event_id,
            "X-MockJira-Event-Type": event_type.split(":", 1)[-1],
        }
        if secret:
            digest = hashlib.sha256(secret.encode() + body).hexdigest()
            headers["X-MockJira-Signature"] = f"sha256={digest}"

        delays = [0.5, 1.0, 2.0]
        attempts = 0
        status = "failed"
        last_status: int | None = None
        for idx in range(len(delays) + 1):
            attempts = idx + 1
            record["attempts"] = attempts
            try:
                if random.random() < self._webhook_poison_prob:
                    raise httpx.HTTPError("Injected failure")
                async with httpx.AsyncClient(timeout=1.5) as client:
                    response = await client.post(url, content=body, headers=headers)
                last_status = response.status_code
                record["lastStatus"] = last_status
                if 500 <= response.status_code < 600:
                    raise httpx.HTTPError("Server error")
                status = "delivered" if response.status_code < 400 else "failed"
                break
            except httpx.HTTPError:
                status = "retrying" if idx < len(delays) else "failed"
                if idx >= len(delays):
                    break
                await asyncio.sleep(delays[idx])
        record["status"] = status
        record["completedAt"] = datetime.now(UTC).isoformat()
        if last_status is not None:
            record["lastStatus"] = last_status
        logger.info(
            "Webhook delivery id=%s event_id=%s attempts=%s status=%s",
            meta["delivery_id"],
            event_id,
            attempts,
            status,
        )

    def replay_delivery(self, delivery_id: str) -> dict[str, Any]:
        meta = self._delivery_index.get(delivery_id)
        if not meta:
            raise ValueError("Unknown delivery id")
        record = meta["record"]
        record["timestamp"] = datetime.now(UTC).isoformat()
        self._schedule_delivery(
            delivery_id=delivery_id,
            event_type=meta["event"],
            event_id=meta["event_id"],
            url=meta["url"],
            secret=meta["secret"],
            payload=meta["payload"],
            record=record,
            force=True,
        )
        return record

    def update_webhook_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        if "poison_prob" in settings:
            try:
                self._webhook_poison_prob = max(0.0, float(settings["poison_prob"]))
            except (TypeError, ValueError):
                pass
        jitter = settings.get("jitter_ms")
        if isinstance(jitter, (list, tuple)) and len(jitter) == 2:
            try:
                low = int(jitter[0])
                high = int(jitter[1])
            except (TypeError, ValueError):
                low, high = self._webhook_jitter_ms
            else:
                if low > high:
                    low, high = high, low
                self._webhook_jitter_ms = (low, high)
        return {
            "poison_prob": self._webhook_poison_prob,
            "jitter_ms": list(self._webhook_jitter_ms),
        }

    # ------------------------ Utilities --------------------------------
    def export_seed(self) -> dict[str, Any]:
        return {
            "users": [asdict(user) for user in self.users.values()],
            "projects": [asdict(project) for project in self.projects.values()],
            "issue_types": [asdict(it) for it in self.issue_types.values()],
            "issues": [self._issue_to_seed(issue) for issue in self.issues.values()],
        }

    def import_seed(self, payload: dict[str, Any]) -> None:
        self.users = {
            item["account_id"]: User(**item)
            for item in payload.get("users", [])
        }
        self.projects = {
            item["key"]: Project(**item)
            for item in payload.get("projects", [])
        }
        self.issue_types = {
            item["id"]: IssueType(**item)
            for item in payload.get("issue_types", [])
        }
        self.issues = {}
        self.issue_counter = defaultdict(int)
        self.next_issue_id = 10000
        self.next_comment_id = 20000
        for item in payload.get("issues", []):
            issue = self._issue_from_seed(item)
            self.issues[issue.key] = issue
            try:
                seq = int(issue.key.split("-", 1)[1])
            except (IndexError, ValueError):
                seq = 0
            self.issue_counter[issue.project_key] = max(
                self.issue_counter[issue.project_key], seq
            )
            self.next_issue_id = max(self.next_issue_id, int(issue.id) + 1)
            if issue.comments:
                last_comment_id = max(int(c.id) for c in issue.comments)
                self.next_comment_id = max(self.next_comment_id, last_comment_id + 1)

    def normalize_adf(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict) and value.get("type") == "doc":
            return value
        if isinstance(value, str):
            return self._adf(value)
        raise ValueError("Unsupported ADF payload")

    def _issue_to_seed(self, issue: Issue) -> dict[str, Any]:
        payload = asdict(issue)
        payload["created"] = issue.created.isoformat()
        payload["updated"] = issue.updated.isoformat()
        payload["comments"] = [
            {
                **asdict(comment),
                "created": comment.created.isoformat(),
            }
            for comment in issue.comments
        ]
        return payload

    def _issue_from_seed(self, payload: dict[str, Any]) -> Issue:
        comments = [
            Comment(
                id=str(comment["id"]),
                author_id=comment.get("author_id") or comment.get("authorId"),
                body=comment.get("body", {}),
                created=self._parse_datetime(comment.get("created"))
                or datetime.now(UTC),
            )
            for comment in payload.get("comments", [])
        ]
        issue = Issue(
            id=str(payload["id"]),
            key=payload["key"],
            project_key=payload.get("project_key", payload.get("projectKey")),
            issue_type_id=payload.get("issue_type_id", payload.get("issueTypeId", "10001")),
            summary=payload.get("summary", "Imported issue"),
            description=payload.get("description", self._adf("")),
            status_id=payload.get("status_id", "1"),
            reporter_id=payload.get("reporter_id"),
            assignee_id=payload.get("assignee_id"),
            labels=payload.get("labels", []),
            created=self._parse_datetime(payload.get("created")) or datetime.now(UTC),
            updated=self._parse_datetime(payload.get("updated")) or datetime.now(UTC),
            sprint_id=payload.get("sprint_id"),
            comments=comments,
            custom_fields=payload.get("custom_fields", {}),
            links=payload.get("links", []),
            changelog=payload.get("changelog", []),
        )
        return issue

    def _ensure_service_request(self, issue: Issue) -> ServiceRequest:
        request_id = str(self.next_request_id)
        self.next_request_id += 1
        service_request = ServiceRequest(
            id=request_id,
            issue_key=issue.key,
            request_type_id="100",
        )
        self.service_requests[request_id] = service_request
        return service_request

    def _parse_datetime(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        try:
            raw = str(value).strip()
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            parsed = datetime.fromisoformat(raw)
        except Exception:  # pragma: no cover - invalid date fallback
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
