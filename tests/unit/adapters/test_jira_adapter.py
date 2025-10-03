"""Unit tests for JiraAdapter."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.adapters import (
    JiraAdapter,
    SourceType,
    WorkItemStatus,
    WorkItemPriority,
    WorkItemType,
)


@pytest.fixture
def instance_id():
    """Create a test instance ID."""
    return uuid4()


@pytest.fixture
def jira_adapter(instance_id):
    """Create a Jira adapter with mocked client."""
    adapter = JiraAdapter(
        instance_id=instance_id,
        base_url="https://test.atlassian.net",
        auth_config={"email": "test@example.com", "api_token": "test-token"},
    )
    adapter.client = AsyncMock()
    return adapter


class TestJiraAdapter:
    """Tests for JiraAdapter."""

    async def test_test_connection_success(self, jira_adapter):
        """Test successful connection test."""
        jira_adapter.client.get = AsyncMock(
            return_value=MagicMock(status_code=200)
        )
        
        result = await jira_adapter.test_connection()
        assert result is True

    async def test_test_connection_failure(self, jira_adapter):
        """Test failed connection test."""
        jira_adapter.client.get = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await jira_adapter.test_connection()
        assert result is False

    async def test_normalize_status(self, jira_adapter):
        """Test status normalization."""
        assert jira_adapter.normalize_status("To Do") == WorkItemStatus.TODO
        assert jira_adapter.normalize_status("In Progress") == WorkItemStatus.IN_PROGRESS
        assert jira_adapter.normalize_status("Done") == WorkItemStatus.DONE
        assert jira_adapter.normalize_status("Blocked") == WorkItemStatus.BLOCKED

    async def test_normalize_priority(self, jira_adapter):
        """Test priority normalization."""
        assert jira_adapter.normalize_priority("Highest") == WorkItemPriority.CRITICAL
        assert jira_adapter.normalize_priority("High") == WorkItemPriority.HIGH
        assert jira_adapter.normalize_priority("Medium") == WorkItemPriority.MEDIUM
        assert jira_adapter.normalize_priority("Low") == WorkItemPriority.LOW

    async def test_normalize_type(self, jira_adapter):
        """Test type normalization."""
        assert jira_adapter.normalize_type("Epic") == WorkItemType.EPIC
        assert jira_adapter.normalize_type("Story") == WorkItemType.STORY
        assert jira_adapter.normalize_type("Task") == WorkItemType.TASK
        assert jira_adapter.normalize_type("Bug") == WorkItemType.BUG
        assert jira_adapter.normalize_type("Sub-task") == WorkItemType.SUBTASK

    async def test_fetch_work_items(self, jira_adapter, instance_id):
        """Test fetching work items."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": "10001",
                    "key": "PROJ-1",
                    "fields": {
                        "summary": "Test issue",
                        "description": None,
                        "status": {"name": "To Do"},
                        "priority": {"name": "Medium"},
                        "issuetype": {"name": "Task"},
                        "project": {"key": "PROJ"},
                        "created": "2025-01-01T00:00:00.000+0000",
                        "updated": "2025-01-02T00:00:00.000+0000",
                    },
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        jira_adapter.client.get = AsyncMock(return_value=mock_response)
        
        items = await jira_adapter.fetch_work_items(project_id="PROJ", limit=10)
        
        assert len(items) == 1
        assert items[0].source_key == "PROJ-1"
        assert items[0].title == "Test issue"
        assert items[0].status == WorkItemStatus.TODO
        assert items[0].priority == WorkItemPriority.MEDIUM
        assert items[0].type == WorkItemType.TASK
        assert items[0].source_type == SourceType.JIRA
        assert items[0].instance_id == instance_id

    async def test_fetch_work_item(self, jira_adapter):
        """Test fetching a single work item."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "10001",
            "key": "PROJ-1",
            "fields": {
                "summary": "Test issue",
                "description": None,
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "issuetype": {"name": "Bug"},
                "project": {"key": "PROJ"},
                "created": "2025-01-01T00:00:00.000+0000",
                "updated": "2025-01-02T00:00:00.000+0000",
            },
        }
        mock_response.raise_for_status = MagicMock()
        jira_adapter.client.get = AsyncMock(return_value=mock_response)
        
        item = await jira_adapter.fetch_work_item("PROJ-1")
        
        assert item.source_key == "PROJ-1"
        assert item.title == "Test issue"
        assert item.status == WorkItemStatus.IN_PROGRESS
        assert item.priority == WorkItemPriority.HIGH
        assert item.type == WorkItemType.BUG

    async def test_create_work_item(self, jira_adapter):
        """Test creating a work item."""
        # Mock the create response
        create_response = MagicMock()
        create_response.json.return_value = {"key": "PROJ-2"}
        create_response.raise_for_status = MagicMock()
        
        # Mock the fetch response
        fetch_response = MagicMock()
        fetch_response.json.return_value = {
            "id": "10002",
            "key": "PROJ-2",
            "fields": {
                "summary": "New issue",
                "description": None,
                "status": {"name": "To Do"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Task"},
                "project": {"key": "PROJ"},
                "created": "2025-01-03T00:00:00.000+0000",
                "updated": "2025-01-03T00:00:00.000+0000",
            },
        }
        fetch_response.raise_for_status = MagicMock()
        
        jira_adapter.client.post = AsyncMock(return_value=create_response)
        jira_adapter.client.get = AsyncMock(return_value=fetch_response)
        
        item = await jira_adapter.create_work_item(
            project_id="PROJ",
            title="New issue",
            type=WorkItemType.TASK,
            priority=WorkItemPriority.MEDIUM,
        )
        
        assert item.source_key == "PROJ-2"
        assert item.title == "New issue"
        assert item.status == WorkItemStatus.TODO

    async def test_extract_description_from_adf(self, jira_adapter):
        """Test extracting description from ADF format."""
        adf_description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "This is "},
                        {"type": "text", "text": "a test"},
                    ],
                }
            ],
        }
        
        result = jira_adapter._extract_description(adf_description)
        assert result == "This is a test"

    async def test_extract_description_from_string(self, jira_adapter):
        """Test extracting description from plain string."""
        result = jira_adapter._extract_description("Plain text description")
        assert result == "Plain text description"

    async def test_extract_description_none(self, jira_adapter):
        """Test extracting description when None."""
        result = jira_adapter._extract_description(None)
        assert result is None

