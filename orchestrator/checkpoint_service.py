"""Checkpoint service for tracking and rolling back Jira write operations."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class Checkpoint(Base):
    """Model for storing write operation checkpoints."""
    
    __tablename__ = "checkpoints"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    action_name = Column(String(255), nullable=False)
    issue_key = Column(String(255), nullable=True, index=True)
    params = Column(Text, nullable=False)  # JSON
    rollback_data = Column(Text, nullable=False)  # JSON
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    rolled_back = Column(Integer, nullable=False, default=0)  # 0 = not rolled back, 1 = rolled back
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "action_name": self.action_name,
            "issue_key": self.issue_key,
            "params": json.loads(self.params),
            "rollback_data": json.loads(self.rollback_data),
            "timestamp": self.timestamp.isoformat(),
            "rolled_back": bool(self.rolled_back)
        }


class CheckpointService:
    """Service for managing checkpoints and rollbacks."""
    
    def __init__(self, db_path: str = "artifacts/checkpoints.db"):
        """Initialize checkpoint service.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def create_checkpoint(
        self,
        tenant_id: str,
        action_name: str,
        params: Dict[str, Any],
        rollback_data: Dict[str, Any],
        issue_key: Optional[str] = None
    ) -> int:
        """Create a checkpoint before write operation.
        
        Args:
            tenant_id: Tenant ID
            action_name: Name of the action (e.g., "add_comment")
            params: Action parameters
            rollback_data: Data needed to rollback the operation
            issue_key: Optional issue key for filtering
            
        Returns:
            Checkpoint ID
        """
        session = self._get_session()
        try:
            checkpoint = Checkpoint(
                tenant_id=tenant_id,
                action_name=action_name,
                issue_key=issue_key,
                params=json.dumps(params),
                rollback_data=json.dumps(rollback_data),
                timestamp=datetime.utcnow(),
                rolled_back=0
            )
            session.add(checkpoint)
            session.commit()
            
            logger.info(f"Created checkpoint {checkpoint.id} for {action_name}")
            return checkpoint.id
        finally:
            session.close()
    
    def get_checkpoint(self, checkpoint_id: int) -> Optional[Dict[str, Any]]:
        """Get checkpoint by ID.
        
        Args:
            checkpoint_id: Checkpoint ID
            
        Returns:
            Checkpoint data or None
        """
        session = self._get_session()
        try:
            checkpoint = session.query(Checkpoint).filter_by(id=checkpoint_id).first()
            return checkpoint.to_dict() if checkpoint else None
        finally:
            session.close()
    
    def list_checkpoints(
        self,
        tenant_id: str,
        issue_key: Optional[str] = None,
        limit: int = 50,
        include_rolled_back: bool = False
    ) -> List[Dict[str, Any]]:
        """List checkpoints for a tenant.
        
        Args:
            tenant_id: Tenant ID
            issue_key: Optional issue key filter
            limit: Maximum number of checkpoints to return
            include_rolled_back: Include rolled back checkpoints
            
        Returns:
            List of checkpoint data
        """
        session = self._get_session()
        try:
            query = session.query(Checkpoint).filter_by(tenant_id=tenant_id)
            
            if issue_key:
                query = query.filter_by(issue_key=issue_key)
            
            if not include_rolled_back:
                query = query.filter_by(rolled_back=0)
            
            query = query.order_by(Checkpoint.timestamp.desc()).limit(limit)
            
            return [cp.to_dict() for cp in query.all()]
        finally:
            session.close()
    
    def mark_rolled_back(self, checkpoint_id: int) -> bool:
        """Mark checkpoint as rolled back.
        
        Args:
            checkpoint_id: Checkpoint ID
            
        Returns:
            True if successful, False otherwise
        """
        session = self._get_session()
        try:
            checkpoint = session.query(Checkpoint).filter_by(id=checkpoint_id).first()
            if not checkpoint:
                return False
            
            checkpoint.rolled_back = 1
            session.commit()
            
            logger.info(f"Marked checkpoint {checkpoint_id} as rolled back")
            return True
        finally:
            session.close()
    
    def get_rollback_data(self, checkpoint_id: int) -> Optional[Dict[str, Any]]:
        """Get rollback data for a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint ID
            
        Returns:
            Rollback data or None
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return None
        
        if checkpoint["rolled_back"]:
            logger.warning(f"Checkpoint {checkpoint_id} already rolled back")
            return None
        
        return checkpoint["rollback_data"]


# Global checkpoint service instance
_checkpoint_service: Optional[CheckpointService] = None


def get_checkpoint_service() -> CheckpointService:
    """Get global checkpoint service instance."""
    global _checkpoint_service
    if _checkpoint_service is None:
        _checkpoint_service = CheckpointService()
    return _checkpoint_service


def create_rollback_data(
    action_name: str,
    current_state: Dict[str, Any],
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Create rollback data for a write operation.
    
    Args:
        action_name: Name of the action
        current_state: Current state before the operation
        params: Action parameters
        
    Returns:
        Rollback data
    """
    if action_name == "add_comment":
        # To rollback: delete the comment
        return {
            "action": "delete_comment",
            "issue_key": params["issue_key"],
            "comment_id": None  # Will be filled after comment is created
        }
    
    elif action_name == "transition_issue":
        # To rollback: transition back to original status
        return {
            "action": "transition_issue",
            "issue_key": params["issue_key"],
            "transition_id": current_state.get("original_transition_id"),
            "original_status": current_state.get("original_status")
        }
    
    elif action_name == "assign_issue":
        # To rollback: assign back to original assignee
        return {
            "action": "assign_issue",
            "issue_key": params["issue_key"],
            "assignee": current_state.get("original_assignee")
        }
    
    elif action_name == "add_watcher":
        # To rollback: remove the watcher
        return {
            "action": "remove_watcher",
            "issue_key": params["issue_key"],
            "account_id": params["account_id"]
        }
    
    elif action_name == "link_issues":
        # To rollback: delete the link
        return {
            "action": "delete_link",
            "link_id": None  # Will be filled after link is created
        }
    
    elif action_name == "update_issue_field":
        # To rollback: restore original field value
        return {
            "action": "update_issue_field",
            "issue_key": params["issue_key"],
            "field_name": params["field_name"],
            "field_value": current_state.get("original_value")
        }
    
    else:
        logger.warning(f"No rollback data defined for action: {action_name}")
        return {"action": "unknown"}

