#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

TENANT_ID=${DEMO_TENANT:-demo}
TENANT_SECRET=${DEMO_SECRET:-forge-dev-secret}
ORCH_URL=${ORCH_URL:-http://localhost:7010}
JIRA_BASE=${JIRA_BASE_URL:-http://localhost:9000}
JIRA_TOKEN=${JIRA_TOKEN:-mock-token}

printf 'Starting core services...\n'
docker compose up -d postgres mock-jira mock-jira-seed orchestrator >/dev/null

printf 'Waiting for orchestrator readiness'
for _ in $(seq 1 60); do
  if curl -sSf "${ORCH_URL}/readyz" >/dev/null 2>&1; then
    printf '\n'
    break
  fi
  printf '.'
  sleep 2
  if [[ $_ == 60 ]]; then
    echo "\nOrchestrator failed to become ready" >&2
    exit 1
  fi

done

ISSUE_KEY=$(python - <<'PY'
import os
from clients.python.jira_adapter import JiraAdapter

adapter = JiraAdapter(os.getenv("JIRA_BASE_URL", "http://localhost:9000"), os.getenv("JIRA_TOKEN", "mock-token"))
issue = adapter.create_issue(
    "SUP",
    "10003",
    "Demo orchestration",
    description_adf={
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Demo run from scripts/demo.sh"}]}
        ],
    },
)
print(issue["key"])
PY
)

if [[ -z "${ISSUE_KEY}" ]]; then
  echo "Failed to create demo issue" >&2
  exit 1
fi

export ISSUE_KEY

forge_sig() {
  python - <<'PY' "$TENANT_SECRET" "$1"
import hashlib
import sys
secret = sys.argv[1]
body = sys.argv[2].encode("utf-8")
print(hashlib.sha256(secret.encode("utf-8") + body).hexdigest())
PY
}

post_apply() {
  local body=$1
  local idem=$2
  local signature
  signature=$(forge_sig "$body")
  curl -sSf \
    -X POST "${ORCH_URL}/v1/jira/apply" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: ${idem}" \
    -H "X-Tenant-Id: ${TENANT_ID}" \
    -H "X-DS-Secret: ${TENANT_SECRET}" \
    -H "X-Forge-Signature: ${signature}" \
    -H "X-DS-Actor: human.demo" \
    --data "${body}" >/dev/null
}

APPLY_BODY_1=$(python - <<'PY'
import json
import os
issue_key = os.environ["ISSUE_KEY"]
payload = {
    "issueKey": issue_key,
    "action": {
        "id": "demo-comment",
        "kind": "comment",
        "body_adf": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Follow-up from automation."}
                    ],
                }
            ],
        },
    },
}
print(json.dumps(payload, separators=(",", ":")))
PY
)

APPLY_BODY_2=$(python - <<'PY'
import json
import os
issue_key = os.environ["ISSUE_KEY"]
payload = {
    "issueKey": issue_key,
    "action": {
        "id": "demo-label",
        "kind": "set-labels",
        "labels": ["automation", "demo"],
        "mode": "merge",
    },
}
print(json.dumps(payload, separators=(",", ":")))
PY
)

post_apply "$APPLY_BODY_1" "$(uuidgen)"
post_apply "$APPLY_BODY_2" "$(uuidgen)"

mkdir -p artifacts
python scripts/report_credit_value.py --tenant "$TENANT_ID" --window 14d --out artifacts/report.md

echo "Report written to artifacts/report.md"
