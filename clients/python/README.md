# Python Jira Adapter

## Purpose
`clients/python` delivers a thin Jira REST wrapper that agents can call directly or through Codex-generated snippets. It embodies the Codex goal of translating natural language tasks into code, providing a ready-made client that handles retries, authentication, and resource grouping.

## Features
- High-level methods for platform, agile, and service management APIs.
- Automatic retry logic and structured exception hierarchy (`JiraError`).
- Configurable base URL, token, timeout, and user agent fields via constructor arguments.

## Quick Start
```python
from clients.python.jira_adapter import JiraAdapter

adapter = JiraAdapter("http://localhost:9000", "mock-token")
issue = adapter.create_issue("SUP", "10003", "Hello from Codex agent")
print(issue["key"])
```

## Tips for Codex-Style Workflows
- Combine this adapter with the MCP tooling to let natural language prompts choose between direct REST usage and tool invocations.
- Keep summaries and descriptions concise—Codex-generated code tends to mirror the prompt closely.
- Capture responses and errors to provide feedback loops for iterative prompt refinement, a technique highlighted in the Codex introduction article.
