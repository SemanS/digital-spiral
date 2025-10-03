"""Jira webhook handlers."""

from __future__ import annotations

import hashlib
import hmac
import logging
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Jira webhook event types."""

    # Issue events
    ISSUE_CREATED = "jira:issue_created"
    ISSUE_UPDATED = "jira:issue_updated"
    ISSUE_DELETED = "jira:issue_deleted"

    # Comment events
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"

    # Project events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # User events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

    # Sprint events
    SPRINT_CREATED = "sprint_created"
    SPRINT_UPDATED = "sprint_updated"
    SPRINT_DELETED = "sprint_deleted"
    SPRINT_STARTED = "sprint_started"
    SPRINT_CLOSED = "sprint_closed"

    # Version events
    VERSION_CREATED = "jira:version_created"
    VERSION_UPDATED = "jira:version_updated"
    VERSION_DELETED = "jira:version_deleted"
    VERSION_RELEASED = "jira:version_released"
    VERSION_UNRELEASED = "jira:version_unreleased"


class WebhookVerificationError(Exception):
    """Webhook verification failed."""
    pass


class JiraWebhookHandler:
    """
    Handler for Jira webhooks.
    
    Processes incoming webhook events from Jira and routes them
    to appropriate handlers.
    """

    def __init__(self, secret: str | None = None):
        """
        Initialize webhook handler.

        Args:
            secret: Webhook secret for signature verification
        """
        self.secret = secret
        self.handlers: dict[WebhookEventType, list[Callable]] = {}

    def register_handler(
        self,
        event_type: WebhookEventType,
        handler: Callable[[dict], Any],
    ):
        """
        Register a handler for a specific event type.

        Args:
            event_type: Event type to handle
            handler: Handler function (async or sync)
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Signature from X-Hub-Signature header

        Returns:
            True if signature is valid

        Raises:
            WebhookVerificationError: If verification fails
        """
        if not self.secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True

        # Jira uses HMAC-SHA256
        expected_signature = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Signature format: "sha256=<hash>"
        if signature.startswith("sha256="):
            signature = signature[7:]

        if not hmac.compare_digest(expected_signature, signature):
            raise WebhookVerificationError("Invalid webhook signature")

        return True

    async def handle_webhook(
        self,
        payload: dict,
        signature: str | None = None,
        raw_payload: bytes | None = None,
    ) -> dict[str, Any]:
        """
        Handle incoming webhook.

        Args:
            payload: Webhook payload (parsed JSON)
            signature: Webhook signature (optional)
            raw_payload: Raw payload bytes for signature verification

        Returns:
            Processing result

        Raises:
            WebhookVerificationError: If signature verification fails
        """
        # Verify signature if provided
        if signature and raw_payload:
            self.verify_signature(raw_payload, signature)

        # Extract event type
        webhook_event = payload.get("webhookEvent")
        if not webhook_event:
            logger.warning("No webhookEvent in payload")
            return {"status": "error", "message": "Missing webhookEvent"}

        try:
            event_type = WebhookEventType(webhook_event)
        except ValueError:
            logger.warning(f"Unknown webhook event: {webhook_event}")
            return {"status": "ignored", "message": f"Unknown event: {webhook_event}"}

        # Get handlers for this event type
        handlers = self.handlers.get(event_type, [])
        if not handlers:
            logger.info(f"No handlers registered for {event_type}")
            return {"status": "ignored", "message": f"No handlers for {event_type}"}

        # Execute handlers
        results = []
        for handler in handlers:
            try:
                # Check if handler is async
                if hasattr(handler, "__call__"):
                    import inspect
                    if inspect.iscoroutinefunction(handler):
                        result = await handler(payload)
                    else:
                        result = handler(payload)
                    results.append(result)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}", exc_info=True)
                results.append({"error": str(e)})

        return {
            "status": "success",
            "event_type": event_type,
            "handlers_executed": len(handlers),
            "results": results,
        }

    def extract_issue_data(self, payload: dict) -> dict | None:
        """
        Extract issue data from webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            Issue data or None
        """
        return payload.get("issue")

    def extract_comment_data(self, payload: dict) -> dict | None:
        """
        Extract comment data from webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            Comment data or None
        """
        return payload.get("comment")

    def extract_project_data(self, payload: dict) -> dict | None:
        """
        Extract project data from webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            Project data or None
        """
        return payload.get("project")

    def extract_user_data(self, payload: dict) -> dict | None:
        """
        Extract user data from webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            User data or None
        """
        return payload.get("user")

    def extract_changelog(self, payload: dict) -> dict | None:
        """
        Extract changelog from webhook payload.

        Args:
            payload: Webhook payload

        Returns:
            Changelog data or None
        """
        return payload.get("changelog")


# Example handler functions
async def handle_issue_created(payload: dict):
    """
    Example handler for issue created event.

    Args:
        payload: Webhook payload
    """
    issue = payload.get("issue", {})
    issue_key = issue.get("key")
    
    logger.info(f"Issue created: {issue_key}")
    
    # TODO: Process issue creation
    # - Map Jira data to domain entity
    # - Save to database
    # - Trigger notifications
    
    return {"issue_key": issue_key, "action": "created"}


async def handle_issue_updated(payload: dict):
    """
    Example handler for issue updated event.

    Args:
        payload: Webhook payload
    """
    issue = payload.get("issue", {})
    issue_key = issue.get("key")
    changelog = payload.get("changelog", {})
    
    logger.info(f"Issue updated: {issue_key}")
    
    # TODO: Process issue update
    # - Map Jira data to domain entity
    # - Update in database
    # - Process changelog
    # - Trigger notifications
    
    return {
        "issue_key": issue_key,
        "action": "updated",
        "changes": len(changelog.get("items", [])),
    }


async def handle_comment_created(payload: dict):
    """
    Example handler for comment created event.

    Args:
        payload: Webhook payload
    """
    comment = payload.get("comment", {})
    comment_id = comment.get("id")
    issue = payload.get("issue", {})
    issue_key = issue.get("key")
    
    logger.info(f"Comment created on {issue_key}: {comment_id}")
    
    # TODO: Process comment creation
    # - Map Jira data to domain entity
    # - Save to database
    # - Trigger notifications
    
    return {
        "issue_key": issue_key,
        "comment_id": comment_id,
        "action": "created",
    }


__all__ = [
    "JiraWebhookHandler",
    "WebhookEventType",
    "WebhookVerificationError",
    "handle_issue_created",
    "handle_issue_updated",
    "handle_comment_created",
]

