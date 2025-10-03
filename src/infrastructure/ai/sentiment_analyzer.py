"""AI-powered sentiment analysis."""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    AI-powered sentiment analyzer.
    
    Analyzes sentiment in issue descriptions and comments.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize analyzer.

        Args:
            llm_client: LLM client
        """
        self.llm_client = llm_client

    async def analyze_issue(self, issue: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze sentiment of issue.

        Args:
            issue: Issue data

        Returns:
            Sentiment analysis result
        """
        logger.info(f"Analyzing sentiment for issue: {issue.get('summary', 'N/A')}")

        # Combine summary and description
        text = f"{issue.get('summary', '')} {issue.get('description', '')}"

        return await self.llm_client.extract_sentiment(text)

    async def analyze_comment(self, comment: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze sentiment of comment.

        Args:
            comment: Comment data

        Returns:
            Sentiment analysis result
        """
        logger.info(f"Analyzing sentiment for comment: {comment.get('id', 'N/A')}")

        text = comment.get("body", "")

        return await self.llm_client.extract_sentiment(text)

    async def analyze_issue_trend(
        self,
        issue: dict[str, Any],
        comments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze sentiment trend over time.

        Args:
            issue: Issue data
            comments: List of comments

        Returns:
            Sentiment trend analysis
        """
        logger.info(f"Analyzing sentiment trend for: {issue.get('summary', 'N/A')}")

        # Analyze issue
        issue_sentiment = await self.analyze_issue(issue)

        # Analyze comments
        comment_sentiments = []
        for comment in comments:
            sentiment = await self.analyze_comment(comment)
            comment_sentiments.append({
                "comment_id": comment.get("id"),
                "created_at": comment.get("created_at"),
                "sentiment": sentiment,
            })

        # Calculate overall trend
        all_sentiments = [issue_sentiment] + [c["sentiment"] for c in comment_sentiments]
        
        positive_count = sum(1 for s in all_sentiments if s.get("sentiment") == "positive")
        negative_count = sum(1 for s in all_sentiments if s.get("sentiment") == "negative")
        neutral_count = sum(1 for s in all_sentiments if s.get("sentiment") == "neutral")
        
        total = len(all_sentiments)
        
        return {
            "issue_sentiment": issue_sentiment,
            "comment_sentiments": comment_sentiments,
            "overall": {
                "positive_percentage": (positive_count / total) * 100 if total > 0 else 0,
                "negative_percentage": (negative_count / total) * 100 if total > 0 else 0,
                "neutral_percentage": (neutral_count / total) * 100 if total > 0 else 0,
                "total_analyzed": total,
            },
            "trend": self._determine_trend(comment_sentiments),
        }

    def _determine_trend(self, comment_sentiments: list[dict[str, Any]]) -> str:
        """
        Determine sentiment trend.

        Args:
            comment_sentiments: List of comment sentiments

        Returns:
            Trend description
        """
        if len(comment_sentiments) < 2:
            return "insufficient_data"

        # Get last 3 sentiments
        recent = comment_sentiments[-3:]
        
        positive_count = sum(1 for c in recent if c["sentiment"].get("sentiment") == "positive")
        negative_count = sum(1 for c in recent if c["sentiment"].get("sentiment") == "negative")

        if positive_count > negative_count:
            return "improving"
        elif negative_count > positive_count:
            return "declining"
        else:
            return "stable"

    async def detect_frustration(self, text: str) -> dict[str, Any]:
        """
        Detect frustration in text.

        Args:
            text: Text to analyze

        Returns:
            Frustration detection result
        """
        logger.info("Detecting frustration in text")

        prompt = f"""Analyze this text for signs of frustration and respond in JSON format:

Text: {text}

Respond with JSON containing:
- is_frustrated: boolean
- frustration_level: "low", "medium", or "high"
- indicators: list of phrases indicating frustration
- recommendation: suggested action

Example: {{"is_frustrated": true, "frustration_level": "high", "indicators": ["this is ridiculous", "not working"], "recommendation": "Escalate to senior support"}}"""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=300,
            temperature=0.3,
        )

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse frustration response: {response}")
            return {
                "is_frustrated": False,
                "frustration_level": "low",
                "indicators": [],
                "recommendation": "Continue monitoring",
            }

    async def detect_urgency(self, text: str) -> dict[str, Any]:
        """
        Detect urgency in text.

        Args:
            text: Text to analyze

        Returns:
            Urgency detection result
        """
        logger.info("Detecting urgency in text")

        prompt = f"""Analyze this text for urgency indicators and respond in JSON format:

Text: {text}

Respond with JSON containing:
- is_urgent: boolean
- urgency_level: "low", "medium", or "high"
- indicators: list of phrases indicating urgency
- recommended_priority: "Highest", "High", "Medium", "Low", or "Lowest"

Example: {{"is_urgent": true, "urgency_level": "high", "indicators": ["asap", "critical"], "recommended_priority": "Highest"}}"""

        response = await self.llm_client.complete(
            prompt=prompt,
            max_tokens=300,
            temperature=0.3,
        )

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse urgency response: {response}")
            return {
                "is_urgent": False,
                "urgency_level": "low",
                "indicators": [],
                "recommended_priority": "Medium",
            }


__all__ = ["SentimentAnalyzer"]

