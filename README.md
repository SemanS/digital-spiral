# Mock Jira Cloud Server

This repository implements a stateful mock server that emulates the most used
surfaces of the Jira Cloud REST APIs. It is meant for integration testing and
local development where hitting the real Atlassian endpoints is impractical.

## Features

- **Jira Platform REST API v3**: Issues, search, transitions, comments,
  projects, fields, users and webhook registration.
- **Jira Software (Agile) API**: Boards, sprints and backlog listings with
  pagination support.
- **Jira Service Management API**: Portal request CRUD with simple approvals.
- **ADF aware payloads**: descriptions and comments are stored and returned as
  Atlassian Document Format documents.
- **Webhooks**: Register mock webhook listeners with jitter, retry/backoff,
  signature verification helpers and delivery inspection endpoints.
- **Auth + rate limiting**: Bearer token authentication using seeded API tokens
  and a light cost counter with optional `X-Force-429` simulation header.

The in-memory store ships with a realistic data seed (projects `DEV` and `SUP`,
multiple users, boards and sprints). All write operations update this state so
responses stay consistent across calls.

## Getting started

```bash
python -m pip install -e .[test]
mock-jira-server --port 9000
```

### One-click Docker seed

Spin up a fresh mock Jira with deterministic seed data using Docker Compose:

```bash
docker compose up mock-jira-seed
```

This builds the local image, waits for the API to become healthy, generates the
seed described in `scripts/seed_profiles/default.json`, and loads it through the
`/_mock/seed/generate` endpoint. The `mock-jira` container keeps running after
the seeding job finishes, exposing FastAPI docs at
`http://localhost:9000/docs`.

To customise the dataset, edit the JSON profile or point to another file:

```bash
MOCK_JIRA_SEED_CONFIG=scripts/seed_profiles/support.json \
  docker compose up mock-jira-seed
```

Curated profiles live under `scripts/seed_profiles/`. In addition to the
default generator-driven setup, you can load declarative datasets, such as the
new `docker_manual_onboarding.json` profile that mirrors tasks from the official
[Docker manuals](https://docs.docker.com/manuals/) for documentation and
DevOps teams:

```bash
python scripts/generate_dummy_jira.py \
  --config scripts/seed_profiles/docker_manual_onboarding.json \
  --out artifacts/docker-manual-seed.json
```

Each profile can either list explicit `seed_data` (matching the structure
returned by `/_mock/seed/export`) or a `generator` object with
`GenConfig` overrides. The same config file can be used with the standalone
generator:

```bash
python scripts/generate_dummy_jira.py --config scripts/seed_profiles/default.json
```

Authenticated requests must include `Authorization: Bearer mock-token` unless
you customise the store.

### MCP Jira bridge

Run the lightweight HTTP bridge and point your MCP-enabled client at it. The
bridge supports two authentication modes:

1. **Static bearer token / PAT** – quickest for local testing.

   ```bash
   export JIRA_BASE_URL="https://dotxan-team-ttygqm7b.atlassian.net"
   export JIRA_TOKEN="<your_jira_pat>"
   python -m mcp_jira.http_server --port 8055
   ```

2. **OAuth 2.0 (3LO)** – no static token; the bridge walks you through browser
   consent and persists refresh tokens under `~/.config/mcp-jira/token.json`.
   Provide the Atlassian app credentials before launch:

   ```bash
   export ATLASSIAN_CLIENT_ID="<client_id>"
   export ATLASSIAN_CLIENT_SECRET="<client_secret>"
   export ATLASSIAN_REDIRECT_URI="http://127.0.0.1:8055/oauth/callback"
   python -m mcp_jira.http_server --port 8055
   ```

   The server prints an authorization URL. Open it in your browser, approve the
   access request, and you are ready to use MCP tools. Access/refresh tokens are
   refreshed automatically when they expire.

The bridge exposes `/tools` and `/tools/invoke` endpoints compatible with
`mcp-remote`. Configure your CLI by adding:

```toml
[mcp_servers.jira]
command = "python"
args = ["-m", "mcp_jira.http_server", "--host", "127.0.0.1", "--port", "8055"]
startup_timeout_ms = 20_000
env = {
  ATLASSIAN_CLIENT_ID = "<client_id>",
  ATLASSIAN_CLIENT_SECRET = "<client_secret>",
  ATLASSIAN_REDIRECT_URI = "http://127.0.0.1:8055/oauth/callback",
  ATLASSIAN_SCOPES = "offline_access read:jira-user read:jira-work write:jira-work manage:jira-project",
  PYTHONPATH = "/absolute/path/to/digital-spiral"
}
```

For a smoother experience you can launch everything through the helper script
which starts the bridge, opens the authorization URL (where supported), and
executes a smoke query once authentication succeeds:

```bash
python scripts/run_mcp_jira_oauth.py --open --test
```

The script keeps the bridge running until you press `Ctrl+C`.

If you prefer PATs, replace the env block with `JIRA_BASE_URL` and
`JIRA_TOKEN` instead. Never commit production credentials; keep them local to
your machine or a secure secret store.

To inject one of the seed profiles into a live Jira tenant once the bridge is
running, use the loader utility:

```bash
python scripts/load_seed_jira.py artifacts/docker_manual_seed.json
```

Pass `--project SRC=DST` to remap project keys when necessary.

### Useful endpoints

- `GET /rest/api/3/project` — list seeded projects.
- `POST /rest/api/3/issue` — create an issue. Responses include JQL-searchable
  data and webhook deliveries are recorded.
- `GET /rest/api/3/_mock/webhooks/deliveries` — retrieve all webhook payloads
  emitted during the session (including base64-encoded wire bodies and headers).
- `GET /rest/api/3/_mock/webhooks/logs` — structured attempt log with request
  ids, status codes and retry metadata.
- `GET /rest/agile/1.0/board` — agile boards with pagination metadata.
- `POST /rest/servicedeskapi/request` — create a service request based on the
  seeded Support project.

### Running the test suite

```bash
python -m pip install -e .[test]
pytest
```

### Webhook security

Webhook deliveries include deterministic headers:

- `X-MockJira-Event-Id` – stable event identifier used for dedupe/replay.
- `X-MockJira-Signature-Version` – current signature algorithm version (`2`).
- `X-MockJira-Signature` – `sha256=` digest computed from
  `sha256(secret + body)`.
- `X-MockJira-Legacy-Signature` – optional `sha256` HMAC when
  `WEBHOOK_SIGNATURE_COMPAT=1` is enabled (for old clients).

Example verifier:

```python
import hashlib

def verify(secret: str, body: bytes, header: str) -> bool:
    algorithm, _, digest = header.partition("=")
    if algorithm != "sha256":
        return False
    expected = hashlib.sha256(secret.encode("utf-8") + body).hexdigest()
    return digest == expected
```

Replay requests reuse the original wire body and headers, so capturing systems
can revalidate the same signature on retries.

## Extending

- Update `mockjira/store.py` to add new seed data or stateful behaviours.
- Add new routers under `mockjira/routers/` for further API families (e.g. JQL
  API group or additional webhook utilities).
- Integrate real OpenAPI documents via tooling such as Stoplight Prism if you
  prefer contract-first mocking; this project focuses on a higher-level,
  stateful emulation.

## License

MIT
