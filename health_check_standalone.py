"""Standalone health check handler for Lambda."""

import json
from datetime import datetime
import os


def health_check_handler(event, context):
    """Lambda handler for basic health check."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "ai-learning-assistant",
            "version": "1.0.0",
            "environment": os.environ.get("ENVIRONMENT", "dev"),
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(health_status),
        }
    except Exception as e:
        return {
            "statusCode": 503,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "error": "UNHEALTHY",
                "message": str(e),
            }),
        }


def detailed_health_check_handler(event, context):
    """Lambda handler for detailed health check."""
    try:
        import boto3
        
        # Check AWS services
        aws_services = {}
        
        try:
            boto3.client("bedrock-runtime")
            aws_services["bedrock"] = {"status": "healthy"}
        except Exception as e:
            aws_services["bedrock"] = {"status": "unhealthy", "error": str(e)}
        
        try:
            boto3.client("s3")
            aws_services["s3"] = {"status": "healthy"}
        except Exception as e:
            aws_services["s3"] = {"status": "unhealthy", "error": str(e)}
        
        try:
            boto3.client("dynamodb")
            aws_services["dynamodb"] = {"status": "healthy"}
        except Exception as e:
            aws_services["dynamodb"] = {"status": "unhealthy", "error": str(e)}
        
        all_healthy = all(s["status"] == "healthy" for s in aws_services.values())
        
        health_status = {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "service": "ai-learning-assistant",
            "version": "1.0.0",
            "environment": os.environ.get("ENVIRONMENT", "dev"),
            "aws_services": aws_services,
        }

        return {
            "statusCode": 200 if all_healthy else 503,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(health_status),
        }
    except Exception as e:
        return {
            "statusCode": 503,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "error": "UNHEALTHY",
                "message": str(e),
            }),
        }


def readiness_check_handler(event, context):
    """Lambda handler for readiness check."""
    return health_check_handler(event, context)


def metrics_handler(event, context):
    """Lambda handler for metrics."""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "service": "ai-learning-assistant",
            "environment": os.environ.get("ENVIRONMENT", "dev"),
            "lambda": {
                "function_name": context.function_name if context else "unknown",
                "memory_limit_mb": context.memory_limit_in_mb if context else 0,
            },
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(metrics),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "error": "METRICS_ERROR",
                "message": str(e),
            }),
        }
