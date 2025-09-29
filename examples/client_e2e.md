# Client E2E Script – What happens step‑by‑step

This document explains what the `examples/client_e2e.py` script does and which API calls are invoked against the Digital Spiral mock Jira server.

## Configuration

Environment variables consumed by the script:
- `JIRA_BASE_URL` (default: `http://localhost:9000`)
- `JIRA_TOKEN` (default: `mock-token`)
- `MOCKJIRA_WEBHOOK_URL` (optional; if set, a webhook will be registered)

The script uses the Python JiraAdapter client (`clients/python/jira_adapter.py`) which wraps REST calls with retry/backoff and typed errors.

## Flow Overview

1) Optional webhook registration
- Adapter call: `register_webhook(url, jql, events, secret=None)`
- REST: `POST /rest/api/3/webhook` with body `{ "webhooks": [{"url": url, "jqlFilter": jql, "events": [...] }] }`
- Purpose: demonstrate webhook registration (e.g., `events=["jira:issue_created"]`, `jql="project = DEV"`).

2) Create Jira issue (Platform API)
- Adapter call: `create_issue(project_key, issue_type_id, summary, description_adf, fields=None)`
- REST: `POST /rest/api/3/issue` with `{"fields": {"project": {"key": ...}, "issuetype": {"id": ...}, "summary": ... , "description": ADF}}`
- Output contains the issue `key` (e.g., `SUP-101`).

3) List transitions and perform one
- Adapter call: `list_transitions(key) → [ {"id": ..., "name": ...}, ... ]`
- REST: `GET /rest/api/3/issue/{key}/transitions`
- If any transition is available, script uses the first one:
  - Adapter call: `transition_issue(key, transition_id)`
  - REST: `POST /rest/api/3/issue/{key}/transitions` with `{ "transition": { "id": ... } }`

4) Add comment (ADF)
- Adapter call: `add_comment(key, body_adf)`
- REST: `POST /rest/api/3/issue/{key}/comment` with `{ "body": <ADF> }`
- ADF example:
  ```json
  {"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"Draft reply: working on it."}]}]}
  ```

5) Search for the created issue
- Adapter call: `search(jql, start_at=0, max_results=50)`
- REST: `POST /rest/api/3/search` (fallback `GET` if server prefers)
- JQL example: `key = "SUP-101"`

6) Create a Service Management (JSM) request
- Adapter call: `create_request(service_desk_id, request_type_id, summary, fields=None)`
- REST: `POST /rest/servicedeskapi/request` with:
  ```json
  {
    "serviceDeskId":"1",
    "requestTypeId":"100",
    "requestFieldValues":[
      {"fieldId":"summary","value":"Laptop request from client_e2e"},
      {"fieldId":"description","value":"Need a new laptop for development"}
    ]
  }
  ```
- IDs `1` and `100` are part of the seed data.

7) List Agile sprints for a board
- Adapter call: `list_sprints(board_id, start_at=0, max_results=50)`
- REST: `GET /rest/agile/1.0/board/{boardId}/sprint`
- The script uses `board_id=1`, which exists in seed data.

## Outputs
The script returns (and prints when run as `__main__`) a JSON summary like:
```json
{
  "timestamps": {"started": "...", "finished": "..."},
  "webhook_registered": true,
  "webhook_result": [...],
  "issue": {"id": "...", "key": "SUP-...", ...},
  "transition": {...} | null,
  "comment": {"id": "...", ...},
  "search": {"issues_count": N},
  "jsm_request": {"id": "...", "issueId": "...", ...},
  "agile_sprints": {"count": M}
}
```

## How to run
```bash
# Ensure the mock server is running on 9000 (see AGENTS.md for options)
python -m mockjira.main --host 0.0.0.0 --port 9000 --log-level info

# In another shell, run the client script
export JIRA_BASE_URL=http://localhost:9000
export JIRA_TOKEN=mock-token
# optional webhook for demo
# export MOCKJIRA_WEBHOOK_URL=http://listener

python examples/client_e2e.py
```

If `MOCKJIRA_WEBHOOK_URL` is set (and a listener exists), the server will attempt webhook delivery; you can inspect deliveries at `GET /rest/api/3/_mock/webhooks/deliveries`.

