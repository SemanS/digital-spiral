#!/usr/bin/env python3
"""Assign existing tickets to real Jira users.

This script:
1. Gets all real users from Jira
2. Gets all tickets from project
3. Assigns tickets to users in round-robin fashion

Usage:
    python scripts/assign_tickets_to_users.py \
        --base-url https://insight-bridge.atlassian.net \
        --email slavosmn@gmail.com \
        --token YOUR_API_TOKEN \
        --project SCRUM
"""

import argparse
import sys
import time
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def main():
    parser = argparse.ArgumentParser(description="Assign tickets to real users")
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
    
    print(f"\n🎯 Assigning tickets to real users...")
    
    # Step 1: Get real users
    print("\n1️⃣ Getting real users from Jira...")
    real_users = get_real_users(adapter)
    print(f"✓ Found {len(real_users)} real users")
    for user in real_users[:10]:
        print(f"   - {user['displayName']} ({user['accountId'][:20]}...)")
    
    if not real_users:
        print("❌ No users found. Cannot assign tickets.")
        sys.exit(1)
    
    # Step 2: Get all tickets
    print("\n2️⃣ Getting all tickets...")
    tickets = get_all_tickets(adapter, args.project)
    print(f"✓ Found {len(tickets)} tickets")
    
    if not tickets:
        print("❌ No tickets found.")
        sys.exit(1)
    
    # Step 3: Assign tickets
    print(f"\n3️⃣ Assigning tickets to users...")
    print(f"   This will take ~{len(tickets) * 0.5:.0f} seconds...")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)
    
    assign_tickets(adapter, tickets, real_users)
    
    print("\n✅ All tickets assigned!")
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
        
        return real_users
    
    except Exception as e:
        print(f"⚠ Failed to get users: {e}")
        print("   Using fallback: current user only")
        myself = adapter.get_myself()
        return [{
            "accountId": myself["accountId"],
            "displayName": myself.get("displayName", "Unknown"),
            "emailAddress": myself.get("emailAddress", "")
        }]


def get_all_tickets(adapter: JiraCloudAdapter, project_key: str) -> list[dict]:
    """Get all tickets from project."""
    
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
                "fields": "key,summary,assignee"
            }
        )
        
        issues = result.get("issues", [])
        all_issues.extend(issues)
        
        if len(issues) < max_results:
            break
        
        start_at += max_results
    
    return all_issues


def assign_tickets(adapter: JiraCloudAdapter, tickets: list[dict], users: list[dict]) -> None:
    """Assign tickets to users in round-robin fashion."""
    
    success_count = 0
    failed_count = 0
    
    # Shuffle users for variety
    shuffled_users = users.copy()
    random.shuffle(shuffled_users)
    
    for i, ticket in enumerate(tickets):
        issue_key = ticket["key"]
        summary = ticket["fields"]["summary"]
        
        # Pick user in round-robin
        user = shuffled_users[i % len(shuffled_users)]
        
        try:
            # Assign ticket
            adapter.assign_issue(issue_key, user["accountId"])
            
            print(f"   ✓ {issue_key}: {summary[:40]}... → {user['displayName']}")
            success_count += 1
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ {issue_key}: Failed to assign - {e}")
            failed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✓ Assigned: {success_count}")
    print(f"   ❌ Failed: {failed_count}")


if __name__ == "__main__":
    main()

