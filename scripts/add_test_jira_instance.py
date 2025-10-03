#!/usr/bin/env python3
"""Add a test Jira instance to the orchestrator database."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import pulse_service
from orchestrator.db import session_scope, Tenant

def ensure_tenant_exists(tenant_id: str, site_id: str):
    """Ensure tenant exists in database."""
    with session_scope() as session:
        from sqlalchemy import select
        stmt = select(Tenant).where(Tenant.tenant_id == tenant_id)
        tenant = session.execute(stmt).scalar_one_or_none()

        if not tenant:
            print(f"Creating tenant: {tenant_id}")
            tenant = Tenant(
                tenant_id=tenant_id,
                site_id=site_id,
                forge_shared_secret="forge-dev-secret",
            )
            session.add(tenant)
            session.flush()
            print(f"✅ Tenant created: {tenant_id}")
        else:
            print(f"✅ Tenant already exists: {tenant_id}")

def main():
    """Add test Jira instance."""

    # Test instance configuration
    tenant_id = "insight-bridge"
    site_id = "insight-bridge.atlassian.net"
    base_url = "https://insight-bridge.atlassian.net"
    email = os.getenv("JIRA_EMAIL", "slavomir.seman@hotovo.com")
    api_token = os.getenv("JIRA_API_TOKEN", "test-token")
    display_name = "Insight Bridge Jira"

    print(f"Setting up Jira instance:")
    print(f"  Tenant ID: {tenant_id}")
    print(f"  Site ID: {site_id}")
    print(f"  Base URL: {base_url}")
    print(f"  Email: {email}")
    print(f"  Display Name: {display_name}")
    print()

    # Ensure tenant exists
    try:
        ensure_tenant_exists(tenant_id, site_id)
    except Exception as e:
        print(f"❌ Error creating tenant: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        result = pulse_service.add_jira_instance(
            tenant_id=tenant_id,
            base_url=base_url,
            email=email,
            api_token=api_token,
            display_name=display_name,
        )
        
        print("✅ Jira instance added successfully!")
        print(f"  ID: {result['id']}")
        print(f"  Created at: {result['created_at']}")
        print()
        
        # List all instances
        instances = pulse_service.list_jira_instances(tenant_id)
        print(f"Total instances for tenant '{tenant_id}': {len(instances)}")
        for inst in instances:
            print(f"  - {inst['display_name']} ({inst['base_url']})")
        
    except ValueError as e:
        print(f"⚠️  Instance already exists: {e}")
        
        # List existing instances
        instances = pulse_service.list_jira_instances(tenant_id)
        print(f"\nExisting instances for tenant '{tenant_id}':")
        for inst in instances:
            print(f"  - {inst['display_name']} ({inst['base_url']})")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

