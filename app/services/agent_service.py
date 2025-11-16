from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.services.base_service import BaseService

class AgentService(BaseService):
    """
    Service for managing AI agent information and status.
    """
    
    def __init__(self):
        super().__init__("AgentService")
        self.agents = {}
        self._initialize_demo_agents()
    
    def initialize(self) -> bool:
        """Initialize the agent service"""
        try:
            self.log_info("Initializing agent service")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize agent service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return len(self.agents) > 0
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.agents.clear()
        return True
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """
        Register a new agent or update existing agent info.
        
        Args:
            agent_id: Unique agent identifier
            agent_info: Agent information dictionary
            
        Returns:
            True if registration successful
        """
        try:
            agent_data = {
                "id": agent_id,
                "name": agent_info.get("name", f"Agent {agent_id}"),
                "type": agent_info.get("type", "unknown"),
                "status": agent_info.get("status", "active"),
                "version": agent_info.get("version", "1.0.0"),
                "capabilities": agent_info.get("capabilities", []),
                "last_seen": datetime.utcnow().isoformat(),
                "registered_at": agent_info.get("registered_at", datetime.utcnow().isoformat()),
                "metadata": agent_info.get("metadata", {})
            }
            
            self.agents[agent_id] = agent_data
            self.log_info(f"Agent {agent_id} registered successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    def update_agent_status(self, agent_id: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Update agent status and metadata.
        
        Args:
            agent_id: Agent identifier
            status: New status
            metadata: Optional metadata update
            
        Returns:
            True if update successful
        """
        if agent_id not in self.agents:
            self.log_warning(f"Agent {agent_id} not found for status update")
            return False
        
        self.agents[agent_id]["status"] = status
        self.agents[agent_id]["last_seen"] = datetime.utcnow().isoformat()
        
        if metadata:
            self.agents[agent_id]["metadata"].update(metadata)
        
        self.log_info(f"Agent {agent_id} status updated to {status}")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent information"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents"""
        return [agent for agent in self.agents.values() if agent["status"] == "active"]
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from registry.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if removal successful
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.log_info(f"Agent {agent_id} removed from registry")
            return True
        return False
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total_agents = len(self.agents)
        status_counts = {}
        type_counts = {}
        
        for agent in self.agents.values():
            # Count by status
            status = agent["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            agent_type = agent["type"]
            type_counts[agent_type] = type_counts.get(agent_type, 0) + 1
        
        return {
            "total_agents": total_agents,
            "status_breakdown": status_counts,
            "type_breakdown": type_counts,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _initialize_demo_agents(self):
        """Initialize demo agents for testing"""
        demo_agents = [
            {
                "id": "agent_001",
                "name": "Data Collection Agent",
                "type": "data_collector",
                "status": "active",
                "version": "1.2.0",
                "capabilities": ["data_mining", "log_parsing", "metric_collection"],
                "metadata": {
                    "cpu_usage": 45.2,
                    "memory_usage": 512,
                    "tasks_completed": 1250
                }
            },
            {
                "id": "agent_002", 
                "name": "Monitoring Agent",
                "type": "monitor",
                "status": "active",
                "version": "1.1.5",
                "capabilities": ["system_monitoring", "alert_generation", "health_checks"],
                "metadata": {
                    "cpu_usage": 23.8,
                    "memory_usage": 256,
                    "alerts_sent": 45
                }
            },
            {
                "id": "agent_003",
                "name": "Analysis Agent", 
                "type": "analyzer",
                "status": "idle",
                "version": "1.0.8",
                "capabilities": ["pattern_analysis", "anomaly_detection", "report_generation"],
                "metadata": {
                    "cpu_usage": 15.3,
                    "memory_usage": 1024,
                    "analyses_completed": 89
                }
            },
            {
                "id": "agent_004",
                "name": "Security Agent",
                "type": "security", 
                "status": "active",
                "version": "1.3.2",
                "capabilities": ["threat_detection", "vulnerability_scanning", "incident_response"],
                "metadata": {
                    "cpu_usage": 67.1,
                    "memory_usage": 768,
                    "threats_detected": 12
                }
            },
            {
                "id": "agent_005",
                "name": "Compliance Agent",
                "type": "compliance",
                "status": "active", 
                "version": "1.1.0",
                "capabilities": ["compliance_checking", "audit_trail", "policy_enforcement"],
                "metadata": {
                    "cpu_usage": 34.5,
                    "memory_usage": 384,
                    "violations_found": 3
                }
            }
        ]
        
        for agent_data in demo_agents:
            agent_data["registered_at"] = datetime.utcnow().isoformat()
            agent_data["last_seen"] = datetime.utcnow().isoformat()
            self.agents[agent_data["id"]] = agent_data
