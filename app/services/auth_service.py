"""Firebase-backed authentication service used by the full auth routes."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext  # type: ignore[import]

from app.config import config
from app.firebase_config import Collections
from app.services.base_service import BaseService
from app.services.firebase_service import FirestoreService


class UserRole(str, Enum):
    """Supported user roles for RBAC checks."""

    ADMIN = "admin"
    VIEWER = "viewer"
    AUDITOR = "auditor"
    OPERATOR = "operator"


class AuthService(BaseService):
    """Authentication and authorization service backed by Firestore."""

    def __init__(self) -> None:
        super().__init__("AuthService")
        self._store = FirestoreService(Collections.USERS)
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._secret_key = config.SECRET_KEY
        self._algorithm = config.ALGORITHM
        self._access_expiry = int(config.ACCESS_TOKEN_EXPIRE_MINUTES)
        self._refresh_expiry_days = 7
        self._defaults_seeded = False

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    async def initialize(self) -> bool:
        await self._ensure_default_users()
        return True

    def health_check(self) -> bool:  # pragma: no cover - trivial
        return True

    def cleanup(self) -> bool:  # pragma: no cover - compatibility
        return True

    # ------------------------------------------------------------------
    # Public API consumed by routes
    # ------------------------------------------------------------------
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        await self._ensure_default_users()
        user = await self._find_user_by_username(username)
        if not user or not user.get("is_active", True):
            return None

        if not self._verify_password(password, user.get("password_hash", "")):
            return None

        return user

    async def create_session(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Create JWT access and refresh tokens for the user."""

        access_token = self._build_token(
            {
                "sub": user["username"],
                "role": user.get("role"),
                "type": "access",
            },
            minutes=self._access_expiry,
        )
        refresh_token = self._build_token(
            {"sub": user["username"], "type": "refresh"},
            minutes=self._refresh_expiry_days * 24 * 60,
        )

        await self._store.update(
            user["id"],
            {"last_login": datetime.utcnow().isoformat()},
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self._access_expiry * 60,
            "user": self._sanitize_user(user),
        }

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(refresh_token, self._secret_key, algorithms=[self._algorithm])
        except JWTError:
            return None

        if payload.get("type") != "refresh":
            return None

        username = payload.get("sub")
        if not username:
            return None

        user = await self._find_user_by_username(username)
        if not user or not user.get("is_active", True):
            return None

        return await self.create_session(user)

    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError:
            return None

        if payload.get("type") != "access":
            return None

        username = payload.get("sub")
        if not username:
            return None

        user = await self._find_user_by_username(username)
        if not user or not user.get("is_active", True):
            return None

        return self._sanitize_user(user)

    async def get_user_dashboard_config(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Return a simple dashboard configuration tailored by role."""

        role = user.get("role", UserRole.VIEWER.value)
        widgets = [
            "system-health",
            "recent-activity",
            "compliance-status",
        ]
        if role == UserRole.ADMIN.value:
            widgets.extend(["user-management", "reporting"])
        elif role == UserRole.AUDITOR.value:
            widgets.append("audit-logs")

        return {
            "widgets": widgets,
            "refresh_interval": 30,
            "theme": "dark",
        }

    async def list_users(self) -> List[Dict[str, Any]]:
        await self._ensure_default_users()
        users = await self._store.get_all(order_by="username")
        return [self._sanitize_user(user) for user in users]

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        await self._ensure_default_users()
        existing = await self._find_user_by_username(username)
        if existing:
            raise ValueError("Username already exists")

        payload = {
            "username": username,
            "email": email.lower(),
            "password_hash": self._hash_password(password),
            "role": role.value,
            "full_name": full_name,
            "department": department,
            "is_active": True,
            "permissions": self._role_permissions(role),
        }

        created = await self._store.create(doc_id=username, data=payload)
        return self._sanitize_user(created)

    async def update_user(
        self,
        user_id: str,
        *,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        updates: Dict[str, Any] = {}
        if role is not None:
            updates["role"] = role.value
            updates["permissions"] = self._role_permissions(role)
        if is_active is not None:
            updates["is_active"] = is_active
        if full_name is not None:
            updates["full_name"] = full_name
        if department is not None:
            updates["department"] = department

        if not updates:
            user = await self._store.get(user_id)
            return self._sanitize_user(user) if user else None

        updated = await self._store.update(user_id, updates)
        return self._sanitize_user(updated) if updated else None

    async def deactivate_user(self, user_id: str) -> bool:
        updated = await self._store.update(user_id, {"is_active": False})
        return bool(updated)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _ensure_default_users(self) -> None:
        if self._defaults_seeded:
            return

        admin = await self._find_user_by_username("admin")
        tasks = []
        if not admin:
            tasks.append(
                self._store.create(
                    doc_id="admin",
                    data={
                        "username": "admin",
                        "email": "admin@example.com",
                        "password_hash": self._hash_password("admin123"),
                        "role": UserRole.ADMIN.value,
                        "full_name": "System Admin",
                        "is_active": True,
                        "permissions": self._role_permissions(UserRole.ADMIN),
                    },
                )
            )

        demo = await self._find_user_by_username("demo")
        if not demo:
            tasks.append(
                self._store.create(
                    doc_id="demo",
                    data={
                        "username": "demo",
                        "email": "demo@example.com",
                        "password_hash": self._hash_password("demo123"),
                        "role": UserRole.VIEWER.value,
                        "full_name": "Demo User",
                        "is_active": True,
                        "permissions": self._role_permissions(UserRole.VIEWER),
                    },
                )
            )

        if tasks:
            for task in tasks:
                await task

        self._defaults_seeded = True

    async def _find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        return await self._store.find_one("username", username)

    def _hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self._pwd_context.verify(plain_password, hashed_password)
        except ValueError:
            return False

    def _build_token(self, payload: Dict[str, Any], *, minutes: int) -> str:
        to_encode = payload.copy()
        expire = datetime.utcnow() + timedelta(minutes=minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def _sanitize_user(self, user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not user:
            return {}
        sanitized = dict(user)
        sanitized.pop("password_hash", None)
        sanitized.setdefault("id", sanitized.get("username") or str(uuid4()))
        return sanitized

    def _role_permissions(self, role: UserRole) -> List[str]:
        if role == UserRole.ADMIN:
            return ["admin", "users:manage", "reports:view", "activity:view"]
        if role == UserRole.OPERATOR:
            return ["activity:view", "reports:view", "approvals:manage"]
        if role == UserRole.AUDITOR:
            return ["reports:view", "activity:view"]
        return ["activity:view"]


auth_service = AuthService()
