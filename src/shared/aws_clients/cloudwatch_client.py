"""AWS CloudWatch client for logging and metrics."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from botocore.exceptions import ClientError
import boto3

from src.shared.utils.errors import AWSServiceError

logger = logging.getLogger(__name__)


class CloudWatchClient:
    """Client for AWS CloudWatch Logs and Metrics."""

    def __init__(
        self,
        log_group_name: str = "/aws/ai-learning-assistant",
        region_name: str = "us-east-1",
    ) -> None:
        """
        Initialize CloudWatch client.

        Args:
            log_group_name: CloudWatch log group name
            region_name: AWS region name
        """
        self.log_group_name = log_group_name
        self.region_name = region_name
        
        # Initialize CloudWatch Logs client
        self.logs_client = boto3.client("logs", region_name=region_name)
        
        # Initialize CloudWatch Metrics client
        self.metrics_client = boto3.client("cloudwatch", region_name=region_name)
        
        # Ensure log group exists
        self._ensure_log_group_exists()

    def _ensure_log_group_exists(self) -> None:
        """Ensure CloudWatch log group exists."""
        try:
            self.logs_client.create_log_group(logGroupName=self.log_group_name)
            logger.info(f"Created CloudWatch log group: {self.log_group_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                logger.warning(f"Could not create log group: {str(e)}")

    def put_log_events(
        self,
        log_stream_name: str,
        events: List[Dict[str, Any]],
    ) -> None:
        """
        Put log events to CloudWatch Logs.

        Args:
            log_stream_name: Name of the log stream
            events: List of log events with 'timestamp' and 'message' keys

        Raises:
            AWSServiceError: If putting log events fails
        """
        try:
            # Ensure log stream exists
            self._ensure_log_stream_exists(log_stream_name)
            
            # Format events for CloudWatch
            formatted_events = [
                {
                    "timestamp": int(event.get("timestamp", datetime.utcnow().timestamp() * 1000)),
                    "message": str(event.get("message", "")),
                }
                for event in events
            ]
            
            # Sort events by timestamp
            formatted_events.sort(key=lambda x: x["timestamp"])
            
            # Put log events
            self.logs_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=log_stream_name,
                logEvents=formatted_events,
            )

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to put log events: {str(e)}",
                service="CloudWatch Logs",
                operation="put_log_events",
                details={"log_stream": log_stream_name},
            )

    def _ensure_log_stream_exists(self, log_stream_name: str) -> None:
        """Ensure CloudWatch log stream exists."""
        try:
            self.logs_client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=log_stream_name,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                logger.warning(f"Could not create log stream: {str(e)}")

    def put_metric_data(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[List[Dict[str, str]]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Put metric data to CloudWatch Metrics.

        Args:
            namespace: Metric namespace
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (e.g., 'Count', 'Seconds', 'Bytes')
            dimensions: List of metric dimensions
            timestamp: Metric timestamp (defaults to current time)

        Raises:
            AWSServiceError: If putting metric data fails
        """
        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": timestamp or datetime.utcnow(),
            }
            
            if dimensions:
                metric_data["Dimensions"] = dimensions

            self.metrics_client.put_metric_data(
                Namespace=namespace,
                MetricData=[metric_data],
            )

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to put metric data: {str(e)}",
                service="CloudWatch Metrics",
                operation="put_metric_data",
                details={"metric_name": metric_name},
            )

    def log_error(
        self,
        error_id: str,
        error_type: str,
        error_message: str,
        severity: str,
        context: Dict[str, Any],
        log_stream_name: str = "errors",
    ) -> None:
        """
        Log error to CloudWatch with structured format.

        Args:
            error_id: Unique error identifier
            error_type: Type of error
            error_message: Error message
            severity: Error severity level
            context: Error context information
            log_stream_name: Log stream name

        Raises:
            AWSServiceError: If logging fails
        """
        import json
        
        log_entry = {
            "error_id": error_id,
            "error_type": error_type,
            "error_message": error_message,
            "severity": severity,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        event = {
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "message": json.dumps(log_entry),
        }
        
        self.put_log_events(log_stream_name, [event])

    def log_operation(
        self,
        operation: str,
        status: str,
        duration_ms: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        log_stream_name: str = "operations",
    ) -> None:
        """
        Log operation to CloudWatch with structured format.

        Args:
            operation: Operation name
            status: Operation status (success, failure)
            duration_ms: Operation duration in milliseconds
            user_id: User identifier
            metadata: Additional metadata
            log_stream_name: Log stream name

        Raises:
            AWSServiceError: If logging fails
        """
        import json
        
        log_entry = {
            "operation": operation,
            "status": status,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        event = {
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "message": json.dumps(log_entry),
        }
        
        self.put_log_events(log_stream_name, [event])
        
        # Also put metric for operation duration
        dimensions = [{"Name": "Operation", "Value": operation}]
        if user_id:
            dimensions.append({"Name": "UserId", "Value": user_id})
        
        self.put_metric_data(
            namespace="AILearningAssistant/Operations",
            metric_name="OperationDuration",
            value=duration_ms,
            unit="Milliseconds",
            dimensions=dimensions,
        )

    def query_logs(
        self,
        log_stream_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        filter_pattern: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query CloudWatch logs.

        Args:
            log_stream_name: Name of the log stream
            start_time: Start time for query
            end_time: End time for query
            filter_pattern: CloudWatch Logs filter pattern
            limit: Maximum number of results

        Returns:
            List of log events

        Raises:
            AWSServiceError: If query fails
        """
        try:
            params = {
                "logGroupName": self.log_group_name,
                "logStreamNames": [log_stream_name],
                "limit": limit,
            }
            
            if start_time:
                params["startTime"] = int(start_time.timestamp() * 1000)
            
            if end_time:
                params["endTime"] = int(end_time.timestamp() * 1000)
            
            if filter_pattern:
                params["filterPattern"] = filter_pattern

            response = self.logs_client.filter_log_events(**params)
            
            return response.get("events", [])

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to query logs: {str(e)}",
                service="CloudWatch Logs",
                operation="filter_log_events",
                details={"log_stream": log_stream_name},
            )

    def get_metric_statistics(
        self,
        namespace: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: Optional[List[str]] = None,
        dimensions: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get metric statistics from CloudWatch.

        Args:
            namespace: Metric namespace
            metric_name: Name of the metric
            start_time: Start time for statistics
            end_time: End time for statistics
            period: Period in seconds (minimum 60)
            statistics: List of statistics to retrieve (e.g., ['Average', 'Sum'])
            dimensions: List of metric dimensions

        Returns:
            List of metric data points

        Raises:
            AWSServiceError: If getting statistics fails
        """
        try:
            params = {
                "Namespace": namespace,
                "MetricName": metric_name,
                "StartTime": start_time,
                "EndTime": end_time,
                "Period": period,
                "Statistics": statistics or ["Average", "Sum", "Maximum", "Minimum"],
            }
            
            if dimensions:
                params["Dimensions"] = dimensions

            response = self.metrics_client.get_metric_statistics(**params)
            
            return response.get("Datapoints", [])

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to get metric statistics: {str(e)}",
                service="CloudWatch Metrics",
                operation="get_metric_statistics",
                details={"metric_name": metric_name},
            )

    def create_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        namespace: str,
        threshold: float,
        comparison_operator: str = "GreaterThanThreshold",
        evaluation_periods: int = 2,
        period: int = 300,
        statistic: str = "Average",
        dimensions: Optional[List[Dict[str, str]]] = None,
        alarm_actions: Optional[List[str]] = None,
    ) -> None:
        """
        Create CloudWatch alarm.

        Args:
            alarm_name: Name of the alarm
            metric_name: Name of the metric to monitor
            namespace: Metric namespace
            threshold: Alarm threshold value
            comparison_operator: Comparison operator (e.g., 'GreaterThanThreshold')
            evaluation_periods: Number of periods to evaluate
            period: Period in seconds
            statistic: Statistic to use (e.g., 'Average', 'Sum')
            dimensions: List of metric dimensions
            alarm_actions: List of actions to take when alarm triggers

        Raises:
            AWSServiceError: If creating alarm fails
        """
        try:
            params = {
                "AlarmName": alarm_name,
                "MetricName": metric_name,
                "Namespace": namespace,
                "Threshold": threshold,
                "ComparisonOperator": comparison_operator,
                "EvaluationPeriods": evaluation_periods,
                "Period": period,
                "Statistic": statistic,
            }
            
            if dimensions:
                params["Dimensions"] = dimensions
            
            if alarm_actions:
                params["AlarmActions"] = alarm_actions

            self.metrics_client.put_metric_alarm(**params)
            
            logger.info(f"Created CloudWatch alarm: {alarm_name}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to create alarm: {str(e)}",
                service="CloudWatch Metrics",
                operation="put_metric_alarm",
                details={"alarm_name": alarm_name},
            )
