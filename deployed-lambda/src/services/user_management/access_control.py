"""Role-based access control (RBAC) middleware and utilities."""

import logging
from enum import Enum
from typing import Optional, Set, Callable, Any
from functools import wraps
from datetime import datetime

from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.utils.errors import AuthorizationError, AWSServiceError
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"
    GUEST = "guest"


class Permission(str, Enum):
    """System permissions."""
    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Content management
    CONTENT_READ = "content:read"
    CONTENT_WRITE = "content:write"
    CONTENT_DELETE = "content:delete"
    CONTENT_SHARE = "content:share"
    
    # Quiz management
    QUIZ_READ = "quiz:read"
    QUIZ_WRITE = "quiz:write"
    QUIZ_DELETE = "quiz:delete"
    QUIZ_GRADE = "quiz:grade"
    
    # Code analysis
    CODE_ANALYZE = "code:analyze"
    
    # Voice interface
    VOICE_USE = "voice:use"
    
    # System administration
    SYSTEM_ADMIN = "system:admin"
    AUDIT_READ = "audit:read"
    ANALYTICS_READ = "analytics:read"


# Role-to-permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Admins have all permissions
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.CONTENT_READ,
        Permission.CONTENT_WRITE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_SHARE,
        Permission.QUIZ_READ,
        Permission.QUIZ_WRITE,
        Permission.QUIZ_DELETE,
        Permission.QUIZ_GRADE,
        Permission.CODE_ANALYZE,
        Permission.VOICE_USE,
        Permission.SYSTEM_ADMIN,
        Permission.AUDIT_READ,
        Permission.ANALYTICS_READ,
    },
    Role.INSTRUCTOR: {
        # Instructors can manage content and quizzes
        Permission.USER_READ,
        Permission.CONTENT_READ,
        Permission.CONTENT_WRITE,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_SHARE,
        Permission.QUIZ_READ,
        Permission.QUIZ_WRITE,
        Permission.QUIZ_DELETE,
        Permission.QUIZ_GRADE,
        Permission.CODE_ANALYZE,
        Permission.VOICE_USE,
        Permission.ANALYTICS_READ,
    },
    Role.STUDENT: {
        # Students can read and create their own content
        Permission.USER_READ,
        Permission.CONTENT_READ,
        Permission.CONTENT_WRITE,
        Permission.QUIZ_READ,
        Permission.QUIZ_WRITE,
        Permission.CODE_ANALYZE,
        Permission.VOICE_USE,
    },
    Role.GUEST: {
        # Guests have minimal read-only access
        Permission.CONTENT_READ,
        Permission.QUIZ_READ,
    },
}


class AccessControlManager:
    """Manager for role-based access control."""

    def __init__(self, roles_table: DynamoDBClient) -> None:
        """
        Initialize access control manager.

        Args:
            roles_table: DynamoDB table for user roles
        """
        self.roles_table = roles_table
        logger.info("Initialized AccessControlManager")

    def assign_role(self, user_id: str, role: Role) -> None:
        """
        Assign a role to a user.

        Args:
            user_id: User identifier
            role: Role to assign

        Raises:
            AWSServiceError: If role assignment fails
        """
        try:
            self.roles_table.put_item({
                "user_id": user_id,
                "role": role.value,
                "assigned_at": datetime.utcnow().isoformat(),
            })
            logger.info(f"Assigned role {role.value} to user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to assign role: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )

    def get_user_role(self, user_id: str) -> Role:
        """
        Get user's role.

        Args:
            user_id: User identifier

        Returns:
            User's role (defaults to STUDENT if not found)

        Raises:
            AWSServiceError: If retrieval fails
        """
        try:
            item = self.roles_table.get_item({"user_id": user_id})
            if item and "role" in item:
                return Role(item["role"])
            
            # Default role for new users
            return Role.STUDENT

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to retrieve user role: {str(e)}",
                service="DynamoDB",
                operation="get_item",
            )

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user based on their role.

        Args:
            user_id: User identifier

        Returns:
            Set of permissions

        Raises:
            AWSServiceError: If retrieval fails
        """
        role = self.get_user_role(user_id)
        return ROLE_PERMISSIONS.get(role, set())

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User identifier
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        try:
            permissions = self.get_user_permissions(user_id)
            return permission in permissions
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False

    def require_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: Optional[str] = None,
    ) -> None:
        """
        Require user to have a specific permission.

        Args:
            user_id: User identifier
            permission: Required permission
            resource: Optional resource identifier

        Raises:
            AuthorizationError: If user lacks permission
        """
        if not self.has_permission(user_id, permission):
            role = self.get_user_role(user_id)
            logger.warning(
                f"Access denied: User {user_id} (role: {role.value}) "
                f"lacks permission {permission.value}"
            )
            raise AuthorizationError(
                message=f"Access denied: {permission.value} permission required",
                resource=resource,
                details={
                    "user_id": user_id,
                    "role": role.value,
                    "required_permission": permission.value,
                },
            )

    def check_resource_ownership(
        self,
        user_id: str,
        resource_owner_id: str,
        permission: Permission,
    ) -> None:
        """
        Check if user can access a resource based on ownership or permissions.

        Args:
            user_id: User identifier
            resource_owner_id: Resource owner's user ID
            permission: Permission required for non-owners

        Raises:
            AuthorizationError: If user cannot access resource
        """
        # Owner can always access their own resources
        if user_id == resource_owner_id:
            return

        # Otherwise, check if user has the required permission
        self.require_permission(user_id, permission)

    def revoke_role(self, user_id: str) -> None:
        """
        Revoke user's role (resets to default STUDENT role).

        Args:
            user_id: User identifier

        Raises:
            AWSServiceError: If revocation fails
        """
        try:
            self.assign_role(user_id, Role.STUDENT)
            logger.info(f"Revoked special role for user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to revoke role: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )


def require_permission(permission: Permission) -> Callable:
    """
    Decorator to require a specific permission for a function.

    Args:
        permission: Required permission

    Returns:
        Decorator function

    Example:
        @require_permission(Permission.CONTENT_WRITE)
        def create_content(user_id: str, content: dict):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract user_id from arguments
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            
            if not user_id:
                raise AuthorizationError(
                    message="User ID required for authorization",
                )

            # Get access control manager from kwargs or create new one
            acm = kwargs.get("access_control_manager")
            if not acm:
                raise RuntimeError(
                    "AccessControlManager not provided in function call"
                )

            # Check permission
            acm.require_permission(user_id, permission)

            # Call original function
            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: Role) -> Callable:
    """
    Decorator to require a specific role for a function.

    Args:
        role: Required role

    Returns:
        Decorator function

    Example:
        @require_role(Role.ADMIN)
        def delete_user(user_id: str, target_user_id: str):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract user_id from arguments
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            
            if not user_id:
                raise AuthorizationError(
                    message="User ID required for authorization",
                )

            # Get access control manager from kwargs
            acm = kwargs.get("access_control_manager")
            if not acm:
                raise RuntimeError(
                    "AccessControlManager not provided in function call"
                )

            # Check role
            user_role = acm.get_user_role(user_id)
            if user_role != role:
                logger.warning(
                    f"Access denied: User {user_id} has role {user_role.value}, "
                    f"but {role.value} required"
                )
                raise AuthorizationError(
                    message=f"Access denied: {role.value} role required",
                    details={
                        "user_id": user_id,
                        "user_role": user_role.value,
                        "required_role": role.value,
                    },
                )

            # Call original function
            return func(*args, **kwargs)

        return wrapper
    return decorator
