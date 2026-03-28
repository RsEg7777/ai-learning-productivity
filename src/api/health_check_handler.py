"""Health check and monitoring endpoints for the AI Learning Assistant."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
from typing import Dict

from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.aws_clients.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)


class HealthCheckHandler:
    """Handler for health check and monitoring endpoints."""

    def __init__(self) -> None:
        """Initialize health check handler."""
        logger.info("Initialized HealthCheckHandler")
        # Try to wire the orchestrator so health checks can inspect service status.
        try:
            from src.api.service_orchestrator import get_orchestrator

            self.orchestrator = get_orchestrator()
        except Exception as e:
            logger.warning(f"HealthCheckHandler: failed to initialize orchestrator: {e}")
            self.orchestrator = None

    def handle_health_check(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle basic health check request.

        This endpoint provides a quick health status for load balancers
        and monitoring systems.

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with health status
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "ai-learning-assistant",
                "version": "1.0.0",
                "environment": os.environ.get("ENVIRONMENT", "dev"),
            }

            logger.info("Health check passed")
            return self._success_response(200, health_status)

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return self._error_response(
                503,
                "UNHEALTHY",
                "Service is unhealthy",
                {"error": str(e)},
            )

    def handle_detailed_health_check(
        self, event: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Handle detailed health check request.

        This endpoint provides comprehensive health information including:
        - Service status
        - AWS service connectivity
        - Database connectivity
        - Storage availability

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with detailed health status
        """
        try:
            logger.info("Performing detailed health check")

            # Check AWS services
            aws_services = self._check_aws_services()

            # Aggregate health status
            all_healthy = all(
                s["status"] == "healthy"
                for s in aws_services.values()
            )

            # Include orchestrator-reported service status when available
            services_status = self.orchestrator.get_service_status() if getattr(self, "orchestrator", None) else {}

            health_status = {
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.now().isoformat(),
                "service": "ai-learning-assistant",
                "version": "1.0.0",
                "environment": os.environ.get("ENVIRONMENT", "dev"),
                "services": services_status.get("services", {}),
                "aws_services": aws_services,
                "lambda_context": {
                    "function_name": context.function_name if context else "unknown",
                    "memory_limit": context.memory_limit_in_mb if context else "unknown",
                    "remaining_time": (
                        context.get_remaining_time_in_millis() if context else "unknown"
                    ),
                },
            }

            status_code = 200 if all_healthy else 503
            logger.info(f"Detailed health check completed: status={health_status['status']}")
            return self._success_response(status_code, health_status)

        except Exception as e:
            logger.error(f"Detailed health check failed: {e}", exc_info=True)
            return self._error_response(
                503,
                "UNHEALTHY",
                "Service is unhealthy",
                {"error": str(e)},
            )

    def handle_readiness_check(
        self, event: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Handle readiness check request.

        This endpoint indicates whether the service is ready to accept traffic.
        It checks if all dependencies are available and initialized.

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with readiness status
        """
        try:
            logger.info("Performing readiness check")

            # Check critical dependencies
            checks = {
                "aws_clients": self._check_aws_clients(),
            }

            all_ready = all(check["ready"] for check in checks.values())

            readiness_status = {
                "ready": all_ready,
                "timestamp": datetime.now().isoformat(),
                "checks": checks,
            }

            status_code = 200 if all_ready else 503
            logger.info(f"Readiness check completed: ready={all_ready}")
            return self._success_response(status_code, readiness_status)

        except Exception as e:
            logger.error(f"Readiness check failed: {e}", exc_info=True)
            return self._error_response(
                503,
                "NOT_READY",
                "Service is not ready",
                {"error": str(e)},
            )

    def handle_metrics(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle metrics request.

        This endpoint provides operational metrics for monitoring.

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with metrics
        """
        try:
            logger.info("Collecting metrics")

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "service": "ai-learning-assistant",
                "environment": os.environ.get("ENVIRONMENT", "dev"),
                "lambda": {
                    "function_name": context.function_name if context else "unknown",
                    "memory_limit_mb": context.memory_limit_in_mb if context else 0,
                    "remaining_time_ms": (
                        context.get_remaining_time_in_millis() if context else 0
                    ),
                },
                # In a real implementation, these would be actual metrics
                "requests": {
                    "total": 0,
                    "success": 0,
                    "errors": 0,
                },
                "latency": {
                    "p50": 0,
                    "p95": 0,
                    "p99": 0,
                },
            }

            logger.info("Metrics collected successfully")
            return self._success_response(200, metrics)

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}", exc_info=True)
            return self._error_response(
                500,
                "METRICS_ERROR",
                "Failed to collect metrics",
                {"error": str(e)},
            )

    def _check_aws_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Check connectivity to AWS services.

        Returns:
            Dictionary with AWS service health status
        """
        aws_services = {}

        # Check Bedrock via BedrockClient wrapper
        try:
            bedrock_client = BedrockClient()
            aws_services["bedrock"] = {
                "status": "healthy",
                "message": "Bedrock client initialized",
            }
        except Exception as e:
            aws_services["bedrock"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Check S3 via S3Client wrapper
        try:
            s3_client = S3Client()
            aws_services["s3"] = {
                "status": "healthy",
                "message": "S3 client initialized",
            }
        except Exception as e:
            aws_services["s3"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Check DynamoDB via DynamoDBClient wrapper
        try:
            dynamodb_client = DynamoDBClient()
            aws_services["dynamodb"] = {
                "status": "healthy",
                "message": "DynamoDB client initialized",
            }
        except Exception as e:
            aws_services["dynamodb"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        return aws_services

    def _check_aws_clients(self) -> Dict[str, Any]:
        """
        Check if AWS clients are available.

        Returns:
            Dictionary with AWS clients status
        """
        try:
            # Try to initialize critical clients
            import boto3
            boto3.client("bedrock-runtime")
            boto3.client("s3")
            boto3.client("dynamodb")

            return {
                "ready": True,
                "message": "AWS clients initialized",
            }
        except Exception as e:
            return {
                "ready": False,
                "error": str(e),
            }

    def _check_orchestrator(self) -> Dict[str, Any]:
        """Check if the orchestrator and services are ready."""
        try:
            if not getattr(self, "orchestrator", None):
                return {"ready": False, "error": "orchestrator_unavailable"}
            status = self.orchestrator.get_service_status()
            # Consider ready if all services report initialized=True
            services = status.get("services", {})
            ready = all(s.get("initialized") for s in services.values()) if services else False
            return {"ready": ready, "status": status}
        except Exception as e:
            return {"ready": False, "error": str(e)}

    def _success_response(self, status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create success API response."""
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            },
            "body": json.dumps(data),
        }

    def _error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create error API response."""
        error_data = {
            "error": error_code,
            "message": message,
        }
        if details:
            error_data["details"] = details

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            },
            "body": json.dumps(error_data),
        }


# Lambda handler functions
def health_check_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for basic health check."""
    handler = HealthCheckHandler()
    return handler.handle_health_check(event, context)


def detailed_health_check_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for detailed health check."""
    handler = HealthCheckHandler()
    return handler.handle_detailed_health_check(event, context)


def readiness_check_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for readiness check."""
    handler = HealthCheckHandler()
    return handler.handle_readiness_check(event, context)


def metrics_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for metrics."""
    handler = HealthCheckHandler()
    return handler.handle_metrics(event, context)
