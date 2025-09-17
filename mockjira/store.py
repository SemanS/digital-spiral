"""In-memory persistence layer for the mock Jira server."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
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

    def to_api(self, store: "InMemoryStore") -> dict[str, Any]:
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
        return {
            "id": self.id,
            "key": self.key,
            "fields": fields,
        }


@dataclass
class WebhookRegistration:
    id: str
    url: str
    events: list[str]
    jql: str | None


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
        self.tokens: dict[str, str] = {}
        self.rate_calls: dict[str, deque[tuple[datetime, int]]] = defaultdict(deque)
        self.next_issue_id = 10000
        self.next_comment_id = 20000
        self.next_request_id = 30000
        self.next_webhook_id = 40000
        self.next_sprint_id = 5000

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
        issue = self._create_issue(
            project_key=project_key,
            issue_type_id=issue_type_id,
            summary=summary,
            description=description,
            reporter_id=reporter_id,
            assignee_id=assignee_id,
            status_id="1",
            labels=labels,
        )
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
        issue.updated = datetime.now(UTC)
        self.dispatch_event(
            "jira:issue_updated",
            {"issue": issue.to_api(self)},
        )
        return issue

    def search_issues(self, filters: dict[str, Any]) -> list[Issue]:
        results = list(self.issues.values())
        project = filters.get("project")
        if project:
            if isinstance(project, list):
                allowed = set(project)
            else:
                allowed = {project}
            results = [i for i in results if i.project_key in allowed]
        status = filters.get("status")
        if status:
            if isinstance(status, str):
                status_values = {status.lower()}
            else:
                status_values = {s.lower() for s in status}
            results = [
                i
                for i in results
                if i.status(self).name.lower() in status_values
            ]
        assignee = filters.get("assignee")
        if assignee:
            if isinstance(assignee, str):
                values = {assignee.lower()}
            else:
                values = {a.lower() for a in assignee}
            results = [
                i
                for i in results
                if (i.assignee_id or "unassigned").lower() in values
            ]
        return sorted(results, key=lambda i: i.created)

    def get_transitions(self, issue: Issue) -> list[Transition]:
        return self.transitions.get(issue.status_id, [])

    def apply_transition(self, issue: Issue, transition_id: str) -> Issue:
        transitions = self.get_transitions(issue)
        for transition in transitions:
            if transition.id == transition_id:
                issue.status_id = transition.to_status.id
                issue.updated = datetime.now(UTC)
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
        summary = field_values.get("summary", "Support request")
        description = field_values.get("description", "")
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
            webhook_id = str(self.next_webhook_id)
            self.next_webhook_id += 1
            registration = WebhookRegistration(
                id=webhook_id,
                url=body.get("url"),
                events=body.get("events", []),
                jql=body.get("jql"),
            )
            self.webhooks[webhook_id] = registration
            registrations.append(
                {"createdWebhookId": webhook_id, "failureReason": None}
            )
        return registrations

    def list_webhooks(self) -> list[dict[str, Any]]:
        return [
            {"id": reg.id, "url": reg.url, "events": reg.events, "jql": reg.jql}
            for reg in self.webhooks.values()
        ]

    def delete_webhook(self, webhook_id: str) -> None:
        self.webhooks.pop(webhook_id, None)

    def dispatch_event(self, event_type: str, payload: dict[str, Any]) -> None:
        delivery = {
            "event": event_type,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.deliveries.append(delivery)
        for registration in self.webhooks.values():
            if event_type not in registration.events:
                continue
            self._send_webhook(registration.url, delivery)

    def _send_webhook(self, url: str | None, delivery: dict[str, Any]) -> None:
        if not url:
            return
        try:
            with httpx.Client(timeout=0.5) as client:
                client.post(url, json=delivery)
        except httpx.HTTPError:
            # Fail silently; this is a mock server.
            pass

    # ------------------------ Utilities --------------------------------
    def normalize_adf(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict) and value.get("type") == "doc":
            return value
        if isinstance(value, str):
            return self._adf(value)
        raise ValueError("Unsupported ADF payload")

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
            return value
        try:
            return datetime.fromisoformat(value)
        except Exception:  # pragma: no cover - invalid date fallback
            return None
