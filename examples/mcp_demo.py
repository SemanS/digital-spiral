"""Demo script for MCP Jira and SQL servers.

This script demonstrates how to interact with the MCP servers.
"""

import asyncio
import json
from uuid import uuid4

import httpx


# Configuration
MCP_JIRA_URL = "http://localhost:8055"
MCP_SQL_URL = "http://localhost:8056"
TENANT_ID = str(uuid4())  # Replace with your tenant ID
USER_ID = "demo@example.com"


async def demo_mcp_jira():
    """Demonstrate MCP Jira server functionality."""
    print("=" * 60)
    print("MCP JIRA SERVER DEMO")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Health check
        print("\n1. Health Check")
        response = await client.get(f"{MCP_JIRA_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # 2. List available tools
        print("\n2. List Available Tools")
        response = await client.get(f"{MCP_JIRA_URL}/tools")
        data = response.json()
        print(f"   Available tools ({data['count']}):")
        for tool in data["tools"]:
            print(f"   - {tool}")

        # 3. Search issues
        print("\n3. Search Issues")
        response = await client.post(
            f"{MCP_JIRA_URL}/tools/invoke",
            headers={
                "X-Tenant-ID": TENANT_ID,
                "X-User-ID": USER_ID,
            },
            json={
                "name": "jira.search",
                "arguments": {
                    "query": "project = DEMO",
                    "limit": 5,
                },
            },
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data['result']['issues'])} issues")
            print(f"   Query time: {data['result']['query_time_ms']}ms")
        else:
            print(f"   Error: {response.status_code} - {response.text}")

        # 4. Create issue
        print("\n4. Create Issue")
        idempotency_key = f"demo-{uuid4().hex[:8]}"
        response = await client.post(
            f"{MCP_JIRA_URL}/tools/invoke",
            headers={
                "X-Tenant-ID": TENANT_ID,
                "X-User-ID": USER_ID,
            },
            json={
                "name": "jira.create_issue",
                "arguments": {
                    "instance_id": str(uuid4()),  # Replace with real instance ID
                    "project_key": "DEMO",
                    "issue_type_id": "10001",
                    "summary": "Demo issue from MCP",
                    "idempotency_key": idempotency_key,
                },
            },
        )
        if response.status_code == 200:
            data = response.json()
            issue_key = data["result"]["issue"]["key"]
            print(f"   Created issue: {issue_key}")
            print(f"   Audit log ID: {data['result']['audit_log_id']}")

            # 5. Update issue
            print("\n5. Update Issue")
            response = await client.post(
                f"{MCP_JIRA_URL}/tools/invoke",
                headers={
                    "X-Tenant-ID": TENANT_ID,
                    "X-User-ID": USER_ID,
                },
                json={
                    "name": "jira.update_issue",
                    "arguments": {
                        "issue_key": issue_key,
                        "fields": {
                            "summary": "Updated demo issue",
                            "priority": "High",
                        },
                    },
                },
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   Updated fields: {data['result']['updated_fields']}")
            else:
                print(f"   Error: {response.status_code} - {response.text}")

            # 6. Transition issue
            print("\n6. Transition Issue")
            response = await client.post(
                f"{MCP_JIRA_URL}/tools/invoke",
                headers={
                    "X-Tenant-ID": TENANT_ID,
                    "X-User-ID": USER_ID,
                },
                json={
                    "name": "jira.transition_issue",
                    "arguments": {
                        "issue_key": issue_key,
                        "to_status": "In Progress",
                        "comment": "Starting work on this issue",
                    },
                },
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   Transitioned from {data['result']['from_status']} to {data['result']['to_status']}")
            else:
                print(f"   Error: {response.status_code} - {response.text}")

            # 7. List transitions
            print("\n7. List Available Transitions")
            response = await client.post(
                f"{MCP_JIRA_URL}/tools/invoke",
                headers={
                    "X-Tenant-ID": TENANT_ID,
                    "X-User-ID": USER_ID,
                },
                json={
                    "name": "jira.list_transitions",
                    "arguments": {
                        "issue_key": issue_key,
                    },
                },
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   Current status: {data['result']['current_status']}")
                print(f"   Available transitions:")
                for transition in data["result"]["transitions"]:
                    print(f"   - {transition['name']} -> {transition['to']}")
            else:
                print(f"   Error: {response.status_code} - {response.text}")

        else:
            print(f"   Error: {response.status_code} - {response.text}")

        # 8. Get metrics
        print("\n8. Server Metrics")
        response = await client.get(f"{MCP_JIRA_URL}/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"   Counters: {len(data.get('counters', {}))}")
            print(f"   Histograms: {len(data.get('histograms', {}))}")
            print(f"   Last reset: {data.get('last_reset', 'N/A')}")
        else:
            print(f"   Error: {response.status_code}")


async def demo_mcp_sql():
    """Demonstrate MCP SQL server functionality."""
    print("\n" + "=" * 60)
    print("MCP SQL SERVER DEMO")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Health check
        print("\n1. Health Check")
        response = await client.get(f"{MCP_SQL_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # 2. List available templates
        print("\n2. List Available Templates")
        response = await client.get(f"{MCP_SQL_URL}/templates")
        data = response.json()
        print(f"   Available templates ({data['count']}):")
        for template in data["templates"]:
            print(f"   - {template}")

        # 3. Search issues by project
        print("\n3. Search Issues by Project")
        response = await client.post(
            f"{MCP_SQL_URL}/query",
            headers={"X-Tenant-ID": TENANT_ID},
            json={
                "template_name": "search_issues_by_project",
                "params": {
                    "project_key": "DEMO",
                    "status": "Open",
                    "limit": 10,
                },
            },
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data['total']} results")
            print(f"   Query time: {data['query_time_ms']}ms")
        else:
            print(f"   Error: {response.status_code} - {response.text}")

        # 4. Get project metrics
        print("\n4. Get Project Metrics")
        response = await client.post(
            f"{MCP_SQL_URL}/query",
            headers={"X-Tenant-ID": TENANT_ID},
            json={
                "template_name": "get_project_metrics",
                "params": {
                    "project_key": "DEMO",
                    "days": 30,
                },
            },
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Retrieved {data['total']} metric records")
            print(f"   Query time: {data['query_time_ms']}ms")
        else:
            print(f"   Error: {response.status_code} - {response.text}")

        # 5. Get metrics
        print("\n5. Server Metrics")
        response = await client.get(f"{MCP_SQL_URL}/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"   Counters: {len(data.get('counters', {}))}")
            print(f"   Histograms: {len(data.get('histograms', {}))}")
        else:
            print(f"   Error: {response.status_code}")


async def main():
    """Run all demos."""
    print("\n🚀 MCP Servers Demo")
    print("Make sure both servers are running:")
    print(f"  - MCP Jira: {MCP_JIRA_URL}")
    print(f"  - MCP SQL:  {MCP_SQL_URL}")
    print()

    try:
        await demo_mcp_jira()
        await demo_mcp_sql()

        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the servers are running:")
        print("  make mcp-jira  # Terminal 1")
        print("  make mcp-sql   # Terminal 2")


if __name__ == "__main__":
    asyncio.run(main())

