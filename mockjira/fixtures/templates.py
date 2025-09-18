"""Reusable text templates for the deterministic Jira generator."""

SUMMARY_TOPICS = [
    "Checkout fails with HTTP 500",
    "Latency spike on search endpoint",
    "Add SSO support for administrators",
    "Password reset flow is broken",
    "Mobile push notification bug",
    "Improve structured logging",
    "Customer satisfaction drop investigation",
    "Refactor payments client",
    "Analytics pipeline intermittently stalls",
    "Upgrade database driver",
]

COMMENT_TEMPLATES = [
    "Investigating the report",
    "Able to reproduce the problem",
    "Working on a potential fix",
    "Need more diagnostic logs",
    "Verifying with the QA checklist",
    "Coordinating with on-call engineer",
]

SPRINT_GOALS = [
    "Stabilise core flows",
    "New feature experiments",
    "Bugfix and polish",
    "Platform hardening",
]

REQUEST_SUMMARIES = [
    "Reset VPN access",
    "Provision new laptop",
    "Restore deleted mailbox",
    "Troubleshoot billing discrepancy",
]

REQUEST_DESCRIPTIONS = [
    "Customer reported an outage while accessing the dashboard.",
    "High priority ticket from premium tenant awaiting action.",
    "Requester is blocked on completing onboarding tasks.",
    "Follow-up needed with the infrastructure team.",
]
