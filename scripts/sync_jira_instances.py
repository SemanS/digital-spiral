#!/usr/bin/env python3
"""Sync Jira instances from backend database to orchestrator database."""

import os
from sqlalchemy import create_engine, text
from datetime import datetime

# Database URLs
BACKEND_DB_URL = os.getenv("BACKEND_DB_URL", "postgresql+psycopg://digital_spiral:dev_password@localhost:5433/digital_spiral")
ORCHESTRATOR_DB_URL = os.getenv("ORCHESTRATOR_DB_URL", "postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator")

def sync_instances():
    """Sync Jira instances from backend to orchestrator."""
    backend_engine = create_engine(BACKEND_DB_URL)
    orchestrator_engine = create_engine(ORCHESTRATOR_DB_URL)
    
    print("🔄 Syncing Jira instances from backend to orchestrator...")
    print()
    
    with backend_engine.connect() as backend_conn:
        # Get all active instances from backend
        result = backend_conn.execute(
            text("""
                SELECT 
                    ji.id,
                    ji.tenant_id,
                    ji.base_url,
                    ji.auth_email,
                    ji.encrypted_credentials,
                    ji.is_active,
                    t.slug as tenant_slug
                FROM jira_instances ji
                LEFT JOIN tenants t ON ji.tenant_id = t.id
                WHERE ji.is_active = true
            """)
        )
        instances = result.fetchall()
        
        if not instances:
            print("❌ No active Jira instances found in backend database")
            return
        
        print(f"✅ Found {len(instances)} active instance(s) in backend database")
        print()
        
        with orchestrator_engine.connect() as orch_conn:
            synced_count = 0
            
            for instance in instances:
                instance_id, tenant_id, base_url, auth_email, encrypted_credentials, is_active, tenant_slug = instance

                # Always use 'insight-bridge' as tenant_id for orchestrator
                orch_tenant_id = 'insight-bridge'
                
                print(f"📦 Instance: {base_url}")
                print(f"   ID: {instance_id}")
                print(f"   Email: {auth_email}")
                print(f"   Tenant: {orch_tenant_id}")
                
                # Check if instance already exists in orchestrator
                existing = orch_conn.execute(
                    text("SELECT id FROM jira_instances WHERE id = :id"),
                    {"id": str(instance_id)}
                ).fetchone()
                
                if existing:
                    # Update existing instance
                    orch_conn.execute(
                        text("""
                            UPDATE jira_instances
                            SET
                                tenant_id = :tenant_id,
                                base_url = :base_url,
                                email = :email,
                                api_token_encrypted = :api_token,
                                active = :active,
                                updated_at = :updated_at
                            WHERE id = :id
                        """),
                        {
                            "id": str(instance_id),
                            "tenant_id": orch_tenant_id,
                            "base_url": base_url.rstrip('/'),
                            "email": auth_email,
                            "api_token": encrypted_credentials,
                            "active": is_active,
                            "updated_at": datetime.utcnow()
                        }
                    )
                    print(f"   ✅ Updated in orchestrator")
                else:
                    # Insert new instance
                    # Generate display name from base_url
                    display_name = base_url.replace('https://', '').replace('.atlassian.net/', '').replace('.atlassian.net', '').title()

                    orch_conn.execute(
                        text("""
                            INSERT INTO jira_instances (
                                id, tenant_id, base_url, email, api_token_encrypted,
                                display_name, active, created_at, updated_at
                            ) VALUES (
                                :id, :tenant_id, :base_url, :email, :api_token,
                                :display_name, :active, :created_at, :updated_at
                            )
                        """),
                        {
                            "id": str(instance_id),
                            "tenant_id": orch_tenant_id,
                            "base_url": base_url.rstrip('/'),
                            "email": auth_email,
                            "api_token": encrypted_credentials,
                            "display_name": display_name,
                            "active": is_active,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    )
                    print(f"   ✅ Inserted into orchestrator")
                
                orch_conn.commit()
                synced_count += 1
                print()
            
            print(f"✅ Synced {synced_count} instance(s) successfully!")
            print()
            
            # Show all instances in orchestrator
            print("📋 All instances in orchestrator database:")
            result = orch_conn.execute(
                text("""
                    SELECT id, tenant_id, base_url, email, display_name, active
                    FROM jira_instances
                    ORDER BY created_at DESC
                """)
            )

            for row in result:
                status = "✅ Active" if row[5] else "❌ Inactive"
                print(f"   {status} | {row[4]} | {row[2]} | {row[3]}")

if __name__ == "__main__":
    try:
        sync_instances()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

