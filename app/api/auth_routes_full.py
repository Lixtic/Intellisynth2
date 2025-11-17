from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr

from app.services.auth_service import UserRole, auth_service

router = APIRouter()
security = HTTPBearer()


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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    user = await auth_service.get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
):
    """User login"""
    user = await auth_service.authenticate_user(login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    tokens = await auth_service.create_session(user)
    
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
async def refresh_token(
    refresh_token: Optional[str] = Cookie(None),
):
    """Refresh access token"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    tokens = await auth_service.refresh_access_token(refresh_token)
    
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
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return current_user.to_dict()

@router.get("/dashboard-config")
async def get_dashboard_config(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get user's dashboard configuration"""
    return await auth_service.get_user_dashboard_config(current_user)

# User management endpoints (admin only)
@router.post("/users", response_model=Dict[str, Any])
async def create_user(
    user_data: UserCreateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin),
):
    """Create new user (admin only)"""
    try:
        user = await auth_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            full_name=user_data.full_name,
            department=user_data.department,
        )
        return {"message": "User created successfully", "user": user}

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="User creation failed")

@router.get("/users")
async def get_users(
    admin_user: Dict[str, Any] = Depends(require_admin),
):
    """Get all users (admin only)"""
    return await auth_service.list_users()

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin),
):
    """Update user (admin only)"""
    updated = await auth_service.update_user(
        user_id,
        role=user_data.role,
        is_active=user_data.is_active,
        full_name=user_data.full_name,
        department=user_data.department,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated successfully", "user": updated}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: Dict[str, Any] = Depends(require_admin),
):
    """Deactivate user (admin only)"""
    target = await auth_service.update_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.get("role") == UserRole.ADMIN.value:
        users = await auth_service.list_users()
        active_admins = [u for u in users if u.get("role") == UserRole.ADMIN.value and u.get("is_active", True)]
        if len(active_admins) <= 1:
            raise HTTPException(status_code=400, detail="Cannot deactivate the last admin user")

    success = await auth_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to deactivate user")

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
                "description": ROLE_DESCRIPTIONS.get(role, ""),
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
