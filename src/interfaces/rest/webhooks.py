"""Webhook REST API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from src.infrastructure.external.jira.webhooks import (
    JiraWebhookHandler,
    WebhookEventType,
    WebhookVerificationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize webhook handler
# TODO: Load secret from config
webhook_handler = JiraWebhookHandler(secret=None)


@router.post("/jira")
async def jira_webhook(
    request: Request,
    x_hub_signature: str | None = Header(None, alias="X-Hub-Signature"),
) -> dict[str, Any]:
    """
    Handle incoming Jira webhook.

    Args:
        request: FastAPI request
        x_hub_signature: Webhook signature header

    Returns:
        Processing result

    Raises:
        HTTPException: On verification or processing errors
    """
    try:
        # Get raw body for signature verification
        raw_body = await request.body()
        
        # Parse JSON payload
        payload = await request.json()
        
        # Log webhook event
        webhook_event = payload.get("webhookEvent", "unknown")
        logger.info(f"Received Jira webhook: {webhook_event}")
        
        # Handle webhook
        result = await webhook_handler.handle_webhook(
            payload=payload,
            signature=x_hub_signature,
            raw_payload=raw_body,
        )
        
        return result
        
    except WebhookVerificationError as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )


@router.get("/jira/health")
async def webhook_health() -> dict[str, str]:
    """
    Health check endpoint for webhook service.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "jira-webhooks"}


# Register example handlers
# TODO: Replace with actual handlers from application layer

async def log_issue_event(payload: dict):
    """Log issue events."""
    issue = payload.get("issue", {})
    issue_key = issue.get("key", "unknown")
    event = payload.get("webhookEvent", "unknown")
    logger.info(f"Issue event: {event} - {issue_key}")
    return {"logged": True}


async def log_comment_event(payload: dict):
    """Log comment events."""
    comment = payload.get("comment", {})
    comment_id = comment.get("id", "unknown")
    event = payload.get("webhookEvent", "unknown")
    logger.info(f"Comment event: {event} - {comment_id}")
    return {"logged": True}


# Register handlers
webhook_handler.register_handler(WebhookEventType.ISSUE_CREATED, log_issue_event)
webhook_handler.register_handler(WebhookEventType.ISSUE_UPDATED, log_issue_event)
webhook_handler.register_handler(WebhookEventType.ISSUE_DELETED, log_issue_event)
webhook_handler.register_handler(WebhookEventType.COMMENT_CREATED, log_comment_event)
webhook_handler.register_handler(WebhookEventType.COMMENT_UPDATED, log_comment_event)
webhook_handler.register_handler(WebhookEventType.COMMENT_DELETED, log_comment_event)


__all__ = ["router", "webhook_handler"]

