"""User management service module."""

from src.services.user_management.user_service import UserService
from src.services.user_management.session_manager import SessionManager
from src.services.user_management.mfa_manager import MFAManager
from src.services.user_management.access_control import (
    AccessControlManager,
    Role,
    Permission,
    require_permission,
    require_role,
)
from src.services.user_management.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
)
from src.services.user_management.privacy_manager import (
    PrivacyManager,
    ConsentType,
    DataCategory,
    ConsentRecord,
)
from src.services.user_management.data_deletion_service import DataDeletionService
from src.services.user_management.data_export_service import DataExportService

__all__ = [
    "UserService",
    "SessionManager",
    "MFAManager",
    "AccessControlManager",
    "Role",
    "Permission",
    "require_permission",
    "require_role",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "PrivacyManager",
    "ConsentType",
    "DataCategory",
    "ConsentRecord",
    "DataDeletionService",
    "DataExportService",
]
