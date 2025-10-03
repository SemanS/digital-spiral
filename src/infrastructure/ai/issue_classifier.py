"""AI-powered issue classification."""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


class IssueClassifier:
    """
    AI-powered issue classifier.
    
    Classifies issues by type, priority, and other attributes.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize classifier.

        Args:
            llm_client: LLM client
        """
        self.llm_client = llm_client

    async def classify_issue_type(self, issue: dict[str, Any]) -> str:
        """
        Classify issue type.

        Args:
            issue: Issue data

        Returns:
            Issue type (Bug, Task, Story, Epic, etc.)
        """
        logger.info(f"Classifying issue type for: {issue.get('summary', 'N/A')}")

        # Define categories
        categories = ["Bug", "Task", "Story", "Epic", "Improvement", "Sub-task"]

        # Build context
        text = f"""Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}"""

        # Classify
        return await self.llm_client.classify(
            text=text,
            categories=categories,
            system_prompt="You are an expert at classifying Jira issues based on their content.",
        )

    async def classify_priority(self, issue: dict[str, Any]) -> str:
        """
        Classify issue priority.

        Args:
            issue: Issue data

        Returns:
            Priority (Highest, High, Medium, Low, Lowest)
        """
        logger.info(f"Classifying priority for: {issue.get('summary', 'N/A')}")

        # Define categories
        categories = ["Highest", "High", "Medium", "Low", "Lowest"]

        # Build context
        text = f"""Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}"""

        system_prompt = """You are an expert at prioritizing Jira issues. Consider:
- Severity of the problem
- Impact on users
- Urgency
- Business value

Highest: Critical bugs, security issues, production outages
High: Major bugs, important features
Medium: Normal bugs, standard features
Low: Minor bugs, nice-to-have features
Lowest: Trivial issues, cosmetic changes"""

        # Classify
        return await self.llm_client.classify(
            text=text,
            categories=categories,
            system_prompt=system_prompt,
        )

    async def suggest_labels(
        self,
        issue: dict[str, Any],
        max_labels: int = 5,
    ) -> list[str]:
        """
        Suggest labels for issue.

        Args:
            issue: Issue data
            max_labels: Maximum number of labels to suggest

        Returns:
            List of suggested labels
        """
        logger.info(f"Suggesting labels for: {issue.get('summary', 'N/A')}")

        prompt = f"""Analyze this Jira issue and suggest up to {max_labels} relevant labels.

Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}
Type: {issue.get('issue_type', '')}

Respond with a comma-separated list of labels (e.g., "backend, api, performance").
Labels should be:
- Lowercase
- Single words or hyphenated
- Relevant to the issue content
- Technical or domain-specific"""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=100,
            temperature=0.5,
        )

        # Parse labels
        labels = [label.strip() for label in response.split(",")]
        labels = [label for label in labels if label]  # Remove empty

        return labels[:max_labels]

    async def suggest_assignee(
        self,
        issue: dict[str, Any],
        team_members: list[dict[str, Any]],
    ) -> str | None:
        """
        Suggest assignee for issue.

        Args:
            issue: Issue data
            team_members: List of team members with their skills

        Returns:
            Suggested assignee account ID or None
        """
        logger.info(f"Suggesting assignee for: {issue.get('summary', 'N/A')}")

        if not team_members:
            return None

        # Build team members description
        members_desc = []
        for member in team_members:
            name = member.get("display_name", "Unknown")
            skills = ", ".join(member.get("skills", []))
            members_desc.append(f"- {name}: {skills}")

        members_str = "\n".join(members_desc)

        prompt = f"""Suggest the best team member to assign this Jira issue to.

Issue:
Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}
Type: {issue.get('issue_type', '')}

Team Members:
{members_str}

Respond with only the team member's name, nothing else."""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=50,
            temperature=0.3,
        )

        # Find matching team member
        suggested_name = response.strip()
        for member in team_members:
            if member.get("display_name", "").lower() in suggested_name.lower():
                return member.get("account_id")

        return None

    async def estimate_story_points(self, issue: dict[str, Any]) -> int:
        """
        Estimate story points for issue.

        Args:
            issue: Issue data

        Returns:
            Estimated story points (1, 2, 3, 5, 8, 13, 21)
        """
        logger.info(f"Estimating story points for: {issue.get('summary', 'N/A')}")

        prompt = f"""Estimate the story points for this Jira issue using Fibonacci sequence (1, 2, 3, 5, 8, 13, 21).

Summary: {issue.get('summary', '')}
Description: {issue.get('description', '')}
Type: {issue.get('issue_type', '')}

Consider:
- Complexity
- Effort required
- Uncertainty
- Dependencies

Respond with only the number, nothing else."""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=10,
            temperature=0.3,
        )

        # Parse story points
        try:
            points = int(response.strip())
            # Validate Fibonacci
            valid_points = [1, 2, 3, 5, 8, 13, 21]
            if points not in valid_points:
                # Find closest valid value
                points = min(valid_points, key=lambda x: abs(x - points))
            return points
        except ValueError:
            logger.warning(f"Failed to parse story points: {response}")
            return 3  # Default to 3


__all__ = ["IssueClassifier"]

