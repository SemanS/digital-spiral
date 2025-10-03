"""Vector embeddings service."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.infrastructure.ai.llm_client import LLMClient, LLMProvider

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Service for managing vector embeddings.
    
    Handles embedding generation and similarity search.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize embeddings service.

        Args:
            llm_client: LLM client (defaults to OpenAI)
        """
        self.llm_client = llm_client or LLMClient(provider=LLMProvider.OPENAI)
        self.embeddings_cache: dict[str, list[float]] = {}

    async def embed_text(self, text: str, use_cache: bool = True) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            use_cache: Whether to use cache

        Returns:
            Embedding vector
        """
        # Check cache
        if use_cache and text in self.embeddings_cache:
            logger.debug(f"Using cached embedding for text (length: {len(text)})")
            return self.embeddings_cache[text]

        # Generate embedding
        logger.info(f"Generating embedding for text (length: {len(text)})")
        embedding = await self.llm_client.get_embedding(text)

        # Cache embedding
        if use_cache:
            self.embeddings_cache[text] = embedding

        return embedding

    async def embed_issue(self, issue: dict[str, Any]) -> list[float]:
        """
        Generate embedding for issue.

        Args:
            issue: Issue data

        Returns:
            Embedding vector
        """
        # Combine relevant fields
        text_parts = []

        if issue.get("summary"):
            text_parts.append(f"Summary: {issue['summary']}")

        if issue.get("description"):
            text_parts.append(f"Description: {issue['description']}")

        if issue.get("issue_type"):
            text_parts.append(f"Type: {issue['issue_type']}")

        if issue.get("labels"):
            labels = ", ".join(issue["labels"])
            text_parts.append(f"Labels: {labels}")

        text = "\n".join(text_parts)

        return await self.embed_text(text, use_cache=False)

    def calculate_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """
        Calculate cosine similarity between embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)

        # Calculate cosine similarity
        similarity = cosine_similarity(vec1, vec2)[0][0]

        return float(similarity)

    async def find_similar_issues(
        self,
        query_embedding: list[float],
        issue_embeddings: dict[UUID, list[float]],
        top_k: int = 10,
        min_similarity: float = 0.7,
    ) -> list[tuple[UUID, float]]:
        """
        Find similar issues based on embeddings.

        Args:
            query_embedding: Query embedding
            issue_embeddings: Map of issue IDs to embeddings
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (issue_id, similarity_score) tuples
        """
        logger.info(f"Finding similar issues (total: {len(issue_embeddings)})")

        # Calculate similarities
        similarities = []
        for issue_id, embedding in issue_embeddings.items():
            similarity = self.calculate_similarity(query_embedding, embedding)
            if similarity >= min_similarity:
                similarities.append((issue_id, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top k
        return similarities[:top_k]

    async def semantic_search(
        self,
        query: str,
        issue_embeddings: dict[UUID, list[float]],
        top_k: int = 10,
        min_similarity: float = 0.7,
    ) -> list[tuple[UUID, float]]:
        """
        Perform semantic search.

        Args:
            query: Search query
            issue_embeddings: Map of issue IDs to embeddings
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (issue_id, similarity_score) tuples
        """
        logger.info(f"Performing semantic search: {query}")

        # Generate query embedding
        query_embedding = await self.embed_text(query)

        # Find similar issues
        return await self.find_similar_issues(
            query_embedding,
            issue_embeddings,
            top_k,
            min_similarity,
        )

    def clear_cache(self):
        """Clear embeddings cache."""
        logger.info("Clearing embeddings cache")
        self.embeddings_cache.clear()


__all__ = ["EmbeddingsService"]

