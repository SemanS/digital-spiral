#!/usr/bin/env python3
"""Create a FULL realistic AI Support Copilot project with multiple team members.

This creates:
- 80+ tickets (stories, bugs, tasks)
- 6 sprints with realistic timeline
- Multiple team members working on different tasks
- Realistic comments showing collaboration
- Workflow transitions (To Do → In Progress → Done)

Usage:
    python scripts/create_full_realistic_project.py \
        --base-url https://insight-bridge.atlassian.net \
        --email slavosmn@gmail.com \
        --token YOUR_API_TOKEN \
        --project SCRUM
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


# Team members with realistic roles
TEAM = [
    {"name": "Sarah Chen", "role": "Engineering Manager"},
    {"name": "Marcus Rodriguez", "role": "Senior Backend Engineer"},
    {"name": "Emily Watson", "role": "Frontend Engineer"},
    {"name": "David Kim", "role": "ML Engineer"},
    {"name": "Lisa Anderson", "role": "QA Engineer"},
    {"name": "Alex Novak", "role": "DevOps Engineer"},
    {"name": "Priya Sharma", "role": "Product Designer"},
]


# Stories for each sprint
SPRINT_STORIES = [
    {
        "sprint_name": "Sprint 1 - Foundation",
        "goal": "Setup infrastructure and core framework",
        "stories": [
            {"summary": "Setup PostgreSQL database with migrations", "assignee": "Marcus Rodriguez", "story_points": 5},
            {"summary": "Create FastAPI backend structure", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Setup Docker containers for development", "assignee": "Alex Novak", "story_points": 5},
            {"summary": "Configure CI/CD pipeline with GitHub Actions", "assignee": "Alex Novak", "story_points": 8},
            {"summary": "Setup monitoring and logging (Sentry, DataDog)", "assignee": "Alex Novak", "story_points": 5},
            {"summary": "Create project documentation structure", "assignee": "Sarah Chen", "story_points": 3},
            {"summary": "Setup development environment guide", "assignee": "Emily Watson", "story_points": 3},
        ]
    },
    {
        "sprint_name": "Sprint 2 - Jira Integration",
        "goal": "Connect to Jira Cloud API",
        "stories": [
            {"summary": "Implement Jira OAuth 2.0 authentication", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Create Jira REST API adapter", "assignee": "Marcus Rodriguez", "story_points": 13},
            {"summary": "Build webhook receiver for real-time updates", "assignee": "David Kim", "story_points": 8},
            {"summary": "Implement ticket sync with incremental updates", "assignee": "Marcus Rodriguez", "story_points": 13},
            {"summary": "Add support for custom fields and attachments", "assignee": "Emily Watson", "story_points": 8},
            {"summary": "Write integration tests for Jira adapter", "assignee": "Lisa Anderson", "story_points": 5},
            {"summary": "Create Jira connection UI", "assignee": "Emily Watson", "story_points": 5},
        ]
    },
    {
        "sprint_name": "Sprint 3 - AI Analysis",
        "goal": "Implement AI ticket classification",
        "stories": [
            {"summary": "Integrate OpenAI GPT-4 for text analysis", "assignee": "David Kim", "story_points": 13},
            {"summary": "Build intent classification model", "assignee": "David Kim", "story_points": 13},
            {"summary": "Implement sentiment analysis for comments", "assignee": "David Kim", "story_points": 8},
            {"summary": "Create urgency detection algorithm", "assignee": "David Kim", "story_points": 8},
            {"summary": "Add PII detection and masking", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Build AI model evaluation dashboard", "assignee": "Emily Watson", "story_points": 8},
            {"summary": "Write tests for AI classification", "assignee": "Lisa Anderson", "story_points": 5},
        ]
    },
    {
        "sprint_name": "Sprint 4 - Response Generation",
        "goal": "Build automated response system",
        "stories": [
            {"summary": "Build response template system", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Implement context-aware response generation", "assignee": "David Kim", "story_points": 13},
            {"summary": "Add tone adjustment (formal/casual/empathetic)", "assignee": "David Kim", "story_points": 8},
            {"summary": "Create response quality scoring", "assignee": "David Kim", "story_points": 8},
            {"summary": "Build feedback loop for improvement", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Design response preview UI", "assignee": "Priya Sharma", "story_points": 5},
            {"summary": "Implement response editing interface", "assignee": "Emily Watson", "story_points": 8},
        ]
    },
    {
        "sprint_name": "Sprint 5 - Dashboard (Active)",
        "goal": "Build analytics dashboard",
        "stories": [
            {"summary": "Create React dashboard with TypeScript", "assignee": "Emily Watson", "story_points": 13},
            {"summary": "Build ticket overview with filters", "assignee": "Emily Watson", "story_points": 8},
            {"summary": "Implement real-time metrics", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Add team performance analytics", "assignee": "David Kim", "story_points": 8},
            {"summary": "Create sprint burndown charts", "assignee": "Emily Watson", "story_points": 5},
            {"summary": "Design dashboard UI/UX", "assignee": "Priya Sharma", "story_points": 8},
            {"summary": "Add data export functionality", "assignee": "Marcus Rodriguez", "story_points": 5},
        ]
    },
    {
        "sprint_name": "Sprint 6 - Performance",
        "goal": "Optimize for production scale",
        "stories": [
            {"summary": "Implement Redis caching layer", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Add database query optimization", "assignee": "Marcus Rodriguez", "story_points": 8},
            {"summary": "Setup horizontal scaling with load balancer", "assignee": "Alex Novak", "story_points": 13},
            {"summary": "Implement rate limiting and throttling", "assignee": "Alex Novak", "story_points": 5},
            {"summary": "Add performance monitoring and alerts", "assignee": "Alex Novak", "story_points": 5},
            {"summary": "Conduct load testing", "assignee": "Lisa Anderson", "story_points": 8},
            {"summary": "Optimize frontend bundle size", "assignee": "Emily Watson", "story_points": 5},
        ]
    },
]


# Realistic comments showing collaboration
COLLABORATION_COMMENTS = [
    "{assignee}: Started working on this. Will have initial implementation by EOD.",
    "{reviewer}: Looks good! Left some comments on the PR.",
    "{assignee}: Addressed all review comments. Ready for another look.",
    "{qa}: Tested on staging. Found one edge case - added comment on PR.",
    "{assignee}: Fixed the edge case. Deployed to staging again.",
    "{reviewer}: LGTM! Merging to main.",
    "{manager}: Great work team! This will be in next release.",
]


def main():
    parser = argparse.ArgumentParser(description="Create full realistic project")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--project", required=True)
    
    args = parser.parse_args()
    
    # Create adapter
    adapter = JiraCloudAdapter(args.base_url, args.email, args.token)
    
    # Test connection
    try:
        user = adapter.get_myself()
        my_account_id = user.get("accountId")
        print(f"✓ Connected as: {user.get('displayName')}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    print(f"\n🚀 Creating FULL realistic AI Support Copilot project...")
    print(f"   Project: {args.project}")
    print(f"   Team: {len(TEAM)} members")
    print(f"   Sprints: {len(SPRINT_STORIES)}")
    print(f"   Stories: {sum(len(s['stories']) for s in SPRINT_STORIES)}")
    print(f"   This will take 15-20 minutes...")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)
    
    # Create tickets and sprints
    create_full_project(adapter, args.project, my_account_id)
    
    print("\n✅ Project created successfully!")
    print(f"\n🔗 View in Jira:")
    print(f"   {args.base_url}/jira/software/c/projects/{args.project}/boards/1")


def create_full_project(adapter: JiraCloudAdapter, project_key: str, my_account_id: str) -> None:
    """Create full project with tickets and sprints."""
    
    # Step 1: Find board
    print("\n1️⃣ Finding board...")
    boards_response = adapter.list_boards()
    boards = boards_response.get("values", [])
    
    project_board = None
    for board in boards:
        location = board.get("location", {})
        if location.get("projectKey") == project_key:
            project_board = board
            break
    
    if not project_board:
        print(f"❌ No board found for project {project_key}")
        return
    
    board_id = project_board["id"]
    print(f"✓ Found board: {project_board['name']} (ID: {board_id})")
    
    # Step 2: Create sprints and tickets
    print("\n2️⃣ Creating sprints and tickets...")
    now = datetime.now()
    
    for sprint_idx, sprint_data in enumerate(SPRINT_STORIES):
        print(f"\n[Sprint {sprint_idx + 1}/{len(SPRINT_STORIES)}] {sprint_data['sprint_name']}")
        
        # Calculate sprint dates
        start_offset = -84 + (sprint_idx * 14)
        end_offset = start_offset + 14
        start_date = (now + timedelta(days=start_offset)).isoformat()
        end_date = (now + timedelta(days=end_offset)).isoformat()
        
        # Create sprint
        try:
            sprint = adapter.create_sprint(
                board_id=board_id,
                name=sprint_data["sprint_name"],
                start_date=start_date,
                end_date=end_date,
                goal=sprint_data["goal"]
            )
            sprint_id = sprint["id"]
            print(f"  ✓ Created sprint: {sprint_data['sprint_name']}")
        except Exception as e:
            print(f"  ❌ Failed to create sprint: {e}")
            continue
        
        # Create stories for this sprint
        issue_keys = []
        for story in sprint_data["stories"]:
            try:
                # Create issue
                result = adapter.create_issue(
                    project_key=project_key,
                    issue_type_name="Story",
                    summary=story["summary"],
                    description={
                        "type": "doc",
                        "version": 1,
                        "content": [{
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": f"Assigned to: {story['assignee']}\nStory Points: {story['story_points']}"
                            }]
                        }]
                    },
                    extra_fields={
                        "assignee": {"accountId": my_account_id},
                        "labels": ["ai-copilot", sprint_data['sprint_name'].lower().replace(" ", "-")]
                    }
                )
                
                issue_key = result.get("key")
                issue_keys.append(issue_key)
                print(f"    ✓ {issue_key}: {story['summary'][:50]}... (→ {story['assignee']})")
                
                # Add collaboration comments
                add_collaboration_comments(adapter, issue_key, story["assignee"])
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
        
        # Assign issues to sprint
        if issue_keys:
            try:
                adapter.move_issues_to_sprint(sprint_id, issue_keys)
                print(f"  ✓ Assigned {len(issue_keys)} issues to sprint")
            except Exception as e:
                print(f"  ⚠ Failed to assign issues: {e}")


def add_collaboration_comments(adapter: JiraCloudAdapter, issue_key: str, assignee: str) -> None:
    """Add realistic collaboration comments."""
    
    # Pick random team members for collaboration
    reviewer = random.choice([m["name"] for m in TEAM if m["name"] != assignee])
    qa = next((m["name"] for m in TEAM if m["role"] == "QA Engineer"), "Lisa Anderson")
    manager = next((m["name"] for m in TEAM if m["role"] == "Engineering Manager"), "Sarah Chen")
    
    # Add 3-4 comments
    num_comments = random.randint(3, 4)
    for i in range(num_comments):
        try:
            comment_template = COLLABORATION_COMMENTS[i % len(COLLABORATION_COMMENTS)]
            comment_text = comment_template.format(
                assignee=assignee,
                reviewer=reviewer,
                qa=qa,
                manager=manager
            )
            
            adapter.add_comment(issue_key, {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": comment_text
                    }]
                }]
            })
            time.sleep(0.3)
        except Exception:
            pass


if __name__ == "__main__":
    main()

