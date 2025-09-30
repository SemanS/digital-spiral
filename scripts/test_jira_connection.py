#!/usr/bin/env python3
"""Test Jira connection and list projects."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def test_connection(base_url: str, email: str, api_token: str):
    """Test Jira connection and list available projects."""
    
    print(f"🔍 Testing Jira Connection")
    print(f"=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Email: {email}")
    print()
    
    try:
        adapter = JiraCloudAdapter(base_url, email, api_token)
        
        # Test 1: Get current user
        print("1️⃣ Testing authentication...")
        try:
            user = adapter._call("GET", "/rest/api/3/myself")
            print(f"   ✅ Authenticated as: {user.get('displayName')} ({user.get('emailAddress')})")
        except Exception as e:
            print(f"   ❌ Authentication failed: {e}")
            return
        
        print()
        
        # Test 2: List all projects
        print("2️⃣ Fetching projects...")
        try:
            projects = adapter._call("GET", "/rest/api/3/project")
            print(f"   ✅ Found {len(projects)} projects:")
            for proj in projects:
                print(f"      - {proj['key']}: {proj['name']}")
                print(f"        ID: {proj['id']}")
                print(f"        Type: {proj.get('projectTypeKey', 'unknown')}")
                print(f"        Archived: {proj.get('archived', False)}")
                print()
        except Exception as e:
            print(f"   ❌ Failed to fetch projects: {e}")
            return
        
        print()
        
        # Test 3: Try to fetch issues from each project
        print("3️⃣ Testing issue access for each project...")
        for proj in projects:
            project_key = proj['key']
            try:
                result = adapter._call(
                    "GET",
                    "/rest/api/3/search",
                    params={
                        "jql": f"project = {project_key}",
                        "maxResults": 1,
                        "fields": "summary",
                    }
                )
                issue_count = result.get("total", 0)
                print(f"   ✅ {project_key}: {issue_count} issues accessible")
            except Exception as e:
                print(f"   ❌ {project_key}: Failed - {e}")
        
        print()
        print("=" * 60)
        print("✅ Connection test complete!")
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 test_jira_connection.py <base_url> <email> <api_token>")
        print()
        print("Example:")
        print("  python3 test_jira_connection.py https://slavoseman.atlassian.net slavosmn@gmail.com YOUR_TOKEN")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip("/")
    email = sys.argv[2]
    api_token = sys.argv[3]
    
    test_connection(base_url, email, api_token)

