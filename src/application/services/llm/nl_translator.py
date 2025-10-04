"""Natural Language to AnalyticsSpec Translator using LLM."""

from typing import Dict, Any, Optional, List
import json
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from src.domain.schemas.analytics_spec import AnalyticsSpec
from src.domain.analytics.predefined_metrics import PREDEFINED_METRICS, MetricCategory

logger = logging.getLogger(__name__)


class NLTranslator:
    """Translate natural language queries to AnalyticsSpec using LLM."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """Initialize translator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4-turbo-preview)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def translate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsSpec:
        """Translate natural language query to AnalyticsSpec.
        
        Args:
            query: Natural language query
            context: Additional context (tenant info, available fields, etc.)
            
        Returns:
            AnalyticsSpec
            
        Raises:
            ValueError: If translation fails or result is invalid
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(query, context)
        
        # Call LLM
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for consistent output
                response_format={"type": "json_object"},
            )
            
            # Parse response
            content = response.choices[0].message.content
            spec_dict = json.loads(content)
            
            # Validate and create AnalyticsSpec
            spec = AnalyticsSpec(**spec_dict)
            
            logger.info(f"Successfully translated query: {query[:50]}...")
            return spec
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        
        except ValidationError as e:
            logger.error(f"Failed to validate AnalyticsSpec: {e}")
            raise ValueError(f"Invalid AnalyticsSpec from LLM: {e}")
        
        except Exception as e:
            logger.error(f"LLM translation failed: {e}")
            raise ValueError(f"Translation failed: {e}")
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt for LLM.
        
        Args:
            context: Additional context
            
        Returns:
            System prompt
        """
        # Get available metrics for context
        metrics_info = self._get_metrics_info()
        
        prompt = f"""You are an expert analytics query translator. Your task is to convert natural language queries into structured AnalyticsSpec JSON objects.

## AnalyticsSpec Schema

An AnalyticsSpec has the following structure:

{{
  "entity": "issues" | "sprints" | "comments" | "changelogs",
  "metrics": [
    {{
      "name": "metric_name",
      "aggregation": "sum" | "avg" | "count" | "min" | "max" | "median" | "percentile",
      "field": "field_name",  // required for sum, avg, min, max, median
      "percentile": 0-100  // required for percentile aggregation
    }}
  ],
  "filters": [
    {{
      "field": "field_name",
      "operator": "eq" | "ne" | "gt" | "gte" | "lt" | "lte" | "in" | "not_in" | "contains" | "starts_with" | "ends_with" | "is_null" | "is_not_null",
      "value": any
    }}
  ],
  "group_by": [
    {{
      "field": "field_name",
      "interval": "day" | "week" | "month" | "quarter" | "year",  // optional, for date fields
      "limit": number  // optional
    }}
  ],
  "sort_by": [
    {{
      "field": "field_name",
      "direction": "asc" | "desc"
    }}
  ],
  "start_date": "ISO 8601 datetime",  // optional
  "end_date": "ISO 8601 datetime",  // optional
  "limit": number,  // optional
  "offset": number,  // optional
  "description": "human-readable description"  // optional
}}

## Available Entities and Fields

### Issues
- id, key, summary, description, issue_type, status, priority
- assignee_id, assignee_name, reporter_id, reporter_name
- story_points, created_at, updated_at, resolved_at, in_progress_at
- project_id, project_key, project_name
- tenant_id, instance_id

### Sprints
- id, sprint_id, board_id, name, state, goal
- start_date, end_date, complete_date
- tenant_id, instance_id

### Comments
- id, body, author_id, author_name
- created_at, updated_at
- issue_id, tenant_id, instance_id

### Changelogs
- id, field, from_value, to_value
- created_at, author_id, author_name
- issue_id, tenant_id, instance_id

## Available Predefined Metrics

{metrics_info}

## Translation Rules

1. Always specify the correct entity based on the query
2. Use appropriate aggregations (count for "how many", avg for "average", etc.)
3. Add filters for any conditions mentioned in the query
4. Use group_by for "by X" or "per X" queries
5. Add sort_by for "top", "bottom", "highest", "lowest" queries
6. Set appropriate date ranges if time periods are mentioned
7. Use limit for "top N" queries
8. Always return valid JSON that matches the AnalyticsSpec schema
9. If the query is ambiguous, make reasonable assumptions and document them in the description field

## Response Format

You must respond with ONLY a valid JSON object that matches the AnalyticsSpec schema. Do not include any explanatory text outside the JSON.
"""
        
        return prompt
    
    def _build_user_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build user prompt for LLM.
        
        Args:
            query: Natural language query
            context: Additional context
            
        Returns:
            User prompt
        """
        prompt = f"Convert this natural language query to an AnalyticsSpec JSON object:\n\n{query}"
        
        if context:
            prompt += f"\n\nAdditional context:\n{json.dumps(context, indent=2)}"
        
        return prompt
    
    def _get_metrics_info(self) -> str:
        """Get information about available metrics.
        
        Returns:
            Formatted metrics information
        """
        # Group metrics by category
        metrics_by_category: Dict[str, List[Dict[str, Any]]] = {}
        
        for metric in PREDEFINED_METRICS:
            category = metric["category"]
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append(metric)
        
        # Format metrics info
        info_parts = []
        
        for category, metrics in sorted(metrics_by_category.items()):
            info_parts.append(f"\n### {category.upper()}")
            for metric in metrics:
                info_parts.append(
                    f"- {metric['name']}: {metric['description']} "
                    f"(unit: {metric.get('unit', 'N/A')})"
                )
        
        return "\n".join(info_parts)
    
    async def validate_translation(
        self,
        query: str,
        spec: AnalyticsSpec,
    ) -> Dict[str, Any]:
        """Validate that translation matches the original query.
        
        Args:
            query: Original natural language query
            spec: Translated AnalyticsSpec
            
        Returns:
            Validation results
        """
        validation_prompt = f"""Given this natural language query:
"{query}"

And this AnalyticsSpec:
{spec.model_dump_json(indent=2)}

Does the AnalyticsSpec accurately represent the query? Respond with a JSON object:
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list of any issues found"],
  "suggestions": ["list of suggestions for improvement"]
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an analytics query validator."},
                    {"role": "user", "content": validation_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "issues": [str(e)],
                "suggestions": [],
            }

