#!/usr/bin/env python3
"""Add worklog entries, workflow transitions, and more comments to existing tickets.

This script:
1. Gets all tickets from project
2. Adds worklog entries (time tracking)
3. Transitions tickets through workflow (To Do → In Progress → Review → Done)
4. Adds more realistic comments

Usage:
    python scripts/add_worklog_and_transitions.py \
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


# Team members for comments
TEAM_MEMBERS = [
    "Slavomir Seman",
    "abhinav",
    "alex.boyko",
    "allan.baril",
    "andrew.eisenberg",
    "andy.clement",
    "artem.bilan",
    "ayyappan.arunachalam",
    "buelent.zeyben",
    "carlos.queiroz",
]


def main():
    parser = argparse.ArgumentParser(description="Add worklog and transitions to tickets")
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
    
    print(f"\n🚀 Adding worklog, transitions, and comments...")
    print(f"   This will take 15-20 minutes...")
    print(f"   - Add worklog entries (time tracking)")
    print(f"   - Transition tickets through workflow")
    print(f"   - Add more realistic comments")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)
    
    # Get all tickets
    print("\n1️⃣ Getting all tickets...")
    tickets = get_all_tickets(adapter, args.project)
    print(f"✓ Found {len(tickets)} tickets")
    
    # Get sprints
    print("\n2️⃣ Getting sprints...")
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
    sprints_response = adapter.list_sprints(board_id, max_results=100)
    sprints = sprints_response.get("values", [])
    print(f"✓ Found {len(sprints)} sprints")
    
    # Update sprint states
    print("\n3️⃣ Updating sprint states...")
    update_sprint_states(adapter, sprints)
    
    # Process tickets
    print("\n4️⃣ Processing tickets...")
    process_tickets(adapter, tickets, sprints)
    
    print("\n✅ All done!")
    print(f"\n🔗 View in Jira:")
    print(f"   {args.base_url}/jira/software/c/projects/{args.project}/boards/1")


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
                "fields": "key,summary,description,created,sprint"
            }
        )
        
        issues = result.get("issues", [])
        all_issues.extend(issues)
        
        if len(issues) < max_results:
            break
        
        start_at += max_results
    
    return all_issues


def update_sprint_states(adapter: JiraCloudAdapter, sprints: list[dict]) -> None:
    """Update sprint states (close old sprints, activate current sprint)."""
    
    now = datetime.now()
    
    for sprint in sprints:
        sprint_id = sprint["id"]
        sprint_name = sprint["name"]
        state = sprint.get("state", "future")
        
        # Parse dates
        start_date_str = sprint.get("startDate")
        end_date_str = sprint.get("endDate")
        
        if not start_date_str or not end_date_str:
            continue
        
        # Parse ISO dates
        start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        
        # Determine correct state
        if end_date < now:
            target_state = "closed"
        elif start_date <= now <= end_date:
            target_state = "active"
        else:
            target_state = "future"
        
        # Update if needed
        if state != target_state:
            try:
                adapter.update_sprint(sprint_id, state=target_state)
                print(f"   ✓ {sprint_name}: {state} → {target_state}")
                time.sleep(0.5)
            except Exception as e:
                print(f"   ⚠ Failed to update {sprint_name}: {e}")


def process_tickets(adapter: JiraCloudAdapter, tickets: list[dict], sprints: list[dict]) -> None:
    """Process each ticket: add worklog, transitions, comments."""
    
    # Group tickets by sprint
    sprint_tickets = {}
    for ticket in tickets:
        issue_key = ticket["key"]
        
        # Find sprint for this ticket
        sprint_field = ticket.get("fields", {}).get("sprint")
        if sprint_field:
            sprint_id = sprint_field.get("id") if isinstance(sprint_field, dict) else None
            if sprint_id:
                if sprint_id not in sprint_tickets:
                    sprint_tickets[sprint_id] = []
                sprint_tickets[sprint_id].append(ticket)
    
    # Process each sprint
    for sprint in sprints:
        sprint_id = sprint["id"]
        sprint_name = sprint["name"]
        sprint_state = sprint.get("state", "future")
        
        tickets_in_sprint = sprint_tickets.get(sprint_id, [])
        if not tickets_in_sprint:
            continue
        
        print(f"\n   [{sprint_name}] ({sprint_state}) - {len(tickets_in_sprint)} tickets")
        
        for ticket in tickets_in_sprint:
            issue_key = ticket["key"]
            summary = ticket["fields"]["summary"]
            
            try:
                # Extract team member from description
                description = ticket["fields"].get("description", {})
                team_member = extract_team_member(description)
                
                # Add worklog
                add_worklog_entries(adapter, issue_key, team_member, sprint_state)
                
                # Add transitions
                add_transitions(adapter, issue_key, sprint_state)
                
                # Add more comments
                add_more_comments(adapter, issue_key, team_member, sprint_state)
                
                print(f"       ✓ {issue_key}: {summary[:40]}...")
                time.sleep(0.8)
                
            except Exception as e:
                print(f"       ❌ {issue_key}: {e}")


def extract_team_member(description: dict) -> str:
    """Extract team member name from description."""
    
    if not description or not isinstance(description, dict):
        return random.choice(TEAM_MEMBERS)
    
    content = description.get("content", [])
    for item in content:
        if item.get("type") == "paragraph":
            for text_item in item.get("content", []):
                text = text_item.get("text", "")
                if "Assigned to:" in text:
                    # Extract name after "Assigned to:"
                    parts = text.split("Assigned to:")
                    if len(parts) > 1:
                        name = parts[1].split("\n")[0].strip()
                        return name
    
    return random.choice(TEAM_MEMBERS)


def add_worklog_entries(adapter: JiraCloudAdapter, issue_key: str, team_member: str, sprint_state: str) -> None:
    """Add worklog entries to ticket."""

    # Closed sprints: add 5-8 worklog entries (realistic work over sprint)
    # Active sprint: add 3-5 worklog entries (work in progress)
    # Future sprint: no worklog

    if sprint_state == "future":
        return

    num_entries = random.randint(5, 8) if sprint_state == "closed" else random.randint(3, 5)

    # Worklog comments for variety
    worklog_comments = [
        f"[{team_member}] Initial research and planning",
        f"[{team_member}] Implementation of core functionality",
        f"[{team_member}] Writing unit tests",
        f"[{team_member}] Code review and refactoring",
        f"[{team_member}] Bug fixes and edge cases",
        f"[{team_member}] Integration testing",
        f"[{team_member}] Documentation and examples",
        f"[{team_member}] Final review and cleanup",
        f"[{team_member}] Deployment preparation",
        f"[{team_member}] Performance optimization",
    ]

    # Generate worklog entries spread over time
    now = datetime.now()
    for i in range(num_entries):
        # Spread work over 2 weeks
        days_ago = random.randint(1, 14)
        work_date = now - timedelta(days=days_ago)

        # Vary hours: 1-8 hours per entry
        hours = random.choice([1, 2, 2, 3, 3, 4, 4, 6, 8])
        time_spent_seconds = hours * 3600

        # Vary start time (morning or afternoon)
        start_hour = random.choice([9, 10, 13, 14])
        started = work_date.strftime(f"%Y-%m-%dT{start_hour:02d}:00:00.000+0000")

        # Pick comment
        comment = worklog_comments[i % len(worklog_comments)]

        try:
            adapter.add_worklog(issue_key, time_spent_seconds, started, comment)
            time.sleep(0.2)  # Small delay between worklog entries
        except Exception:
            pass  # Ignore errors


def add_transitions(adapter: JiraCloudAdapter, issue_key: str, sprint_state: str) -> None:
    """Transition ticket through workflow."""
    
    # Closed sprints: transition to Done
    # Active sprint: transition to In Progress or Review
    # Future sprint: keep in To Do
    
    if sprint_state == "future":
        return
    
    try:
        transitions = adapter.get_transitions(issue_key)
        
        if sprint_state == "closed":
            # Transition to Done
            done_transition = next((t for t in transitions if "done" in t["name"].lower()), None)
            if done_transition:
                adapter.transition_issue(issue_key, done_transition["id"])
        
        elif sprint_state == "active":
            # Transition to In Progress or Review
            target_status = random.choice(["in progress", "review", "done"])
            target_transition = next((t for t in transitions if target_status in t["name"].lower()), None)
            if target_transition:
                adapter.transition_issue(issue_key, target_transition["id"])
    
    except Exception:
        pass  # Ignore errors


def add_more_comments(adapter: JiraCloudAdapter, issue_key: str, team_member: str, sprint_state: str) -> None:
    """Add more realistic comments simulating team discussion."""

    # Expanded comment pool for realistic conversation
    all_comments = [
        # Initial work
        f"[{team_member}] Starting work on this. Will have initial implementation by EOD.",
        f"[{team_member}] Quick question: should we use the new API or stick with the legacy one?",
        f"[Tech Lead] Let's go with the new API. It's more maintainable long-term.",

        # Implementation phase
        f"[{team_member}] Initial implementation complete. Added unit tests covering main scenarios.",
        f"[{team_member}] Found an edge case with null values. Working on a fix.",
        f"[{team_member}] Edge case fixed. Also added validation to prevent similar issues.",

        # Code review
        f"[Code Review - Alex] Overall looks good! Left a few minor comments on the PR.",
        f"[Code Review - Alex] Consider extracting that logic into a separate helper function.",
        f"[{team_member}] Good catch! Refactored as suggested.",
        f"[Code Review - Sarah] LGTM! Nice work on the error handling. 👍",

        # Testing phase
        f"[{team_member}] Deployed to staging for QA testing.",
        f"[QA - Mike] Testing now. Will update with results shortly.",
        f"[QA - Mike] Found a small UI issue on mobile. Screenshot attached.",
        f"[{team_member}] Fixed the mobile layout issue. Can you verify?",
        f"[QA - Mike] Verified on staging. All scenarios pass. LGTM! ✅",

        # Documentation
        f"[{team_member}] Added API documentation and usage examples.",
        f"[{team_member}] Updated README with setup instructions.",

        # Final review
        f"[Product - Lisa] This looks great! Exactly what we needed.",
        f"[Product - Lisa] Ready to ship. Let's include this in the next release.",
        f"[{team_member}] Merged to main. Will be in v2.3.0 release.",

        # Post-deployment
        f"[{team_member}] Deployed to production. Monitoring metrics.",
        f"[{team_member}] All metrics look good. No errors in the last 24h.",
    ]

    # Closed sprints: add 8-12 comments (full conversation)
    # Active sprint: add 5-8 comments (work in progress)
    # Future sprint: add 2-3 comments (planning)

    if sprint_state == "closed":
        num_comments = random.randint(8, 12)
    elif sprint_state == "active":
        num_comments = random.randint(5, 8)
    else:
        num_comments = random.randint(2, 3)

    # Pick random comments to simulate realistic conversation
    selected_comments = random.sample(all_comments, min(num_comments, len(all_comments)))

    for comment_text in selected_comments:
        try:
            adapter.add_comment(issue_key, {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": comment_text
                    }]
                }]
            })
            time.sleep(0.3)  # Rate limiting
        except Exception:
            pass  # Ignore errors


if __name__ == "__main__":
    main()

