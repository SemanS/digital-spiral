"""LLM client for AI operations."""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any

import anthropic
import openai

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """
    Client for LLM operations.
    
    Supports multiple LLM providers (OpenAI, Anthropic).
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider
            api_key: API key (defaults to environment variable)
            model: Model name (defaults to provider's default)
        """
        self.provider = provider
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_default_model()

        # Initialize provider client
        if self.provider == LLMProvider.OPENAI:
            self.client = openai.OpenAI(api_key=self.api_key)
        elif self.provider == LLMProvider.ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_api_key(self) -> str:
        """Get API key from environment."""
        if self.provider == LLMProvider.OPENAI:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY not set")
            return key
        elif self.provider == LLMProvider.ANTHROPIC:
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return key
        raise ValueError(f"Unknown provider: {self.provider}")

    def _get_default_model(self) -> str:
        """Get default model for provider."""
        if self.provider == LLMProvider.OPENAI:
            return "gpt-4o-mini"
        elif self.provider == LLMProvider.ANTHROPIC:
            return "claude-3-5-sonnet-20241022"
        raise ValueError(f"Unknown provider: {self.provider}")

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate completion.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        logger.info(f"Generating completion with {self.provider}")

        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._complete_openai(
                    prompt, system_prompt, max_tokens, temperature
                )
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._complete_anthropic(
                    prompt, system_prompt, max_tokens, temperature
                )
        except Exception as e:
            logger.error(f"LLM completion error: {e}", exc_info=True)
            raise

    async def _complete_openai(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate completion with OpenAI."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content

    async def _complete_anthropic(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate completion with Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    async def get_embedding(self, text: str) -> list[float]:
        """
        Get text embedding.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Note:
            Only supported for OpenAI provider
        """
        if self.provider != LLMProvider.OPENAI:
            raise ValueError("Embeddings only supported for OpenAI provider")

        logger.info("Generating embedding")

        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding error: {e}", exc_info=True)
            raise

    async def classify(
        self,
        text: str,
        categories: list[str],
        system_prompt: str | None = None,
    ) -> str:
        """
        Classify text into categories.

        Args:
            text: Text to classify
            categories: List of categories
            system_prompt: Optional system prompt

        Returns:
            Selected category
        """
        categories_str = ", ".join(categories)
        
        prompt = f"""Classify the following text into one of these categories: {categories_str}

Text: {text}

Respond with only the category name, nothing else."""

        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=50,
            temperature=0.3,
        )

        # Extract category from response
        category = response.strip()
        
        # Validate category
        if category not in categories:
            # Try to find closest match
            category_lower = category.lower()
            for cat in categories:
                if cat.lower() in category_lower or category_lower in cat.lower():
                    return cat
            # Default to first category if no match
            logger.warning(f"Invalid category '{category}', defaulting to '{categories[0]}'")
            return categories[0]

        return category

    async def extract_sentiment(self, text: str) -> dict[str, Any]:
        """
        Extract sentiment from text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result
        """
        prompt = f"""Analyze the sentiment of the following text and respond in JSON format:

Text: {text}

Respond with JSON containing:
- sentiment: "positive", "negative", or "neutral"
- confidence: float between 0 and 1
- reasoning: brief explanation

Example: {{"sentiment": "positive", "confidence": 0.85, "reasoning": "The text expresses satisfaction"}}"""

        response = await self.complete(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
        )

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse sentiment response: {response}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "reasoning": "Failed to parse response",
            }


__all__ = ["LLMClient", "LLMProvider"]

