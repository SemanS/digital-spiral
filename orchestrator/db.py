"""Database layer for the orchestrator service."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv(
    "ORCHESTRATOR_DATABASE_URL",
    "sqlite:///" + str((os.getenv("ORCHESTRATOR_STATE_DIR") or "artifacts")) + "/orchestrator.db",
)

_SQLITE_PREFIX = "sqlite:///"
_SQLITE_KWARGS: dict[str, Any] | None = None
if DATABASE_URL.startswith(_SQLITE_PREFIX):
    _SQLITE_KWARGS = {"connect_args": {"check_same_thread": False}}

engine: Engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    **(_SQLITE_KWARGS or {}),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

metadata_obj = MetaData()
Base = declarative_base(metadata=metadata_obj)


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True)
    site_id = Column(String, unique=True, nullable=False)
    forge_shared_secret = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    credit_events = relationship("CreditEventRecord", back_populates="tenant", cascade="all, delete-orphan")
    apply_actions = relationship("ApplyActionRecord", back_populates="tenant", cascade="all, delete-orphan")


class AgentRecord(Base):
    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    kind = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CreditEventRecord(Base):
    __tablename__ = "credit_events"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    issue_key = Column(String, nullable=False, index=True)
    action_kind = Column(String, nullable=False)
    seconds_saved = Column(Integer, nullable=False)
    impact_quality = Column(Float, nullable=True)
    actor_id = Column(String, nullable=False)
    actor_payload = Column(JSON, nullable=False, default=dict)
    inputs = Column(JSON, nullable=False, default=dict)
    attributions = Column(JSON, nullable=False, default=list)
    parents = Column(JSON, nullable=False, default=list)
    metadata_payload = Column(JSON, nullable=False, default=dict)
    attribution_reason = Column(String, nullable=True)
    hash = Column(String, nullable=False)
    prev_hash = Column(String, nullable=True)
    payload_hash = Column(String, nullable=False)
    idempotency_key = Column(String, nullable=False, unique=True)
    event_ts = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant", back_populates="credit_events")

    __table_args__ = (
        Index("ce_tenant_issue_time", "tenant_id", "issue_key", created_at.desc()),
        Index("ce_tenant_actor_time", "tenant_id", "actor_id", created_at.desc()),
    )


class ApplyActionRecord(Base):
    __tablename__ = "apply_actions"

    apply_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    issue_key = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    idempotency_key = Column(String, nullable=False, unique=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant", back_populates="apply_actions")


def init_models() -> None:
    """Create tables if they do not exist."""

    if DATABASE_URL.startswith(_SQLITE_PREFIX):
        db_path = Path(DATABASE_URL[len(_SQLITE_PREFIX) :])
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Session:
    """Return a new database session."""

    return SessionLocal()


def get_tenant(session: Session, tenant_id: str) -> Optional[Tenant]:
    return session.get(Tenant, tenant_id)


def ensure_tenant(session: Session, tenant_id: str, *, site_id: str, forge_shared_secret: str) -> Tenant:
    tenant = get_tenant(session, tenant_id)
    if tenant is not None:
        return tenant
    tenant = Tenant(tenant_id=tenant_id, site_id=site_id, forge_shared_secret=forge_shared_secret)
    session.add(tenant)
    session.flush()
    return tenant


def get_tenant_secret(session: Session, tenant_id: str) -> Optional[str]:
    tenant = get_tenant(session, tenant_id)
    return tenant.forge_shared_secret if tenant else None


def upsert_agent(session: Session, tenant_id: str, agent_id: str, *, kind: str, display_name: str | None = None) -> None:
    record = session.get(AgentRecord, agent_id)
    if record is None:
        record = AgentRecord(agent_id=agent_id, tenant_id=tenant_id, kind=kind, display_name=display_name)
        session.add(record)
        session.flush()
        return
    changed = False
    if record.tenant_id != tenant_id:
        record.tenant_id = tenant_id
        changed = True
    if display_name and record.display_name != display_name:
        record.display_name = display_name
        changed = True
    if record.kind != kind:
        record.kind = kind
        changed = True
    if changed:
        session.add(record)


def get_apply_by_idempotency(session: Session, tenant_id: str, idempotency_key: str) -> Optional[ApplyActionRecord]:
    stmt = (
        select(ApplyActionRecord)
        .where(
            ApplyActionRecord.tenant_id == tenant_id,
            ApplyActionRecord.idempotency_key == idempotency_key,
        )
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def list_credit_events(
    session: Session,
    tenant_id: str,
    *,
    since: datetime | None = None,
    issue_key: str | None = None,
    order_desc: bool = False,
    limit: int | None = None,
) -> list[CreditEventRecord]:
    stmt = select(CreditEventRecord).where(CreditEventRecord.tenant_id == tenant_id)
    if since is not None:
        stmt = stmt.where(CreditEventRecord.created_at >= since)
    if issue_key is not None:
        stmt = stmt.where(CreditEventRecord.issue_key == issue_key)
    if order_desc:
        stmt = stmt.order_by(CreditEventRecord.created_at.desc(), CreditEventRecord.event_id.desc())
    else:
        stmt = stmt.order_by(CreditEventRecord.created_at.asc(), CreditEventRecord.event_id.asc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars())


def last_event_for_tenant(session: Session, tenant_id: str) -> Optional[CreditEventRecord]:
    stmt = (
        select(CreditEventRecord)
        .where(CreditEventRecord.tenant_id == tenant_id)
        .order_by(CreditEventRecord.created_at.desc(), CreditEventRecord.event_id.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def clear_all(session: Session) -> None:
    session.query(CreditEventRecord).delete()
    session.query(ApplyActionRecord).delete()
    session.query(AgentRecord).delete()
    session.query(Tenant).delete()
    session.flush()


# Import Pulse models to register them with Base.metadata
# This must be done after Base is defined
try:
    from . import pulse_models  # noqa: F401
except ImportError:
    pass  # Pulse models not yet available
