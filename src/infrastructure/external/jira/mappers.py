"""Mappers for converting Jira API responses to domain entities."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.domain.entities import Changelog, Comment, Issue, Project, User

logger = logging.getLogger(__name__)


def parse_datetime(date_str: str | None) -> datetime | None:
    """
    Parse Jira datetime string to datetime object.

    Args:
        date_str: Jira datetime string (ISO format)

    Returns:
        Datetime object or None
    """
    if not date_str:
        return None

    try:
        # Jira uses ISO 8601 format
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse datetime: {date_str} - {e}")
        return None


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested value from dict.

    Args:
        data: Dictionary to search
        *keys: Keys to traverse
        default: Default value if not found

    Returns:
        Value or default
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


class JiraIssueMapper:
    """Mapper for Jira issue data."""

    @staticmethod
    def to_entity(jira_data: dict, instance_id: UUID) -> Issue:
        """
        Convert Jira API issue response to Issue entity.

        Args:
            jira_data: Jira issue JSON
            instance_id: Jira instance ID

        Returns:
            Issue entity
        """
        fields = jira_data.get("fields", {})

        # Extract basic fields
        issue_key = jira_data.get("key", "")
        issue_id = jira_data.get("id", "")
        summary = safe_get(fields, "summary", default="")
        description = safe_get(fields, "description", default="")

        # Extract type and status
        issue_type = safe_get(fields, "issuetype", "name", default="Task")
        status = safe_get(fields, "status", "name", default="To Do")
        status_category = safe_get(fields, "status", "statusCategory", "name")
        priority = safe_get(fields, "priority", "name", default="Medium")

        # Extract assignment
        assignee_account_id = safe_get(fields, "assignee", "accountId")
        reporter_account_id = safe_get(fields, "reporter", "accountId")

        # Extract project
        project_key = safe_get(fields, "project", "key", default="")
        project_id = safe_get(fields, "project", "id")

        # Extract parent (for subtasks)
        parent_key = safe_get(fields, "parent", "key")

        # Extract labels and components
        labels = [label for label in safe_get(fields, "labels", default=[])]
        components = [
            comp.get("name", "")
            for comp in safe_get(fields, "components", default=[])
        ]

        # Extract timestamps
        created_at = parse_datetime(safe_get(fields, "created"))
        updated_at = parse_datetime(safe_get(fields, "updated"))
        resolved_at = parse_datetime(safe_get(fields, "resolutiondate"))

        # Extract custom fields
        custom_fields = {}
        for key, value in fields.items():
            if key.startswith("customfield_"):
                custom_fields[key] = value

        # Create entity
        return Issue(
            id=uuid4(),  # Generate new UUID for our database
            instance_id=instance_id,
            issue_key=issue_key,
            issue_id=issue_id,
            summary=summary,
            description=description,
            issue_type=issue_type,
            status=status,
            priority=priority,
            assignee_account_id=assignee_account_id,
            reporter_account_id=reporter_account_id,
            project_key=project_key,
            parent_key=parent_key,
            labels=labels,
            components=components,
            created_at=created_at,
            updated_at=updated_at,
            resolved_at=resolved_at,
            custom_fields=custom_fields,
            raw_data=jira_data,
        )


class JiraProjectMapper:
    """Mapper for Jira project data."""

    @staticmethod
    def to_entity(jira_data: dict, instance_id: UUID) -> Project:
        """
        Convert Jira API project response to Project entity.

        Args:
            jira_data: Jira project JSON
            instance_id: Jira instance ID

        Returns:
            Project entity
        """
        project_key = jira_data.get("key", "")
        project_id = jira_data.get("id", "")
        name = jira_data.get("name", "")
        description = jira_data.get("description", "")
        project_type = jira_data.get("projectTypeKey", "software")

        # Extract lead
        lead_account_id = safe_get(jira_data, "lead", "accountId")

        # Extract URLs
        avatar_url = safe_get(jira_data, "avatarUrls", "48x48")
        url = jira_data.get("self", "")

        # Extract status
        is_archived = jira_data.get("archived", False)
        is_private = jira_data.get("isPrivate", False)

        return Project(
            id=uuid4(),
            instance_id=instance_id,
            project_key=project_key,
            project_id=project_id,
            name=name,
            description=description,
            project_type=project_type,
            lead_account_id=lead_account_id,
            avatar_url=avatar_url,
            url=url,
            is_archived=is_archived,
            is_private=is_private,
            raw_data=jira_data,
        )


class JiraUserMapper:
    """Mapper for Jira user data."""

    @staticmethod
    def to_entity(jira_data: dict, instance_id: UUID) -> User:
        """
        Convert Jira API user response to User entity.

        Args:
            jira_data: Jira user JSON
            instance_id: Jira instance ID

        Returns:
            User entity
        """
        account_id = jira_data.get("accountId", "")
        account_type = jira_data.get("accountType", "atlassian")
        display_name = jira_data.get("displayName", "")
        email_address = jira_data.get("emailAddress")
        avatar_url = safe_get(jira_data, "avatarUrls", "48x48")
        is_active = jira_data.get("active", True)

        return User(
            id=uuid4(),
            instance_id=instance_id,
            account_id=account_id,
            account_type=account_type,
            display_name=display_name,
            email_address=email_address,
            avatar_url=avatar_url,
            is_active=is_active,
            raw_data=jira_data,
        )


class JiraCommentMapper:
    """Mapper for Jira comment data."""

    @staticmethod
    def to_entity(jira_data: dict, instance_id: UUID, issue_key: str) -> Comment:
        """
        Convert Jira API comment response to Comment entity.

        Args:
            jira_data: Jira comment JSON
            instance_id: Jira instance ID
            issue_key: Issue key

        Returns:
            Comment entity
        """
        comment_id = jira_data.get("id", "")
        
        # Extract body (can be plain text or ADF)
        body = ""
        body_format = "plain"
        
        if "body" in jira_data:
            body_data = jira_data["body"]
            if isinstance(body_data, str):
                body = body_data
                body_format = "plain"
            elif isinstance(body_data, dict):
                # ADF (Atlassian Document Format)
                body = str(body_data)  # Store as JSON string
                body_format = "adf"

        # Extract author
        author_account_id = safe_get(jira_data, "author", "accountId", default="")

        # Extract visibility
        visibility = jira_data.get("visibility", {})
        is_public = not bool(visibility)
        visibility_type = visibility.get("type")
        visibility_value = visibility.get("value")

        # Extract timestamps
        created_at = parse_datetime(jira_data.get("created"))
        updated_at = parse_datetime(jira_data.get("updated"))

        return Comment(
            id=uuid4(),
            instance_id=instance_id,
            comment_id=comment_id,
            issue_key=issue_key,
            body=body,
            body_format=body_format,
            author_account_id=author_account_id,
            is_public=is_public,
            visibility_type=visibility_type,
            visibility_value=visibility_value,
            created_at=created_at,
            updated_at=updated_at,
            raw_data=jira_data,
        )


class JiraChangelogMapper:
    """Mapper for Jira changelog data."""

    @staticmethod
    def to_entity(
        jira_data: dict,
        instance_id: UUID,
        issue_key: str,
    ) -> Changelog:
        """
        Convert Jira API changelog response to Changelog entity.

        Args:
            jira_data: Jira changelog JSON
            instance_id: Jira instance ID
            issue_key: Issue key

        Returns:
            Changelog entity
        """
        changelog_id = jira_data.get("id", "")
        
        # Extract author
        author_account_id = safe_get(jira_data, "author", "accountId", default="")

        # Extract items (changes)
        items = []
        for item in jira_data.get("items", []):
            items.append({
                "field": item.get("field", ""),
                "fieldtype": item.get("fieldtype", ""),
                "from": item.get("from"),
                "fromString": item.get("fromString"),
                "to": item.get("to"),
                "toString": item.get("toString"),
            })

        # Extract timestamp
        created_at = parse_datetime(jira_data.get("created"))

        return Changelog(
            id=uuid4(),
            instance_id=instance_id,
            changelog_id=changelog_id,
            issue_key=issue_key,
            author_account_id=author_account_id,
            items=items,
            created_at=created_at,
            raw_data=jira_data,
        )


__all__ = [
    "JiraIssueMapper",
    "JiraProjectMapper",
    "JiraUserMapper",
    "JiraCommentMapper",
    "JiraChangelogMapper",
    "parse_datetime",
    "safe_get",
]

