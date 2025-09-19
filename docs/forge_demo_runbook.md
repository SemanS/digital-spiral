# Digital Spiral Forge Demo Runbook

This runbook demonstrates the end-to-end flow for the Digital Spiral orchestrator with the Forge issue panel. It assumes you are working from the repository root inside the devcontainer.

## 1. Start mock Jira and the orchestrator

```bash
export MOCK_JIRA_SEED_CONFIG=scripts/seed_profiles/forge_demo.json
docker compose up --build mock-jira mock-jira-seed orchestrator
```

The seed profile provisions:

- one software project with two boards and eight sprints (six closed, one active, one future),
- about ninety software issues with realistic comments and transitions,
- a support/service desk project with ~18 tickets to exercise customer workflows.

Wait for the health checks to report healthy containers before proceeding.

## 2. Capture orchestrator connection details

The orchestrator container exposes the API on http://localhost:7010. Note the secret and base URL you will configure in Forge:

- `ORCH_URL`: `http://localhost:7010`
- `ORCH_SECRET`: value of the `ORCH_SECRET` environment variable you passed to the container (defaults to `forge-dev-secret` in docker-compose).

## 3. Deploy the Forge app

1. Install dependencies if necessary: `npm install --prefix forge-app`.
2. Log in to the Atlassian CLI: `forge login`.
3. Register the app (first time only): `forge register`.
4. Deploy: `forge deploy`.
5. Install the app into your test Jira site: `forge install` (choose the site and scope).

## 4. Configure the project settings page

1. Open any software project in the Jira sandbox where the app is installed.
2. Navigate to **Project settings → Apps → Digital Spiral Settings**.
3. Enter the following values:
   - **Orchestrator URL**: `http://localhost:7010`
   - **Shared secret**: the value from step 2
   - **Tenant identifier**: optional string (for example `demo-tenant`) used for ledger separation.
4. Save the configuration.

## 5. Use the issue panel

1. Open an issue that belongs to the active sprint (for example `DEV1-5`).
2. The Digital Spiral panel loads proposals from `GET /v1/jira/ingest` and displays comment, transition and label suggestions together with the estimated time savings.
3. Click **Explain** to view the reasoning for any proposal.
4. Click **Apply** on the comment suggestion. The button triggers `POST /v1/jira/apply` with an idempotency key and refreshes the proposal list after the orchestrator completes the Jira mutation.
5. Confirm the issue was updated (new comment or label) in the main Jira view.

## 6. Observe orchestrator ledger output

Query the ledger endpoint to verify the credit attribution and audit metadata:

```bash
curl -H "X-DS-Secret: $ORCH_SECRET" "http://localhost:7010/v1/ledger?issueKey=DEV1-5"
```

The response includes the history of applied actions, credit in seconds and the last webhook payload processed for the issue.

## 7. Optional follow-up checks

- Inspect structured UI data: `curl -H "X-DS-Secret: $ORCH_SECRET" "http://localhost:7010/v1/jira/ingest?issueKey=DEV1-5"`.
- Verify idempotency by repeating the `Apply` action in the panel—the orchestrator replays the cached result and does not create duplicate comments.
- Review the HTML ledger dashboard at http://localhost:7010/ui for a quick overview of credit accumulation.

This workflow can be recorded as a short screen capture (60–90 seconds) to demonstrate the proposal → apply → ledger feedback loop end to end.
