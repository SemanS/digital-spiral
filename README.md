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
- **Webhooks**: Register mock webhook listeners and inspect all deliveries via a
  helper endpoint.
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

Or run the prebuilt container image:

```bash
docker run -p 9000:9000 ghcr.io/<your-org>/mock-jira:latest
```

The server exposes FastAPI docs at `http://localhost:9000/docs`.

Authenticated requests must include `Authorization: Bearer mock-token` unless
you customise the store.

### Useful endpoints

- `GET /rest/api/3/project` — list seeded projects.
- `POST /rest/api/3/issue` — create an issue. Responses include JQL-searchable
  data and webhook deliveries are recorded.
- `GET /rest/api/3/_mock/webhooks/deliveries` — retrieve all webhook payloads
  emitted during the session.
- `GET /rest/agile/1.0/board` — agile boards with pagination metadata.
- `POST /rest/servicedeskapi/request` — create a service request based on the
  seeded Support project.

### Running the test suite

```bash
python -m pip install -e .[test]
pytest
```

## Extending

- Update `mockjira/store.py` to add new seed data or stateful behaviours.
- Add new routers under `mockjira/routers/` for further API families (e.g. JQL
  API group or additional webhook utilities).
- Integrate real OpenAPI documents via tooling such as Stoplight Prism if you
  prefer contract-first mocking; this project focuses on a higher-level,
  stateful emulation.

## License

MIT
