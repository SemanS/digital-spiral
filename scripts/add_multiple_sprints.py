#!/usr/bin/env python3
"""Add multiple sprints with realistic timeline to project.

This script:
1. Creates 12 sprints (4 closed, 2 active, 6 future)
2. Sets realistic dates (2-week sprints)
3. Adds sprint goals
4. Distributes tickets across sprints

Usage:
    python scripts/add_multiple_sprints.py \
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

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


# Sprint definitions with goals
SPRINT_DEFINITIONS = [
    # Closed sprints (past)
    {"name": "Sprint 1 - Foundation", "goal": "Setup infrastructure and core framework", "offset_start": -168, "offset_end": -154},
    {"name": "Sprint 2 - Jira Integration", "goal": "Connect to Jira Cloud API and webhooks", "offset_start": -154, "offset_end": -140},
    {"name": "Sprint 3 - AI Analysis", "goal": "Implement AI ticket classification and sentiment analysis", "offset_start": -140, "offset_end": -126},
    {"name": "Sprint 4 - Response Generation", "goal": "Build automated response system with templates", "offset_start": -126, "offset_end": -112},
    
    # Active sprints (current)
    {"name": "Sprint 5 - Dashboard UI", "goal": "Build analytics dashboard with real-time metrics", "offset_start": -14, "offset_end": 0},
    {"name": "Sprint 6 - Performance", "goal": "Optimize for production scale with caching", "offset_start": 0, "offset_end": 14},
    
    # Future sprints (planned)
    {"name": "Sprint 7 - Security", "goal": "Add authentication, authorization, and audit logs", "offset_start": 14, "offset_end": 28},
    {"name": "Sprint 8 - Integrations", "goal": "Add Slack, Teams, and email integrations", "offset_start": 28, "offset_end": 42},
    {"name": "Sprint 9 - Mobile", "goal": "Build mobile-responsive UI and PWA support", "offset_start": 42, "offset_end": 56},
    {"name": "Sprint 10 - Analytics", "goal": "Advanced analytics and reporting features", "offset_start": 56, "offset_end": 70},
    {"name": "Sprint 11 - AI Improvements", "goal": "Fine-tune AI models and add custom training", "offset_start": 70, "offset_end": 84},
    {"name": "Sprint 12 - Launch Prep", "goal": "Final testing, documentation, and launch preparation", "offset_start": 84, "offset_end": 98},
]


def main():
    parser = argparse.ArgumentParser(description="Add multiple sprints to project")
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
    
    print(f"\n🏃 Adding {len(SPRINT_DEFINITIONS)} sprints to {args.project}...")
    print(f"   - 4 closed sprints (past)")
    print(f"   - 2 active sprints (current)")
    print(f"   - 6 future sprints (planned)")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)
    
    # Step 1: Find board
    print("\n1️⃣ Finding board...")
    boards_response = adapter.list_boards()
    boards = boards_response.get("values", [])
    
    project_board = None
    for board in boards:
        location = board.get("location", {})
        if location.get("projectKey") == args.project:
            project_board = board
            break
    
    if not project_board:
        print(f"❌ No board found for project {args.project}")
        sys.exit(1)
    
    board_id = project_board["id"]
    print(f"✓ Found board: {project_board['name']} (ID: {board_id})")
    
    # Step 2: Create sprints
    print("\n2️⃣ Creating sprints...")
    now = datetime.now()
    created_sprints = []
    
    for sprint_def in SPRINT_DEFINITIONS:
        start_date = (now + timedelta(days=sprint_def["offset_start"])).isoformat()
        end_date = (now + timedelta(days=sprint_def["offset_end"])).isoformat()
        
        try:
            sprint = adapter.create_sprint(
                board_id=board_id,
                name=sprint_def["name"],
                start_date=start_date,
                end_date=end_date,
                goal=sprint_def["goal"]
            )
            created_sprints.append(sprint)
            print(f"   ✓ {sprint_def['name']}")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ Failed to create {sprint_def['name']}: {e}")
    
    # Step 3: Update sprint states
    print("\n3️⃣ Updating sprint states...")
    update_sprint_states(adapter, created_sprints)
    
    # Step 4: Get tickets and distribute
    print("\n4️⃣ Distributing tickets across sprints...")
    distribute_tickets(adapter, args.project, created_sprints)
    
    print("\n✅ All sprints created successfully!")
    print(f"\n🔗 View in Jira:")
    print(f"   {args.base_url}/jira/software/c/projects/{args.project}/boards/{board_id}")


def update_sprint_states(adapter: JiraCloudAdapter, sprints: list[dict]) -> None:
    """Update sprint states based on dates."""
    
    now = datetime.now()
    
    for sprint in sprints:
        sprint_id = sprint["id"]
        sprint_name = sprint["name"]
        
        # Parse dates
        start_date_str = sprint.get("startDate")
        end_date_str = sprint.get("endDate")
        
        if not start_date_str or not end_date_str:
            continue
        
        start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        
        # Determine correct state
        if end_date < now:
            target_state = "closed"
        elif start_date <= now <= end_date:
            target_state = "active"
        else:
            target_state = "future"
        
        try:
            adapter.update_sprint(sprint_id, state=target_state)
            print(f"   ✓ {sprint_name}: {target_state}")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠ Failed to update {sprint_name}: {e}")


def distribute_tickets(adapter: JiraCloudAdapter, project_key: str, sprints: list[dict]) -> None:
    """Distribute tickets across sprints."""
    
    # Get all tickets
    all_issues = []
    start_at = 0
    max_results = 50
    
    while True:
        result = adapter._call(
            "GET",
            "/rest/api/3/search",
            params={
                "jql": f"project = {project_key} ORDER BY created ASC",
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "key,summary"
            }
        )
        
        issues = result.get("issues", [])
        all_issues.extend(issues)
        
        if len(issues) < max_results:
            break
        
        start_at += max_results
    
    if not all_issues:
        print("   ⚠ No tickets found to distribute")
        return
    
    print(f"   Found {len(all_issues)} tickets")
    
    # Distribute tickets evenly across sprints
    tickets_per_sprint = max(1, len(all_issues) // len(sprints))
    
    for i, sprint in enumerate(sprints):
        start_idx = i * tickets_per_sprint
        end_idx = start_idx + tickets_per_sprint if i < len(sprints) - 1 else len(all_issues)
        sprint_issues = all_issues[start_idx:end_idx]
        
        if sprint_issues:
            issue_keys = [issue["key"] for issue in sprint_issues]
            try:
                adapter.move_issues_to_sprint(sprint["id"], issue_keys)
                print(f"   ✓ {sprint['name']}: {len(issue_keys)} tickets")
                time.sleep(0.5)
            except Exception as e:
                print(f"   ⚠ Failed to assign tickets to {sprint['name']}: {e}")


if __name__ == "__main__":
    main()

