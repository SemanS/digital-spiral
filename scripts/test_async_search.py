#!/usr/bin/env python3
"""Test async search."""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.python.jira_cloud_adapter import JiraCloudAdapter


def _load_env_from_dotenv() -> None:
    """Load KEY=VALUE pairs from .env at repo root into os.environ."""
    repo_root = Path(__file__).resolve().parent.parent
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
    except Exception:
        # Best-effort only; ignore malformed lines
        pass


async def test_async_search():
    """Test search via asyncio.to_thread()."""
    _load_env_from_dotenv()

    base_url = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")

    if not base_url or not email or not api_token:
        raise RuntimeError(
            "Missing JIRA credentials. Please set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env"
        )

    adapter = JiraCloudAdapter(base_url, email, api_token)
    
    print("🔍 Testing asyncio.to_thread(adapter.search)")
    print("=" * 60)
    
    try:
        result = await asyncio.to_thread(
            adapter.search,
            "project = SCRUM ORDER BY updated DESC",
            50,
            0,
            ["summary", "status", "assignee", "priority", "issuetype", "created", "updated"]
        )
        
        print(f"✅ SUCCESS!")
        print(f"   Type: {type(result)}")
        print(f"   Is None: {result is None}")
        
        if result:
            print(f"   Total: {result.get('total', 'N/A')}")
            print(f"   Issues count: {len(result.get('issues', []))}")
            
            if result.get("issues"):
                print(f"\n   First 3 issues:")
                for issue in result["issues"][:3]:
                    print(f"      - {issue['key']}: {issue['fields']['summary']}")
        else:
            print(f"   ❌ Result is None!")
    
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_async_search())
