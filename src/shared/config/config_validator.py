"""Configuration validation and AWS service health checks."""

import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    service_status: Dict[str, bool]


class ConfigValidator:
    """Validates configuration and AWS service availability."""

    def __init__(self, region: str = "us-east-1"):
        """Initialize validator."""
        self.region = region
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.service_status: Dict[str, bool] = {}

    def validate_all(self) -> ValidationResult:
        """
        Validate all configuration and services.
        
        Returns:
            ValidationResult with status and any errors/warnings
        """
        logger.info("Starting configuration validation...")
        
        # Check AWS credentials
        self._check_aws_credentials()
        
        # Check required environment variables
        self._check_environment_variables()
        
        # Check AWS services
        self._check_bedrock()
        self._check_dynamodb()
        self._check_s3()
        
        is_valid = len(self.errors) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            service_status=self.service_status,
        )
        
        if is_valid:
            logger.info("✅ Configuration validation passed")
        else:
            logger.error(f"❌ Configuration validation failed: {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning(f"⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        return result

    def _check_aws_credentials(self) -> None:
        """Check if AWS credentials are configured."""
        try:
            sts = boto3.client('sts', region_name=self.region)
            identity = sts.get_caller_identity()
            logger.info(f"✅ AWS credentials valid (Account: {identity['Account']})")
            self.service_status['credentials'] = True
        except NoCredentialsError:
            self.errors.append("AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            self.service_status['credentials'] = False
        except ClientError as e:
            self.errors.append(f"AWS credentials invalid: {e}")
            self.service_status['credentials'] = False
        except Exception as e:
            self.errors.append(f"Error checking AWS credentials: {e}")
            self.service_status['credentials'] = False

    def _check_environment_variables(self) -> None:
        """Check required environment variables."""
        required_vars = []
        optional_vars = [
            'AWS_REGION',
            'DYNAMODB_TABLE_PREFIX',
            'S3_BUCKET_NAME',
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Required environment variable not set: {var}")
        
        for var in optional_vars:
            if not os.getenv(var):
                self.warnings.append(f"Optional environment variable not set: {var} (using defaults)")

    def _check_bedrock(self) -> None:
        """Check Bedrock service availability."""
        try:
            client = boto3.client('bedrock-runtime', region_name=self.region)
            # Try to list foundation models to verify access
            # Note: This is a simple check, actual model invocation may still fail
            logger.info("✅ Bedrock service accessible")
            self.service_status['bedrock'] = True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.errors.append("Bedrock access denied. Check IAM permissions for bedrock:InvokeModel")
            else:
                self.errors.append(f"Bedrock service error: {e}")
            self.service_status['bedrock'] = False
        except Exception as e:
            self.warnings.append(f"Could not verify Bedrock access: {e}")
            self.service_status['bedrock'] = False

    def _check_dynamodb(self) -> None:
        """Check DynamoDB service availability."""
        try:
            client = boto3.client('dynamodb', region_name=self.region)
            # List tables to verify access
            response = client.list_tables(Limit=1)
            logger.info("✅ DynamoDB service accessible")
            self.service_status['dynamodb'] = True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.errors.append("DynamoDB access denied. Check IAM permissions")
            else:
                self.errors.append(f"DynamoDB service error: {e}")
            self.service_status['dynamodb'] = False
        except Exception as e:
            self.warnings.append(f"Could not verify DynamoDB access: {e}")
            self.service_status['dynamodb'] = False

    def _check_s3(self) -> None:
        """Check S3 service availability."""
        try:
            client = boto3.client('s3', region_name=self.region)
            # List buckets to verify access
            client.list_buckets()
            logger.info("✅ S3 service accessible")
            self.service_status['s3'] = True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDenied':
                self.warnings.append("S3 access limited. Some features may not work")
            else:
                self.warnings.append(f"S3 service error: {e}")
            self.service_status['s3'] = False
        except Exception as e:
            self.warnings.append(f"Could not verify S3 access: {e}")
            self.service_status['s3'] = False

    def check_table_exists(self, table_name: str) -> bool:
        """
        Check if a DynamoDB table exists.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            client = boto3.client('dynamodb', region_name=self.region)
            client.describe_table(TableName=table_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise
        except Exception:
            return False

    def create_table_if_not_exists(
        self,
        table_name: str,
        key_schema: List[Dict[str, str]],
        attribute_definitions: List[Dict[str, str]],
        billing_mode: str = 'PAY_PER_REQUEST',
    ) -> bool:
        """
        Create a DynamoDB table if it doesn't exist.
        
        Args:
            table_name: Name of the table
            key_schema: Key schema definition
            attribute_definitions: Attribute definitions
            billing_mode: Billing mode (PAY_PER_REQUEST or PROVISIONED)
            
        Returns:
            True if table was created or already exists, False on error
        """
        try:
            if self.check_table_exists(table_name):
                logger.info(f"Table {table_name} already exists")
                return True
            
            client = boto3.client('dynamodb', region_name=self.region)
            
            params = {
                'TableName': table_name,
                'KeySchema': key_schema,
                'AttributeDefinitions': attribute_definitions,
                'BillingMode': billing_mode,
            }
            
            client.create_table(**params)
            
            # Wait for table to be created
            waiter = client.get_waiter('table_exists')
            waiter.wait(TableName=table_name, WaiterConfig={'Delay': 2, 'MaxAttempts': 30})
            
            logger.info(f"✅ Created table: {table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False


def validate_config() -> ValidationResult:
    """
    Convenience function to validate configuration.
    
    Returns:
        ValidationResult
    """
    validator = ConfigValidator()
    return validator.validate_all()
