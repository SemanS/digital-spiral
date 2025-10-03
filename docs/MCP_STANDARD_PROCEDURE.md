# MCP Standard Procedure - Pridávanie nových akcií

Tento dokument popisuje štandardizovaný postup pre pridávanie nových MCP akcií do AI asistenta.

## 📋 Checklist pre pridanie novej MCP akcie

### ✅ Krok 1: Implementuj metódu v Jira Adapter

**Súbor:** `clients/python/jira_cloud_adapter.py`

```python
def new_action(self, param1: str, param2: int) -> dict[str, Any]:
    """Description of what this action does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Dictionary with result
    """
    return self._call(
        "POST",  # or GET, PUT, DELETE
        f"/rest/api/3/endpoint/{param1}",
        json_body={"field": param2}
    )
```

**Príklad:**
```python
def get_comments(self, issue_key: str) -> dict[str, Any]:
    """Get all comments for an issue.
    
    Args:
        issue_key: Issue key (e.g., "SCRUM-123")
    
    Returns:
        Dictionary with comments list
    """
    return self._call("GET", f"/rest/api/3/issue/{issue_key}/comment")
```

---

### ✅ Krok 2: Pridaj MCP tool definition

**Súbor:** `orchestrator/ai_assistant_api.py`

Pridaj do `MCP_TOOLS` listu:

```python
{
    "type": "function",
    "function": {
        "name": "action_name",
        "description": "Clear description of what this action does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of param1"
                },
                "param2": {
                    "type": "integer",
                    "description": "Description of param2"
                }
            },
            "required": ["param1"]  # List required params
        }
    }
}
```

**Príklad:**
```python
{
    "type": "function",
    "function": {
        "name": "get_comments",
        "description": "Get all comments from a Jira issue",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {
                    "type": "string",
                    "description": "The Jira issue key (e.g., SCRUM-123)"
                }
            },
            "required": ["issue_key"]
        }
    }
}
```

---

### ✅ Krok 3: Implementuj MCP executor

**Súbor:** `orchestrator/ai_assistant_api.py`

Pridaj do `execute_mcp_action()` funkcie:

```python
elif action_name == "action_name":
    result = await asyncio.to_thread(
        adapter.new_action,
        params["param1"],
        params.get("param2", default_value)
    )
    return {"success": True, "result": result}
```

**Príklad:**
```python
elif action_name == "get_comments":
    result = await asyncio.to_thread(
        adapter.get_comments,
        params["issue_key"]
    )
    
    # Format comments for better readability
    comments = result.get("comments", [])
    formatted = [
        {
            "id": c["id"],
            "author": c["author"]["displayName"],
            "body": c["body"],  # ADF format
            "created": c["created"]
        }
        for c in comments
    ]
    
    return {"success": True, "result": {"comments": formatted, "total": len(formatted)}}
```

---

### ✅ Krok 4: Testuj akciu

**Manuálny test cez curl:**

```bash
curl -s -X POST http://localhost:7010/v1/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -d '{
    "messages": [
      {"role": "user", "content": "Zobraz komentáre z SCRUM-229"}
    ],
    "project_key": "SCRUM"
  }' | jq .
```

**Automatický test:**

```python
# scripts/test_mcp_action.py

import asyncio
from orchestrator.ai_assistant_api import execute_mcp_action

async def test_action():
    result = await execute_mcp_action(
        "get_comments",
        {"issue_key": "SCRUM-229"},
        "demo"
    )
    print(result)

asyncio.run(test_action())
```

---

### ✅ Krok 5: Dokumentuj akciu

**Súbor:** `docs/AI_ASSISTANT_README.md`

Pridaj do sekcie **MCP Actions**:

```markdown
- ✅ **action_name** - Description of action
```

**Príklad:**
```markdown
- ✅ **get_comments** - Získať všetky komentáre z issue
```

---

## 🎯 Štandardné MCP akcie (Best Practices)

### 1. **Read Operations** (GET)
- `get_comments` - Získať komentáre
- `get_attachments` - Získať prílohy
- `get_watchers` - Získať sledujúcich
- `get_links` - Získať linky na iné issues
- `get_worklog` - Získať worklog záznamy

### 2. **Write Operations** (POST/PUT)
- `add_comment` - Pridať komentár ✅ (už implementované)
- `add_attachment` - Pridať prílohu
- `add_watcher` - Pridať sledujúceho
- `link_issues` - Linkovať issues
- `log_work` - Zaznamenať prácu

### 3. **Update Operations** (PUT)
- `update_issue` - Aktualizovať issue fields
- `assign_issue` - Priradiť issue ✅ (už implementované)
- `set_priority` - Nastaviť prioritu
- `set_labels` - Nastaviť labels

### 4. **Delete Operations** (DELETE)
- `delete_comment` - Zmazať komentár
- `remove_watcher` - Odstrániť sledujúceho
- `delete_attachment` - Zmazať prílohu

### 5. **Search Operations** (GET)
- `search_issues` - Vyhľadať issues ✅ (už implementované)
- `search_users` - Vyhľadať používateľov
- `search_projects` - Vyhľadať projekty

---

## 📝 Príklady implementácie

### Príklad 1: Get Comments

```python
# 1. Adapter method
def get_comments(self, issue_key: str) -> dict[str, Any]:
    """Get all comments for an issue."""
    return self._call("GET", f"/rest/api/3/issue/{issue_key}/comment")

# 2. MCP tool definition
{
    "type": "function",
    "function": {
        "name": "get_comments",
        "description": "Get all comments from a Jira issue",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key (e.g., SCRUM-123)"}
            },
            "required": ["issue_key"]
        }
    }
}

# 3. MCP executor
elif action_name == "get_comments":
    result = await asyncio.to_thread(adapter.get_comments, params["issue_key"])
    return {"success": True, "result": result}
```

### Príklad 2: Add Watcher

```python
# 1. Adapter method
def add_watcher(self, issue_key: str, account_id: str) -> None:
    """Add a watcher to an issue."""
    self._call("POST", f"/rest/api/3/issue/{issue_key}/watchers", json_body=account_id)

# 2. MCP tool definition
{
    "type": "function",
    "function": {
        "name": "add_watcher",
        "description": "Add a watcher to a Jira issue",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key"},
                "account_id": {"type": "string", "description": "User account ID"}
            },
            "required": ["issue_key", "account_id"]
        }
    }
}

# 3. MCP executor
elif action_name == "add_watcher":
    await asyncio.to_thread(adapter.add_watcher, params["issue_key"], params["account_id"])
    return {"success": True, "result": "Watcher added"}
```

### Príklad 3: Link Issues

```python
# 1. Adapter method
def link_issues(self, inward_issue: str, outward_issue: str, link_type: str) -> dict[str, Any]:
    """Link two issues together."""
    return self._call(
        "POST",
        "/rest/api/3/issueLink",
        json_body={
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue}
        }
    )

# 2. MCP tool definition
{
    "type": "function",
    "function": {
        "name": "link_issues",
        "description": "Link two Jira issues together",
        "parameters": {
            "type": "object",
            "properties": {
                "inward_issue": {"type": "string", "description": "First issue key"},
                "outward_issue": {"type": "string", "description": "Second issue key"},
                "link_type": {"type": "string", "description": "Link type (e.g., 'Blocks', 'Relates')"}
            },
            "required": ["inward_issue", "outward_issue", "link_type"]
        }
    }
}

# 3. MCP executor
elif action_name == "link_issues":
    result = await asyncio.to_thread(
        adapter.link_issues,
        params["inward_issue"],
        params["outward_issue"],
        params["link_type"]
    )
    return {"success": True, "result": result}
```

---

## 🔧 Error Handling

Vždy pridaj error handling do MCP executora:

```python
elif action_name == "action_name":
    try:
        result = await asyncio.to_thread(adapter.new_action, params["param1"])
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Action failed: {e}")
        return {"success": False, "error": str(e)}
```

---

## 📊 Testing Checklist

- [ ] Adapter metóda funguje samostatne
- [ ] MCP tool definition je správny
- [ ] MCP executor volá správnu metódu
- [ ] AI asistent rozpozná akciu z promptu
- [ ] Akcia sa vykoná úspešne
- [ ] Error handling funguje
- [ ] Dokumentácia je aktualizovaná

---

## 🚀 Quick Start Template

```python
# === 1. ADAPTER METHOD ===
# File: clients/python/jira_cloud_adapter.py

def ACTION_NAME(self, param1: str) -> dict[str, Any]:
    """ACTION DESCRIPTION."""
    return self._call("METHOD", f"/rest/api/3/ENDPOINT/{param1}")


# === 2. MCP TOOL DEFINITION ===
# File: orchestrator/ai_assistant_api.py (add to MCP_TOOLS)

{
    "type": "function",
    "function": {
        "name": "ACTION_NAME",
        "description": "ACTION DESCRIPTION",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "PARAM DESCRIPTION"}
            },
            "required": ["param1"]
        }
    }
}


# === 3. MCP EXECUTOR ===
# File: orchestrator/ai_assistant_api.py (add to execute_mcp_action)

elif action_name == "ACTION_NAME":
    result = await asyncio.to_thread(adapter.ACTION_NAME, params["param1"])
    return {"success": True, "result": result}


# === 4. TEST ===
curl -s -X POST http://localhost:7010/v1/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -d '{"messages": [{"role": "user", "content": "TEST PROMPT"}], "project_key": "SCRUM"}' | jq .
```

---

**Vytvoril:** AI Assistant  
**Dátum:** 2025-01-03  
**Verzia:** 1.0.0

