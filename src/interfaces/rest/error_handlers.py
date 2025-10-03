"""Error handlers for FastAPI."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.application.validation import ValidationException
from src.infrastructure.external.jira import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraNotFoundError,
    JiraRateLimitError,
)

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: ValidationException,
) -> JSONResponse:
    """
    Handle validation exceptions.

    Args:
        request: Request
        exc: Validation exception

    Returns:
        JSON response with error details
    """
    logger.warning(f"Validation error: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "message": exc.message,
            "errors": exc.errors,
        },
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation exceptions.

    Args:
        request: Request
        exc: Pydantic validation error

    Returns:
        JSON response with error details
    """
    logger.warning(f"Pydantic validation error: {exc}")

    # Convert Pydantic errors to our format
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "errors": errors,
        },
    )


async def jira_authentication_error_handler(
    request: Request,
    exc: JiraAuthenticationError,
) -> JSONResponse:
    """
    Handle Jira authentication errors.

    Args:
        request: Request
        exc: Jira authentication error

    Returns:
        JSON response with error details
    """
    logger.error(f"Jira authentication error: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "jira_authentication_error",
            "message": "Jira authentication failed",
            "details": exc.message,
        },
    )


async def jira_not_found_error_handler(
    request: Request,
    exc: JiraNotFoundError,
) -> JSONResponse:
    """
    Handle Jira not found errors.

    Args:
        request: Request
        exc: Jira not found error

    Returns:
        JSON response with error details
    """
    logger.warning(f"Jira resource not found: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "jira_not_found",
            "message": "Jira resource not found",
            "details": exc.message,
        },
    )


async def jira_rate_limit_error_handler(
    request: Request,
    exc: JiraRateLimitError,
) -> JSONResponse:
    """
    Handle Jira rate limit errors.

    Args:
        request: Request
        exc: Jira rate limit error

    Returns:
        JSON response with error details
    """
    logger.warning(f"Jira rate limit exceeded: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "jira_rate_limit",
            "message": "Jira API rate limit exceeded",
            "details": exc.message,
        },
    )


async def jira_api_error_handler(
    request: Request,
    exc: JiraAPIError,
) -> JSONResponse:
    """
    Handle generic Jira API errors.

    Args:
        request: Request
        exc: Jira API error

    Returns:
        JSON response with error details
    """
    logger.error(f"Jira API error: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "jira_api_error",
            "message": "Jira API error",
            "details": exc.message,
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle generic exceptions.

    Args:
        request: Request
        exc: Exception

    Returns:
        JSON response with error details
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": str(exc) if logger.level == logging.DEBUG else None,
        },
    )


def register_error_handlers(app):
    """
    Register error handlers with FastAPI app.

    Args:
        app: FastAPI application
    """
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(JiraAuthenticationError, jira_authentication_error_handler)
    app.add_exception_handler(JiraNotFoundError, jira_not_found_error_handler)
    app.add_exception_handler(JiraRateLimitError, jira_rate_limit_error_handler)
    app.add_exception_handler(JiraAPIError, jira_api_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


__all__ = ["register_error_handlers"]

