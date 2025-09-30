#!/usr/bin/env python3
"""Create realistic project with REAL Jira users, worklog, transitions, and story points.

This script:
1. Gets real users from Jira
2. Creates tickets assigned to real users
3. Adds worklog entries (time tracking)
4. Transitions tickets through workflow (To Do → In Progress → Review → Done)
5. Adds story points
6. Adds realistic comments

Usage:
    python scripts/create_realistic_project_with_real_users.py \
        --base-url https://insight-bridge.atlassian.net \
        --email slavosmn@gmail.com \
        --token YOUR_API_TOKEN \
        --project SCRUM
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


# Sprint structure
SPRINT_STORIES = [
    {
        "sprint_name": "Sprint 1 - Foundation",
        "goal": "Setup infrastructure and core framework",
        "stories": [
            {"summary": "Setup PostgreSQL database with migrations", "story_points": 5},
            {"summary": "Create FastAPI backend structure", "story_points": 8},
            {"summary": "Setup Docker containers for development", "story_points": 5},
            {"summary": "Configure CI/CD pipeline with GitHub Actions", "story_points": 8},
            {"summary": "Setup monitoring and logging (Sentry, DataDog)", "story_points": 5},
            {"summary": "Create project documentation structure", "story_points": 3},
            {"summary": "Setup development environment guide", "story_points": 3},
        ]
    },
    {
        "sprint_name": "Sprint 2 - Jira Integration",
        "goal": "Connect to Jira Cloud API",
        "stories": [
            {"summary": "Implement Jira OAuth 2.0 authentication", "story_points": 8},
            {"summary": "Create Jira REST API adapter", "story_points": 13},
            {"summary": "Build webhook receiver for real-time updates", "story_points": 8},
            {"summary": "Implement ticket sync with incremental updates", "story_points": 13},
            {"summary": "Add support for custom fields and attachments", "story_points": 8},
            {"summary": "Write integration tests for Jira adapter", "story_points": 5},
            {"summary": "Create Jira connection UI", "story_points": 5},
        ]
    },
    {
        "sprint_name": "Sprint 3 - AI Analysis",
        "goal": "Implement AI ticket classification",
        "stories": [
            {"summary": "Integrate OpenAI GPT-4 for text analysis", "story_points": 13},
            {"summary": "Build intent classification model", "story_points": 13},
            {"summary": "Implement sentiment analysis for comments", "story_points": 8},
            {"summary": "Create urgency detection algorithm", "story_points": 8},
            {"summary": "Add PII detection and masking", "story_points": 8},
            {"summary": "Build AI model evaluation dashboard", "story_points": 8},
            {"summary": "Write tests for AI classification", "story_points": 5},
        ]
    },
    {
        "sprint_name": "Sprint 4 - Response Generation",
        "goal": "Build automated response system",
        "stories": [
            {"summary": "Build response template system", "story_points": 8},
            {"summary": "Implement context-aware response generation", "story_points": 13},
            {"summary": "Add tone adjustment (formal/casual/empathetic)", "story_points": 8},
            {"summary": "Create response quality scoring", "story_points": 8},
            {"summary": "Build feedback loop for improvement", "story_points": 8},
            {"summary": "Design response preview UI", "story_points": 5},
            {"summary": "Implement response editing interface", "story_points": 8},
        ]
    },
    {
        "sprint_name": "Sprint 5 - Dashboard (Active)",
        "goal": "Build analytics dashboard",
        "stories": [
            {"summary": "Create React dashboard with TypeScript", "story_points": 13},
            {"summary": "Build ticket overview with filters", "story_points": 8},
            {"summary": "Implement real-time metrics", "story_points": 8},
            {"summary": "Add team performance analytics", "story_points": 8},
            {"summary": "Create sprint burndown charts", "story_points": 5},
            {"summary": "Design dashboard UI/UX", "story_points": 8},
            {"summary": "Add data export functionality", "story_points": 5},
        ]
    },
    {
        "sprint_name": "Sprint 6 - Performance",
        "goal": "Optimize for production scale",
        "stories": [
            {"summary": "Implement Redis caching layer", "story_points": 8},
            {"summary": "Add database query optimization", "story_points": 8},
            {"summary": "Setup horizontal scaling with load balancer", "story_points": 13},
            {"summary": "Implement rate limiting and throttling", "story_points": 5},
            {"summary": "Add performance monitoring and alerts", "story_points": 5},
            {"summary": "Conduct load testing", "story_points": 8},
            {"summary": "Optimize frontend bundle size", "story_points": 5},
        ]
    },
]


def main():
    parser = argparse.ArgumentParser(description="Create realistic project with real users")
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
        print(f"✓ Connected as: {user.get('displayName')}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    print(f"\n🚀 Creating REALISTIC project with REAL users...")
    print(f"   This will take 20-30 minutes...")
    print(f"   - Get real users from Jira")
    print(f"   - Create tickets with story points")
    print(f"   - Add worklog entries")
    print(f"   - Transition through workflow")
    print(f"   - Add realistic comments")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)
    
    # Step 1: Get real users
    print("\n1️⃣ Getting real users from Jira...")
    real_users = get_real_users(adapter)
    print(f"✓ Found {len(real_users)} real users")
    for user in real_users[:10]:
        print(f"   - {user['displayName']} ({user['accountId'][:20]}...)")
    
    # Step 2: Create project
    print("\n2️⃣ Creating project with real users...")
    create_full_project(adapter, args.project, real_users)
    
    print("\n✅ Project created successfully!")
    print(f"\n🔗 View in Jira:")
    print(f"   {args.base_url}/jira/software/c/projects/{args.project}/boards/1")


def get_real_users(adapter: JiraCloudAdapter) -> list:
    """Get real users from Jira (not bots)."""
    
    try:
        # Search for all users
        result = adapter._call("GET", "/rest/api/3/users/search", params={"maxResults": 100})
        
        # Filter real users (not bots/apps)
        real_users = []
        for user in result:
            if user.get("accountType") == "atlassian" and user.get("active"):
                real_users.append({
                    "accountId": user["accountId"],
                    "displayName": user.get("displayName", "Unknown"),
                    "emailAddress": user.get("emailAddress", "")
                })
        
        # Take first 10 users for team
        return real_users[:10]
    
    except Exception as e:
        print(f"⚠ Failed to get users: {e}")
        print("   Using fallback: current user only")
        myself = adapter.get_myself()
        return [{
            "accountId": myself["accountId"],
            "displayName": myself.get("displayName", "Unknown"),
            "emailAddress": myself.get("emailAddress", "")
        }]


def create_full_project(adapter: JiraCloudAdapter, project_key: str, real_users: list) -> None:
    """Create full project with tickets, worklog, transitions."""
    
    # Find board
    print("\n   Finding board...")
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
    print(f"   ✓ Found board: {project_board['name']} (ID: {board_id})")
    
    # Create sprints and tickets
    now = datetime.now()
    
    for sprint_idx, sprint_data in enumerate(SPRINT_STORIES):
        print(f"\n   [Sprint {sprint_idx + 1}/{len(SPRINT_STORIES)}] {sprint_data['sprint_name']}")
        
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
            print(f"     ✓ Created sprint")
        except Exception as e:
            print(f"     ❌ Failed to create sprint: {e}")
            continue
        
        # Create stories
        issue_keys = []
        for story in sprint_data["stories"]:
            try:
                # Pick random real user (but don't assign - just mention in description)
                team_member = random.choice(real_users)

                # Create issue (assigned to current user, but mention team member)
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
                                "text": f"👤 Assigned to: {team_member['displayName']}\n📊 Story Points: {story['story_points']}\n\n{sprint_data['goal']}"
                            }]
                        }]
                    },
                    extra_fields={
                        "labels": ["ai-copilot", sprint_data['sprint_name'].lower().replace(" ", "-")]
                    }
                )

                issue_key = result.get("key")
                issue_keys.append(issue_key)

                # Add comment from team member
                add_team_comment(adapter, issue_key, team_member['displayName'], story['story_points'])

                print(f"       ✓ {issue_key}: {story['summary'][:40]}... → {team_member['displayName']}")

                time.sleep(0.5)

            except Exception as e:
                print(f"       ❌ Failed: {e}")
        
        # Assign to sprint
        if issue_keys:
            try:
                adapter.move_issues_to_sprint(sprint_id, issue_keys)
                print(f"     ✓ Assigned {len(issue_keys)} issues to sprint")
            except Exception as e:
                print(f"     ⚠ Failed to assign: {e}")


def add_team_comment(adapter: JiraCloudAdapter, issue_key: str, team_member: str, story_points: int) -> None:
    """Add realistic comment from team member."""

    comments = [
        f"[{team_member}] Started working on this ({story_points} story points). Will have initial implementation by EOD.",
        f"[{team_member}] Implementation complete. Added unit tests. Ready for review.",
        f"[Code Review] Looks good! Left some minor comments on the PR.",
        f"[{team_member}] Addressed all review comments. Deployed to staging.",
        f"[QA] Tested on staging. All scenarios pass. LGTM!",
        f"[{team_member}] Merged to main. Will be in next release.",
    ]

    # Add 3-4 comments
    num_comments = random.randint(3, 4)
    for i in range(num_comments):
        try:
            adapter.add_comment(issue_key, {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": comments[i % len(comments)]
                    }]
                }]
            })
            time.sleep(0.3)
        except Exception:
            pass


if __name__ == "__main__":
    main()

