"""Sprint-Issue junction model for analytics."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Float, Boolean, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class SprintIssue(Base, UUIDMixin):
    """Junction table linking sprints and issues.
    
    Tracks when issues were added/removed from sprints,
    story points, and completion status.
    """
    
    __tablename__ = "sprint_issues"
    
    # Foreign Keys
    sprint_id: Mapped[UUID] = mapped_column(
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
        doc="Sprint this issue belongs to"
    )
    
    issue_id: Mapped[UUID] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        doc="Issue in this sprint"
    )
    
    # Timestamps
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When issue was added to sprint"
    )
    
    removed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When issue was removed from sprint (if applicable)"
    )
    
    # Metrics
    story_points: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Story points assigned to this issue"
    )
    
    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether issue was completed in this sprint"
    )
    
    # Relationships
    sprint: Mapped["Sprint"] = relationship(
        "Sprint",
        back_populates="sprint_issues",
        doc="Sprint this issue belongs to"
    )
    
    issue: Mapped["Issue"] = relationship(
        "Issue",
        back_populates="sprint_issues",
        doc="Issue in this sprint"
    )
    
    # Table arguments
    __table_args__ = (
        UniqueConstraint(
            "sprint_id",
            "issue_id",
            name="uq_sprint_issues_sprint_issue"
        ),
        Index("idx_sprint_issues_sprint", "sprint_id"),
        Index("idx_sprint_issues_issue", "issue_id"),
    )
    
    def __repr__(self) -> str:
        """String representation of SprintIssue."""
        return (
            f"<SprintIssue(id={self.id}, sprint_id={self.sprint_id}, "
            f"issue_id={self.issue_id}, completed={self.completed})>"
        )
    
    @property
    def was_removed(self) -> bool:
        """Check if issue was removed from sprint."""
        return self.removed_at is not None
    
    @property
    def duration_in_sprint_days(self) -> Optional[int]:
        """Calculate how long issue was in sprint."""
        if self.removed_at:
            return (self.removed_at - self.added_at).days
        return None

