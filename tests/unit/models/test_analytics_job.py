"""Unit tests for AnalyticsJob model."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.infrastructure.database.models import AnalyticsJob, JobType, JobStatus


class TestAnalyticsJob:
    """Test AnalyticsJob model."""

    def test_analytics_job_creation(self):
        """Test creating an AnalyticsJob instance."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={"query": "Show me sprint velocity"},
        )

        assert job.user_id == "user-123"
        assert job.job_type == JobType.NL_QUERY.value
        assert job.status == JobStatus.PENDING.value
        assert job.input_data["query"] == "Show me sprint velocity"

    def test_analytics_job_repr(self):
        """Test AnalyticsJob __repr__ method."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.SPEC_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
        )

        repr_str = repr(job)
        assert "AnalyticsJob" in repr_str
        assert "spec_query" in repr_str
        assert "running" in repr_str
        assert "user-123" in repr_str

    def test_is_pending_property(self):
        """Test is_pending property."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={},
        )

        assert job.is_pending is True
        assert job.is_running is False
        assert job.is_completed is False
        assert job.is_failed is False

    def test_is_running_property(self):
        """Test is_running property."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
        )

        assert job.is_pending is False
        assert job.is_running is True
        assert job.is_completed is False
        assert job.is_failed is False

    def test_is_completed_property(self):
        """Test is_completed property."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.COMPLETED.value,
            input_data={},
        )

        assert job.is_pending is False
        assert job.is_running is False
        assert job.is_completed is True
        assert job.is_failed is False

    def test_is_failed_property(self):
        """Test is_failed property."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.FAILED.value,
            input_data={},
        )

        assert job.is_pending is False
        assert job.is_running is False
        assert job.is_completed is False
        assert job.is_failed is True

    def test_is_finished_property(self):
        """Test is_finished property."""
        completed_job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.COMPLETED.value,
            input_data={},
        )

        failed_job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.FAILED.value,
            input_data={},
        )

        cancelled_job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.CANCELLED.value,
            input_data={},
        )

        running_job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
        )

        assert completed_job.is_finished is True
        assert failed_job.is_finished is True
        assert cancelled_job.is_finished is True
        assert running_job.is_finished is False

    def test_execution_time_seconds(self):
        """Test execution_time_seconds property."""
        started = datetime.utcnow()
        completed = started + timedelta(seconds=45)

        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.COMPLETED.value,
            input_data={},
            started_at=started,
            completed_at=completed,
        )

        assert job.execution_time_seconds == 45.0

    def test_execution_time_seconds_none_when_not_finished(self):
        """Test execution_time_seconds returns None when not finished."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
            started_at=datetime.utcnow(),
        )

        assert job.execution_time_seconds is None

    def test_natural_language_query_property(self):
        """Test natural_language_query property."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={"query": "Show me sprint velocity"},
        )

        assert job.natural_language_query == "Show me sprint velocity"

    def test_natural_language_query_none_for_other_types(self):
        """Test natural_language_query returns None for non-NL jobs."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.SPEC_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={"spec": {}},
        )

        assert job.natural_language_query is None

    def test_metric_name_property(self):
        """Test metric_name property."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.METRIC_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={"metric_name": "sprint_velocity"},
        )

        assert job.metric_name == "sprint_velocity"

    def test_metric_name_none_for_other_types(self):
        """Test metric_name returns None for non-metric jobs."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={"query": "test"},
        )

        assert job.metric_name is None

    def test_mark_as_running(self):
        """Test mark_as_running method."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.PENDING.value,
            input_data={},
        )

        job.mark_as_running()

        assert job.status == JobStatus.RUNNING.value
        assert job.started_at is not None

    def test_mark_as_completed(self):
        """Test mark_as_completed method."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
        )

        result_data = {"rows": [], "count": 0}
        job.mark_as_completed(result_data)

        assert job.status == JobStatus.COMPLETED.value
        assert job.completed_at is not None
        assert job.result_data == result_data

    def test_mark_as_failed(self):
        """Test mark_as_failed method."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
        )

        error_message = "Query execution failed"
        job.mark_as_failed(error_message)

        assert job.status == JobStatus.FAILED.value
        assert job.completed_at is not None
        assert job.error_message == error_message

    def test_mark_as_cancelled(self):
        """Test mark_as_cancelled method."""
        job = AnalyticsJob(
            tenant_id=uuid4(),
            user_id="user-123",
            job_type=JobType.NL_QUERY.value,
            status=JobStatus.RUNNING.value,
            input_data={},
        )

        job.mark_as_cancelled()

        assert job.status == JobStatus.CANCELLED.value
        assert job.completed_at is not None

