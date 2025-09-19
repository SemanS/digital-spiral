from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class Impact(BaseModel):
    """Captures measured impact of an action."""

    secondsSaved: int = Field(
        ge=0,
        validation_alias=AliasChoices("secondsSaved", "seconds_saved"),
        serialization_alias="secondsSaved",
    )
    quality: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class Attribution(BaseModel):
    """Describes how credit is attributed to contributors."""

    agentId: str = Field(
        validation_alias=AliasChoices("agentId", "agent_id", "id"),
        serialization_alias="agentId",
    )
    weight: float = Field(ge=0.0)
    displayName: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("displayName", "display_name"),
        serialization_alias="displayName",
    )

    model_config = ConfigDict(populate_by_name=True)


class CreditEvent(BaseModel):
    """Append-only ledger event with hash chaining."""

    id: str
    ts: datetime
    issueKey: str = Field(
        validation_alias=AliasChoices("issueKey", "issue_key"),
        serialization_alias="issueKey",
    )
    actor: Dict[str, Any] = Field(default_factory=dict)
    action: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    impact: Impact
    attributions: List[Attribution] = Field(
        default_factory=list,
        validation_alias=AliasChoices("attributions", "attribution"),
        serialization_alias="attributions",
    )
    parents: List[str] = Field(default_factory=list)
    prevHash: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("prevHash", "prev", "prev_hash"),
        serialization_alias="prevHash",
    )
    hash: Optional[str] = None
    attributionReason: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("attributionReason", "reason", "attribution_reason"),
        serialization_alias="attributionReason",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _convert_legacy(cls, values: Mapping[str, Any]) -> Mapping[str, Any]:
        """Accept legacy payloads that used attribution.split."""

        if not isinstance(values, Mapping):  # pragma: no cover - defensive
            return values
        materialised = dict(values)
        if "attribution" in materialised and "attributions" not in materialised:
            legacy = materialised.pop("attribution")
            if isinstance(legacy, Mapping):
                splits = legacy.get("split") or []
                attributions: List[Dict[str, Any]] = []
                for item in splits:
                    if not isinstance(item, Mapping):
                        continue
                    agent_id = item.get("id") or item.get("agentId")
                    weight = item.get("weight")
                    if agent_id is None or weight is None:
                        continue
                    attributions.append({"agentId": agent_id, "weight": weight})
                if attributions:
                    materialised["attributions"] = attributions
                reason = legacy.get("reason") if isinstance(legacy, Mapping) else None
                if reason and "attributionReason" not in materialised:
                    materialised["attributionReason"] = reason
        return materialised


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


__all__ = [
    "AgentCreditSummary",
    "Attribution",
    "ContributorSummary",
    "CreditEvent",
    "CreditSummary",
    "Impact",
    "IssueCreditSummary",
]

