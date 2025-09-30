#!/usr/bin/env python3
"""Check Pulse database state."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.db import session_scope
from orchestrator.pulse_models import JiraInstance, WorkItem
from sqlalchemy import select, func


def check_database():
    """Check database state and print summary."""
    
    print("🔍 Checking Executive Work Pulse Database")
    print("=" * 60)
    print()
    
    with session_scope() as session:
        # Check Jira instances
        instances = session.execute(
            select(JiraInstance).where(JiraInstance.active == True)
        ).scalars().all()
        
        print(f"📊 Jira Instances: {len(instances)}")
        for inst in instances:
            print(f"  - {inst.display_name}")
            print(f"    ID: {inst.id}")
            print(f"    Base URL: {inst.base_url}")
            print(f"    Email: {inst.email}")
            print(f"    Tenant: {inst.tenant_id}")
            print()
        
        if not instances:
            print("  ⚠️  No Jira instances found!")
            print("  💡 Add one via: http://localhost:7010/v1/pulse/")
            print()
            return
        
        # Check work items
        work_items_count = session.execute(
            select(func.count(WorkItem.id))
        ).scalar()
        
        print(f"📝 Work Items: {work_items_count}")
        
        if work_items_count == 0:
            print("  ⚠️  No work items found!")
            print("  💡 Backfill may still be running or failed.")
            print("  💡 Check server logs for backfill progress.")
            print()
            return
        
        # Check by project
        projects = session.execute(
            select(
                WorkItem.project_key,
                func.count(WorkItem.id).label('count')
            ).group_by(WorkItem.project_key)
        ).all()
        
        print()
        print(f"📁 Projects: {len(projects)}")
        for project_key, count in projects:
            print(f"  - {project_key}: {count} items")
        
        # Check by status
        print()
        statuses = session.execute(
            select(
                WorkItem.status,
                func.count(WorkItem.id).label('count')
            ).group_by(WorkItem.status)
        ).all()
        
        print(f"🏷️  Statuses:")
        for status, count in statuses:
            print(f"  - {status}: {count} items")
        
        # Sample items
        print()
        sample_items = session.execute(
            select(WorkItem).limit(5)
        ).scalars().all()
        
        print(f"📋 Sample Items:")
        for item in sample_items:
            print(f"  - {item.source_key}: {item.title[:50]}...")
            print(f"    Project: {item.project_key}, Status: {item.status}")
        
        print()
        print("✅ Database check complete!")
        print()
        print("🌐 Open dashboard: http://localhost:7010/v1/pulse/")
        print("🔧 Debug endpoint: http://localhost:7010/v1/pulse/debug")


if __name__ == "__main__":
    check_database()

