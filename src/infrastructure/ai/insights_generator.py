"""AI-powered insights generator."""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    AI-powered insights generator.
    
    Generates insights and recommendations from Jira data.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize generator.

        Args:
            llm_client: LLM client
        """
        self.llm_client = llm_client

    async def generate_issue_summary(self, issue: dict[str, Any]) -> str:
        """
        Generate concise summary of issue.

        Args:
            issue: Issue data

        Returns:
            Generated summary
        """
        logger.info(f"Generating summary for: {issue.get('summary', 'N/A')}")

        prompt = f"""Summarize this Jira issue in 1-2 sentences:

Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}
Type: {issue.get('issue_type', '')}
Status: {issue.get('status', '')}

Provide a concise, technical summary."""

        return await self.llm_client.complete(
            prompt=prompt,
            max_tokens=150,
            temperature=0.5,
        )

    async def suggest_next_steps(self, issue: dict[str, Any]) -> list[str]:
        """
        Suggest next steps for issue.

        Args:
            issue: Issue data

        Returns:
            List of suggested next steps
        """
        logger.info(f"Suggesting next steps for: {issue.get('summary', 'N/A')}")

        prompt = f"""Based on this Jira issue, suggest 3-5 concrete next steps:

Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}
Type: {issue.get('issue_type', '')}
Status: {issue.get('status', '')}

Respond with a numbered list of actionable next steps."""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=300,
            temperature=0.7,
        )

        # Parse numbered list
        steps = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering
                step = line.lstrip("0123456789.-) ")
                if step:
                    steps.append(step)

        return steps

    async def identify_blockers(self, issue: dict[str, Any]) -> list[dict[str, str]]:
        """
        Identify potential blockers.

        Args:
            issue: Issue data

        Returns:
            List of identified blockers
        """
        logger.info(f"Identifying blockers for: {issue.get('summary', 'N/A')}")

        prompt = f"""Analyze this Jira issue and identify potential blockers or dependencies:

Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}
Type: {issue.get('issue_type', '')}

Respond in JSON format with an array of blockers:
[
  {{"type": "technical", "description": "Missing API documentation"}},
  {{"type": "resource", "description": "Need database access"}}
]

Types: technical, resource, dependency, approval"""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=400,
            temperature=0.5,
        )

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse blockers response: {response}")
            return []

    async def generate_project_insights(
        self,
        project: dict[str, Any],
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate insights for project.

        Args:
            project: Project data
            issues: List of issues

        Returns:
            Project insights
        """
        logger.info(f"Generating insights for project: {project.get('name', 'N/A')}")

        # Calculate statistics
        total_issues = len(issues)
        bug_count = sum(1 for i in issues if i.get("issue_type") == "Bug")
        open_count = sum(1 for i in issues if i.get("status") not in ["Done", "Closed"])

        # Build context
        context = f"""Project: {project.get('name', '')}
Total Issues: {total_issues}
Bugs: {bug_count}
Open Issues: {open_count}

Recent Issues:
"""
        for issue in issues[:5]:
            context += f"- {issue.get('summary', '')}\n"

        prompt = f"""{context}

Analyze this project and provide insights in JSON format:
{{
  "health_score": 0-100,
  "key_findings": ["finding1", "finding2"],
  "recommendations": ["rec1", "rec2"],
  "risks": ["risk1", "risk2"],
  "trends": ["trend1", "trend2"]
}}"""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=600,
            temperature=0.6,
        )

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse insights response: {response}")
            return {
                "health_score": 70,
                "key_findings": [],
                "recommendations": [],
                "risks": [],
                "trends": [],
            }

    async def detect_patterns(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Detect patterns in issues.

        Args:
            issues: List of issues

        Returns:
            Detected patterns
        """
        logger.info(f"Detecting patterns in {len(issues)} issues")

        # Build context
        summaries = [i.get("summary", "") for i in issues[:20]]
        context = "\n".join(f"- {s}" for s in summaries)

        prompt = f"""Analyze these issue summaries and detect patterns:

{context}

Respond in JSON format:
{{
  "common_themes": ["theme1", "theme2"],
  "recurring_issues": ["issue1", "issue2"],
  "suggested_epics": ["epic1", "epic2"],
  "technical_debt_indicators": ["indicator1", "indicator2"]
}}"""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=500,
            temperature=0.6,
        )

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse patterns response: {response}")
            return {
                "common_themes": [],
                "recurring_issues": [],
                "suggested_epics": [],
                "technical_debt_indicators": [],
            }

    async def generate_release_notes(
        self,
        issues: list[dict[str, Any]],
        version: str,
    ) -> str:
        """
        Generate release notes from issues.

        Args:
            issues: List of issues in release
            version: Version number

        Returns:
            Generated release notes
        """
        logger.info(f"Generating release notes for version {version}")

        # Group by type
        features = [i for i in issues if i.get("issue_type") in ["Story", "Epic"]]
        bugs = [i for i in issues if i.get("issue_type") == "Bug"]
        improvements = [i for i in issues if i.get("issue_type") == "Improvement"]

        context = f"""Version: {version}

Features ({len(features)}):
"""
        for issue in features[:10]:
            context += f"- {issue.get('summary', '')}\n"

        context += f"\nBug Fixes ({len(bugs)}):\n"
        for issue in bugs[:10]:
            context += f"- {issue.get('summary', '')}\n"

        prompt = f"""{context}

Generate professional release notes in markdown format. Include:
- Overview
- New Features
- Bug Fixes
- Improvements
- Known Issues (if any)"""

        return await self.llm_client.complete(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )


__all__ = ["InsightsGenerator"]

