"""Adapter factory for creating source adapters."""

from typing import Any, Dict, Type
from uuid import UUID

from .base import SourceAdapter, SourceType
from .jira_adapter import JiraAdapter
from .github_adapter import GitHubAdapter
from .asana_adapter import AsanaAdapter
from .linear_adapter import LinearAdapter


class AdapterRegistry:
    """Registry for source adapters."""

    _adapters: Dict[SourceType, Type[SourceAdapter]] = {
        SourceType.JIRA: JiraAdapter,
        SourceType.GITHUB: GitHubAdapter,
        SourceType.ASANA: AsanaAdapter,
        SourceType.LINEAR: LinearAdapter,
    }

    @classmethod
    def register(cls, source_type: SourceType, adapter_class: Type[SourceAdapter]):
        """Register a new adapter.

        Args:
            source_type: Source type
            adapter_class: Adapter class
        """
        cls._adapters[source_type] = adapter_class

    @classmethod
    def get_adapter_class(cls, source_type: SourceType) -> Type[SourceAdapter]:
        """Get adapter class for a source type.

        Args:
            source_type: Source type

        Returns:
            Adapter class

        Raises:
            ValueError: If source type is not supported
        """
        if source_type not in cls._adapters:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        return cls._adapters[source_type]

    @classmethod
    def create_adapter(
        cls,
        source_type: SourceType,
        instance_id: UUID,
        base_url: str,
        auth_config: Dict[str, Any],
    ) -> SourceAdapter:
        """Create an adapter instance.

        Args:
            source_type: Source type
            instance_id: Instance UUID
            base_url: Base URL for the source API
            auth_config: Authentication configuration

        Returns:
            Adapter instance

        Raises:
            ValueError: If source type is not supported
        """
        adapter_class = cls.get_adapter_class(source_type)
        return adapter_class(
            instance_id=instance_id,
            base_url=base_url,
            auth_config=auth_config,
        )

    @classmethod
    def list_supported_sources(cls) -> list[SourceType]:
        """List all supported source types.

        Returns:
            List of supported source types
        """
        return list(cls._adapters.keys())


# Convenience function
def create_adapter(
    source_type: SourceType,
    instance_id: UUID,
    base_url: str,
    auth_config: Dict[str, Any],
) -> SourceAdapter:
    """Create an adapter instance.

    Args:
        source_type: Source type (jira, github, etc.)
        instance_id: Instance UUID
        base_url: Base URL for the source API
        auth_config: Authentication configuration

    Returns:
        Adapter instance

    Example:
        >>> adapter = create_adapter(
        ...     source_type=SourceType.JIRA,
        ...     instance_id=uuid4(),
        ...     base_url="https://company.atlassian.net",
        ...     auth_config={"email": "user@example.com", "api_token": "..."},
        ... )
        >>> await adapter.test_connection()
        True
    """
    return AdapterRegistry.create_adapter(
        source_type=source_type,
        instance_id=instance_id,
        base_url=base_url,
        auth_config=auth_config,
    )


__all__ = [
    "AdapterRegistry",
    "create_adapter",
]

