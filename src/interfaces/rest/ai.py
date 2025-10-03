"""AI REST API endpoints."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.infrastructure.ai import (
    EmbeddingsService,
    InsightsGenerator,
    IssueClassifier,
    LLMClient,
    LLMProvider,
    SentimentAnalyzer,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# Request/Response models
class ClassifyIssueRequest(BaseModel):
    """Request to classify issue."""
    summary: str
    description: str | None = None
    issue_type: str | None = None


class ClassifyIssueResponse(BaseModel):
    """Response from issue classification."""
    suggested_type: str
    suggested_priority: str
    suggested_labels: list[str]
    estimated_story_points: int


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis."""
    text: str


class SentimentAnalysisResponse(BaseModel):
    """Response from sentiment analysis."""
    sentiment: str
    confidence: float
    reasoning: str


class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str
    instance_id: UUID
    top_k: int = 10
    min_similarity: float = 0.7


class InsightsRequest(BaseModel):
    """Request for AI insights."""
    issue_summary: str
    issue_description: str | None = None
    issue_type: str | None = None
    status: str | None = None


class InsightsResponse(BaseModel):
    """Response with AI insights."""
    summary: str
    next_steps: list[str]
    blockers: list[dict[str, str]]


# Dependency injection
async def get_llm_client() -> LLMClient:
    """Get LLM client."""
    return LLMClient(provider=LLMProvider.OPENAI)


async def get_issue_classifier(
    llm_client: LLMClient = Depends(get_llm_client),
) -> IssueClassifier:
    """Get issue classifier."""
    return IssueClassifier(llm_client)


async def get_sentiment_analyzer(
    llm_client: LLMClient = Depends(get_llm_client),
) -> SentimentAnalyzer:
    """Get sentiment analyzer."""
    return SentimentAnalyzer(llm_client)


async def get_insights_generator(
    llm_client: LLMClient = Depends(get_llm_client),
) -> InsightsGenerator:
    """Get insights generator."""
    return InsightsGenerator(llm_client)


async def get_embeddings_service(
    llm_client: LLMClient = Depends(get_llm_client),
) -> EmbeddingsService:
    """Get embeddings service."""
    return EmbeddingsService(llm_client)


# Endpoints
@router.post("/classify", response_model=ClassifyIssueResponse)
async def classify_issue(
    request: ClassifyIssueRequest,
    classifier: IssueClassifier = Depends(get_issue_classifier),
):
    """
    Classify issue using AI.

    Args:
        request: Classification request
        classifier: Issue classifier

    Returns:
        Classification results
    """
    logger.info(f"POST /ai/classify - {request.summary}")

    try:
        issue_data = {
            "summary": request.summary,
            "description": request.description or "",
            "issue_type": request.issue_type or "",
        }

        # Classify
        suggested_type = await classifier.classify_issue_type(issue_data)
        suggested_priority = await classifier.classify_priority(issue_data)
        suggested_labels = await classifier.suggest_labels(issue_data)
        story_points = await classifier.estimate_story_points(issue_data)

        return ClassifyIssueResponse(
            suggested_type=suggested_type,
            suggested_priority=suggested_priority,
            suggested_labels=suggested_labels,
            estimated_story_points=story_points,
        )

    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@router.post("/sentiment", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    analyzer: SentimentAnalyzer = Depends(get_sentiment_analyzer),
):
    """
    Analyze sentiment of text.

    Args:
        request: Sentiment analysis request
        analyzer: Sentiment analyzer

    Returns:
        Sentiment analysis results
    """
    logger.info("POST /ai/sentiment")

    try:
        result = await analyzer.llm_client.extract_sentiment(request.text)

        return SentimentAnalysisResponse(
            sentiment=result.get("sentiment", "neutral"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", ""),
        )

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}",
        )


@router.post("/insights", response_model=InsightsResponse)
async def generate_insights(
    request: InsightsRequest,
    generator: InsightsGenerator = Depends(get_insights_generator),
):
    """
    Generate AI insights for issue.

    Args:
        request: Insights request
        generator: Insights generator

    Returns:
        Generated insights
    """
    logger.info("POST /ai/insights")

    try:
        issue_data = {
            "summary": request.issue_summary,
            "description": request.issue_description or "",
            "issue_type": request.issue_type or "",
            "status": request.status or "",
        }

        # Generate insights
        summary = await generator.generate_issue_summary(issue_data)
        next_steps = await generator.suggest_next_steps(issue_data)
        blockers = await generator.identify_blockers(issue_data)

        return InsightsResponse(
            summary=summary,
            next_steps=next_steps,
            blockers=blockers,
        )

    except Exception as e:
        logger.error(f"Insights generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights generation failed: {str(e)}",
        )


@router.post("/embed")
async def generate_embedding(
    text: str = Query(..., description="Text to embed"),
    embeddings_service: EmbeddingsService = Depends(get_embeddings_service),
):
    """
    Generate embedding for text.

    Args:
        text: Text to embed
        embeddings_service: Embeddings service

    Returns:
        Embedding vector
    """
    logger.info("POST /ai/embed")

    try:
        embedding = await embeddings_service.embed_text(text)

        return {
            "text": text,
            "embedding": embedding,
            "dimension": len(embedding),
        }

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}",
        )


__all__ = ["router"]

