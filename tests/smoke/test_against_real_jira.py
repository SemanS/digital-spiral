from __future__ import annotations

import os

import pytest

from clients.python.jira_adapter import JiraAdapter

REAL_URL = os.getenv("REAL_JIRA_URL")
REAL_TOKEN = os.getenv("REAL_JIRA_TOKEN")


@pytest.mark.skipif(
    not REAL_URL or not REAL_TOKEN,
    reason="REAL_JIRA_URL and REAL_JIRA_TOKEN environment variables required",
)
def test_smoke_search_against_real_jira() -> None:
    adapter = JiraAdapter(REAL_URL, REAL_TOKEN)
    result = adapter.search("order by updated DESC", max_results=1)
    assert "issues" in result
