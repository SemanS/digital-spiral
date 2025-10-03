"""AI Assistant API with OpenAI integration and MCP bridge."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from clients.python.jira_cloud_adapter import JiraCloudAdapter
from . import pulse_service
from .ai_providers import get_ai_provider
from .sql_tools import execute_sql_query
from .checkpoint_service import get_checkpoint_service, create_rollback_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ai-assistant", tags=["AI Assistant"])


# --- Pydantic Models ---

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    project_keys: Optional[List[str]] = None  # Changed to support multi-select
    project_key: Optional[str] = None  # Deprecated, kept for backwards compatibility
    issue_key: Optional[str] = None


class AutocompleteRequest(BaseModel):
    query: str
    type: str  # "user" or "issue"
    project_keys: Optional[List[str]] = None  # Changed to support multi-select
    project_key: Optional[str] = None  # Deprecated, kept for backwards compatibility


class MCPAction(BaseModel):
    action: str  # "add_comment", "transition_issue", "update_issue", etc.
    issue_key: str
    params: Dict[str, Any]


# --- AI Provider Configuration ---
# Removed - now using ai_providers.py


# --- MCP Tools Definition ---

MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_comment",
            "description": "Add a comment to a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    },
                    "comment": {
                        "type": "string",
                        "description": "The comment text to add"
                    }
                },
                "required": ["issue_key", "comment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transition_issue",
            "description": "Change the status of a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    },
                    "status": {
                        "type": "string",
                        "description": "The target status (e.g., 'In Progress', 'Done')"
                    }
                },
                "required": ["issue_key", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_issues",
            "description": "Search for Jira issues using JQL",
            "parameters": {
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query (e.g., 'project = SCRUM AND status = Open')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["jql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue",
            "description": "Get detailed information about a specific Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assign_issue",
            "description": "Assign a Jira issue to a user",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "The username or account ID of the assignee"
                    }
                },
                "required": ["issue_key", "assignee"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_comments",
            "description": "Get all comments from a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aggregate_comments_by_author",
            "description": "Aggregate comments by author for visualization (e.g., pie chart showing comment count per author). Returns chart-ready data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aggregate_issues_by_status",
            "description": "Aggregate issues by status for visualization (e.g., pie chart showing issue count per status). Use with JQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query to filter issues (e.g., 'project = SCRUM')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of issues to aggregate",
                        "default": 100
                    }
                },
                "required": ["jql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aggregate_issues_by_assignee",
            "description": "Aggregate issues by assignee for visualization (e.g., bar chart showing issue count per assignee). Use with JQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query to filter issues (e.g., 'project = SCRUM AND status != Done')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of issues to aggregate",
                        "default": 100
                    }
                },
                "required": ["jql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_watcher",
            "description": "Add a watcher to a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    },
                    "account_id": {
                        "type": "string",
                        "description": "User account ID to add as watcher"
                    }
                },
                "required": ["issue_key", "account_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_watchers",
            "description": "Get all watchers of a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_issues",
            "description": "Link two Jira issues together",
            "parameters": {
                "type": "object",
                "properties": {
                    "inward_issue": {
                        "type": "string",
                        "description": "First issue key (e.g., SCRUM-123)"
                    },
                    "outward_issue": {
                        "type": "string",
                        "description": "Second issue key (e.g., SCRUM-124)"
                    },
                    "link_type": {
                        "type": "string",
                        "description": "Link type (e.g., 'Blocks', 'Relates', 'Duplicates')"
                    }
                },
                "required": ["inward_issue", "outward_issue", "link_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue_links",
            "description": "Get all links for a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_users",
            "description": "Search for Jira users by name or email",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (username, email, or display name)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 50
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_issue_field",
            "description": "Update a single field on a Jira issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    },
                    "field_name": {
                        "type": "string",
                        "description": "Field name (e.g., 'priority', 'labels', 'description')"
                    },
                    "field_value": {
                        "type": "string",
                        "description": "New field value"
                    }
                },
                "required": ["issue_key", "field_name", "field_value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_get_issue_history",
            "description": "Get full transition history for an issue from database (FAST - use for read operations)",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., SCRUM-123)"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_get_project_metrics",
            "description": "Get aggregated metrics for a project from database (throughput, WIP, lead time) - FAST",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Project key (e.g., SCRUM)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 30)",
                        "default": 30
                    }
                },
                "required": ["project_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_get_stuck_issues",
            "description": "Get issues that are stuck (no updates for X days) from database - FAST",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Project key (optional, searches all projects if not provided)"
                    },
                    "days_threshold": {
                        "type": "integer",
                        "description": "Days threshold for stuck issues (default: 7)",
                        "default": 7
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_get_user_workload",
            "description": "Get workload summary for a user from database (assigned issues by status) - FAST",
            "parameters": {
                "type": "object",
                "properties": {
                    "assignee": {
                        "type": "string",
                        "description": "User email or account ID"
                    },
                    "project_key": {
                        "type": "string",
                        "description": "Project key (optional, searches all projects if not provided)"
                    }
                },
                "required": ["assignee"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_search_issues_by_text",
            "description": "Full-text search in issue titles from database - FAST",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "project_key": {
                        "type": "string",
                        "description": "Project key (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# --- MCP Action Executor ---

async def execute_mcp_action(
    action_name: str,
    params: Dict[str, Any],
    tenant_id: str,
    project_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Execute an MCP action using Jira adapter.

    Args:
        action_name: Name of the action to execute
        params: Action parameters
        tenant_id: Tenant ID
        project_keys: List of selected project keys (for filtering SQL queries)
    """

    logger.info(f"Executing MCP action: {action_name} with params: {params}, project_keys: {project_keys}")
    
    # Get Jira instance for tenant
    instances = pulse_service.list_jira_instances(tenant_id)
    if not instances:
        raise HTTPException(404, "No Jira instance configured")
    
    instance = instances[0]
    inst_details = pulse_service.get_jira_instance(instance["id"])
    
    adapter = JiraCloudAdapter(
        inst_details["base_url"],
        inst_details["email"],
        inst_details["api_token"],
    )
    
    try:
        if action_name == "add_comment":
            # Convert plain text to ADF format
            comment_adf = {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": params["comment"]
                            }
                        ]
                    }
                ]
            }

            # Execute the operation
            result = await asyncio.to_thread(
                adapter.add_comment,
                params["issue_key"],
                comment_adf
            )

            # Create checkpoint for rollback
            checkpoint_service = get_checkpoint_service()
            rollback_data = {
                "action": "delete_comment",
                "issue_key": params["issue_key"],
                "comment_id": result.get("id")
            }
            checkpoint_id = checkpoint_service.create_checkpoint(
                tenant_id=tenant_id,
                action_name=action_name,
                params=params,
                rollback_data=rollback_data,
                issue_key=params["issue_key"]
            )

            return {
                "success": True,
                "result": result,
                "checkpoint_id": checkpoint_id
            }
        
        elif action_name == "transition_issue":
            # Get available transitions
            transitions = await asyncio.to_thread(
                adapter.list_transitions,
                params["issue_key"]
            )
            
            # Find transition by name
            target_status = params["status"].lower()
            transition_id = None
            for trans in transitions:
                if trans["name"].lower() == target_status or trans["to"]["name"].lower() == target_status:
                    transition_id = trans["id"]
                    break
            
            if not transition_id:
                return {
                    "success": False,
                    "error": f"Transition to '{params['status']}' not found. Available: {[t['name'] for t in transitions]}"
                }
            
            result = await asyncio.to_thread(
                adapter.transition_issue,
                params["issue_key"],
                transition_id
            )
            return {"success": True, "result": result}
        
        elif action_name == "search_issues":
            # Smart JQL engine - always remove project filter and use multi-project abstraction
            jql = params["jql"]

            # Remove any existing project filter from JQL
            import re
            # Remove patterns like: "project = XXX AND", "project IN (...) AND", "AND project = XXX"
            jql_clean = re.sub(r'\bproject\s*=\s*\w+\s+AND\s+', '', jql, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\bproject\s+IN\s*\([^)]+\)\s+AND\s+', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\s+AND\s+project\s*=\s*\w+', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\s+AND\s+project\s+IN\s*\([^)]+\)', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'^\s*project\s*=\s*\w+\s*$', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'^\s*project\s+IN\s*\([^)]+\)\s*$', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = jql_clean.strip()

            logger.info(f"Original JQL: {jql}")
            logger.info(f"Cleaned JQL: {jql_clean}")

            # Get project keys to use
            target_projects = project_keys

            # If ALL projects selected, get all available projects
            if not target_projects or 'ALL' in target_projects:
                try:
                    all_projects = await asyncio.to_thread(adapter.list_projects)
                    target_projects = [p["key"] for p in all_projects if p.get("key")]
                    logger.info(f"Got {len(target_projects)} projects for search: {target_projects}")
                except Exception as e:
                    logger.error(f"Failed to get projects for search: {e}")
                    return {"success": False, "error": f"Failed to get projects: {str(e)}"}

            # If multiple projects, query each separately and aggregate
            if target_projects and len(target_projects) > 1:
                logger.info(f"Querying {len(target_projects)} projects separately")
                all_issues = []
                max_results = params.get("max_results", 10)
                per_project_limit = max(1, max_results // len(target_projects))

                for project_key in target_projects:
                    try:
                        project_jql = f"project = {project_key} AND {jql_clean}" if jql_clean else f"project = {project_key}"
                        logger.info(f"Querying project {project_key}: {project_jql}")

                        result = await asyncio.to_thread(
                            adapter.search,
                            project_jql,
                            per_project_limit,
                            0,
                            ["summary", "status", "assignee", "priority"]
                        )

                        all_issues.extend(result.get("issues", []))
                    except Exception as e:
                        logger.warning(f"Failed to query project {project_key}: {e}")
                        continue

                # Limit total results
                all_issues = all_issues[:max_results]

                return {
                    "success": True,
                    "result": {
                        "issues": all_issues,
                        "total": len(all_issues)
                    }
                }

            # Single project - use simple query
            elif target_projects:
                project_jql = f"project = {target_projects[0]} AND {jql_clean}" if jql_clean else f"project = {target_projects[0]}"
                logger.info(f"Single project query: {project_jql}")

                result = await asyncio.to_thread(
                    adapter.search,
                    project_jql,
                    params.get("max_results", 10),
                    0,
                    ["summary", "status", "assignee", "priority"]
                )
                return {"success": True, "result": result}
            else:
                logger.warning("No projects available for search")
                return {"success": False, "error": "No projects available"}
        
        elif action_name == "get_issue":
            result = await asyncio.to_thread(
                adapter.get_issue,
                params["issue_key"]
            )
            return {"success": True, "result": result}
        
        elif action_name == "assign_issue":
            # Update issue assignee
            result = await asyncio.to_thread(
                adapter.update_issue,
                params["issue_key"],
                {"assignee": {"name": params["assignee"]}}
            )
            return {"success": True, "result": result}

        elif action_name == "get_comments":
            result = await asyncio.to_thread(
                adapter.get_comments,
                params["issue_key"]
            )

            # Format comments for better readability
            comments = result.get("comments", [])
            formatted = []
            for c in comments:
                # Extract text from ADF body
                body_text = ""
                if isinstance(c.get("body"), dict):
                    content = c["body"].get("content", [])
                    for block in content:
                        if block.get("type") == "paragraph":
                            for item in block.get("content", []):
                                if item.get("type") == "text":
                                    body_text += item.get("text", "")

                formatted.append({
                    "id": c.get("id"),
                    "author": c.get("author", {}).get("displayName", "Unknown"),
                    "body": body_text,
                    "created": c.get("created", "")
                })

            return {"success": True, "result": {"comments": formatted, "total": len(formatted)}}

        elif action_name == "aggregate_comments_by_author":
            # Get comments first
            result = await asyncio.to_thread(
                adapter.get_comments,
                params["issue_key"]
            )

            # Format and aggregate by author
            comments = result.get("comments", [])
            author_counts = {}

            for c in comments:
                # Extract author
                author = c.get("author", {}).get("displayName", "Unknown")
                author_counts[author] = author_counts.get(author, 0) + 1

            # Sort by count descending
            sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)

            return {
                "success": True,
                "result": {
                    "aggregation": "comments_by_author",
                    "issue_key": params["issue_key"],
                    "total_comments": len(comments),
                    "authors": [{"author": author, "count": count} for author, count in sorted_authors],
                    "chart_data": {
                        "labels": [author for author, _ in sorted_authors],
                        "values": [count for _, count in sorted_authors]
                    }
                }
            }

        elif action_name == "aggregate_issues_by_status":
            # Smart JQL engine - always remove project filter and use multi-project abstraction
            jql = params.get("jql", "")

            # Remove any existing project filter from JQL
            import re
            jql_clean = re.sub(r'\bproject\s*=\s*\w+\s+AND\s+', '', jql, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\bproject\s+IN\s*\([^)]+\)\s+AND\s+', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\s+AND\s+project\s*=\s*\w+', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\s+AND\s+project\s+IN\s*\([^)]+\)', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'^\s*project\s*=\s*\w+\s*$', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'^\s*project\s+IN\s*\([^)]+\)\s*$', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = jql_clean.strip()

            logger.info(f"Original JQL: {jql}")
            logger.info(f"Cleaned JQL: {jql_clean}")

            # Get project keys to use
            target_projects = project_keys

            # If ALL projects selected, get all available projects
            if not target_projects or 'ALL' in target_projects:
                try:
                    all_projects = await asyncio.to_thread(adapter.list_projects)
                    target_projects = [p["key"] for p in all_projects if p.get("key")]
                    logger.info(f"Got {len(target_projects)} projects for aggregation: {target_projects}")
                except Exception as e:
                    logger.error(f"Failed to get projects for aggregation: {e}")
                    return {"success": False, "error": f"Failed to get projects: {str(e)}"}

            # If multiple projects, query each separately and aggregate
            if target_projects and len(target_projects) > 1:
                logger.info(f"Aggregating {len(target_projects)} projects separately")
                all_issues = []
                max_results = params.get("max_results", 100)
                per_project_limit = max(10, max_results // len(target_projects))

                for project_key in target_projects:
                    try:
                        project_jql = f"project = {project_key}" + (f" AND {jql_clean}" if jql_clean else "")
                        logger.info(f"Aggregating project {project_key}: {project_jql}")

                        result = await asyncio.to_thread(
                            adapter.search,
                            project_jql,
                            per_project_limit,
                            0,
                            ["status"]
                        )

                        all_issues.extend(result.get("issues", []))
                    except Exception as e:
                        logger.warning(f"Failed to aggregate project {project_key}: {e}")
                        continue

                # Use aggregated issues
                issues = all_issues[:max_results]

                # Aggregate by status
                status_counts = {}
                for issue in issues:
                    status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                sorted_statuses = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)

                return {
                    "success": True,
                    "result": {
                        "aggregation": "issues_by_status",
                        "jql": jql_clean,
                        "total_issues": len(issues),
                        "statuses": [{"status": status, "count": count} for status, count in sorted_statuses],
                        "chart_data": {
                            "labels": [status for status, _ in sorted_statuses],
                            "values": [count for _, count in sorted_statuses]
                        }
                    }
                }

            # Single project - use simple query
            elif target_projects:
                jql_final = f"project = {target_projects[0]}" + (f" AND {jql_clean}" if jql_clean else "")
                logger.info(f"Single project aggregation: {jql_final}")

                result = await asyncio.to_thread(
                    adapter.search,
                    jql_final,
                    params.get("max_results", 100),
                    0,
                    ["status"]
                )

                issues = result.get("issues", [])
                status_counts = {}

                for issue in issues:
                    status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                sorted_statuses = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)

                return {
                    "success": True,
                    "result": {
                        "aggregation": "issues_by_status",
                        "jql": jql_clean,
                        "total_issues": len(issues),
                        "statuses": [{"status": status, "count": count} for status, count in sorted_statuses],
                        "chart_data": {
                            "labels": [status for status, _ in sorted_statuses],
                            "values": [count for _, count in sorted_statuses]
                        }
                    }
                }
            else:
                logger.warning("No projects available for aggregation")
                return {"success": False, "error": "No projects available"}

        elif action_name == "aggregate_issues_by_assignee":
            # Smart JQL engine - always remove project filter and use multi-project abstraction
            jql = params.get("jql", "")

            # Remove any existing project filter from JQL
            import re
            jql_clean = re.sub(r'\bproject\s*=\s*\w+\s+AND\s+', '', jql, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\bproject\s+IN\s*\([^)]+\)\s+AND\s+', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\s+AND\s+project\s*=\s*\w+', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'\s+AND\s+project\s+IN\s*\([^)]+\)', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'^\s*project\s*=\s*\w+\s*$', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = re.sub(r'^\s*project\s+IN\s*\([^)]+\)\s*$', '', jql_clean, flags=re.IGNORECASE)
            jql_clean = jql_clean.strip()

            logger.info(f"Original JQL: {jql}")
            logger.info(f"Cleaned JQL: {jql_clean}")

            # Get project keys to use
            target_projects = project_keys

            # If ALL projects selected, get all available projects
            if not target_projects or 'ALL' in target_projects:
                try:
                    all_projects = await asyncio.to_thread(adapter.list_projects)
                    target_projects = [p["key"] for p in all_projects if p.get("key")]
                    logger.info(f"Got {len(target_projects)} projects for aggregation: {target_projects}")
                except Exception as e:
                    logger.error(f"Failed to get projects for aggregation: {e}")
                    return {"success": False, "error": f"Failed to get projects: {str(e)}"}

            # If multiple projects, query each separately and aggregate
            if target_projects and len(target_projects) > 1:
                logger.info(f"Aggregating {len(target_projects)} projects separately")
                all_issues = []
                max_results = params.get("max_results", 100)
                per_project_limit = max(10, max_results // len(target_projects))

                for project_key in target_projects:
                    try:
                        project_jql = f"project = {project_key}" + (f" AND {jql_clean}" if jql_clean else "")
                        logger.info(f"Aggregating project {project_key}: {project_jql}")

                        result = await asyncio.to_thread(
                            adapter.search,
                            project_jql,
                            per_project_limit,
                            0,
                            ["assignee"]
                        )

                        all_issues.extend(result.get("issues", []))
                    except Exception as e:
                        logger.warning(f"Failed to aggregate project {project_key}: {e}")
                        continue

                # Use aggregated issues
                issues = all_issues[:max_results]

                # Aggregate by assignee
                assignee_counts = {}
                for issue in issues:
                    assignee = issue.get("fields", {}).get("assignee")
                    if assignee:
                        name = assignee.get("displayName", "Unknown")
                    else:
                        name = "Unassigned"
                    assignee_counts[name] = assignee_counts.get(name, 0) + 1

                sorted_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)

                return {
                    "success": True,
                    "result": {
                        "aggregation": "issues_by_assignee",
                        "jql": jql_clean,
                        "total_issues": len(issues),
                        "assignees": [{"assignee": assignee, "count": count} for assignee, count in sorted_assignees],
                        "chart_data": {
                            "labels": [assignee for assignee, _ in sorted_assignees],
                            "values": [count for _, count in sorted_assignees]
                        }
                    }
                }

            # Single project - use simple query
            elif target_projects:
                jql_final = f"project = {target_projects[0]}" + (f" AND {jql_clean}" if jql_clean else "")
                logger.info(f"Single project aggregation: {jql_final}")

                result = await asyncio.to_thread(
                    adapter.search,
                    jql_final,
                    params.get("max_results", 100),
                    0,
                    ["assignee"]
                )

                issues = result.get("issues", [])
                assignee_counts = {}

                for issue in issues:
                    assignee = issue.get("fields", {}).get("assignee")
                    if assignee:
                        name = assignee.get("displayName", "Unknown")
                    else:
                        name = "Unassigned"
                    assignee_counts[name] = assignee_counts.get(name, 0) + 1

                sorted_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)

                return {
                    "success": True,
                    "result": {
                        "aggregation": "issues_by_assignee",
                        "jql": jql_clean,
                        "total_issues": len(issues),
                        "assignees": [{"assignee": assignee, "count": count} for assignee, count in sorted_assignees],
                        "chart_data": {
                            "labels": [assignee for assignee, _ in sorted_assignees],
                            "values": [count for _, count in sorted_assignees]
                        }
                    }
                }
            else:
                logger.warning("No projects available for aggregation")
                return {"success": False, "error": "No projects available"}

        elif action_name == "add_watcher":
            await asyncio.to_thread(
                adapter.add_watcher,
                params["issue_key"],
                params["account_id"]
            )
            return {"success": True, "result": "Watcher added successfully"}

        elif action_name == "get_watchers":
            result = await asyncio.to_thread(
                adapter.get_watchers,
                params["issue_key"]
            )

            # Format watchers
            watchers = result.get("watchers", [])
            formatted = [
                {
                    "accountId": w.get("accountId"),
                    "displayName": w.get("displayName"),
                    "emailAddress": w.get("emailAddress")
                }
                for w in watchers
            ]

            return {"success": True, "result": {"watchers": formatted, "total": len(formatted)}}

        elif action_name == "link_issues":
            result = await asyncio.to_thread(
                adapter.link_issues,
                params["inward_issue"],
                params["outward_issue"],
                params["link_type"]
            )
            return {"success": True, "result": "Issues linked successfully"}

        elif action_name == "get_issue_links":
            result = await asyncio.to_thread(
                adapter.get_issue_links,
                params["issue_key"]
            )

            # Format links
            formatted = []
            for link in result:
                link_type = link.get("type", {})
                formatted.append({
                    "id": link.get("id"),
                    "type": link_type.get("name"),
                    "inward": link_type.get("inward"),
                    "outward": link_type.get("outward"),
                    "inwardIssue": link.get("inwardIssue", {}).get("key"),
                    "outwardIssue": link.get("outwardIssue", {}).get("key")
                })

            return {"success": True, "result": {"links": formatted, "total": len(formatted)}}

        elif action_name == "search_users":
            result = await asyncio.to_thread(
                adapter.search_users,
                params["query"],
                params.get("max_results", 50)
            )

            # Format users
            formatted = [
                {
                    "accountId": u.get("accountId"),
                    "displayName": u.get("displayName"),
                    "emailAddress": u.get("emailAddress"),
                    "active": u.get("active")
                }
                for u in result
            ]

            return {"success": True, "result": {"users": formatted, "total": len(formatted)}}

        elif action_name == "update_issue_field":
            await asyncio.to_thread(
                adapter.update_issue_field,
                params["issue_key"],
                params["field_name"],
                params["field_value"]
            )
            return {"success": True, "result": f"Field '{params['field_name']}' updated successfully"}

        # SQL Tools (fast read operations from database)
        elif action_name == "sql_get_issue_history":
            result = await execute_sql_query(
                "get_issue_history",
                {"issue_key": params["issue_key"]},
                tenant_id
            )
            return result

        elif action_name == "sql_get_project_metrics":
            # If project_keys provided, use them; otherwise use param
            target_projects = project_keys if project_keys and 'ALL' not in project_keys else [params.get("project_key")]

            result = await execute_sql_query(
                "get_project_metrics",
                {
                    "project_keys": target_projects,
                    "days": params.get("days", 30)
                },
                tenant_id
            )
            return result

        elif action_name == "sql_get_stuck_issues":
            # If project_keys provided, use them; otherwise use param
            target_projects = project_keys if project_keys and 'ALL' not in project_keys else [params.get("project_key")] if params.get("project_key") else None

            result = await execute_sql_query(
                "get_stuck_issues",
                {
                    "project_keys": target_projects,
                    "days_threshold": params.get("days_threshold", 7)
                },
                tenant_id
            )
            return result

        elif action_name == "sql_get_user_workload":
            # If project_keys provided, use them; otherwise use param
            target_projects = project_keys if project_keys and 'ALL' not in project_keys else [params.get("project_key")] if params.get("project_key") else None

            result = await execute_sql_query(
                "get_user_workload",
                {
                    "assignee": params["assignee"],
                    "project_keys": target_projects
                },
                tenant_id
            )
            return result

        elif action_name == "sql_search_issues_by_text":
            # If project_keys provided, use them; otherwise use param
            target_projects = project_keys if project_keys and 'ALL' not in project_keys else [params.get("project_key")] if params.get("project_key") else None

            result = await execute_sql_query(
                "search_issues_by_text",
                {
                    "query": params["query"],
                    "project_keys": target_projects,
                    "limit": params.get("limit", 20)
                },
                tenant_id
            )
            return result

        else:
            return {"success": False, "error": f"Unknown action: {action_name}"}
    
    except Exception as e:
        logger.error(f"MCP action failed: {e}")
        return {"success": False, "error": str(e)}


# --- API Endpoints ---

@router.post("/chat")
async def chat(request: Request, chat_req: ChatRequest):
    """Chat with AI assistant that can execute Jira actions via MCP."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    # Log incoming request
    logger.info(f"Chat request - project_keys: {chat_req.project_keys}, project_key: {chat_req.project_key}")

    try:
        # Get AI provider (Google AI or OpenAI)
        provider = get_ai_provider(tenant_id)

        # Build system message with context and visualization instructions
        system_message = (
            "Si užitočný Jira asistent. Môžeš pomôcť používateľom spravovať ich Jira issues. "
            "\n\n"
            "**DÔLEŽITÉ - Výber nástroja:**\n"
            "- Pre READ operácie (čítanie dát): VŽDY použi SQL nástroje (sql_*) - sú RÝCHLEJŠIE!\n"
            "  Príklady: história issue, metriky projektu, stuck issues, workload používateľa\n"
            "- Pre WRITE operácie (zmeny): Použi MCP nástroje (add_comment, transition_issue, atď.)\n"
            "  Príklady: pridať komentár, zmeniť status, priradiť issue\n"
            "\n"
            "**Dostupné SQL nástroje (RÝCHLE čítanie z databázy):**\n"
            "- sql_get_issue_history - História zmien issue\n"
            "- sql_get_project_metrics - Metriky projektu (throughput, WIP, lead time)\n"
            "- sql_get_stuck_issues - Stuck issues (žiadne updaty X dní)\n"
            "- sql_get_user_workload - Workload používateľa\n"
            "- sql_search_issues_by_text - Full-text search v názvoch\n"
            "\n"
            "**Dostupné MCP nástroje (zápis cez Jira API):**\n"
            "- add_comment, get_comments, transition_issue, search_issues, get_issue\n"
            "- assign_issue, add_watcher, get_watchers, link_issues, get_issue_links\n"
            "- search_users, update_issue_field\n"
            "\n"
            "**DÔLEŽITÉ - JQL queries:**\n"
            "- Keď používaš search_issues alebo agregačné funkcie, NEMUSÍŠ pridávať project filter do JQL\n"
            "- Systém automaticky pridá project filter na základe vybraných projektov v UI\n"
            "- Príklad: Namiesto 'project = SCRUM AND created >= \"-3d\"' použi len 'created >= \"-3d\"'\n"
            "\n"
            "**Dostupné agregačné nástroje (pre vizualizáciu):**\n"
            "- aggregate_comments_by_author(issue_key) - Komentáre podľa autora (doughnut chart)\n"
            "- aggregate_issues_by_status(jql) - Issues podľa statusu (doughnut chart)\n"
            "- aggregate_issues_by_assignee(jql) - Issues podľa assignee (bar chart)\n"
            "\n"
            "**KRITICKY DÔLEŽITÉ - Vizualizácia dát:**\n"
            "\n"
            "Keď používateľ žiada o dáta (metriky, zoznamy, štatistiky), MUSÍŠ ich vizualizovať!\n"
            "\n"
            "**Kedy použiť CHART:**\n"
            "- Metriky projektu (throughput, WIP, lead time)\n"
            "- Workload používateľa (issues podľa statusu)\n"
            "- Štatistiky, porovnania čísel\n"
            "\n"
            "**Kedy použiť TABLE:**\n"
            "- Zoznam issues (stuck issues, search results)\n"
            "- História zmien\n"
            "- Akýkoľvek zoznam položiek\n"
            "\n"
            "**Formát odpovede s vizualizáciou:**\n"
            "\n"
            "Keď chceš vytvoriť CHART, odpoveď MUSÍ obsahovať:\n"
            "```visualization:chart\n"
            '{"title": "Názov", "chartType": "bar|doughnut", "labels": [...], "values": [...]}\n'
            "```\n"
            "\n"
            "Keď chceš vytvoriť TABLE, odpoveď MUSÍ obsahovať:\n"
            "```visualization:table\n"
            '{"title": "Názov", "columns": [...], "rows": [[...], [...]]}\n'
            "```\n"
            "\n"
            "**Príklady:**\n"
            "\n"
            "Používateľ: 'Aké sú metriky projektu SCRUM?'\n"
            "→ Zavolaj sql_get_project_metrics\n"
            "→ Odpoveď:\n"
            "```visualization:chart\n"
            '{"title": "Metriky projektu SCRUM", "chartType": "bar", "labels": ["Vytvorených", "Uzavretých", "WIP", "Lead time"], "values": [45, 38, 12, 5.2]}\n'
            "```\n"
            "\n"
            "Používateľ: 'Ktoré issues sú stuck?'\n"
            "→ Zavolaj sql_get_stuck_issues\n"
            "→ Odpoveď:\n"
            "```visualization:table\n"
            '{"title": "Stuck issues", "columns": ["Issue", "Summary", "Status", "Days"], "rows": [["SCRUM-1", "Bug", "In Progress", "10"], ["SCRUM-2", "Task", "Todo", "8"]]}\n'
            "```\n"
            "\n"
            "Používateľ: 'Zobraz komentáre v koláčovom grafe pre SCRUM-229'\n"
            "→ Zavolaj aggregate_comments_by_author(issue_key='SCRUM-229')\n"
            "→ Dostaneš: {chart_data: {labels: ['John', 'Jane'], values: [5, 3]}}\n"
            "→ Odpoveď:\n"
            "```visualization:chart\n"
            '{"title": "Komentáre v SCRUM-229 podľa autora", "chartType": "doughnut", "labels": ["John", "Jane"], "values": [5, 3]}\n'
            "```\n"
            "\n"
            "Používateľ: 'Zobraz issues v projekte SCRUM podľa statusu'\n"
            "→ Zavolaj aggregate_issues_by_status(jql='project = SCRUM')\n"
            "→ Dostaneš: {chart_data: {labels: ['Done', 'In Progress', 'Todo'], values: [20, 5, 3]}}\n"
            "→ Odpoveď:\n"
            "```visualization:chart\n"
            '{"title": "Issues v SCRUM podľa statusu", "chartType": "doughnut", "labels": ["Done", "In Progress", "Todo"], "values": [20, 5, 3]}\n'
            "```\n"
            "\n"
            "Používateľ: 'Kto má najviac issues v projekte SCRUM?'\n"
            "→ Zavolaj aggregate_issues_by_assignee(jql='project = SCRUM AND status != Done')\n"
            "→ Dostaneš: {chart_data: {labels: ['John', 'Jane', 'Bob'], values: [8, 5, 2]}}\n"
            "→ Odpoveď:\n"
            "```visualization:chart\n"
            '{"title": "Aktívne issues v SCRUM podľa assignee", "chartType": "bar", "labels": ["John", "Jane", "Bob"], "values": [8, 5, 2]}\n'
            "```\n"
            "\n"
            "Buď stručný a užitočný vo svojich odpovediach. Odpovedaj v slovenčine."
        )

        # Add context if issue_key or project_keys provided
        if chat_req.issue_key:
            system_message += f"\n\nAktuálne issue: {chat_req.issue_key}"

        # Support both project_keys (new) and project_key (old)
        project_keys = chat_req.project_keys or ([chat_req.project_key] if chat_req.project_key else [])

        if project_keys:
            if 'ALL' in project_keys:
                system_message += f"\n\nVybrané projekty: VŠETKY PROJEKTY"
            elif len(project_keys) == 1:
                system_message += f"\n\nVybraný projekt: {project_keys[0]}"
            else:
                system_message += f"\n\nVybrané projekty: {', '.join(project_keys)}"

        # Convert messages to provider format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in chat_req.messages
        ]

        # Call AI provider with tools
        response = await provider.chat(
            messages=messages,
            tools=MCP_TOOLS,
            system_message=system_message
        )

        # Check if AI wants to call tools
        if response.get("tool_calls"):
            tool_results = []

            for tool_call in response["tool_calls"]:
                function_name = tool_call["function_name"]
                function_args = tool_call["arguments"]

                # Execute MCP action with project_keys context
                result = await execute_mcp_action(function_name, function_args, tenant_id, project_keys)

                tool_results.append({
                    "tool_call_id": tool_call["tool_call_id"],
                    "function_name": function_name,
                    "result": result
                })

            # Add tool results to conversation as user message
            # (Gemini doesn't support role: "tool", so we format it as user message)
            tool_results_text = "\n\n".join([
                f"Tool: {tr['function_name']}\nResult: {tr['result']}"
                for tr in tool_results
            ])

            messages.append({
                "role": "user",
                "content": f"Tool results:\n\n{tool_results_text}\n\nTeraz vytvor vizualizáciu týchto dát."
            })

            # Call AI again with tool results to get final response
            final_response = await provider.chat(
                messages=messages,
                tools=MCP_TOOLS,
                system_message=system_message
            )

            return {
                "message": final_response["message"],
                "tool_calls": tool_results,
                "content": final_response.get("message", "")
            }

        return {
            "message": response["message"],
            "tool_calls": [],
            "content": response.get("message", "")
        }

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Chat failed: {str(e)}")


@router.post("/autocomplete")
async def autocomplete(request: Request, autocomplete_req: AutocompleteRequest):
    """Autocomplete for @users and /issues."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        # Get Jira instance
        instances = pulse_service.list_jira_instances(tenant_id)
        if not instances:
            return {"suggestions": []}

        instance = instances[0]
        inst_details = pulse_service.get_jira_instance(instance["id"])

        adapter = JiraCloudAdapter(
            inst_details["base_url"],
            inst_details["email"],
            inst_details["api_token"],
        )

        if autocomplete_req.type == "user":
            # Search for users
            # Note: Jira Cloud API has user search endpoint
            # For now, return mock data
            # TODO: Implement real user search via adapter
            users = [
                {"id": "user1", "name": "John Doe", "email": "john@example.com"},
                {"id": "user2", "name": "Jane Smith", "email": "jane@example.com"},
                {"id": "user3", "name": "Bob Johnson", "email": "bob@example.com"},
            ]

            query_lower = autocomplete_req.query.lower()
            filtered = [
                u for u in users
                if query_lower in u["name"].lower() or query_lower in u["email"].lower()
            ]

            return {
                "suggestions": [
                    {
                        "type": "user",
                        "id": u["id"],
                        "display": u["name"],
                        "secondary": u["email"]
                    }
                    for u in filtered[:10]
                ]
            }

        elif autocomplete_req.type == "issue":
            # Search for issues
            # Support both project_keys (new) and project_key (old)
            project_keys = autocomplete_req.project_keys or ([autocomplete_req.project_key] if autocomplete_req.project_key else [])

            # If ALL projects selected, get all available projects first
            if not project_keys or 'ALL' in project_keys:
                # Get all projects using list_projects()
                try:
                    all_projects = await asyncio.to_thread(adapter.list_projects)
                    project_keys = [p["key"] for p in all_projects if p.get("key")]
                    logger.info(f"Got {len(project_keys)} projects for autocomplete: {project_keys}")
                except Exception as e:
                    logger.error(f"Failed to get projects for autocomplete: {e}")
                    traceback.print_exc()
                    # Fallback to empty list
                    project_keys = []

                # If no projects found, return empty
                if not project_keys:
                    logger.warning("No projects found for autocomplete")
                    return {"suggestions": []}

            # Use Jira API with project filter
            if project_keys:
                all_issues = []

                # Query each project separately to avoid JQL issues
                for project_key in project_keys[:5]:  # Limit to first 5 projects for performance
                    try:
                        jql = f"project = {project_key} AND text ~ \"{autocomplete_req.query}*\" ORDER BY updated DESC"

                        result = await asyncio.to_thread(
                            adapter.search,
                            jql,
                            5,  # Get 5 issues per project
                            0,
                            ["summary", "status", "issuetype"]
                        )

                        all_issues.extend(result.get("issues", []))
                    except Exception as e:
                        logger.warning(f"Failed to search in project {project_key}: {e}")
                        continue

                # Limit total results to 10
                all_issues = all_issues[:10]

                return {
                    "suggestions": [
                        {
                            "type": "issue",
                            "id": issue["key"],
                            "display": f"{issue['key']}: {issue['fields']['summary']}",
                            "secondary": f"{issue['fields']['issuetype']['name']} - {issue['fields']['status']['name']}"
                        }
                        for issue in all_issues
                    ]
                }

        else:
            return {"suggestions": []}

    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        return {"suggestions": []}


@router.get("/context/{issue_key}")
async def get_issue_context(request: Request, issue_key: str):
    """Get context about an issue for the AI assistant."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        # Get Jira instance
        instances = pulse_service.list_jira_instances(tenant_id)
        if not instances:
            raise HTTPException(404, "No Jira instance configured")

        instance = instances[0]
        inst_details = pulse_service.get_jira_instance(instance["id"])

        adapter = JiraCloudAdapter(
            inst_details["base_url"],
            inst_details["email"],
            inst_details["api_token"],
        )

        # Get issue details
        issue = await asyncio.to_thread(adapter.get_issue, issue_key)

        # Get comments
        comments = issue.get("fields", {}).get("comment", {}).get("comments", [])

        # Get transitions
        transitions = await asyncio.to_thread(adapter.list_transitions, issue_key)

        return {
            "issue": {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "description": issue["fields"].get("description"),
                "status": issue["fields"]["status"]["name"],
                "assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned"),
                "priority": issue["fields"].get("priority", {}).get("name", "None"),
                "type": issue["fields"]["issuetype"]["name"],
                "created": issue["fields"]["created"],
                "updated": issue["fields"]["updated"],
            },
            "comments": [
                {
                    "author": c.get("author", {}).get("displayName", "Unknown"),
                    "body": c.get("body"),
                    "created": c.get("created")
                }
                for c in comments[-5:]  # Last 5 comments
            ],
            "available_transitions": [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "to": t["to"]["name"]
                }
                for t in transitions
            ]
        }

    except Exception as e:
        logger.error(f"Get context failed: {e}")
        raise HTTPException(500, f"Failed to get issue context: {str(e)}")


@router.get("/checkpoints")
async def list_checkpoints(request: Request, issue_key: Optional[str] = None, limit: int = 50):
    """List checkpoints for rollback."""

    tenant_id = request.headers.get("x-tenant-id", "demo")
    checkpoint_service = get_checkpoint_service()

    checkpoints = checkpoint_service.list_checkpoints(
        tenant_id=tenant_id,
        issue_key=issue_key,
        limit=limit,
        include_rolled_back=False
    )

    return {"checkpoints": checkpoints}


@router.post("/rollback/{checkpoint_id}")
async def rollback_checkpoint(request: Request, checkpoint_id: int):
    """Rollback a write operation using checkpoint."""

    tenant_id = request.headers.get("x-tenant-id", "demo")
    checkpoint_service = get_checkpoint_service()

    # Get checkpoint
    checkpoint = checkpoint_service.get_checkpoint(checkpoint_id)
    if not checkpoint:
        raise HTTPException(404, "Checkpoint not found")

    if checkpoint["rolled_back"]:
        raise HTTPException(400, "Checkpoint already rolled back")

    if checkpoint["tenant_id"] != tenant_id:
        raise HTTPException(403, "Unauthorized")

    # Get rollback data
    rollback_data = checkpoint["rollback_data"]
    rollback_action = rollback_data.get("action")

    # Get Jira adapter
    instances = pulse_service.list_jira_instances(tenant_id)
    if not instances:
        raise HTTPException(404, "No Jira instance configured")

    instance = instances[0]
    adapter = JiraCloudAdapter(
        base_url=instance["base_url"],
        email=instance["email"],
        api_token=instance["api_token"]
    )

    try:
        # Execute rollback operation
        if rollback_action == "delete_comment":
            await asyncio.to_thread(
                adapter.delete_comment,
                rollback_data["issue_key"],
                rollback_data["comment_id"]
            )

        elif rollback_action == "transition_issue":
            await asyncio.to_thread(
                adapter.transition_issue,
                rollback_data["issue_key"],
                rollback_data["transition_id"]
            )

        elif rollback_action == "assign_issue":
            await asyncio.to_thread(
                adapter.assign_issue,
                rollback_data["issue_key"],
                rollback_data["assignee"]
            )

        elif rollback_action == "remove_watcher":
            await asyncio.to_thread(
                adapter.remove_watcher,
                rollback_data["issue_key"],
                rollback_data["account_id"]
            )

        elif rollback_action == "update_issue_field":
            await asyncio.to_thread(
                adapter.update_issue_field,
                rollback_data["issue_key"],
                rollback_data["field_name"],
                rollback_data["field_value"]
            )

        else:
            raise HTTPException(400, f"Unknown rollback action: {rollback_action}")

        # Mark checkpoint as rolled back
        checkpoint_service.mark_rolled_back(checkpoint_id)

        return {
            "success": True,
            "message": f"Successfully rolled back {checkpoint['action_name']}",
            "checkpoint_id": checkpoint_id
        }

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(500, f"Rollback failed: {str(e)}")


@router.get("/", response_class=HTMLResponse)
async def ai_assistant_page():
    """Serve the AI Assistant HTML page."""

    template_path = Path(__file__).parent / "templates" / "ai_assistant.html"
    if not template_path.exists():
        raise HTTPException(404, "AI Assistant page not found")

    return template_path.read_text()

