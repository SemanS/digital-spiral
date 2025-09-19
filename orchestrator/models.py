from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreditSplit(BaseModel):
    """Represents an individual participant share in a credit event."""

    id: str
    weight: float = Field(ge=0.0)


class Impact(BaseModel):
    """Captures measured impact of an action."""

    secondsSaved: int = Field(ge=0)
    quality: Optional[float] = Field(default=None)


class Attribution(BaseModel):
    """Describes how credit is attributed to contributors."""

    split: List[CreditSplit] = Field(default_factory=list)
    reason: Optional[str] = None


class CreditEvent(BaseModel):
    """Append-only ledger event with hash chaining."""

    id: str
    ts: datetime
    issueKey: str
    actor: Dict[str, Any]
    action: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    impact: Impact
    attribution: Attribution
    parents: List[str] = Field(default_factory=list)
    prev: Optional[str] = None
    hash: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ContributorSummary(BaseModel):
    """Aggregated view of contributions for an entity."""

    id: str
    secondsSaved: float
    share: float
    events: int


class IssueCreditSummary(BaseModel):
    """Summary of credit information for a single issue."""

    issueKey: str
    totalSecondsSaved: float
    windowSecondsSaved: Optional[float] = None
    windowStart: Optional[datetime] = None
    contributors: List[ContributorSummary] = Field(default_factory=list)
    recentEvents: List[CreditEvent] = Field(default_factory=list)


class AgentCreditSummary(BaseModel):
    """Summary of accumulated credit and score for an agent/human."""

    agentId: str
    totalSecondsSaved: float
    score: float
    events: List[CreditEvent] = Field(default_factory=list)


class CreditSummary(BaseModel):
    """Overall summary roll-up for reporting purposes."""

    since: Optional[datetime] = None
    totalSecondsSaved: float
    eventCount: int
    topContributors: List[ContributorSummary] = Field(default_factory=list)
