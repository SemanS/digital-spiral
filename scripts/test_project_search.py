#!/usr/bin/env python3
"""Test project search directly."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.db import session_scope
from orchestrator.pulse_models import JiraInstance
from clients.python.jira_cloud_adapter import JiraCloudAdapter
from sqlalchemy import select


def test_project_search():
    """Test searching for issues in a project."""
    
    print("🔍 Testing Project Search")
    print("=" * 60)
    
    with session_scope() as session:
        # Get first active Jira instance
        instance = session.execute(
            select(JiraInstance).where(JiraInstance.active == True).limit(1)
        ).scalar_one_or_none()
        
        if not instance:
            print("❌ No active Jira instances found!")
            return
        
        print(f"Instance: {instance.display_name}")
        print(f"Base URL: {instance.base_url}")
        print(f"Email: {instance.email}")
        print()
        
        # Decrypt API token (for now just use it as-is since we're not encrypting)
        api_token = instance.api_token_encrypted
        
        # Create adapter
        adapter = JiraCloudAdapter(instance.base_url, instance.email, api_token)

        # Test 0: Check authentication
        print("0️⃣ Testing authentication...")
        try:
            myself = adapter._call("GET", "/rest/api/3/myself")
            print(f"   ✅ Authenticated as: {myself.get('displayName')} ({myself.get('emailAddress')})")
            print(f"      Account ID: {myself.get('accountId')}")
            print(f"      Active: {myself.get('active')}")
        except Exception as e:
            print(f"   ❌ Authentication failed: {e}")
            import traceback
            traceback.print_exc()
            return

        print()

        # Test 1: List all projects
        print("1️⃣ Listing all projects...")
        try:
            projects = adapter._call("GET", "/rest/api/3/project")
            print(f"   ✅ Found {len(projects)} projects:")
            for proj in projects:
                print(f"      - {proj['key']}: {proj['name']}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return
        
        print()
        
        # Test 2: Search for issues in each project
        print("2️⃣ Searching for issues in each project...")
        for proj in projects[:3]:  # Test first 3 projects
            project_key = proj['key']
            print(f"\n   Testing {project_key}...")
            
            # Try different JQL queries
            queries = [
                f"project = {project_key}",
                f"project = '{project_key}'",
                f"project = \"{project_key}\"",
            ]
            
            for jql in queries:
                try:
                    print(f"      Trying JQL: {jql}")
                    result = adapter._call(
                        "GET",
                        "/rest/api/3/search",
                        params={
                            "jql": jql,
                            "maxResults": 5,
                            "fields": "summary,status",
                        }
                    )
                    total = result.get("total", 0)
                    issues = result.get("issues", [])
                    print(f"      ✅ SUCCESS! Found {total} issues, returned {len(issues)}")
                    if issues:
                        print(f"         First issue: {issues[0]['key']} - {issues[0]['fields']['summary']}")
                    break
                except Exception as e:
                    print(f"      ❌ Failed: {e}")
        
        print()
        print("=" * 60)
        print("✅ Test complete!")


if __name__ == "__main__":
    test_project_search()

