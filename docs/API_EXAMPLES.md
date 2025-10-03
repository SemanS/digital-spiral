# Digital Spiral API Examples

This document provides practical examples of using the Digital Spiral API.

## Table of Contents

- [Authentication](#authentication)
- [Issue Operations](#issue-operations)
- [Sync Operations](#sync-operations)
- [AI Features](#ai-features)
- [Webhooks](#webhooks)
- [Python Client Examples](#python-client-examples)

## Authentication

### OAuth 2.0 Flow

```bash
# Step 1: Get authorization URL
curl http://localhost:8000/auth/authorize?instance_id=UUID

# Step 2: User authorizes in browser

# Step 3: Exchange code for token
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "authorization_code",
    "state": "state_value"
  }'
```

## Issue Operations

### Get Issue by ID

```bash
curl http://localhost:8000/issues/550e8400-e29b-41d4-a716-446655440000
```

### Get Issue by Key

```bash
curl http://localhost:8000/issues/key/PROJ-123
```

### Search Issues

```bash
# Search by project
curl "http://localhost:8000/issues?instance_id=UUID&project_key=PROJ&skip=0&limit=50"

# Search by status
curl "http://localhost:8000/issues?instance_id=UUID&status=In%20Progress"

# Search by assignee
curl "http://localhost:8000/issues?instance_id=UUID&assignee_account_id=user123"

# Text search
curl "http://localhost:8000/issues?instance_id=UUID&query=login%20bug"

# Combined filters
curl "http://localhost:8000/issues?instance_id=UUID&project_key=PROJ&status=Open&priority=High"
```

### Get Issues by Project

```bash
curl "http://localhost:8000/issues/project/PROJ?instance_id=UUID&skip=0&limit=50"
```

### Sync Issue from Jira

```bash
curl -X POST http://localhost:8000/issues/sync \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "550e8400-e29b-41d4-a716-446655440000",
    "issue_key": "PROJ-123"
  }'
```

## Sync Operations

### Full Sync

```bash
curl -X POST http://localhost:8000/sync/full/550e8400-e29b-41d4-a716-446655440000
```

### Incremental Sync

```bash
# Sync changes from last hour
curl -X POST http://localhost:8000/sync/incremental \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# Sync changes since specific date
curl -X POST http://localhost:8000/sync/incremental \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "550e8400-e29b-41d4-a716-446655440000",
    "since": "2024-01-01T00:00:00Z"
  }'
```

### Get Sync Status

```bash
curl http://localhost:8000/sync/status/550e8400-e29b-41d4-a716-446655440000
```

## AI Features

### Classify Issue

```bash
curl -X POST http://localhost:8000/ai/classify \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Login page crashes on mobile devices",
    "description": "Users report that the app crashes when they try to login on iOS devices. This started happening after the latest update.",
    "issue_type": "Bug"
  }'

# Response:
# {
#   "suggested_type": "Bug",
#   "suggested_priority": "Highest",
#   "suggested_labels": ["authentication", "mobile", "ios", "critical"],
#   "estimated_story_points": 5
# }
```

### Analyze Sentiment

```bash
# Positive sentiment
curl -X POST http://localhost:8000/ai/sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This new feature is absolutely amazing! It works perfectly and saves us so much time."
  }'

# Negative sentiment
curl -X POST http://localhost:8000/ai/sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is completely broken. Nothing works and we are losing customers."
  }'

# Response:
# {
#   "sentiment": "negative",
#   "confidence": 0.95,
#   "reasoning": "The text expresses strong frustration and reports critical issues"
# }
```

### Generate AI Insights

```bash
curl -X POST http://localhost:8000/ai/insights \
  -H "Content-Type: application/json" \
  -d '{
    "issue_summary": "API response time degradation",
    "issue_description": "The API response times have increased from 100ms to 2 seconds over the past week. This is affecting all endpoints.",
    "issue_type": "Bug",
    "status": "Open"
  }'

# Response:
# {
#   "summary": "Critical performance issue affecting all API endpoints with 20x response time increase",
#   "next_steps": [
#     "Profile API endpoints to identify performance bottlenecks",
#     "Check database query performance and indexes",
#     "Review recent code changes and deployments",
#     "Monitor server resources (CPU, memory, disk I/O)",
#     "Consider implementing caching for frequently accessed data"
#   ],
#   "blockers": [
#     {
#       "type": "technical",
#       "description": "Need production database access for query analysis"
#     },
#     {
#       "type": "resource",
#       "description": "May need additional server capacity"
#     }
#   ]
# }
```

### Generate Embeddings

```bash
curl -X POST "http://localhost:8000/ai/embed?text=login%20authentication%20issues%20on%20mobile"

# Response:
# {
#   "text": "login authentication issues on mobile",
#   "embedding": [0.123, -0.456, 0.789, ...],
#   "dimension": 1536
# }
```

## Webhooks

### Jira Webhook

```bash
# Jira sends webhook to your endpoint
POST http://localhost:8000/webhooks/jira
Content-Type: application/json
X-Hub-Signature: sha256=...

{
  "webhookEvent": "jira:issue_created",
  "issue": {
    "id": "10001",
    "key": "PROJ-123",
    "fields": {
      "summary": "New issue",
      "status": {"name": "To Do"}
    }
  }
}
```

### Webhook Health Check

```bash
curl http://localhost:8000/webhooks/jira/health
```

## Python Client Examples

### Basic Usage

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Get issue
        response = await client.get(
            "http://localhost:8000/issues/key/PROJ-123"
        )
        issue = response.json()
        print(f"Issue: {issue['summary']}")
        
        # Classify issue
        response = await client.post(
            "http://localhost:8000/ai/classify",
            json={
                "summary": "Login broken",
                "description": "Users cannot login"
            }
        )
        classification = response.json()
        print(f"Suggested priority: {classification['suggested_priority']}")

asyncio.run(main())
```

### Batch Processing

```python
import httpx
import asyncio

async def sync_issues(issue_keys: list[str]):
    """Sync multiple issues in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = []
        for key in issue_keys:
            task = client.post(
                "http://localhost:8000/issues/sync",
                json={
                    "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                    "issue_key": key
                }
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# Usage
issue_keys = ["PROJ-1", "PROJ-2", "PROJ-3"]
results = asyncio.run(sync_issues(issue_keys))
```

### Sentiment Analysis Pipeline

```python
import httpx
import asyncio

async def analyze_issue_sentiment(issue_key: str):
    """Analyze sentiment of issue and its comments."""
    async with httpx.AsyncClient() as client:
        # Get issue
        response = await client.get(
            f"http://localhost:8000/issues/key/{issue_key}"
        )
        issue = response.json()
        
        # Analyze issue sentiment
        text = f"{issue['summary']} {issue['description']}"
        response = await client.post(
            "http://localhost:8000/ai/sentiment",
            json={"text": text}
        )
        sentiment = response.json()
        
        print(f"Issue {issue_key}:")
        print(f"  Sentiment: {sentiment['sentiment']}")
        print(f"  Confidence: {sentiment['confidence']}")
        print(f"  Reasoning: {sentiment['reasoning']}")

asyncio.run(analyze_issue_sentiment("PROJ-123"))
```

### AI-Powered Issue Triage

```python
import httpx
import asyncio

async def triage_issue(summary: str, description: str):
    """Automatically triage new issue using AI."""
    async with httpx.AsyncClient() as client:
        # Classify issue
        response = await client.post(
            "http://localhost:8000/ai/classify",
            json={
                "summary": summary,
                "description": description
            }
        )
        classification = response.json()
        
        # Analyze sentiment
        response = await client.post(
            "http://localhost:8000/ai/sentiment",
            json={"text": f"{summary} {description}"}
        )
        sentiment = response.json()
        
        # Generate insights
        response = await client.post(
            "http://localhost:8000/ai/insights",
            json={
                "issue_summary": summary,
                "issue_description": description,
                "issue_type": classification["suggested_type"]
            }
        )
        insights = response.json()
        
        return {
            "classification": classification,
            "sentiment": sentiment,
            "insights": insights
        }

# Usage
result = asyncio.run(triage_issue(
    "Login page not responding",
    "Users are unable to access the login page. It shows a blank screen."
))

print(f"Type: {result['classification']['suggested_type']}")
print(f"Priority: {result['classification']['suggested_priority']}")
print(f"Labels: {', '.join(result['classification']['suggested_labels'])}")
print(f"Sentiment: {result['sentiment']['sentiment']}")
print(f"Next steps: {result['insights']['next_steps']}")
```

## Error Handling

```python
import httpx
import asyncio

async def safe_api_call():
    """Example with proper error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8000/issues/key/INVALID"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print("Issue not found")
            elif e.response.status_code == 400:
                error = e.response.json()
                print(f"Validation error: {error['message']}")
            else:
                print(f"HTTP error: {e}")
                
        except httpx.RequestError as e:
            print(f"Request error: {e}")

asyncio.run(safe_api_call())
```

## Rate Limiting

The API implements rate limiting. Handle 429 responses:

```python
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def api_call_with_retry():
    """API call with automatic retry on rate limit."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/issues/key/PROJ-123")
        response.raise_for_status()
        return response.json()

asyncio.run(api_call_with_retry())
```

