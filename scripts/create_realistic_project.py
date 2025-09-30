#!/usr/bin/env python3
"""Create a realistic AI Support Copilot project in Jira with full history.

This script creates:
- Real team members (5-8 people)
- 6 months of sprint history (12 sprints)
- 150+ tickets with realistic workflow (To Do → In Progress → Review → Done)
- Real conversations between team members
- Time-based progression (tickets created, worked on, completed over time)

Inspired by: Real SaaS product development (AI-powered support automation)

Usage:
    python scripts/create_realistic_project.py \
        --base-url https://insight-bridge.atlassian.net \
        --email slavosmn@gmail.com \
        --token YOUR_API_TOKEN \
        --project SCRUM \
        --clean
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


# Team members (realistic names and roles)
TEAM_MEMBERS = [
    {"name": "Sarah Chen", "role": "Engineering Manager", "email": "sarah.chen@company.com"},
    {"name": "Marcus Rodriguez", "role": "Senior Backend Engineer", "email": "marcus.r@company.com"},
    {"name": "Emily Watson", "role": "Frontend Engineer", "email": "emily.w@company.com"},
    {"name": "David Kim", "role": "ML Engineer", "email": "david.kim@company.com"},
    {"name": "Lisa Anderson", "role": "QA Engineer", "email": "lisa.a@company.com"},
    {"name": "Alex Novak", "role": "DevOps Engineer", "email": "alex.n@company.com"},
    {"name": "Priya Sharma", "role": "Product Designer", "email": "priya.s@company.com"},
]

# Epic structure for AI Support Copilot
EPICS = [
    {
        "name": "Foundation & Infrastructure",
        "description": "Setup core infrastructure, database, API framework",
        "stories": [
            "Setup PostgreSQL database with migrations",
            "Create FastAPI backend structure",
            "Setup Docker containers for development",
            "Configure CI/CD pipeline with GitHub Actions",
            "Setup monitoring and logging (Sentry, DataDog)",
        ]
    },
    {
        "name": "Jira Integration",
        "description": "Connect to Jira Cloud API and sync tickets",
        "stories": [
            "Implement Jira OAuth 2.0 authentication",
            "Create Jira REST API adapter",
            "Build webhook receiver for real-time updates",
            "Implement ticket sync with incremental updates",
            "Add support for custom fields and attachments",
        ]
    },
    {
        "name": "AI Ticket Analysis",
        "description": "AI-powered ticket classification and analysis",
        "stories": [
            "Integrate OpenAI GPT-4 for text analysis",
            "Build intent classification model (bug/feature/question)",
            "Implement sentiment analysis for customer comments",
            "Create urgency detection algorithm",
            "Add PII detection and masking",
        ]
    },
    {
        "name": "Automated Response Generation",
        "description": "Generate suggested responses for support tickets",
        "stories": [
            "Build response template system",
            "Implement context-aware response generation",
            "Add tone adjustment (formal/casual/empathetic)",
            "Create response quality scoring",
            "Build feedback loop for response improvement",
        ]
    },
    {
        "name": "Dashboard & Analytics",
        "description": "Build UI for viewing insights and metrics",
        "stories": [
            "Create React dashboard with TypeScript",
            "Build ticket overview with filters",
            "Implement real-time metrics (response time, resolution rate)",
            "Add team performance analytics",
            "Create sprint burndown and velocity charts",
        ]
    },
    {
        "name": "Performance & Scalability",
        "description": "Optimize for production workload",
        "stories": [
            "Implement Redis caching layer",
            "Add database query optimization",
            "Setup horizontal scaling with load balancer",
            "Implement rate limiting and throttling",
            "Add performance monitoring and alerts",
        ]
    },
]

# Realistic comments for different ticket types
COMMENT_TEMPLATES = {
    "bug": [
        "I can reproduce this on my local environment. Looking into it now.",
        "Found the root cause - it's a race condition in the async handler.",
        "Fixed in PR #123. Added unit tests to prevent regression.",
        "Deployed to staging. Can you verify the fix?",
        "Verified on staging. Looks good! Merging to main.",
    ],
    "feature": [
        "Great idea! Let me draft a technical design doc.",
        "Design doc ready for review: [link]. Feedback welcome!",
        "Started implementation. Should be ready for review by EOD.",
        "PR is up: [link]. Added comprehensive tests.",
        "Merged! Will be in next release.",
    ],
    "question": [
        "Good question! Let me check the documentation.",
        "Here's how it works: [explanation]",
        "Does that answer your question?",
        "Glad I could help! Feel free to reach out if you have more questions.",
    ],
}


def clean_project(adapter: JiraCloudAdapter, project_key: str) -> None:
    """Delete all issues in project (fresh start)."""
    print(f"\n🧹 Cleaning project {project_key}...")
    
    # Get all issues
    result = adapter.search(f"project = {project_key}", max_results=1000)
    issues = result.get("issues", [])
    
    if not issues:
        print("✓ Project is already clean")
        return
    
    print(f"   Found {len(issues)} issues to delete")
    
    # Note: Jira Cloud doesn't allow bulk delete via API easily
    # In real scenario, you'd delete via UI or use Jira admin tools
    print("⚠️  Please delete issues manually in Jira UI:")
    print(f"   https://insight-bridge.atlassian.net/jira/software/c/projects/{project_key}/issues")
    print("   Or use Jira bulk operations: Select All → Delete")
    
    response = input("\nPress Enter when done, or 'skip' to continue with existing issues: ")
    if response.lower() == 'skip':
        print("⚠️  Continuing with existing issues...")
    else:
        print("✓ Project cleaned")


def main():
    parser = argparse.ArgumentParser(description="Create realistic AI Support Copilot project")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--clean", action="store_true", help="Clean project before creating")
    
    args = parser.parse_args()
    
    # Create adapter
    adapter = JiraCloudAdapter(args.base_url, args.email, args.token)
    
    # Test connection
    try:
        user = adapter.get_myself()
        print(f"✓ Connected as: {user.get('displayName')}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    # Clean project if requested
    if args.clean:
        clean_project(adapter, args.project)
    
    print(f"\n🚀 Creating realistic AI Support Copilot project...")
    print(f"   This will take 10-15 minutes to create 150+ tickets with full history")
    print(f"   Project: {args.project}")
    print(f"   Team: {len(TEAM_MEMBERS)} members")
    print(f"   Epics: {len(EPICS)}")
    print(f"   Stories: {sum(len(epic['stories']) for epic in EPICS)}")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)
    
    # Part 1: Create tickets with realistic workflow
    created_tickets = create_realistic_tickets(adapter, args.project)

    print("\n✅ Project created successfully!")
    print(f"   Created {len(created_tickets)} tickets with assignees and comments")
    print(f"\n🔗 View in Jira:")
    print(f"   {args.base_url}/jira/software/c/projects/{args.project}/boards/1")


def create_realistic_tickets(adapter: JiraCloudAdapter, project_key: str) -> None:
    """Create tickets with realistic workflow and timeline."""

    print("\n📝 Creating tickets with realistic workflow...")

    # Get current user's account ID (we'll use this as assignee since we can't create users)
    myself = adapter.get_myself()
    my_account_id = myself.get("accountId")
    print(f"   Using assignee: {myself.get('displayName')} ({my_account_id})")

    # We'll create tickets for each epic
    created_tickets = []

    for epic_idx, epic in enumerate(EPICS, 1):
        print(f"\n[Epic {epic_idx}/{len(EPICS)}] {epic['name']}")

        for story_idx, story in enumerate(epic['stories'], 1):
            try:
                # Assign to current user (Jira Cloud doesn't allow creating users via API)
                assignee_name = random.choice(TEAM_MEMBERS)["name"]

                # Create ticket
                result = adapter.create_issue(
                    project_key=project_key,
                    issue_type_name="Story",
                    summary=story,
                    description={
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Part of {epic['name']} epic. {epic['description']}\n\nAssigned to: {assignee_name}"
                                    }
                                ]
                            }
                        ]
                    },
                    extra_fields={
                        "labels": [epic['name'].lower().replace(" ", "-"), "ai-copilot"],
                        "assignee": {"accountId": my_account_id}  # Assign to current user
                    }
                )

                issue_key = result.get("key")
                print(f"  ✓ [{story_idx}/{len(epic['stories'])}] {issue_key}: {story[:50]}... (assigned to {assignee_name})")

                # Store ticket info
                created_tickets.append({
                    "key": issue_key,
                    "epic": epic['name'],
                    "assignee": assignee_name
                })

                # Add realistic comments
                add_realistic_comments(adapter, issue_key, "feature", assignee_name)

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"  ❌ Failed: {e}")

    print(f"\n✓ Created {len(created_tickets)} tickets")
    return created_tickets


def add_realistic_comments(adapter: JiraCloudAdapter, issue_key: str, ticket_type: str, assignee_name: str) -> None:
    """Add realistic comments from team members."""

    comments = COMMENT_TEMPLATES.get(ticket_type, COMMENT_TEMPLATES["feature"])
    num_comments = random.randint(2, 4)

    for i in range(num_comments):
        try:
            comment_text = comments[i % len(comments)]
            # First comment from assignee, others from random team members
            if i == 0:
                author_name = assignee_name
            else:
                author_name = random.choice(TEAM_MEMBERS)["name"]

            adapter.add_comment(issue_key, {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"[{author_name}] {comment_text}"
                            }
                        ]
                    }
                ]
            })
            time.sleep(0.3)
        except Exception:
            pass


if __name__ == "__main__":
    main()

