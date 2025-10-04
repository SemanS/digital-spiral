"""Sprint model for analytics."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin


class Sprint(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """Sprint model representing Jira/Agile sprints.
    
    Stores sprint metadata including dates, state, and goals.
    Related to issues through sprint_issues junction table.
    """
    
    __tablename__ = "sprints"
    
    # Foreign Keys
    instance_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_instances.id", ondelete="CASCADE"),
        nullable=False,
        doc="Source instance (Jira, Linear, etc.) this sprint belongs to"
    )
    
    # Sprint Identifiers
    sprint_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="External sprint ID from source system"
    )
    
    board_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Board ID this sprint belongs to"
    )
    
    # Sprint Details
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Sprint name (e.g., 'Sprint 42', 'Q1 2024 Sprint 3')"
    )
    
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Sprint state: future, active, or closed"
    )
    
    goal: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Sprint goal or objective"
    )
    
    # Dates
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Sprint start date"
    )
    
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Planned sprint end date"
    )
    
    complete_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Actual sprint completion date"
    )
    
    # Relationships
    sprint_issues: Mapped[List["SprintIssue"]] = relationship(
        "SprintIssue",
        back_populates="sprint",
        cascade="all, delete-orphan",
        doc="Issues in this sprint"
    )
    
    instance: Mapped["SourceInstance"] = relationship(
        "SourceInstance",
        back_populates="sprints",
        doc="Source instance this sprint belongs to"
    )
    
    # Table arguments
    __table_args__ = (
        UniqueConstraint(
            "instance_id",
            "sprint_id",
            name="uq_sprints_instance_sprint"
        ),
        Index("idx_sprints_tenant_instance", "tenant_id", "instance_id"),
        Index("idx_sprints_state", "state"),
        Index("idx_sprints_dates", "start_date", "end_date"),
    )
    
    def __repr__(self) -> str:
        """String representation of Sprint."""
        return (
            f"<Sprint(id={self.id}, name='{self.name}', "
            f"state='{self.state}', sprint_id='{self.sprint_id}')>"
        )
    
    @property
    def is_active(self) -> bool:
        """Check if sprint is currently active."""
        return self.state == "active"
    
    @property
    def is_closed(self) -> bool:
        """Check if sprint is closed."""
        return self.state == "closed"
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate sprint duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

