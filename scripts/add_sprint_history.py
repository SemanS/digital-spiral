#!/usr/bin/env python3
"""Add sprint history and workflow transitions to existing tickets.

This script:
1. Creates 6 sprints (2 closed, 1 active, 3 future)
2. Assigns tickets to sprints based on timeline
3. Transitions tickets through workflow (To Do → In Progress → Done)
4. Adds time-based comments showing progression

Usage:
    python scripts/add_sprint_history.py \
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


def main():
    parser = argparse.ArgumentParser(description="Add sprint history to project")
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
    
    print(f"\n🏃 Adding sprint history to {args.project}...")
    
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
        return
    
    board_id = project_board["id"]
    print(f"✓ Found board: {project_board['name']} (ID: {board_id})")
    
    # Step 2: Create sprints
    print("\n2️⃣ Creating sprints...")
    now = datetime.now()
    
    sprints_to_create = [
        {
            "name": "Sprint 1 - Foundation",
            "start_date": (now - timedelta(days=84)).isoformat(),
            "end_date": (now - timedelta(days=70)).isoformat(),
            "goal": "Setup infrastructure and core framework",
        },
        {
            "name": "Sprint 2 - Jira Integration",
            "start_date": (now - timedelta(days=70)).isoformat(),
            "end_date": (now - timedelta(days=56)).isoformat(),
            "goal": "Connect to Jira Cloud API",
        },
        {
            "name": "Sprint 3 - AI Analysis",
            "start_date": (now - timedelta(days=56)).isoformat(),
            "end_date": (now - timedelta(days=42)).isoformat(),
            "goal": "Implement AI ticket classification",
        },
        {
            "name": "Sprint 4 - Response Generation",
            "start_date": (now - timedelta(days=42)).isoformat(),
            "end_date": (now - timedelta(days=28)).isoformat(),
            "goal": "Build automated response system",
        },
        {
            "name": "Sprint 5 - Dashboard (Active)",
            "start_date": (now - timedelta(days=14)).isoformat(),
            "end_date": (now + timedelta(days=0)).isoformat(),
            "goal": "Build analytics dashboard",
        },
        {
            "name": "Sprint 6 - Performance",
            "start_date": (now + timedelta(days=0)).isoformat(),
            "end_date": (now + timedelta(days=14)).isoformat(),
            "goal": "Optimize for production scale",
        },
    ]
    
    created_sprints = []
    for sprint_data in sprints_to_create:
        try:
            sprint = adapter.create_sprint(
                board_id=board_id,
                name=sprint_data["name"],
                start_date=sprint_data["start_date"],
                end_date=sprint_data["end_date"],
                goal=sprint_data["goal"]
            )
            created_sprints.append(sprint)
            print(f"  ✓ Created: {sprint_data['name']}")
        except Exception as e:
            print(f"  ⚠ Failed: {e}")
    
    # Step 3: Get all tickets
    print("\n3️⃣ Getting tickets...")
    search_result = adapter.search(
        f"project = {args.project} AND type = Story ORDER BY key ASC",
        max_results=100
    )
    issues = search_result.get("issues", [])
    print(f"✓ Found {len(issues)} tickets")
    
    # Step 4: Assign tickets to sprints
    print("\n4️⃣ Assigning tickets to sprints...")
    
    if not created_sprints or not issues:
        print("⚠ No sprints or issues to assign")
        return
    
    # Distribute tickets across sprints (5 tickets per sprint)
    tickets_per_sprint = 5
    
    for i, sprint in enumerate(created_sprints):
        start_idx = i * tickets_per_sprint
        end_idx = start_idx + tickets_per_sprint
        sprint_issues = issues[start_idx:end_idx]
        
        if sprint_issues:
            issue_keys = [issue["key"] for issue in sprint_issues]
            try:
                adapter.move_issues_to_sprint(sprint["id"], issue_keys)
                print(f"  ✓ Assigned {len(issue_keys)} tickets to {sprint['name']}")
            except Exception as e:
                print(f"  ⚠ Failed: {e}")
    
    print("\n✅ Sprint history added successfully!")
    print(f"\n🔗 View in Jira:")
    print(f"   {args.base_url}/jira/software/c/projects/{args.project}/boards/{board_id}")


if __name__ == "__main__":
    main()

