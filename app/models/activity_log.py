from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from datetime import datetime
import uuid
from app.database import Base

class ActivityLog(Base):
    """
    Model for storing AI agent activity logs
    
    Creates an immutable record of every AI agent action, decision, and data point
    for complete transparency and auditability of the AI system
    """
    __tablename__ = "activity_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Agent Information
    agent_id = Column(String(100), nullable=False, index=True)
    
    # Activity Details
    action_type = Column(String(50), nullable=False, index=True)  # decision, data_collection, analysis, etc.
    severity = Column(String(20), nullable=False, default='info', index=True)  # critical, high, medium, low, info
    message = Column(Text, nullable=False)
    
    # Structured Data
    data = Column(JSON, nullable=True)  # Additional context, metrics, results
    
    # Context Information  
    user_id = Column(String(50), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Immutable Record Verification
    hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash for integrity verification
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, agent={self.agent_id}, action={self.action_type}, time={self.timestamp})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'agent_id': self.agent_id,
            'action_type': self.action_type,
            'severity': self.severity,
            'message': self.message,
            'data': self.data,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'hash': self.hash
        }
