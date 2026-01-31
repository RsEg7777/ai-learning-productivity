"""Unit tests for access control module."""

import pytest
from unittest.mock import Mock, MagicMock
from botocore.exceptions import ClientError

from src.services.user_management.access_control import (
    AccessControlManager,
    Role,
    Permission,
    ROLE_PERMISSIONS,
    require_permission,
    require_role,
)
from src.shared.utils.errors import AuthorizationError, AWSServiceError


@pytest.fixture
def mock_roles_table():
    """Mock roles DynamoDB table."""
    return Mock()


@pytest.fixture
def access_control_manager(mock_roles_table):
    """Create access control manager with mocked dependencies."""
    return AccessControlManager(roles_table=mock_roles_table)


class TestAccessControlManager:
    """Test AccessControlManager class."""

    def test_assign_role_success(self, access_control_manager, mock_roles_table):
        """Test successful role assignment."""
        user_id = "user123"
        role = Role.INSTRUCTOR

        access_control_manager.assign_role(user_id, role)

        mock_roles_table.put_item.assert_called_once()
        call_args = mock_roles_table.put_item.call_args[0][0]
        assert call_args["user_id"] == user_id
        assert call_args["role"] == role.value

    def test_assign_role_failure(self, access_control_manager, mock_roles_table):
        """Test role assignment failure."""
        mock_roles_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "PutItem",
        )

        with pytest.raises(AWSServiceError):
            access_control_manager.assign_role("user123", Role.ADMIN)

    def test_get_user_role_existing(self, access_control_manager, mock_roles_table):
        """Test getting existing user role."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "admin",
        }

        role = access_control_manager.get_user_role("user123")

        assert role == Role.ADMIN
        mock_roles_table.get_item.assert_called_once()

    def test_get_user_role_default(self, access_control_manager, mock_roles_table):
        """Test getting default role for new user."""
        mock_roles_table.get_item.return_value = None

        role = access_control_manager.get_user_role("user123")

        assert role == Role.STUDENT

    def test_get_user_permissions_admin(self, access_control_manager, mock_roles_table):
        """Test getting admin permissions."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "admin",
        }

        permissions = access_control_manager.get_user_permissions("user123")

        assert Permission.SYSTEM_ADMIN in permissions
        assert Permission.USER_DELETE in permissions
        assert Permission.AUDIT_READ in permissions

    def test_get_user_permissions_student(self, access_control_manager, mock_roles_table):
        """Test getting student permissions."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "student",
        }

        permissions = access_control_manager.get_user_permissions("user123")

        assert Permission.CONTENT_READ in permissions
        assert Permission.CONTENT_WRITE in permissions
        assert Permission.SYSTEM_ADMIN not in permissions
        assert Permission.USER_DELETE not in permissions

    def test_has_permission_true(self, access_control_manager, mock_roles_table):
        """Test has_permission returns True when user has permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "admin",
        }

        result = access_control_manager.has_permission(
            "user123", Permission.CONTENT_DELETE
        )

        assert result is True

    def test_has_permission_false(self, access_control_manager, mock_roles_table):
        """Test has_permission returns False when user lacks permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "student",
        }

        result = access_control_manager.has_permission(
            "user123", Permission.SYSTEM_ADMIN
        )

        assert result is False

    def test_require_permission_success(self, access_control_manager, mock_roles_table):
        """Test require_permission succeeds when user has permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "admin",
        }

        # Should not raise
        access_control_manager.require_permission(
            "user123", Permission.CONTENT_DELETE
        )

    def test_require_permission_failure(self, access_control_manager, mock_roles_table):
        """Test require_permission raises when user lacks permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "student",
        }

        with pytest.raises(AuthorizationError) as exc_info:
            access_control_manager.require_permission(
                "user123", Permission.SYSTEM_ADMIN
            )

        assert "Access denied" in str(exc_info.value)
        assert "system:admin" in str(exc_info.value)

    def test_check_resource_ownership_owner(
        self, access_control_manager, mock_roles_table
    ):
        """Test resource ownership check for owner."""
        # Owner should always have access
        access_control_manager.check_resource_ownership(
            user_id="user123",
            resource_owner_id="user123",
            permission=Permission.CONTENT_DELETE,
        )
        # Should not raise

    def test_check_resource_ownership_non_owner_with_permission(
        self, access_control_manager, mock_roles_table
    ):
        """Test resource ownership check for non-owner with permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "admin123",
            "role": "admin",
        }

        # Admin should have access to other users' content
        access_control_manager.check_resource_ownership(
            user_id="admin123",
            resource_owner_id="user123",
            permission=Permission.CONTENT_DELETE,
        )
        # Should not raise

    def test_check_resource_ownership_non_owner_without_permission(
        self, access_control_manager, mock_roles_table
    ):
        """Test resource ownership check for non-owner without permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user456",
            "role": "student",
        }

        # Student should not have access to other users' content
        with pytest.raises(AuthorizationError):
            access_control_manager.check_resource_ownership(
                user_id="user456",
                resource_owner_id="user123",
                permission=Permission.CONTENT_DELETE,
            )

    def test_revoke_role(self, access_control_manager, mock_roles_table):
        """Test role revocation."""
        access_control_manager.revoke_role("user123")

        mock_roles_table.put_item.assert_called_once()
        call_args = mock_roles_table.put_item.call_args[0][0]
        assert call_args["user_id"] == "user123"
        assert call_args["role"] == Role.STUDENT.value


class TestRolePermissions:
    """Test role-to-permission mappings."""

    def test_admin_has_all_permissions(self):
        """Test admin role has all permissions."""
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        
        # Admin should have system admin permission
        assert Permission.SYSTEM_ADMIN in admin_perms
        assert Permission.USER_DELETE in admin_perms
        assert Permission.AUDIT_READ in admin_perms

    def test_instructor_has_content_permissions(self):
        """Test instructor role has content management permissions."""
        instructor_perms = ROLE_PERMISSIONS[Role.INSTRUCTOR]
        
        assert Permission.CONTENT_WRITE in instructor_perms
        assert Permission.CONTENT_DELETE in instructor_perms
        assert Permission.QUIZ_GRADE in instructor_perms
        # But not system admin
        assert Permission.SYSTEM_ADMIN not in instructor_perms

    def test_student_has_basic_permissions(self):
        """Test student role has basic permissions."""
        student_perms = ROLE_PERMISSIONS[Role.STUDENT]
        
        assert Permission.CONTENT_READ in student_perms
        assert Permission.CONTENT_WRITE in student_perms
        assert Permission.QUIZ_READ in student_perms
        # But not delete or admin
        assert Permission.CONTENT_DELETE not in student_perms
        assert Permission.SYSTEM_ADMIN not in student_perms

    def test_guest_has_minimal_permissions(self):
        """Test guest role has minimal permissions."""
        guest_perms = ROLE_PERMISSIONS[Role.GUEST]
        
        assert Permission.CONTENT_READ in guest_perms
        assert Permission.QUIZ_READ in guest_perms
        # But not write permissions
        assert Permission.CONTENT_WRITE not in guest_perms
        assert Permission.QUIZ_WRITE not in guest_perms


class TestDecorators:
    """Test permission and role decorators."""

    def test_require_permission_decorator_success(self, mock_roles_table):
        """Test require_permission decorator allows access with permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "admin",
        }
        acm = AccessControlManager(mock_roles_table)

        @require_permission(Permission.CONTENT_DELETE)
        def delete_content(user_id: str, content_id: str, access_control_manager=None):
            return f"Deleted {content_id}"

        result = delete_content(
            user_id="user123",
            content_id="content456",
            access_control_manager=acm,
        )

        assert result == "Deleted content456"

    def test_require_permission_decorator_failure(self, mock_roles_table):
        """Test require_permission decorator denies access without permission."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "student",
        }
        acm = AccessControlManager(mock_roles_table)

        @require_permission(Permission.SYSTEM_ADMIN)
        def admin_action(user_id: str, access_control_manager=None):
            return "Admin action"

        with pytest.raises(AuthorizationError):
            admin_action(user_id="user123", access_control_manager=acm)

    def test_require_role_decorator_success(self, mock_roles_table):
        """Test require_role decorator allows access with correct role."""
        mock_roles_table.get_item.return_value = {
            "user_id": "admin123",
            "role": "admin",
        }
        acm = AccessControlManager(mock_roles_table)

        @require_role(Role.ADMIN)
        def admin_only_action(user_id: str, access_control_manager=None):
            return "Admin action"

        result = admin_only_action(user_id="admin123", access_control_manager=acm)

        assert result == "Admin action"

    def test_require_role_decorator_failure(self, mock_roles_table):
        """Test require_role decorator denies access with wrong role."""
        mock_roles_table.get_item.return_value = {
            "user_id": "user123",
            "role": "student",
        }
        acm = AccessControlManager(mock_roles_table)

        @require_role(Role.ADMIN)
        def admin_only_action(user_id: str, access_control_manager=None):
            return "Admin action"

        with pytest.raises(AuthorizationError):
            admin_only_action(user_id="user123", access_control_manager=acm)
