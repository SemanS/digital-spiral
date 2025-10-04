"""Unit tests for Sprint model."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.infrastructure.database.models import Sprint


class TestSprint:
    """Test Sprint model."""

    def test_sprint_creation(self):
        """Test creating a Sprint instance."""
        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="active",
            goal="Complete user stories",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=14),
        )

        assert sprint.sprint_id == "123"
        assert sprint.board_id == "456"
        assert sprint.name == "Sprint 1"
        assert sprint.state == "active"
        assert sprint.goal == "Complete user stories"

    def test_sprint_repr(self):
        """Test Sprint __repr__ method."""
        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="active",
        )

        repr_str = repr(sprint)
        assert "Sprint" in repr_str
        assert "Sprint 1" in repr_str
        assert "active" in repr_str
        assert "123" in repr_str

    def test_is_active_property(self):
        """Test is_active property."""
        sprint_active = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="active",
        )

        sprint_closed = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="124",
            board_id="456",
            name="Sprint 2",
            state="closed",
        )

        assert sprint_active.is_active is True
        assert sprint_closed.is_active is False

    def test_is_closed_property(self):
        """Test is_closed property."""
        sprint_closed = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="closed",
        )

        sprint_active = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="124",
            board_id="456",
            name="Sprint 2",
            state="active",
        )

        assert sprint_closed.is_closed is True
        assert sprint_active.is_closed is False

    def test_duration_days_property(self):
        """Test duration_days property."""
        start = datetime.utcnow()
        end = start + timedelta(days=14)

        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="active",
            start_date=start,
            end_date=end,
        )

        assert sprint.duration_days == 14

    def test_duration_days_none_when_dates_missing(self):
        """Test duration_days returns None when dates are missing."""
        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="future",
        )

        assert sprint.duration_days is None

    def test_sprint_states(self):
        """Test different sprint states."""
        states = ["future", "active", "closed"]

        for state in states:
            sprint = Sprint(
                tenant_id=uuid4(),
                instance_id=uuid4(),
                sprint_id=f"sprint-{state}",
                board_id="456",
                name=f"Sprint {state}",
                state=state,
            )
            assert sprint.state == state

    def test_sprint_with_complete_date(self):
        """Test sprint with complete_date."""
        complete_date = datetime.utcnow()

        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="closed",
            complete_date=complete_date,
        )

        assert sprint.complete_date == complete_date

    def test_sprint_without_goal(self):
        """Test sprint without goal."""
        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name="Sprint 1",
            state="active",
        )

        assert sprint.goal is None

    def test_sprint_with_long_name(self):
        """Test sprint with long name."""
        long_name = "A" * 255

        sprint = Sprint(
            tenant_id=uuid4(),
            instance_id=uuid4(),
            sprint_id="123",
            board_id="456",
            name=long_name,
            state="active",
        )

        assert sprint.name == long_name
        assert len(sprint.name) == 255

