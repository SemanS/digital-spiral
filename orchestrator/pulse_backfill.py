"""Backfill service for loading historical Jira data into Work Items."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter

from .pulse_service import upsert_work_item_from_jira, get_jira_instance

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)


def backfill_jira_instance(
    instance_id: str,
    days_back: int = 90,
    max_issues: int = 1000,
) -> dict[str, Any]:
    """Backfill historical data from a Jira instance.
    
    Args:
        instance_id: Jira instance ID
        days_back: How many days of history to fetch
        max_issues: Maximum number of issues to fetch
    
    Returns:
        Statistics about the backfill
    """
    
    # Get instance details
    instance = get_jira_instance(instance_id)
    if not instance:
        raise ValueError(f"Jira instance {instance_id} not found")
    
    tenant_id = instance["tenant_id"]
    base_url = instance["base_url"]
    email = instance["email"]
    api_token = instance["api_token"]
    
    # Create adapter
    adapter = JiraCloudAdapter(base_url, email, api_token)
    
    # Calculate date range
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days_back)
    
    logger.info(
        f"🚀 Starting backfill for {instance['display_name']} "
        f"from {start_date.date()} to {end_date.date()}"
    )

    stats = {
        "instance_id": instance_id,
        "instance_name": instance["display_name"],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "issues_fetched": 0,
        "issues_created": 0,
        "issues_updated": 0,
        "errors": 0,
        "projects": set(),
    }
    
    # Fetch issues in batches
    start_at = 0
    batch_size = 50
    
    while stats["issues_fetched"] < max_issues:
        try:
            # JQL query for updated issues in date range
            # Use simpler JQL without expand to avoid 410 errors
            jql = f"updated >= -{days_back}d ORDER BY updated ASC"

            result = adapter._call(
                "GET",
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": batch_size,
                    "fields": "summary,status,assignee,reporter,priority,issuetype,created,updated,resolutiondate,project,labels",
                }
            )
            
            issues = result.get("issues", [])
            if not issues:
                break
            
            logger.info(f"Processing batch: {start_at} to {start_at + len(issues)}")
            
            for issue in issues:
                try:
                    work_item_id = upsert_work_item_from_jira(
                        tenant_id=tenant_id,
                        jira_instance_id=instance_id,
                        issue_data=issue,
                    )

                    stats["issues_fetched"] += 1

                    # Track project
                    project_key = issue.get("fields", {}).get("project", {}).get("key")
                    if project_key:
                        stats["projects"].add(project_key)

                    # Log progress every 10 issues
                    if stats["issues_fetched"] % 10 == 0:
                        logger.info(
                            f"Progress: {stats['issues_fetched']} issues fetched, "
                            f"{len(stats['projects'])} projects"
                        )

                except Exception as e:
                    logger.error(f"❌ Error processing issue {issue.get('key')}: {e}")
                    stats["errors"] += 1
            
            # Check if we've fetched all issues
            total = result.get("total", 0)
            if start_at + len(issues) >= total:
                break
            
            start_at += batch_size
            
            # Safety limit
            if stats["issues_fetched"] >= max_issues:
                logger.warning(f"Reached max_issues limit: {max_issues}")
                break
        
        except Exception as e:
            logger.error(f"Error fetching batch at {start_at}: {e}")
            stats["errors"] += 1
            break
    
    # Convert set to list for JSON serialization
    stats["projects"] = list(stats["projects"])

    logger.info(
        f"✅ Backfill complete: {stats['issues_fetched']} issues fetched, "
        f"{len(stats['projects'])} projects, {stats['errors']} errors"
    )

    return stats


def test_jira_connection(base_url: str, email: str, api_token: str) -> dict[str, Any]:
    """Test Jira connection and return basic info.
    
    Args:
        base_url: Jira base URL
        email: Jira account email
        api_token: Jira API token
    
    Returns:
        Connection test results
    """
    
    try:
        adapter = JiraCloudAdapter(base_url, email, api_token)
        
        # Test connection by getting current user
        user = adapter.get_myself()
        
        # Get projects
        projects = adapter.list_projects()
        
        return {
            "success": True,
            "user": {
                "accountId": user.get("accountId"),
                "displayName": user.get("displayName"),
                "emailAddress": user.get("emailAddress"),
            },
            "projects_count": len(projects),
            "projects": [
                {
                    "key": p.get("key"),
                    "name": p.get("name"),
                }
                for p in projects[:5]  # First 5 projects
            ],
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    # CLI for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill Jira data")
    parser.add_argument("--instance-id", required=True, help="Jira instance ID")
    parser.add_argument("--days", type=int, default=90, help="Days of history to fetch")
    parser.add_argument("--max-issues", type=int, default=1000, help="Max issues to fetch")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    stats = backfill_jira_instance(
        instance_id=args.instance_id,
        days_back=args.days,
        max_issues=args.max_issues,
    )
    
    print("\n=== Backfill Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

