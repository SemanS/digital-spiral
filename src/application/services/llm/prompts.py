"""Prompt templates for LLM interactions."""

from typing import Dict, Any, List
import json


class PromptTemplates:
    """Collection of prompt templates for LLM interactions."""
    
    @staticmethod
    def get_system_prompt_for_translation(
        available_entities: List[str],
        available_metrics: List[Dict[str, Any]],
        schema_example: Dict[str, Any],
    ) -> str:
        """Get system prompt for NL to AnalyticsSpec translation.
        
        Args:
            available_entities: List of available entities
            available_metrics: List of available metrics
            schema_example: Example AnalyticsSpec
            
        Returns:
            System prompt
        """
        metrics_info = "\n".join([
            f"- {m['name']}: {m['description']} (category: {m['category']}, unit: {m.get('unit', 'N/A')})"
            for m in available_metrics
        ])
        
        return f"""You are an expert analytics query translator for a Jira/project management analytics system.

Your task is to convert natural language queries into structured AnalyticsSpec JSON objects.

## Available Entities
{', '.join(available_entities)}

## Available Predefined Metrics
{metrics_info}

## AnalyticsSpec Schema Example
{json.dumps(schema_example, indent=2)}

## Translation Guidelines

1. **Entity Selection**: Choose the most appropriate entity based on the query
   - Use "issues" for queries about tasks, bugs, stories, tickets
   - Use "sprints" for queries about sprint performance, velocity
   - Use "comments" for queries about collaboration, discussions
   - Use "changelogs" for queries about changes, history

2. **Metrics**: Define appropriate metrics with correct aggregations
   - count: "how many", "number of"
   - avg: "average", "mean"
   - sum: "total", "sum of"
   - min/max: "minimum", "maximum", "lowest", "highest"
   - median: "median", "middle value"
   - percentile: "95th percentile", "top 10%"

3. **Filters**: Extract all conditions from the query
   - eq: "is", "equals", "="
   - ne: "is not", "not equal to"
   - gt/gte: "greater than", "more than", "above"
   - lt/lte: "less than", "fewer than", "below"
   - in: "in", "one of"
   - contains: "contains", "includes"

4. **Grouping**: Identify grouping requirements
   - "by status", "per assignee", "for each project" → group_by
   - "over time", "by month", "daily" → group_by with interval

5. **Sorting**: Identify sorting requirements
   - "top", "highest", "most" → sort desc
   - "bottom", "lowest", "least" → sort asc

6. **Time Ranges**: Extract date ranges
   - "last week", "this month", "Q1 2024" → start_date, end_date
   - "in the last 30 days" → calculate dates

7. **Limits**: Extract result limits
   - "top 10", "first 5", "bottom 3" → limit

## Response Format
Respond with ONLY a valid JSON object matching the AnalyticsSpec schema. No explanatory text.
"""
    
    @staticmethod
    def get_user_prompt_for_translation(
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get user prompt for translation.
        
        Args:
            query: Natural language query
            context: Additional context
            
        Returns:
            User prompt
        """
        prompt = f"Convert this query to AnalyticsSpec JSON:\n\n{query}"
        
        if context:
            prompt += f"\n\nContext:\n{json.dumps(context, indent=2)}"
        
        return prompt
    
    @staticmethod
    def get_validation_prompt(
        query: str,
        spec: Dict[str, Any],
    ) -> str:
        """Get prompt for validating translation.
        
        Args:
            query: Original query
            spec: Translated spec
            
        Returns:
            Validation prompt
        """
        return f"""Validate this translation:

Original Query: "{query}"

Translated AnalyticsSpec:
{json.dumps(spec, indent=2)}

Respond with JSON:
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list of issues"],
  "suggestions": ["list of suggestions"]
}}
"""
    
    @staticmethod
    def get_query_explanation_prompt(spec: Dict[str, Any]) -> str:
        """Get prompt for explaining AnalyticsSpec in natural language.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            Explanation prompt
        """
        return f"""Explain this AnalyticsSpec in simple, natural language:

{json.dumps(spec, indent=2)}

Provide a clear, concise explanation of what this query does, what data it retrieves, and how it's aggregated/filtered.
"""
    
    @staticmethod
    def get_query_suggestion_prompt(
        query: str,
        available_metrics: List[str],
    ) -> str:
        """Get prompt for suggesting related queries.
        
        Args:
            query: Original query
            available_metrics: List of available metric names
            
        Returns:
            Suggestion prompt
        """
        return f"""Given this analytics query:
"{query}"

And these available metrics:
{', '.join(available_metrics)}

Suggest 5 related queries that the user might be interested in. Respond with JSON:
{{
  "suggestions": [
    {{
      "query": "suggested query text",
      "reason": "why this might be interesting"
    }}
  ]
}}
"""
    
    @staticmethod
    def get_error_correction_prompt(
        query: str,
        error: str,
        previous_spec: Dict[str, Any],
    ) -> str:
        """Get prompt for correcting translation errors.
        
        Args:
            query: Original query
            error: Error message
            previous_spec: Previous (failed) spec
            
        Returns:
            Correction prompt
        """
        return f"""The previous translation failed with this error:
{error}

Original Query: "{query}"

Previous AnalyticsSpec (failed):
{json.dumps(previous_spec, indent=2)}

Please provide a corrected AnalyticsSpec that addresses the error. Respond with ONLY valid JSON.
"""
    
    @staticmethod
    def get_ambiguity_resolution_prompt(
        query: str,
        ambiguities: List[str],
    ) -> str:
        """Get prompt for resolving query ambiguities.
        
        Args:
            query: Original query
            ambiguities: List of detected ambiguities
            
        Returns:
            Resolution prompt
        """
        ambiguities_text = "\n".join([f"- {a}" for a in ambiguities])
        
        return f"""This query has some ambiguities:

Query: "{query}"

Ambiguities:
{ambiguities_text}

Please provide:
1. Clarifying questions to ask the user
2. Reasonable default assumptions if we can't ask

Respond with JSON:
{{
  "questions": ["list of clarifying questions"],
  "assumptions": ["list of reasonable default assumptions"],
  "recommended_spec": {{...}}  // AnalyticsSpec with assumptions applied
}}
"""


# Example usage and constants
EXAMPLE_ANALYTICS_SPEC = {
    "entity": "issues",
    "metrics": [
        {
            "name": "total_issues",
            "aggregation": "count",
        }
    ],
    "filters": [
        {
            "field": "status",
            "operator": "eq",
            "value": "Done"
        }
    ],
    "group_by": [
        {
            "field": "assignee_name"
        }
    ],
    "sort_by": [
        {
            "field": "total_issues",
            "direction": "desc"
        }
    ],
    "limit": 10,
    "description": "Top 10 assignees by number of completed issues"
}

COMMON_QUERY_PATTERNS = {
    "velocity": [
        "What is our sprint velocity?",
        "Show me velocity trend over last 6 months",
        "Compare velocity across teams",
    ],
    "cycle_time": [
        "What is the average cycle time?",
        "Show cycle time by issue type",
        "How has cycle time changed over time?",
    ],
    "throughput": [
        "How many issues did we complete this month?",
        "Show throughput by week",
        "What is our completion rate?",
    ],
    "quality": [
        "What is our defect rate?",
        "How many bugs were reopened?",
        "Show quality metrics by project",
    ],
}

