from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.services.base_service import BaseService

class AuthService(BaseService):
    """
    Full authentication and authorization service for AI Flight Recorder.
    """
    
    def __init__(self):
        super().__init__("AuthService")
        self.users = {}
        self.sessions = {}
        self.permissions = {}
        self._initialize_default_users()
    
    def initialize(self) -> bool:
        """Initialize the authentication service"""
        try:
            self.log_info("Initializing authentication service")
            self._setup_permissions()
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize auth service: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        return len(self.users) > 0
    
    def cleanup(self) -> bool:
        """Cleanup service resources"""
        self.sessions.clear()
        return True
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Authentication result with token if successful
        """
        if username not in self.users:
            self.log_warning(f"Authentication failed for unknown user: {username}")
            return {
                "success": False,
                "message": "Invalid credentials",
                "token": None
            }
        
        user = self.users[username]
        
        # Simple password check (in production, use proper hashing)
        if user["password"] != password:
            self.log_warning(f"Authentication failed for user: {username}")
            return {
                "success": False,
                "message": "Invalid credentials",
                "token": None
            }
        
        # Create session token
        token = self._generate_token(username)
        session = {
            "username": username,
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "permissions": user["permissions"]
        }
        
        self.sessions[token] = session
        self.log_info(f"User {username} authenticated successfully")
        
        return {
            "success": True,
            "message": "Authentication successful",
            "token": token,
            "user": {
                "username": username,
                "role": user["role"],
                "permissions": user["permissions"]
            }
        }
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an authentication token.
        
        Args:
            token: Authentication token
            
        Returns:
            Validation result with user info if valid
        """
        if token not in self.sessions:
            return {
                "valid": False,
                "message": "Invalid token"
            }
        
        session = self.sessions[token]
        
        # Check if token is expired
        if datetime.utcnow() > session["expires_at"]:
            del self.sessions[token]
            return {
                "valid": False,
                "message": "Token expired"
            }
        
        return {
            "valid": True,
            "username": session["username"],
            "permissions": session["permissions"]
        }
    
    def authorize(self, token: str, required_permission: str) -> bool:
        """
        Check if a token has the required permission.
        
        Args:
            token: Authentication token
            required_permission: Permission to check
            
        Returns:
            True if authorized, False otherwise
        """
        validation = self.validate_token(token)
        if not validation["valid"]:
            return False
        
        permissions = validation["permissions"]
        return required_permission in permissions or "admin" in permissions
    
    def logout(self, token: str) -> bool:
        """
        Logout a user by invalidating their token.
        
        Args:
            token: Authentication token
            
        Returns:
            True if logout successful
        """
        if token in self.sessions:
            username = self.sessions[token]["username"]
            del self.sessions[token]
            self.log_info(f"User {username} logged out")
            return True
        return False
    
    def create_user(self, username: str, password: str, role: str, permissions: List[str]) -> bool:
        """
        Create a new user.
        
        Args:
            username: Username
            password: Password
            role: User role
            permissions: List of permissions
            
        Returns:
            True if user created successfully
        """
        if username in self.users:
            self.log_warning(f"User {username} already exists")
            return False
        
        self.users[username] = {
            "username": username,
            "password": password,  # In production, hash this
            "role": role,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.log_info(f"User {username} created with role {role}")
        return True
    
    def _generate_token(self, username: str) -> str:
        """Generate a session token"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        return f"token_{username}_{timestamp}"
    
    def _initialize_default_users(self):
        """Initialize default users"""
        self.users = {
            "admin": {
                "username": "admin",
                "password": "admin123",
                "role": "administrator",
                "permissions": ["admin", "read", "write", "delete"],
                "created_at": datetime.utcnow().isoformat()
            },
            "operator": {
                "username": "operator",
                "password": "op123",
                "role": "operator",
                "permissions": ["read", "write"],
                "created_at": datetime.utcnow().isoformat()
            },
            "viewer": {
                "username": "viewer",
                "password": "view123",
                "role": "viewer",
                "permissions": ["read"],
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    def _setup_permissions(self):
        """Setup permission definitions"""
        self.permissions = {
            "read": "Can view data and reports",
            "write": "Can modify data and settings",
            "delete": "Can delete data",
            "admin": "Full administrative access"
        }
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active sessions"""
        current_time = datetime.utcnow()
        active_sessions = []
        
        for token, session in self.sessions.items():
            if current_time < session["expires_at"]:
                active_sessions.append({
                    "username": session["username"],
                    "created_at": session["created_at"].isoformat(),
                    "expires_at": session["expires_at"].isoformat()
                })
        
        return active_sessions
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        if username not in self.users:
            return None
        
        user = self.users[username].copy()
        del user["password"]  # Don't return password
        return user
