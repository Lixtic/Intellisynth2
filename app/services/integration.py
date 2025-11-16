from typing import Dict, List, Any, Optional
from datetime import datetime
from app.services.base_service import BaseService

class IntegrationService(BaseService):
    """
    Service for managing external integrations and API connections.
    """
    
    def __init__(self):
        super().__init__("IntegrationService")
        self.integrations = {}
        self.connection_status = {}
        self.webhook_endpoints = []
        self._initialize_integrations()
    
    def initialize(self) -> bool:
        """Initialize the integration service"""
        try:
            self.log_info("Initializing integration service")
            self._test_all_connections()
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize integration service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        # Service is healthy if at least one integration is working
        return any(status["connected"] for status in self.connection_status.values())
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.webhook_endpoints.clear()
        return True
    
    def register_integration(self, integration_id: str, config: Dict[str, Any]) -> bool:
        """
        Register a new external integration.
        
        Args:
            integration_id: Unique identifier for the integration
            config: Integration configuration
            
        Returns:
            True if registration successful
        """
        try:
            integration = {
                "id": integration_id,
                "name": config.get("name", integration_id),
                "type": config.get("type", "unknown"),
                "endpoint": config.get("endpoint"),
                "api_key": config.get("api_key"),
                "auth_type": config.get("auth_type", "api_key"),
                "enabled": config.get("enabled", True),
                "timeout": config.get("timeout", 30),
                "retry_count": config.get("retry_count", 3),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.integrations[integration_id] = integration
            
            # Test connection
            if integration["enabled"]:
                self._test_connection(integration_id)
            
            self.log_info(f"Integration {integration_id} registered successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to register integration {integration_id}: {e}")
            return False
    
    def send_data(self, integration_id: str, data: Dict[str, Any], endpoint_path: str = "") -> Dict[str, Any]:
        """
        Send data to an external integration.
        
        Args:
            integration_id: Integration to send data to
            data: Data to send
            endpoint_path: Optional endpoint path to append
            
        Returns:
            Response from the integration
        """
        if integration_id not in self.integrations:
            return {"success": False, "error": f"Integration {integration_id} not found"}
        
        integration = self.integrations[integration_id]
        
        if not integration["enabled"]:
            return {"success": False, "error": f"Integration {integration_id} is disabled"}
        
        try:
            # Simulate API call
            response = self._make_api_call(integration, data, endpoint_path)
            
            self.log_info(f"Data sent to integration {integration_id} successfully")
            return {"success": True, "response": response}
            
        except Exception as e:
            self.log_error(f"Failed to send data to integration {integration_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def receive_webhook(self, webhook_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook data.
        
        Args:
            webhook_id: Webhook identifier
            payload: Incoming data payload
            
        Returns:
            Processing result
        """
        try:
            webhook_event = {
                "id": f"webhook_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                "webhook_id": webhook_id,
                "payload": payload,
                "received_at": datetime.utcnow().isoformat(),
                "processed": False
            }
            
            # Process webhook based on type
            result = self._process_webhook(webhook_event)
            
            webhook_event["processed"] = True
            webhook_event["result"] = result
            
            self.log_info(f"Webhook {webhook_id} processed successfully")
            return {"success": True, "result": result}
            
        except Exception as e:
            self.log_error(f"Failed to process webhook {webhook_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_integration_status(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific integration"""
        if integration_id not in self.integrations:
            return None
        
        integration = self.integrations[integration_id]
        status = self.connection_status.get(integration_id, {"connected": False})
        
        return {
            "id": integration_id,
            "name": integration["name"],
            "type": integration["type"],
            "enabled": integration["enabled"],
            "connected": status["connected"],
            "last_test": status.get("last_test"),
            "last_error": status.get("last_error")
        }
    
    def get_all_integrations(self) -> List[Dict[str, Any]]:
        """Get status of all integrations"""
        return [self.get_integration_status(integration_id) 
                for integration_id in self.integrations.keys()]
    
    def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Test connection to a specific integration.
        
        Args:
            integration_id: Integration to test
            
        Returns:
            Test result
        """
        if integration_id not in self.integrations:
            return {"success": False, "error": f"Integration {integration_id} not found"}
        
        return self._test_connection(integration_id)
    
    def enable_integration(self, integration_id: str) -> bool:
        """Enable an integration"""
        if integration_id in self.integrations:
            self.integrations[integration_id]["enabled"] = True
            self.log_info(f"Integration {integration_id} enabled")
            return True
        return False
    
    def disable_integration(self, integration_id: str) -> bool:
        """Disable an integration"""
        if integration_id in self.integrations:
            self.integrations[integration_id]["enabled"] = False
            self.log_info(f"Integration {integration_id} disabled")
            return True
        return False
    
    def _initialize_integrations(self):
        """Initialize default integrations"""
        default_integrations = [
            {
                "id": "slack_notifications",
                "name": "Slack Notifications",
                "type": "messaging",
                "endpoint": "https://hooks.slack.com/services/DEMO",
                "auth_type": "webhook",
                "enabled": False
            },
            {
                "id": "email_alerts",
                "name": "Email Alerts",
                "type": "notification",
                "endpoint": "smtp://mail.example.com",
                "auth_type": "smtp",
                "enabled": False
            },
            {
                "id": "siem_system",
                "name": "SIEM Integration",
                "type": "security",
                "endpoint": "https://siem.example.com/api",
                "auth_type": "api_key",
                "enabled": False
            },
            {
                "id": "metrics_collector",
                "name": "Metrics Collector",
                "type": "monitoring",
                "endpoint": "https://metrics.example.com/api",
                "auth_type": "bearer_token",
                "enabled": True
            }
        ]
        
        for integration_config in default_integrations:
            self.register_integration(integration_config["id"], integration_config)
    
    def _test_connection(self, integration_id: str) -> Dict[str, Any]:
        """Test connection to an integration"""
        integration = self.integrations[integration_id]
        
        try:
            # Simulate connection test
            test_result = {
                "connected": True,
                "response_time": 150,  # ms
                "last_test": datetime.utcnow().isoformat()
            }
            
            self.connection_status[integration_id] = test_result
            
            return {
                "success": True,
                "message": f"Connection to {integration['name']} successful",
                "response_time": test_result["response_time"]
            }
            
        except Exception as e:
            error_status = {
                "connected": False,
                "last_test": datetime.utcnow().isoformat(),
                "last_error": str(e)
            }
            
            self.connection_status[integration_id] = error_status
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_all_connections(self):
        """Test connections to all enabled integrations"""
        for integration_id, integration in self.integrations.items():
            if integration["enabled"]:
                self._test_connection(integration_id)
    
    def _make_api_call(self, integration: Dict[str, Any], data: Dict[str, Any], endpoint_path: str) -> Dict[str, Any]:
        """Simulate making an API call to an integration"""
        # In a real implementation, this would make actual HTTP requests
        return {
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat(),
            "data_size": len(str(data)),
            "endpoint": integration["endpoint"] + endpoint_path
        }
    
    def _process_webhook(self, webhook_event: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook data"""
        # In a real implementation, this would route to appropriate handlers
        return {
            "processed_at": datetime.utcnow().isoformat(),
            "action": "logged",
            "webhook_type": webhook_event["webhook_id"]
        }
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of integration service status"""
        total_integrations = len(self.integrations)
        enabled_integrations = len([i for i in self.integrations.values() if i["enabled"]])
        connected_integrations = len([s for s in self.connection_status.values() if s["connected"]])
        
        return {
            "total_integrations": total_integrations,
            "enabled_integrations": enabled_integrations,
            "connected_integrations": connected_integrations,
            "connection_rate": f"{(connected_integrations/enabled_integrations*100):.1f}%" if enabled_integrations > 0 else "0%",
            "last_test": max([s.get("last_test", "1970-01-01") for s in self.connection_status.values()]) if self.connection_status else None
        }
