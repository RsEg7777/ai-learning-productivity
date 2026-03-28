"""Application initialization and health checks."""

import logging
import sys
from typing import Dict, Any
from ..shared.config.config_validator import validate_config
from ..shared.config.table_setup import setup_tables

logger = logging.getLogger(__name__)


class AppInitializer:
    """Initialize application and validate configuration."""

    def __init__(self, region: str = "us-east-1", table_prefix: str = "ai-learning-"):
        """Initialize app initializer."""
        self.region = region
        self.table_prefix = table_prefix
        self.validation_result = None

    def initialize(self, strict: bool = False) -> bool:
        """
        Initialize application with validation and setup.
        
        Args:
            strict: If True, fail on any errors. If False, continue with warnings.
            
        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("AI Learning Assistant - Initialization")
        logger.info("=" * 60)
        
        # Step 1: Validate configuration
        logger.info("\n[1/3] Validating configuration...")
        self.validation_result = validate_config()
        
        if not self.validation_result.is_valid:
            logger.error("Configuration validation failed!")
            if strict:
                logger.error("Strict mode enabled - aborting initialization")
                return False
            else:
                logger.warning("Continuing with errors (non-strict mode)")
        
        # Step 2: Setup DynamoDB tables
        logger.info("\n[2/3] Setting up DynamoDB tables...")
        if self.validation_result.service_status.get('dynamodb', False):
            tables_ok = setup_tables(region=self.region, table_prefix=self.table_prefix)
            if not tables_ok:
                logger.error("Failed to setup some tables")
                if strict:
                    return False
        else:
            logger.warning("Skipping table setup (DynamoDB not available)")
        
        # Step 3: Final health check
        logger.info("\n[3/3] Final health check...")
        health = self.get_health_status()
        
        logger.info("\n" + "=" * 60)
        logger.info("Initialization Summary:")
        logger.info("=" * 60)
        logger.info(f"Status: {'✅ READY' if health['status'] == 'healthy' else '⚠️  DEGRADED'}")
        logger.info(f"Errors: {len(self.validation_result.errors)}")
        logger.info(f"Warnings: {len(self.validation_result.warnings)}")
        logger.info("\nService Status:")
        for service, status in self.validation_result.service_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"  {status_icon} {service}")
        logger.info("=" * 60 + "\n")
        
        return health['status'] in ['healthy', 'degraded']

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status.
        
        Returns:
            Dictionary with health information
        """
        if not self.validation_result:
            return {
                'status': 'unknown',
                'message': 'Not initialized',
                'services': {},
            }
        
        # Determine overall status
        if len(self.validation_result.errors) == 0:
            if len(self.validation_result.warnings) == 0:
                status = 'healthy'
                message = 'All systems operational'
            else:
                status = 'degraded'
                message = f'{len(self.validation_result.warnings)} warnings present'
        else:
            status = 'unhealthy'
            message = f'{len(self.validation_result.errors)} errors present'
        
        return {
            'status': status,
            'message': message,
            'services': self.validation_result.service_status,
            'errors': self.validation_result.errors,
            'warnings': self.validation_result.warnings,
        }


# Global initializer instance
_initializer = None


def initialize_app(region: str = "us-east-1", table_prefix: str = "ai-learning-", strict: bool = False) -> bool:
    """
    Initialize the application.
    
    Args:
        region: AWS region
        table_prefix: Prefix for DynamoDB tables
        strict: If True, fail on any errors
        
    Returns:
        True if successful, False otherwise
    """
    global _initializer
    _initializer = AppInitializer(region=region, table_prefix=table_prefix)
    return _initializer.initialize(strict=strict)


def get_health_status() -> Dict[str, Any]:
    """
    Get current health status.
    
    Returns:
        Dictionary with health information
    """
    global _initializer
    if _initializer is None:
        return {
            'status': 'unknown',
            'message': 'Application not initialized',
            'services': {},
        }
    return _initializer.get_health_status()
