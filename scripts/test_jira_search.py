#!/usr/bin/env python3
"""Test different Jira search methods."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def test_search_methods(base_url: str, email: str, api_token: str, project_key: str):
    """Test different ways to search for issues."""
    
    print(f"🔍 Testing Jira Search Methods for {project_key}")
    print(f"=" * 60)
    
    adapter = JiraCloudAdapter(base_url, email, api_token)
    
    # Method 1: Direct project issues endpoint
    print(f"\n1️⃣ Method 1: GET /rest/api/3/search with project={project_key}")
    try:
        result = adapter._call(
            "GET",
            "/rest/api/3/search",
            params={
                "jql": f"project={project_key}",
                "maxResults": 5,
            }
        )
        print(f"   ✅ SUCCESS! Total: {result.get('total', 0)}")
        for issue in result.get("issues", [])[:3]:
            print(f"      - {issue['key']}: {issue['fields']['summary']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Method 2: With quotes
    print(f"\n2️⃣ Method 2: GET /rest/api/3/search with project='{project_key}'")
    try:
        result = adapter._call(
            "GET",
            "/rest/api/3/search",
            params={
                "jql": f"project='{project_key}'",
                "maxResults": 5,
            }
        )
        print(f"   ✅ SUCCESS! Total: {result.get('total', 0)}")
        for issue in result.get("issues", [])[:3]:
            print(f"      - {issue['key']}: {issue['fields']['summary']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Method 3: With spaces
    print(f"\n3️⃣ Method 3: GET /rest/api/3/search with 'project = {project_key}'")
    try:
        result = adapter._call(
            "GET",
            "/rest/api/3/search",
            params={
                "jql": f"project = {project_key}",
                "maxResults": 5,
            }
        )
        print(f"   ✅ SUCCESS! Total: {result.get('total', 0)}")
        for issue in result.get("issues", [])[:3]:
            print(f"      - {issue['key']}: {issue['fields']['summary']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Method 4: Get project info first
    print(f"\n4️⃣ Method 4: GET /rest/api/3/project/{project_key}")
    try:
        project = adapter._call("GET", f"/rest/api/3/project/{project_key}")
        print(f"   ✅ Project found: {project.get('name')}")
        print(f"      ID: {project.get('id')}")
        print(f"      Key: {project.get('key')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Method 5: Search by project ID
    print(f"\n5️⃣ Method 5: Try getting project ID and search by ID")
    try:
        project = adapter._call("GET", f"/rest/api/3/project/{project_key}")
        project_id = project.get('id')
        print(f"   Project ID: {project_id}")
        
        result = adapter._call(
            "GET",
            "/rest/api/3/search",
            params={
                "jql": f"project={project_id}",
                "maxResults": 5,
            }
        )
        print(f"   ✅ SUCCESS! Total: {result.get('total', 0)}")
        for issue in result.get("issues", [])[:3]:
            print(f"      - {issue['key']}: {issue['fields']['summary']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Method 6: Use Agile API (board issues)
    print(f"\n6️⃣ Method 6: GET /rest/agile/1.0/board (Agile API)")
    try:
        boards = adapter._call("GET", "/rest/agile/1.0/board", params={"projectKeyOrId": project_key})
        print(f"   ✅ Found {len(boards.get('values', []))} boards")
        for board in boards.get('values', [])[:2]:
            print(f"      - Board: {board['name']} (ID: {board['id']})")
            
            # Get issues from board
            try:
                issues = adapter._call("GET", f"/rest/agile/1.0/board/{board['id']}/issue", params={"maxResults": 5})
                print(f"        ✅ Found {issues.get('total', 0)} issues")
                for issue in issues.get('issues', [])[:3]:
                    print(f"           - {issue['key']}: {issue['fields']['summary']}")
            except Exception as e2:
                print(f"        ❌ Failed to get issues: {e2}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print()
    print("=" * 60)
    print("✅ Test complete!")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 test_jira_search.py <base_url> <email> <api_token> <project_key>")
        print()
        print("Example:")
        print("  python3 test_jira_search.py https://insight-bridge.atlassian.net slavosmn@gmail.com TOKEN SCRUM")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip("/")
    email = sys.argv[2]
    api_token = sys.argv[3]
    project_key = sys.argv[4]
    
    test_search_methods(base_url, email, api_token, project_key)

