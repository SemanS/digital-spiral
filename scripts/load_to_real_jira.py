#!/usr/bin/env python3
"""Load AI Support Copilot dummy data into a real Jira Cloud instance.

This script creates projects, users, and issues in your Jira Cloud instance
based on the AI Support Copilot seed data.

Usage:
    python scripts/load_to_real_jira.py \
        --base-url https://insight-bridge.atlassian.net \
        --token YOUR_API_TOKEN \
        --seed artifacts/ai_support_copilot_seed.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def create_project_if_not_exists(adapter: JiraCloudAdapter, project_key: str, project_name: str) -> dict:
    """Create a project if it doesn't exist."""
    try:
        # Check if project exists
        existing = adapter._call("GET", f"/rest/api/3/project/{project_key}")
        print(f"✓ Project {project_key} already exists")
        return existing
    except Exception:
        # Project doesn't exist, create it
        print(f"Creating project {project_key}...")
        
        # For Jira Cloud, we need to use the simplified project creation
        # Note: This requires admin permissions
        project_data = {
            "key": project_key,
            "name": project_name,
            "projectTypeKey": "service_desk",
            "leadAccountId": None,  # Will use current user
        }
        
        try:
            result = adapter._call("POST", "/rest/api/3/project", json_body=project_data)
            print(f"✓ Created project {project_key}")
            return result
        except Exception as e:
            print(f"⚠ Could not create project {project_key}: {e}")
            print(f"  Please create project '{project_key}' manually in Jira")
            return None


def load_issues_to_jira(adapter: JiraCloudAdapter, seed_data: dict, limit: int = 10, target_project: str = None) -> None:
    """Load issues from seed data into Jira."""

    issues = seed_data.get("issues", [])

    print(f"\n📊 Found {len(issues)} issues in seed data")
    print(f"   Loading first {limit} issues to avoid overwhelming your Jira...\n")

    # Get existing projects
    existing_projects = adapter.list_projects()
    project_map = {p["key"]: p for p in existing_projects}

    print(f"✓ Found {len(project_map)} existing projects: {', '.join(project_map.keys())}\n")

    if not project_map:
        print("\n❌ No projects available. Please create at least one project manually.")
        return

    # Use target project or first available
    if target_project and target_project in project_map:
        use_project = target_project
    else:
        use_project = list(project_map.keys())[0]

    print(f"📝 Loading issues into project: {use_project}\n")
    
    # Load issues
    created_count = 0
    skipped_count = 0
    
    for i, issue in enumerate(issues[:limit]):
        if i >= limit:
            break
            
        try:
            # Use target project instead of original
            project_key = use_project

            # Get summary and description from issue
            summary = issue.get("summary", "No summary")
            description = issue.get("description")
            labels = issue.get("labels", [])

            # Create issue
            result = adapter.create_issue(
                project_key=project_key,
                issue_type_name="Task",
                summary=summary,
                description=description,
                extra_fields={
                    "labels": labels
                }
            )

            created_key = result.get("key", "unknown")
            print(f"✓ Created issue {created_key}: {summary[:60]}...")
            created_count += 1
            
        except Exception as e:
            print(f"⚠ Failed to create issue: {e}")
            skipped_count += 1
    
    print(f"\n✅ Summary:")
    print(f"   Created: {created_count} issues")
    print(f"   Skipped: {skipped_count} issues")
    print(f"\n💡 Tip: Check your Jira at https://insight-bridge.atlassian.net/jira/projects")


def main():
    parser = argparse.ArgumentParser(
        description="Load AI Support Copilot data into real Jira Cloud"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Jira Cloud base URL (e.g., https://insight-bridge.atlassian.net)"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Jira account email (e.g., slavosmn@gmail.com)"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Jira API token (create at https://id.atlassian.com/manage-profile/security/api-tokens)"
    )
    parser.add_argument(
        "--seed",
        default="artifacts/ai_support_copilot_seed.json",
        help="Path to seed data JSON file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of issues to create (default: 10)"
    )
    parser.add_argument(
        "--project",
        help="Target project key (e.g., SCRUM, PROT). If not specified, uses first available project."
    )

    args = parser.parse_args()
    
    # Load seed data
    seed_path = Path(args.seed)
    if not seed_path.exists():
        print(f"❌ Seed file not found: {seed_path}")
        print(f"   Generate it first with:")
        print(f"   python scripts/generate_dummy_jira.py --config scripts/seed_profiles/ai_support_copilot.json --out {seed_path}")
        sys.exit(1)
    
    with open(seed_path) as f:
        seed_data = json.load(f)
    
    # Create adapter
    adapter = JiraCloudAdapter(args.base_url, args.email, args.token)

    # Test connection
    try:
        user = adapter.get_myself()
        print(f"✓ Connected as: {user.get('displayName')} ({user.get('emailAddress')})\n")
    except Exception as e:
        print(f"❌ Failed to connect to Jira: {e}")
        print(f"   Please check your email and API token")
        sys.exit(1)

    print(f"🚀 Loading data to Jira Cloud: {args.base_url}")
    print(f"   Using seed file: {seed_path}")
    print(f"   Limit: {args.limit} issues\n")

    # Load data
    load_issues_to_jira(adapter, seed_data, limit=args.limit, target_project=args.project)


if __name__ == "__main__":
    main()

