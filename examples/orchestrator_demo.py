"""Mini orchestrator proof-of-concept built on top of the Jira adapter."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from clients.python.jira_adapter import JiraAdapter


def _adapter() -> JiraAdapter:
    return JiraAdapter(
        os.getenv("JIRA_BASE_URL", "http://localhost:9000"),
        os.getenv("JIRA_TOKEN", "mock-token"),
    )


def _ledger_path() -> Path:
    path = os.getenv("MOCKJIRA_LEDGER_PATH")
    if path:
        return Path(path)
    return Path(__file__).with_name("ledger.csv")


def main() -> Dict[str, Any]:
    adapter = _adapter()
    webhook_url = os.getenv("MOCKJIRA_WEBHOOK_URL")
    if webhook_url:
        adapter.register_webhook(webhook_url, "project = DEV", events=["jira:issue_created"])

    start = datetime.now()
    issue = adapter.create_issue(
        "SUP",
        "10003",
        "Orchestrator demo",
        description_adf={
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello orchestrator"}],
                }
            ],
        },
    )
    key = issue["key"]

    transitions = adapter.list_transitions(key)
    if transitions:
        adapter.transition_issue(key, transitions[0]["id"])

    search = adapter.search(f'key = "{key}"')
    adapter.add_comment(
        key,
        {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Draft reply: we are on it!",
                        }
                    ],
                }
            ],
        },
    )

    elapsed = (datetime.now() - start).total_seconds()
    ledger_row = {
        "ticket": issue["id"],
        "key": key,
        "delta_t": f"{elapsed:.2f}",
        "q": str(len(search.get("issues", []))),
        "credit": "ok",
    }

    ledger_file = _ledger_path()
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    file_exists = ledger_file.exists()
    with ledger_file.open("a", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(ledger_row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(ledger_row)

    return {"issue": issue, "ledger": str(ledger_file)}


if __name__ == "__main__":  # pragma: no cover
    main()
