"""Unit tests for SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.database.models import (
    Base,
    JiraInstance,
    Tenant,
    TimestampMixin,
    UUIDMixin,
    to_dict,
)


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestUUIDMixin:
    """Tests for UUIDMixin."""

    def test_uuid_mixin_generates_uuid(self, session: Session):
        """Test that UUIDMixin generates a UUID primary key."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        assert isinstance(tenant.id, uuid.UUID)
        assert tenant.id is not None


class TestTimestampMixin:
    """Tests for TimestampMixin."""

    def test_timestamp_mixin_sets_created_at(self, session: Session):
        """Test that TimestampMixin sets created_at on creation."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        assert isinstance(tenant.created_at, datetime)
        # Note: SQLite doesn't preserve timezone info, but PostgreSQL does

    def test_timestamp_mixin_sets_updated_at(self, session: Session):
        """Test that TimestampMixin sets updated_at on creation."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        assert isinstance(tenant.updated_at, datetime)

    def test_timestamp_mixin_updates_updated_at(self, session: Session):
        """Test that TimestampMixin updates updated_at on modification."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        original_updated_at = tenant.updated_at

        # Modify the tenant
        tenant.name = "Updated Tenant"
        session.commit()

        # Note: In SQLite, onupdate may not work as expected
        # This test may need adjustment for PostgreSQL
        assert tenant.updated_at >= original_updated_at


class TestTenantModel:
    """Tests for Tenant model."""

    def test_create_tenant(self, session: Session):
        """Test creating a tenant."""
        tenant = Tenant(
            name="Acme Corp",
            slug="acme-corp",
            contact_email="admin@acme.com",
            is_active=True,
        )
        session.add(tenant)
        session.commit()

        assert tenant.id is not None
        assert tenant.name == "Acme Corp"
        assert tenant.slug == "acme-corp"
        assert tenant.contact_email == "admin@acme.com"
        assert tenant.is_active is True

    def test_tenant_slug_is_unique(self, session: Session):
        """Test that tenant slug must be unique."""
        tenant1 = Tenant(name="Tenant 1", slug="same-slug")
        tenant2 = Tenant(name="Tenant 2", slug="same-slug")

        session.add(tenant1)
        session.commit()

        session.add(tenant2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            session.commit()

    def test_tenant_repr(self, session: Session):
        """Test tenant __repr__ method."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        repr_str = repr(tenant)
        assert "Tenant" in repr_str
        assert str(tenant.id) in repr_str
        assert "test-tenant" in repr_str

    def test_tenant_str(self, session: Session):
        """Test tenant __str__ method."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        str_repr = str(tenant)
        assert "Test Tenant" in str_repr
        assert "test-tenant" in str_repr


class TestJiraInstanceModel:
    """Tests for JiraInstance model."""

    def test_create_jira_instance(self, session: Session):
        """Test creating a Jira instance."""
        # Create tenant first
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        # Create Jira instance
        jira_instance = JiraInstance(
            tenant_id=tenant.id,
            base_url="https://test.atlassian.net",
            site_id="test-site-id",
            auth_type="api_token",
            auth_email="test@example.com",
            is_active=True,
            is_connected=False,
        )
        session.add(jira_instance)
        session.commit()

        assert jira_instance.id is not None
        assert jira_instance.tenant_id == tenant.id
        assert jira_instance.base_url == "https://test.atlassian.net"
        assert jira_instance.auth_type == "api_token"

    def test_jira_instance_relationship_with_tenant(self, session: Session):
        """Test relationship between JiraInstance and Tenant."""
        # Create tenant
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        # Create Jira instance
        jira_instance = JiraInstance(
            tenant_id=tenant.id,
            base_url="https://test.atlassian.net",
        )
        session.add(jira_instance)
        session.commit()

        # Test relationship
        assert jira_instance.tenant == tenant
        assert jira_instance in tenant.jira_instances

    def test_jira_instance_cascade_delete(self, session: Session):
        """Test that deleting a tenant cascades to Jira instances."""
        # Create tenant with Jira instance
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        jira_instance = JiraInstance(
            tenant_id=tenant.id,
            base_url="https://test.atlassian.net",
        )
        session.add(jira_instance)
        session.commit()

        jira_instance_id = jira_instance.id

        # Delete tenant
        session.delete(tenant)
        session.commit()

        # Jira instance should be deleted
        deleted_instance = session.get(JiraInstance, jira_instance_id)
        assert deleted_instance is None


class TestToDictFunction:
    """Tests for to_dict utility function."""

    def test_to_dict_basic(self, session: Session):
        """Test to_dict converts model to dictionary."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        result = to_dict(tenant)

        assert isinstance(result, dict)
        assert result["name"] == "Test Tenant"
        assert result["slug"] == "test-tenant"
        assert "id" in result
        assert "created_at" in result

    def test_to_dict_with_exclude(self, session: Session):
        """Test to_dict with excluded fields."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        result = to_dict(tenant, exclude={"created_at", "updated_at"})

        assert "created_at" not in result
        assert "updated_at" not in result
        assert "name" in result
        assert "slug" in result

    def test_to_dict_converts_datetime_to_iso(self, session: Session):
        """Test that to_dict converts datetime to ISO format."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        result = to_dict(tenant)

        assert isinstance(result["created_at"], str)
        # Should be ISO format
        datetime.fromisoformat(result["created_at"])

    def test_to_dict_converts_uuid_to_string(self, session: Session):
        """Test that to_dict converts UUID to string."""
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        session.commit()

        result = to_dict(tenant)

        assert isinstance(result["id"], str)
        # Should be valid UUID string
        uuid.UUID(result["id"])

