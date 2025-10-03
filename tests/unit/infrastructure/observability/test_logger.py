"""Unit tests for logger."""

from __future__ import annotations

import logging

import pytest

from src.infrastructure.observability.logger import (
    LoggerAdapter,
    configure_logging,
    get_logger,
    redact_sensitive_data,
)


class TestLogger:
    """Tests for logger configuration."""

    def test_configure_logging_json(self):
        """Test configuring logging with JSON format."""
        configure_logging(level=logging.INFO, format_type="json")

        # Check root logger level
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_configure_logging_text(self):
        """Test configuring logging with text format."""
        configure_logging(level=logging.DEBUG, format_type="text")

        # Check root logger level
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_logger_adapter(self):
        """Test logger adapter with context."""
        configure_logging(level=logging.INFO, format_type="text")

        logger = get_logger(__name__)
        context_logger = LoggerAdapter(
            logger,
            {
                "request_id": "req-123",
                "tenant_id": "tenant-456",
            },
        )

        # Just verify that the adapter can log without errors
        context_logger.info("Test message")
        # The actual logging is tested by the fact that no exception is raised

    def test_redact_sensitive_data(self):
        """Test redacting sensitive data."""
        data = {
            "username": "john",
            "password": "secret123",
            "api_key": "key123",
            "email": "john@example.com",
        }

        redacted = redact_sensitive_data(data)

        assert redacted["username"] == "john"
        assert redacted["password"] == "***REDACTED***"
        assert redacted["api_key"] == "***REDACTED***"
        assert redacted["email"] == "john@example.com"

    def test_redact_nested_data(self):
        """Test redacting nested sensitive data."""
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "password": "secret",
                    "token": "abc123",
                },
            },
            "settings": {
                "theme": "dark",
            },
        }

        redacted = redact_sensitive_data(data)

        assert redacted["user"]["name"] == "John"
        assert redacted["user"]["credentials"]["password"] == "***REDACTED***"
        assert redacted["user"]["credentials"]["token"] == "***REDACTED***"
        assert redacted["settings"]["theme"] == "dark"

    def test_redact_list_data(self):
        """Test redacting sensitive data in lists."""
        data = {
            "users": [
                {"name": "Alice", "password": "secret1"},
                {"name": "Bob", "password": "secret2"},
            ]
        }

        redacted = redact_sensitive_data(data)

        assert redacted["users"][0]["name"] == "Alice"
        assert redacted["users"][0]["password"] == "***REDACTED***"
        assert redacted["users"][1]["name"] == "Bob"
        assert redacted["users"][1]["password"] == "***REDACTED***"

