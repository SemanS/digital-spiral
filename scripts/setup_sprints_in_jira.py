#!/usr/bin/env python3
"""Setup sprints in Jira Cloud project.

This script:
1. Finds the board for the project
2. Creates sprints with realistic dates
3. Assigns existing issues to sprints

Usage:
    python scripts/setup_sprints_in_jira.py \
        --base-url https://insight-bridge.atlassian.net \
        --email slavosmn@gmail.com \
        --token YOUR_API_TOKEN \
        --project SCRUM
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def setup_sprints(adapter: JiraCloudAdapter, project_key: str) -> None:
    """Setup sprints for a project."""
    
    print(f"\n🏃 Setting up sprints for project: {project_key}\n")
    
    # 1. Find board for project
    print("1️⃣ Finding board...")
    boards_response = adapter.list_boards()
    boards = boards_response.get("values", [])
    
    project_board = None
    for board in boards:
        # Check if board belongs to our project
        location = board.get("location", {})
        if location.get("projectKey") == project_key:
            project_board = board
            break
    
    if not project_board:
        print(f"❌ No board found for project {project_key}")
        print(f"   Available boards: {[b.get('name') for b in boards]}")
        print(f"\n💡 Create a board in Jira first:")
        print(f"   https://insight-bridge.atlassian.net/jira/software/c/projects/{project_key}/boards")
        return
    
    board_id = project_board["id"]
    board_name = project_board["name"]
    print(f"✓ Found board: {board_name} (ID: {board_id})")
    
    # 2. Check existing sprints
    print(f"\n2️⃣ Checking existing sprints...")
    sprints_response = adapter.list_sprints(board_id)
    existing_sprints = sprints_response.get("values", [])
    print(f"✓ Found {len(existing_sprints)} existing sprints")
    
    # 3. Create new sprints
    print(f"\n3️⃣ Creating sprints...")
    
    now = datetime.now()
    sprints_to_create = [
        {
            "name": "Sprint 1 - Foundation",
            "start_date": (now - timedelta(days=28)).isoformat(),
            "end_date": (now - timedelta(days=14)).isoformat(),
            "goal": "Setup infrastructure and basic features",
            "state": "closed"
        },
        {
            "name": "Sprint 2 - Core Features",
            "start_date": (now - timedelta(days=14)).isoformat(),
            "end_date": now.isoformat(),
            "goal": "Implement core support features",
            "state": "closed"
        },
        {
            "name": "Sprint 3 - AI Integration",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=14)).isoformat(),
            "goal": "Integrate AI-powered ticket analysis",
            "state": "active"
        },
        {
            "name": "Sprint 4 - Polish & Testing",
            "start_date": (now + timedelta(days=14)).isoformat(),
            "end_date": (now + timedelta(days=28)).isoformat(),
            "goal": "Polish UI and comprehensive testing",
            "state": "future"
        }
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
            print(f"  ⚠ Failed to create {sprint_data['name']}: {e}")
    
    print(f"\n✓ Created {len(created_sprints)} sprints")
    
    # 4. Assign issues to sprints
    print(f"\n4️⃣ Assigning issues to sprints...")
    
    # Get all issues in project
    search_result = adapter.search(f"project = {project_key} ORDER BY created ASC", max_results=100)
    issues = search_result.get("issues", [])
    
    if not issues:
        print("⚠ No issues found to assign")
        return
    
    print(f"✓ Found {len(issues)} issues")
    
    # Distribute issues across sprints
    if created_sprints:
        issues_per_sprint = len(issues) // len(created_sprints)
        
        for i, sprint in enumerate(created_sprints):
            start_idx = i * issues_per_sprint
            end_idx = start_idx + issues_per_sprint if i < len(created_sprints) - 1 else len(issues)
            sprint_issues = issues[start_idx:end_idx]
            
            if sprint_issues:
                issue_keys = [issue["key"] for issue in sprint_issues]
                try:
                    adapter.move_issues_to_sprint(sprint["id"], issue_keys)
                    print(f"  ✓ Assigned {len(issue_keys)} issues to {sprint['name']}")
                except Exception as e:
                    print(f"  ⚠ Failed to assign issues to {sprint['name']}: {e}")
    
    print(f"\n✅ Sprint setup complete!")
    print(f"\n💡 View sprints in Jira:")
    print(f"   https://insight-bridge.atlassian.net/jira/software/c/projects/{project_key}/boards/{board_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Setup sprints in Jira Cloud project"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Jira base URL (e.g., https://insight-bridge.atlassian.net)"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Jira account email"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Jira API token"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Project key (e.g., SCRUM)"
    )
    
    args = parser.parse_args()
    
    # Create adapter
    adapter = JiraCloudAdapter(args.base_url, args.email, args.token)
    
    # Test connection
    try:
        user = adapter.get_myself()
        print(f"✓ Connected as: {user.get('displayName')} ({user.get('emailAddress')})")
    except Exception as e:
        print(f"❌ Failed to connect to Jira: {e}")
        sys.exit(1)
    
    # Setup sprints
    setup_sprints(adapter, args.project)


if __name__ == "__main__":
    main()

