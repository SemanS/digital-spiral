"""Unit tests for Jira webhook handlers."""

from __future__ import annotations

import hashlib
import hmac

import pytest

from src.infrastructure.external.jira.webhooks import (
    JiraWebhookHandler,
    WebhookEventType,
    WebhookVerificationError,
)


class TestJiraWebhookHandler:
    """Tests for JiraWebhookHandler."""

    @pytest.fixture
    def handler(self):
        """Create webhook handler."""
        return JiraWebhookHandler(secret="test-secret")

    @pytest.fixture
    def handler_no_secret(self):
        """Create webhook handler without secret."""
        return JiraWebhookHandler()

    @pytest.fixture
    def issue_created_payload(self):
        """Sample issue created webhook payload."""
        return {
            "webhookEvent": "jira:issue_created",
            "issue": {
                "id": "10001",
                "key": "PROJ-123",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "To Do"},
                }
            }
        }

    @pytest.fixture
    def issue_updated_payload(self):
        """Sample issue updated webhook payload."""
        return {
            "webhookEvent": "jira:issue_updated",
            "issue": {
                "id": "10001",
                "key": "PROJ-123",
                "fields": {
                    "summary": "Updated issue",
                    "status": {"name": "In Progress"},
                }
            },
            "changelog": {
                "items": [
                    {
                        "field": "status",
                        "fromString": "To Do",
                        "toString": "In Progress"
                    }
                ]
            }
        }

    def test_register_handler(self, handler):
        """Test registering a handler."""
        def test_handler(payload):
            return {"processed": True}

        handler.register_handler(WebhookEventType.ISSUE_CREATED, test_handler)

        assert WebhookEventType.ISSUE_CREATED in handler.handlers
        assert len(handler.handlers[WebhookEventType.ISSUE_CREATED]) == 1

    def test_register_multiple_handlers(self, handler):
        """Test registering multiple handlers for same event."""
        def handler1(payload):
            return {"handler": 1}

        def handler2(payload):
            return {"handler": 2}

        handler.register_handler(WebhookEventType.ISSUE_CREATED, handler1)
        handler.register_handler(WebhookEventType.ISSUE_CREATED, handler2)

        assert len(handler.handlers[WebhookEventType.ISSUE_CREATED]) == 2

    def test_verify_signature_valid(self, handler):
        """Test signature verification with valid signature."""
        payload = b'{"test": "data"}'
        
        # Generate valid signature
        signature = hmac.new(
            b"test-secret",
            payload,
            hashlib.sha256
        ).hexdigest()

        result = handler.verify_signature(payload, f"sha256={signature}")
        assert result is True

    def test_verify_signature_invalid(self, handler):
        """Test signature verification with invalid signature."""
        payload = b'{"test": "data"}'
        invalid_signature = "sha256=invalid"

        with pytest.raises(WebhookVerificationError):
            handler.verify_signature(payload, invalid_signature)

    def test_verify_signature_no_secret(self, handler_no_secret):
        """Test signature verification without secret."""
        payload = b'{"test": "data"}'
        signature = "sha256=anything"

        # Should pass without verification
        result = handler_no_secret.verify_signature(payload, signature)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_webhook_issue_created(self, handler, issue_created_payload):
        """Test handling issue created webhook."""
        # Register handler
        async def test_handler(payload):
            return {"processed": True, "issue_key": payload["issue"]["key"]}

        handler.register_handler(WebhookEventType.ISSUE_CREATED, test_handler)

        # Handle webhook
        result = await handler.handle_webhook(issue_created_payload)

        assert result["status"] == "success"
        assert result["event_type"] == WebhookEventType.ISSUE_CREATED
        assert result["handlers_executed"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["issue_key"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_handle_webhook_no_handlers(self, handler, issue_created_payload):
        """Test handling webhook with no registered handlers."""
        result = await handler.handle_webhook(issue_created_payload)

        assert result["status"] == "ignored"
        assert "No handlers" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_webhook_unknown_event(self, handler):
        """Test handling webhook with unknown event type."""
        payload = {
            "webhookEvent": "unknown:event",
            "data": {}
        }

        result = await handler.handle_webhook(payload)

        assert result["status"] == "ignored"
        assert "Unknown event" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_webhook_missing_event(self, handler):
        """Test handling webhook with missing event type."""
        payload = {"data": {}}

        result = await handler.handle_webhook(payload)

        assert result["status"] == "error"
        assert "Missing webhookEvent" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_webhook_handler_error(self, handler, issue_created_payload):
        """Test handling webhook when handler raises error."""
        # Register handler that raises error
        async def error_handler(payload):
            raise ValueError("Test error")

        handler.register_handler(WebhookEventType.ISSUE_CREATED, error_handler)

        # Should not raise, but return error in results
        result = await handler.handle_webhook(issue_created_payload)

        assert result["status"] == "success"
        assert len(result["results"]) == 1
        assert "error" in result["results"][0]

    @pytest.mark.asyncio
    async def test_handle_webhook_with_signature(self, handler, issue_created_payload):
        """Test handling webhook with signature verification."""
        import json
        
        raw_payload = json.dumps(issue_created_payload).encode()
        
        # Generate valid signature
        signature = hmac.new(
            b"test-secret",
            raw_payload,
            hashlib.sha256
        ).hexdigest()

        # Register handler
        async def test_handler(payload):
            return {"processed": True}

        handler.register_handler(WebhookEventType.ISSUE_CREATED, test_handler)

        # Handle webhook with signature
        result = await handler.handle_webhook(
            issue_created_payload,
            signature=f"sha256={signature}",
            raw_payload=raw_payload
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_signature(self, handler, issue_created_payload):
        """Test handling webhook with invalid signature."""
        import json
        
        raw_payload = json.dumps(issue_created_payload).encode()
        invalid_signature = "sha256=invalid"

        with pytest.raises(WebhookVerificationError):
            await handler.handle_webhook(
                issue_created_payload,
                signature=invalid_signature,
                raw_payload=raw_payload
            )

    def test_extract_issue_data(self, handler, issue_created_payload):
        """Test extracting issue data from payload."""
        issue = handler.extract_issue_data(issue_created_payload)

        assert issue is not None
        assert issue["key"] == "PROJ-123"

    def test_extract_comment_data(self, handler):
        """Test extracting comment data from payload."""
        payload = {
            "webhookEvent": "comment_created",
            "comment": {
                "id": "10001",
                "body": "Test comment"
            }
        }

        comment = handler.extract_comment_data(payload)

        assert comment is not None
        assert comment["id"] == "10001"

    def test_extract_changelog(self, handler, issue_updated_payload):
        """Test extracting changelog from payload."""
        changelog = handler.extract_changelog(issue_updated_payload)

        assert changelog is not None
        assert len(changelog["items"]) == 1
        assert changelog["items"][0]["field"] == "status"

    @pytest.mark.asyncio
    async def test_sync_handler(self, handler, issue_created_payload):
        """Test handling webhook with synchronous handler."""
        # Register sync handler
        def sync_handler(payload):
            return {"sync": True, "issue_key": payload["issue"]["key"]}

        handler.register_handler(WebhookEventType.ISSUE_CREATED, sync_handler)

        # Handle webhook
        result = await handler.handle_webhook(issue_created_payload)

        assert result["status"] == "success"
        assert result["results"][0]["sync"] is True
        assert result["results"][0]["issue_key"] == "PROJ-123"

