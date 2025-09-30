#!/usr/bin/env python3
"""Clean Jira project by deleting all issues.

Usage:
    python scripts/clean_jira_project.py \
        --base-url https://insight-bridge.atlassian.net \
        --email slavosmn@gmail.com \
        --token YOUR_API_TOKEN \
        --project SCRUM
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def main():
    parser = argparse.ArgumentParser(description="Clean Jira project")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation")
    
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
    
    print(f"\n🧹 Cleaning project {args.project}...")
    
    # Get all issues
    print("   Fetching all issues...")
    result = adapter.search(f"project = {args.project}", max_results=1000)
    issues = result.get("issues", [])
    
    if not issues:
        print("✓ Project is already clean (0 issues)")
        return
    
    print(f"   Found {len(issues)} issues to delete")
    
    # Show first 10 issues
    print("\n   First 10 issues:")
    for issue in issues[:10]:
        print(f"   - {issue['key']}: {issue['fields'].get('summary', 'No summary')}")
    
    if len(issues) > 10:
        print(f"   ... and {len(issues) - 10} more")
    
    # Confirm deletion
    if not args.confirm:
        print(f"\n⚠️  WARNING: This will delete ALL {len(issues)} issues in {args.project}!")
        response = input("   Type 'DELETE' to confirm: ")
        if response != 'DELETE':
            print("Cancelled")
            sys.exit(0)
    
    # Delete issues
    print(f"\n🗑️  Deleting {len(issues)} issues...")
    deleted_count = 0
    failed_count = 0
    
    for i, issue in enumerate(issues, 1):
        issue_key = issue["key"]
        try:
            adapter._call("DELETE", f"/rest/api/3/issue/{issue_key}")
            deleted_count += 1
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(issues)} deleted")
            time.sleep(0.2)  # Rate limiting
        except Exception as e:
            failed_count += 1
            print(f"   ⚠ Failed to delete {issue_key}: {e}")
    
    print(f"\n✅ Issues deleted!")
    print(f"   Deleted: {deleted_count}")
    print(f"   Failed: {failed_count}")

    # Delete sprints
    print(f"\n🗑️  Deleting sprints...")
    try:
        boards_response = adapter.list_boards()
        boards = boards_response.get("values", [])

        project_board = None
        for board in boards:
            location = board.get("location", {})
            if location.get("projectKey") == args.project:
                project_board = board
                break

        if project_board:
            board_id = project_board["id"]
            print(f"   Found board: {project_board['name']} (ID: {board_id})")

            # Get all sprints
            sprints_response = adapter.list_sprints(board_id)
            sprints = sprints_response.get("values", [])

            if sprints:
                print(f"   Found {len(sprints)} sprints to delete")

                for sprint in sprints:
                    try:
                        sprint_id = sprint["id"]
                        sprint_name = sprint["name"]
                        adapter._call("DELETE", f"/rest/agile/1.0/sprint/{sprint_id}")
                        print(f"   ✓ Deleted sprint: {sprint_name}")
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"   ⚠ Failed to delete sprint {sprint_name}: {e}")
            else:
                print("   No sprints to delete")
        else:
            print(f"   No board found for project {args.project}")
    except Exception as e:
        print(f"   ⚠ Failed to delete sprints: {e}")

    print(f"\n✅ Complete cleanup done!")


if __name__ == "__main__":
    main()

