# Source Adapters - Multi-Source Support

This package provides adapters for different issue tracking systems, enabling Digital Spiral to work with Jira, GitHub, Asana, and other sources through a unified interface.

---

## 📚 Overview

The adapter framework allows Digital Spiral to:
- **Normalize** data from different sources into a common format
- **Query** work items across multiple systems
- **Create/Update** work items in any supported system
- **Sync** data bidirectionally
- **Extend** easily to support new sources

---

## 🏗️ Architecture

### Base Adapter

All adapters implement the `SourceAdapter` abstract base class:

```python
from src.domain.adapters import SourceAdapter, SourceType

class MyAdapter(SourceAdapter):
    async def test_connection(self) -> bool:
        # Test connection to source
        pass
    
    async def fetch_work_items(self, ...) -> List[NormalizedWorkItem]:
        # Fetch work items
        pass
    
    # ... implement all abstract methods
```

### Normalized Models

All adapters return normalized models:

- **NormalizedWorkItem** - Unified work item representation
- **NormalizedComment** - Unified comment representation
- **NormalizedTransition** - Unified status transition

### Enums

Standardized enums for cross-source compatibility:

- **SourceType** - jira, github, asana, linear, clickup
- **WorkItemStatus** - todo, in_progress, blocked, in_review, done, cancelled
- **WorkItemPriority** - critical, high, medium, low, none
- **WorkItemType** - epic, story, task, bug, subtask, feature

---

## 🔌 Supported Adapters

### 1. Jira Adapter ✅

**Status:** Complete  
**File:** `jira_adapter.py`

```python
from src.domain.adapters import JiraAdapter, SourceType
from uuid import uuid4

adapter = JiraAdapter(
    instance_id=uuid4(),
    base_url="https://company.atlassian.net",
    auth_config={
        "email": "user@example.com",
        "api_token": "your-api-token",
    },
)

# Test connection
connected = await adapter.test_connection()

# Fetch issues
issues = await adapter.fetch_work_items(project_id="PROJ", limit=10)

# Create issue
issue = await adapter.create_issue(
    project_id="PROJ",
    title="New issue",
    description="Description",
)
```

**Features:**
- ✅ JQL query support
- ✅ ADF (Atlassian Document Format) parsing
- ✅ Custom fields support
- ✅ Transition history
- ✅ Comments and attachments

### 2. GitHub Adapter ✅

**Status:** Complete  
**File:** `github_adapter.py`

```python
from src.domain.adapters import GitHubAdapter, SourceType

adapter = GitHubAdapter(
    instance_id=uuid4(),
    base_url="https://api.github.com",
    auth_config={
        "token": "ghp_your_token",
    },
)

# Fetch issues
issues = await adapter.fetch_work_items(
    project_id="owner/repo",
    limit=10,
)

# Create issue
issue = await adapter.create_work_item(
    project_id="owner/repo",
    title="New issue",
    description="Description",
)
```

**Features:**
- ✅ GitHub Issues API
- ✅ Label-based priority/type
- ✅ Timeline events
- ✅ Pull request filtering
- ✅ Markdown support

### 3. Asana Adapter ✅

**Status:** Complete  
**File:** `asana_adapter.py`

```python
from src.domain.adapters import AsanaAdapter, SourceType

adapter = AsanaAdapter(
    instance_id=uuid4(),
    base_url="https://app.asana.com/api/1.0",
    auth_config={
        "access_token": "your-access-token",
    },
)

# Fetch tasks
tasks = await adapter.fetch_work_items(
    project_id="project_gid",
    limit=10,
)

# Create task
task = await adapter.create_work_item(
    project_id="project_gid",
    title="New task",
    description="Description",
)
```

**Features:**
- ✅ Asana API v1.0
- ✅ Custom fields support
- ✅ Tags for priority/type
- ✅ Stories (comments)
- ✅ Subtasks support

### 4. Linear Adapter ⏳

**Status:** Planned  
**File:** `linear_adapter.py` (not yet implemented)

**Planned Features:**
- GraphQL API integration
- Cycle and project support
- Issue relations
- Custom workflows

### 5. ClickUp Adapter ⏳

**Status:** Planned  
**File:** `clickup_adapter.py` (not yet implemented)

**Planned Features:**
- ClickUp API v2
- Custom statuses
- Multiple assignees
- Time tracking

---

## 🚀 Usage

### Creating an Adapter

Use the factory to create adapters dynamically:

```python
from src.domain.adapters import create_adapter, SourceType
from uuid import uuid4

# Create Jira adapter
jira = create_adapter(
    source_type=SourceType.JIRA,
    instance_id=uuid4(),
    base_url="https://company.atlassian.net",
    auth_config={"email": "...", "api_token": "..."},
)

# Create GitHub adapter
github = create_adapter(
    source_type=SourceType.GITHUB,
    instance_id=uuid4(),
    base_url="https://api.github.com",
    auth_config={"token": "..."},
)
```

### Fetching Work Items

```python
# Fetch from Jira
jira_issues = await jira.fetch_work_items(
    project_id="PROJ",
    updated_since=datetime(2025, 1, 1),
    limit=50,
)

# Fetch from GitHub
github_issues = await github.fetch_work_items(
    project_id="owner/repo",
    updated_since=datetime(2025, 1, 1),
    limit=50,
)

# All return NormalizedWorkItem objects
for issue in jira_issues + github_issues:
    print(f"{issue.source_key}: {issue.title} ({issue.status})")
```

### Creating Work Items

```python
# Create in Jira
jira_issue = await jira.create_work_item(
    project_id="PROJ",
    title="Bug fix needed",
    description="Description",
    type=WorkItemType.BUG,
    priority=WorkItemPriority.HIGH,
)

# Create in GitHub
github_issue = await github.create_work_item(
    project_id="owner/repo",
    title="Feature request",
    description="Description",
    type=WorkItemType.FEATURE,
    priority=WorkItemPriority.MEDIUM,
)
```

### Updating Work Items

```python
# Update in any source
updated = await adapter.update_work_item(
    work_item_id="PROJ-123",
    title="Updated title",
    description="Updated description",
)
```

### Transitioning Status

```python
# Transition to done
done_issue = await adapter.transition_work_item(
    work_item_id="PROJ-123",
    to_status=WorkItemStatus.DONE,
    comment="Completed the work",
)
```

---

## 🔧 Extending with New Adapters

To add a new source adapter:

### 1. Create Adapter Class

```python
from src.domain.adapters.base import SourceAdapter, NormalizedWorkItem

class MySourceAdapter(SourceAdapter):
    async def test_connection(self) -> bool:
        # Implement connection test
        pass
    
    async def fetch_work_items(self, ...) -> List[NormalizedWorkItem]:
        # Implement fetch logic
        pass
    
    # ... implement all abstract methods
```

### 2. Register Adapter

```python
from src.domain.adapters import AdapterRegistry, SourceType

# Add new source type to base.py SourceType enum
# Then register adapter
AdapterRegistry.register(SourceType.MY_SOURCE, MySourceAdapter)
```

### 3. Add Tests

```python
# tests/unit/adapters/test_my_source_adapter.py
import pytest
from src.domain.adapters import MySourceAdapter

async def test_fetch_work_items():
    adapter = MySourceAdapter(...)
    items = await adapter.fetch_work_items(...)
    assert len(items) > 0
```

---

## 📊 Normalization

### Status Mapping

Each adapter maps source-specific statuses to normalized statuses:

| Normalized | Jira | GitHub | Asana |
|------------|------|--------|-------|
| TODO | To Do, Open, Backlog | open | incomplete |
| IN_PROGRESS | In Progress, In Development | - | in_progress |
| BLOCKED | Blocked, Impediment | - | - |
| IN_REVIEW | In Review, Code Review | - | - |
| DONE | Done, Closed, Resolved | closed | complete |
| CANCELLED | Cancelled, Rejected | - | - |

### Priority Mapping

| Normalized | Jira | GitHub | Asana |
|------------|------|--------|-------|
| CRITICAL | Highest, Critical | priority: critical, p0 | critical |
| HIGH | High | priority: high, p1 | high |
| MEDIUM | Medium | priority: medium, p2 | medium |
| LOW | Low, Lowest | priority: low, p3 | low |

### Type Mapping

| Normalized | Jira | GitHub | Asana |
|------------|------|--------|-------|
| EPIC | Epic | - | epic |
| STORY | Story | story | story |
| TASK | Task | task | task |
| BUG | Bug | bug | bug |
| SUBTASK | Sub-task | - | subtask |
| FEATURE | - | enhancement, feature | feature |

---

## 🔒 Security

### Authentication

Each adapter handles authentication differently:

- **Jira:** Basic Auth (email + API token) or Bearer token
- **GitHub:** Personal Access Token
- **Asana:** Personal Access Token

### Best Practices

1. **Never commit credentials** - Use environment variables
2. **Encrypt at rest** - Encrypt auth_config in database
3. **Rotate tokens** - Implement token rotation
4. **Least privilege** - Use minimal required permissions

---

## 📝 Testing

Run adapter tests:

```bash
# All adapter tests
pytest tests/unit/adapters/ -v

# Specific adapter
pytest tests/unit/adapters/test_jira_adapter.py -v

# With coverage
pytest tests/unit/adapters/ --cov=src.domain.adapters
```

---

## 📚 Resources

- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [Asana API](https://developers.asana.com/docs)
- [Linear API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)

---

**Last Updated:** 2025-10-03  
**Adapters:** 3 of 5 complete  
**Status:** 🔄 In Progress

