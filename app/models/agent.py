from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, Enum
from datetime import datetime
import uuid
import enum
from app.database import Base


class AgentStatus(str, enum.Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentType(str, enum.Enum):
    """Agent type enumeration"""
    MONITOR = "monitor"
    ANALYZER = "analyzer"
    COLLECTOR = "collector"
    DECISION_MAKER = "decision_maker"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    GENERAL = "general"


class Agent(Base):
    """
    Model for AI Agent management
    
    Stores information about AI agents in the system for monitoring and management
    """
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Agent Configuration
    agent_type = Column(String(50), nullable=False, default=AgentType.GENERAL.value)
    status = Column(String(20), nullable=False, default=AgentStatus.ACTIVE.value, index=True)
    version = Column(String(20), nullable=True, default="1.0.0")
    
    # Capabilities and Configuration
    capabilities = Column(JSON, nullable=True)  # List of capabilities
    configuration = Column(JSON, nullable=True)  # Agent-specific config
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, nullable=True)
    
    # Statistics
    total_activities = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    success_rate = Column(Integer, default=100)  # Percentage
    
    # Operational
    is_enabled = Column(Boolean, default=True, nullable=False)
    owner = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags for categorization
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, type={self.agent_type}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type,
            'status': self.status,
            'version': self.version,
            'capabilities': self.capabilities or [],
            'configuration': self.configuration or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'total_activities': self.total_activities,
            'total_errors': self.total_errors,
            'success_rate': self.success_rate,
            'is_enabled': self.is_enabled,
            'owner': self.owner,
            'tags': self.tags or []
        }
    
    def update_stats(self, activities: int = 0, errors: int = 0):
        """Update agent statistics"""
        self.total_activities += activities
        self.total_errors += errors
        if self.total_activities > 0:
            self.success_rate = int(((self.total_activities - self.total_errors) / self.total_activities) * 100)
        self.last_active = datetime.utcnow()
