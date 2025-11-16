from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User, UserRole

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.VIEWER
    full_name: Optional[str] = None
    department: Optional[str] = None

class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    department: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

# Dependency to get current user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    auth_service = AuthService(db)
    user = auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Dependency to check admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """User login"""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    tokens = auth_service.create_access_token(user)
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return tokens

@router.post("/refresh")
def refresh_token(
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    auth_service = AuthService(db)
    tokens = auth_service.refresh_access_token(refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return tokens

@router.post("/logout")
def logout(response: Response):
    """User logout"""
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user.to_dict()

@router.get("/dashboard-config")
def get_dashboard_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's dashboard configuration"""
    auth_service = AuthService(db)
    return auth_service.get_user_dashboard_config(current_user)

# User management endpoints (admin only)
@router.post("/users", response_model=Dict[str, Any])
def create_user(
    user_data: UserCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    auth_service = AuthService(db)
    
    try:
        user = auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            full_name=user_data.full_name,
            department=user_data.department
        )
        return {"message": "User created successfully", "user": user.to_dict()}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="User creation failed")

@router.get("/users")
def get_users(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(User).all()
    return [user.to_dict() for user in users]

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.department is not None:
        user.department = user_data.department
    
    db.commit()
    
    return {"message": "User updated successfully", "user": user.to_dict()}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN, 
            User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, 
                detail="Cannot deactivate the last admin user"
            )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

# Role management
@router.get("/roles")
def get_roles():
    """Get available roles"""
    return {
        "roles": [
            {
                "name": role.value,
                "display_name": role.value.title(),
                "description": ROLE_DESCRIPTIONS.get(role, "")
            }
            for role in UserRole
        ]
    }

# Role descriptions
ROLE_DESCRIPTIONS = {
    UserRole.ADMIN: "Full system access including user management and settings",
    UserRole.VIEWER: "Read-only access to dashboards and reports",
    UserRole.AUDITOR: "Read access plus report generation capabilities",
    UserRole.OPERATOR: "Operational access including approval management"
}
