#!/usr/bin/env python3
"""Update Jira instance API token in orchestrator database."""

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://ds:ds@localhost:5433/ds_orchestrator")

def update_jira_token(tenant_id: str, new_email: str, new_token: str):
    """Update Jira instance API token."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if instance exists
        result = conn.execute(
            text("SELECT id, base_url FROM jira_instances WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        instance = result.fetchone()
        
        if not instance:
            print(f"❌ No Jira instance found for tenant: {tenant_id}")
            return False
        
        instance_id, base_url = instance
        print(f"✅ Found Jira instance: {instance_id}")
        print(f"   Base URL: {base_url}")
        
        # Update token (simple encryption - just prepend a salt)
        # TODO: Use proper encryption in production
        encrypted_token = f"4c5dc9b7708905f77f5e5d16316b5dfb425e68cb326dcd55a860e90a7707031e:{new_token}"
        
        # Update instance
        conn.execute(
            text("""
                UPDATE jira_instances 
                SET email = :email,
                    api_token_encrypted = :token,
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
            """),
            {
                "email": new_email,
                "token": encrypted_token,
                "tenant_id": tenant_id
            }
        )
        conn.commit()
        
        print(f"✅ Updated Jira instance token")
        print(f"   Email: {new_email}")
        print(f"   Token: {new_token[:10]}...")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 update_jira_token.py <tenant_id> <email> <api_token>")
        print("Example: python3 update_jira_token.py insight-bridge slavomir.seman@hotovo.com ATATT...")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    email = sys.argv[2]
    api_token = sys.argv[3]
    
    success = update_jira_token(tenant_id, email, api_token)
    sys.exit(0 if success else 1)

