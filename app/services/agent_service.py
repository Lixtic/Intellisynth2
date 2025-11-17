"""
Agent Service
Manages AI agents in the system with database persistence
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import SessionLocal, engine
from app.models.agent import Agent, AgentStatus, AgentType, Base
from app.services.base_service import BaseService

# Create tables only when SQLite backend is enabled
if engine is not None:
    Base.metadata.create_all(bind=engine)


class AgentService(BaseService):
    """Service for managing AI agents with database persistence"""
    
    def __init__(self):
        super().__init__("AgentService")
    
    def _get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    def initialize(self) -> bool:
        """Initialize the agent service"""
        try:
            self.log_info("Initializing agent service with database")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize agent service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            db = self._get_db()
            count = db.query(Agent).count()
            db.close()
            return True
        except:
            return False
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        return True
    
    def create_agent(
        self,
        name: str,
        agent_type: str = AgentType.GENERAL.value,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new agent"""
        db = self._get_db()
        try:
            agent = Agent(
                name=name,
                agent_type=agent_type,
                description=description,
                capabilities=capabilities or [],
                configuration=configuration or {},
                status=AgentStatus.ACTIVE.value,
                owner=owner,
                tags=tags or [],
                is_enabled=True
            )
            
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            self.log_info(f"Created agent: {name} ({agent.id})")
            return agent.to_dict()
        except Exception as e:
            db.rollback()
            self.log_error(f"Failed to create agent: {str(e)}")
            raise Exception(f"Failed to create agent: {str(e)}")
        finally:
            db.close()
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        db = self._get_db()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            return agent.to_dict() if agent else None
        finally:
            db.close()
    
    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name"""
        db = self._get_db()
        try:
            agent = db.query(Agent).filter(Agent.name == name).first()
            return agent.to_dict() if agent else None
        finally:
            db.close()
    
    def get_all_agents(
        self,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all agents with optional filters"""
        db = self._get_db()
        try:
            query = db.query(Agent)
            
            # Apply filters
            if status:
                query = query.filter(Agent.status == status)
            if agent_type:
                query = query.filter(Agent.agent_type == agent_type)
            if is_enabled is not None:
                query = query.filter(Agent.is_enabled == is_enabled)
            
            # Order by last_active descending, then by name
            query = query.order_by(Agent.last_active.desc().nullslast(), Agent.name)
            
            agents = query.limit(limit).all()
            return [agent.to_dict() for agent in agents]
        finally:
            db.close()
    
    def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_enabled: Optional[bool] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing agent"""
        db = self._get_db()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return None
            
            # Update fields if provided
            if name is not None:
                agent.name = name
            if description is not None:
                agent.description = description
            if agent_type is not None:
                agent.agent_type = agent_type
            if status is not None:
                agent.status = status
            if capabilities is not None:
                agent.capabilities = capabilities
            if configuration is not None:
                agent.configuration = configuration
            if is_enabled is not None:
                agent.is_enabled = is_enabled
            if owner is not None:
                agent.owner = owner
            if tags is not None:
                agent.tags = tags
            
            agent.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(agent)
            
            self.log_info(f"Updated agent: {agent.name} ({agent_id})")
            return agent.to_dict()
        except Exception as e:
            db.rollback()
            self.log_error(f"Failed to update agent: {str(e)}")
            raise Exception(f"Failed to update agent: {str(e)}")
        finally:
            db.close()
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        db = self._get_db()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return False
            
            db.delete(agent)
            db.commit()
            
            self.log_info(f"Deleted agent: {agent.name} ({agent_id})")
            return True
        except Exception as e:
            db.rollback()
            self.log_error(f"Failed to delete agent: {str(e)}")
            raise Exception(f"Failed to delete agent: {str(e)}")
        finally:
            db.close()
    
    def update_agent_activity(
        self,
        agent_id: str,
        activities: int = 1,
        errors: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Update agent activity statistics"""
        db = self._get_db()
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return None
            
            agent.update_stats(activities=activities, errors=errors)
            agent.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(agent)
            
            return agent.to_dict()
        except Exception as e:
            db.rollback()
            self.log_error(f"Failed to update agent activity: {str(e)}")
            raise Exception(f"Failed to update agent activity: {str(e)}")
        finally:
            db.close()
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get aggregated agent statistics"""
        db = self._get_db()
        try:
            all_agents = db.query(Agent).all()
            
            total_agents = len(all_agents)
            active_agents = len([a for a in all_agents if a.status == AgentStatus.ACTIVE.value])
            inactive_agents = len([a for a in all_agents if a.status == AgentStatus.INACTIVE.value])
            error_agents = len([a for a in all_agents if a.status == AgentStatus.ERROR.value])
            
            # Count by type
            type_counts = {}
            for agent_type in AgentType:
                type_counts[agent_type.value] = len([a for a in all_agents if a.agent_type == agent_type.value])
            
            total_activities = sum(a.total_activities for a in all_agents)
            total_errors = sum(a.total_errors for a in all_agents)
            avg_success_rate = sum(a.success_rate for a in all_agents) / total_agents if total_agents > 0 else 100
            
            return {
                'total_agents': total_agents,
                'active_agents': active_agents,
                'inactive_agents': inactive_agents,
                'error_agents': error_agents,
                'agents_by_type': type_counts,
                'total_activities': total_activities,
                'total_errors': total_errors,
                'avg_success_rate': round(avg_success_rate, 2)
            }
        finally:
            db.close()
    
    def search_agents(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search agents by name or description"""
        db = self._get_db()
        try:
            agents = db.query(Agent).filter(
                or_(
                    Agent.name.contains(query),
                    Agent.description.contains(query)
                )
            ).limit(limit).all()
            
            return [agent.to_dict() for agent in agents]
        finally:
            db.close()


# Global agent service instance
agent_service = AgentService()

# Global agent service instance
agent_service = AgentService()
