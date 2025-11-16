# Import all services for easy access
from .base_service import BaseService
from .agent_service import AgentService
from .anomaly_detection import AnomalyDetectionService
from .approval_service import ApprovalService
from .auth_service import AuthService
from .auth_service_simple import AuthServiceSimple
from .compliance_engine import ComplianceEngine, ComplianceRule
from .compliance_service import ComplianceService
from .integration import IntegrationService
from .monitoring_service import MonitoringService
from .report_service import ReportService
from .security_service import SecurityService
from .settings_service import SettingsService

__all__ = [
    'BaseService',
    'AgentService',
    'AnomalyDetectionService',
    'ApprovalService', 
    'AuthService',
    'AuthServiceSimple',
    'ComplianceEngine',
    'ComplianceRule',
    'ComplianceService',
    'IntegrationService',
    'MonitoringService',
    'ReportService',
    'SecurityService',
    'SettingsService'
]

# Service registry for dynamic service management
SERVICE_REGISTRY = {
    'agent': AgentService,
    'anomaly_detection': AnomalyDetectionService,
    'approval': ApprovalService,
    'auth': AuthService,
    'auth_simple': AuthServiceSimple,
    'compliance': ComplianceService,
    'integration': IntegrationService,
    'monitoring': MonitoringService,
    'report': ReportService,
    'security': SecurityService,
    'settings': SettingsService
}

def get_service(service_name: str) -> BaseService:
    """
    Get a service instance by name.
    
    Args:
        service_name: Name of the service to get
        
    Returns:
        Service instance
        
    Raises:
        KeyError: If service name is not found
    """
    if service_name not in SERVICE_REGISTRY:
        raise KeyError(f"Service '{service_name}' not found in registry")
    
    return SERVICE_REGISTRY[service_name]()

def list_available_services() -> list:
    """Get list of available service names"""
    return list(SERVICE_REGISTRY.keys())
