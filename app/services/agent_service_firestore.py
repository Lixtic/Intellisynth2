"""
Agent Service - Firestore Version
Manages AI agents in the system with Firebase Firestore persistence
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.services.firebase_service import FirestoreService
from app.firebase_config import Collections
from app.services.base_service import BaseService


class AgentStatus:
    """Agent status constants"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentType:
    """Agent type constants"""
    MONITOR = "monitor"
    ANALYZER = "analyzer"
    COLLECTOR = "collector"
    DECISION_MAKER = "decision_maker"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    GENERAL = "general"


class AgentServiceFirestore(BaseService):
    """Service for managing AI agents with Firestore persistence"""
    
    def __init__(self):
        super().__init__("AgentServiceFirestore")
        self.firestore_service = FirestoreService(Collections.AGENTS)
    
    def initialize(self) -> bool:
        """Initialize the agent service"""
        try:
            self.log_info("Initializing agent service with Firestore")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize agent service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            # Test Firestore connection by checking if collection exists
            import asyncio
            asyncio.run(self.firestore_service.count())
            return True
        except:
            return False
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        return True
    
    async def create_agent(
        self,
        name: str,
        agent_type: str = AgentType.GENERAL,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new agent"""
        try:
            agent_id = str(uuid.uuid4())
            
            agent_data = {
                'name': name,
                'agent_type': agent_type,
                'description': description,
                'capabilities': capabilities or [],
                'configuration': configuration or {},
                'status': AgentStatus.ACTIVE,
                'version': '1.0.0',
                'owner': owner,
                'tags': tags or [],
                'is_enabled': True,
                'total_activities': 0,
                'total_errors': 0,
                'success_rate': 100,
                'last_active': None
            }
            
            created = await self.firestore_service.create(doc_id=agent_id, data=agent_data)
            
            self.log_info(f"Created agent: {name} ({agent_id})")
            return created
        except Exception as e:
            self.log_error(f"Failed to create agent: {str(e)}")
            raise Exception(f"Failed to create agent: {str(e)}")
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        return await self.firestore_service.get(agent_id)
    
    async def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name"""
        return await self.firestore_service.find_one('name', name)
    
    async def get_all_agents(
        self,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all agents with optional filters"""
        try:
            filters = []
            
            # Apply filters
            if status:
                filters.append(('status', '==', status))
            if agent_type:
                filters.append(('agent_type', '==', agent_type))
            if is_enabled is not None:
                filters.append(('is_enabled', '==', is_enabled))
            
            # Order by last_active descending (use '-last_active' for descending)
            agents = await self.firestore_service.get_all(
                filters=filters if filters else None,
                order_by='-updated_at',  # Order by most recently updated
                limit=limit
            )
            
            return agents
        except Exception as e:
            self.log_error(f"Failed to get agents: {str(e)}")
            return []
    
    async def update_agent(
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
        try:
            # Build update data (only include provided fields)
            update_data = {}
            
            if name is not None:
                update_data['name'] = name
            if description is not None:
                update_data['description'] = description
            if agent_type is not None:
                update_data['agent_type'] = agent_type
            if status is not None:
                update_data['status'] = status
            if capabilities is not None:
                update_data['capabilities'] = capabilities
            if configuration is not None:
                update_data['configuration'] = configuration
            if is_enabled is not None:
                update_data['is_enabled'] = is_enabled
            if owner is not None:
                update_data['owner'] = owner
            if tags is not None:
                update_data['tags'] = tags
            
            if not update_data:
                # Nothing to update
                return await self.get_agent(agent_id)
            
            updated = await self.firestore_service.update(agent_id, update_data)
            
            if updated:
                self.log_info(f"Updated agent: {updated.get('name')} ({agent_id})")
            
            return updated
        except Exception as e:
            self.log_error(f"Failed to update agent: {str(e)}")
            raise Exception(f"Failed to update agent: {str(e)}")
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        try:
            result = await self.firestore_service.delete(agent_id)
            
            if result:
                self.log_info(f"Deleted agent ({agent_id})")
            
            return result
        except Exception as e:
            self.log_error(f"Failed to delete agent: {str(e)}")
            raise Exception(f"Failed to delete agent: {str(e)}")
    
    async def update_agent_activity(
        self,
        agent_id: str,
        activities: int = 1,
        errors: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Update agent activity statistics"""
        try:
            agent = await self.get_agent(agent_id)
            
            if not agent:
                return None
            
            # Calculate new statistics
            total_activities = agent.get('total_activities', 0) + activities
            total_errors = agent.get('total_errors', 0) + errors
            
            # Calculate success rate
            if total_activities > 0:
                success_rate = ((total_activities - total_errors) / total_activities) * 100
            else:
                success_rate = 100
            
            # Update agent
            update_data = {
                'total_activities': total_activities,
                'total_errors': total_errors,
                'success_rate': round(success_rate, 2),
                'last_active': datetime.utcnow().isoformat()
            }
            
            return await self.firestore_service.update(agent_id, update_data)
        except Exception as e:
            self.log_error(f"Failed to update agent activity: {str(e)}")
            raise Exception(f"Failed to update agent activity: {str(e)}")
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get aggregated agent statistics"""
        try:
            all_agents = await self.firestore_service.get_all()
            
            total_agents = len(all_agents)
            active_agents = len([a for a in all_agents if a.get('status') == AgentStatus.ACTIVE])
            inactive_agents = len([a for a in all_agents if a.get('status') == AgentStatus.INACTIVE])
            error_agents = len([a for a in all_agents if a.get('status') == AgentStatus.ERROR])
            
            # Count by type
            type_counts = {
                AgentType.MONITOR: 0,
                AgentType.ANALYZER: 0,
                AgentType.COLLECTOR: 0,
                AgentType.DECISION_MAKER: 0,
                AgentType.COMPLIANCE: 0,
                AgentType.SECURITY: 0,
                AgentType.GENERAL: 0
            }
            
            for agent in all_agents:
                agent_type = agent.get('agent_type', AgentType.GENERAL)
                if agent_type in type_counts:
                    type_counts[agent_type] += 1
            
            total_activities = sum(a.get('total_activities', 0) for a in all_agents)
            total_errors = sum(a.get('total_errors', 0) for a in all_agents)
            avg_success_rate = sum(a.get('success_rate', 100) for a in all_agents) / total_agents if total_agents > 0 else 100
            
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
        except Exception as e:
            self.log_error(f"Failed to get agent stats: {str(e)}")
            return {
                'total_agents': 0,
                'active_agents': 0,
                'inactive_agents': 0,
                'error_agents': 0,
                'agents_by_type': {},
                'total_activities': 0,
                'total_errors': 0,
                'avg_success_rate': 100
            }
    
    async def search_agents(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search agents by name or description
        Note: Firestore has limited text search capabilities
        This does prefix matching on the name field
        """
        try:
            # Search by name (prefix matching)
            agents = await self.firestore_service.search('name', query, case_sensitive=False)
            
            # Limit results
            return agents[:limit]
        except Exception as e:
            self.log_error(f"Failed to search agents: {str(e)}")
            return []


# Global agent service instance (Firestore version)
agent_service_firestore = AgentServiceFirestore()
