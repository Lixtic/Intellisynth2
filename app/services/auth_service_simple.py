from typing import Dict, Any
from datetime import datetime
from app.services.base_service import BaseService

class AuthServiceSimple(BaseService):
    """
    Simple authentication service for basic demo purposes.
    """
    
    def __init__(self):
        super().__init__("AuthServiceSimple")
        self.demo_user = {
            "username": "demo",
            "password": "demo123",
            "role": "demo_user"
        }
    
    def initialize(self) -> bool:
        """Initialize the simple auth service"""
        self.log_info("Simple auth service initialized")
        return True
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        return True
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Simple authentication check.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication result
        """
        if (username == self.demo_user["username"] and 
            password == self.demo_user["password"]):
            
            self.log_info(f"Demo user {username} authenticated")
            return {
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "username": username,
                    "role": self.demo_user["role"],
                    "authenticated_at": datetime.utcnow().isoformat()
                }
            }
        
        self.log_warning(f"Authentication failed for user: {username}")
        return {
            "success": False,
            "message": "Invalid credentials"
        }
    
    def get_demo_credentials(self) -> Dict[str, str]:
        """Get demo credentials for testing"""
        return {
            "username": self.demo_user["username"],
            "password": self.demo_user["password"]
        }
