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
