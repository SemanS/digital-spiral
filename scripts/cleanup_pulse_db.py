#!/usr/bin/env python3
"""Cleanup Pulse database - remove duplicates and orphaned data."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.db import session_scope
from orchestrator.pulse_models import JiraInstance, WorkItem


def cleanup_database():
    """Remove duplicate Jira instances and orphaned work items."""
    
    print("🧹 Cleaning up Executive Work Pulse Database")
    print("=" * 60)
    print()
    
    with session_scope() as session:
        # Find duplicate instances (same base_url + email)
        instances = session.query(JiraInstance).filter(
            JiraInstance.active == True
        ).all()
        
        seen = {}
        duplicates = []
        
        for inst in instances:
            key = (inst.base_url, inst.email, inst.tenant_id)
            if key in seen:
                duplicates.append(inst)
                print(f"❌ Found duplicate: {inst.display_name} ({inst.id})")
            else:
                seen[key] = inst
                print(f"✅ Keeping: {inst.display_name} ({inst.id})")
        
        if duplicates:
            print()
            print(f"🗑️  Removing {len(duplicates)} duplicate instance(s)...")
            for inst in duplicates:
                inst.active = False
                print(f"   Deactivated: {inst.display_name}")
            session.flush()
            print("✅ Duplicates removed!")
        else:
            print()
            print("✅ No duplicates found!")
        
        # Remove orphaned work items (no active Jira instance)
        print()
        print("🔍 Checking for orphaned work items...")
        
        active_instance_ids = [inst.id for inst in seen.values()]
        
        orphaned = session.query(WorkItem).filter(
            WorkItem.jira_instance_id.notin_(active_instance_ids)
        ).all()
        
        if orphaned:
            print(f"🗑️  Found {len(orphaned)} orphaned work items")
            for item in orphaned:
                session.delete(item)
            session.flush()
            print("✅ Orphaned items removed!")
        else:
            print("✅ No orphaned items found!")
        
        print()
        print("=" * 60)
        print("✅ Cleanup complete!")
        print()
        
        # Show final state
        active_instances = session.query(JiraInstance).filter(
            JiraInstance.active == True
        ).all()
        
        work_items_count = session.query(WorkItem).count()
        
        print(f"📊 Final state:")
        print(f"   Active Jira instances: {len(active_instances)}")
        print(f"   Work items: {work_items_count}")
        print()
        
        if len(active_instances) == 0:
            print("💡 No Jira instances. Add one via:")
            print("   http://localhost:7010/v1/pulse/")
        elif work_items_count == 0:
            print("💡 No work items. Try manual backfill:")
            for inst in active_instances:
                print(f"   curl -X POST http://localhost:7010/v1/pulse/jira/backfill \\")
                print(f"     -H 'Content-Type: application/json' \\")
                print(f"     -d '{{\"instance_id\": \"{inst.id}\", \"days_back\": 90, \"max_issues\": 1000}}'")
                print()


if __name__ == "__main__":
    cleanup_database()

