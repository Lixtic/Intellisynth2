from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """
    Base service class providing common functionality for all services.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def log_info(self, message: str, **kwargs):
        """Log info message with service context"""
        logger.info(f"[{self.name}] {message}", extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with service context"""
        logger.error(f"[{self.name}] {message}", extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with service context"""
        logger.warning(f"[{self.name}] {message}", extra=kwargs)
    
    def update_timestamp(self):
        """Update the last_updated timestamp"""
        self.last_updated = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """Get basic service status"""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status": "active"
        }
    
    @abstractmethod
    def health_check(self) -> bool:
        """Perform health check for the service"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        pass
