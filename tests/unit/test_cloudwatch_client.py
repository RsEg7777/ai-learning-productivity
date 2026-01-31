"""Unit tests for CloudWatch client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from src.shared.aws_clients.cloudwatch_client import CloudWatchClient
from src.shared.utils.errors import AWSServiceError


class TestCloudWatchClient:
    """Test CloudWatchClient class."""

    @patch("boto3.client")
    def test_initialization(self, mock_boto_client):
        """Test CloudWatch client initialization."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient(
            log_group_name="/test/logs",
            region_name="us-west-2",
        )

        assert client.log_group_name == "/test/logs"
        assert client.region_name == "us-west-2"
        assert mock_boto_client.call_count == 2

    @patch("boto3.client")
    def test_ensure_log_group_exists_creates_new(self, mock_boto_client):
        """Test log group creation when it doesn't exist."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()

        mock_logs.create_log_group.assert_called_once_with(
            logGroupName="/aws/ai-learning-assistant"
        )

    @patch("boto3.client")
    def test_ensure_log_group_exists_already_exists(self, mock_boto_client):
        """Test log group creation when it already exists."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]
        
        error = ClientError(
            {"Error": {"Code": "ResourceAlreadyExistsException"}},
            "create_log_group",
        )
        mock_logs.create_log_group.side_effect = error

        # Should not raise exception
        client = CloudWatchClient()
        assert client is not None

    @patch("boto3.client")
    def test_put_log_events(self, mock_boto_client):
        """Test putting log events."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()
        
        events = [
            {"timestamp": 1234567890000, "message": "Test message 1"},
            {"timestamp": 1234567891000, "message": "Test message 2"},
        ]

        client.put_log_events("test-stream", events)

        # Verify log stream creation was attempted
        mock_logs.create_log_stream.assert_called_once()
        
        # Verify log events were put
        mock_logs.put_log_events.assert_called_once()
        call_args = mock_logs.put_log_events.call_args[1]
        assert call_args["logGroupName"] == "/aws/ai-learning-assistant"
        assert call_args["logStreamName"] == "test-stream"
        assert len(call_args["logEvents"]) == 2

    @patch("boto3.client")
    def test_put_log_events_error(self, mock_boto_client):
        """Test error handling when putting log events fails."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        error = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "put_log_events",
        )
        mock_logs.put_log_events.side_effect = error

        client = CloudWatchClient()
        events = [{"timestamp": 1234567890000, "message": "Test"}]

        with pytest.raises(AWSServiceError) as exc_info:
            client.put_log_events("test-stream", events)

        assert "Failed to put log events" in str(exc_info.value)

    @patch("boto3.client")
    def test_put_metric_data(self, mock_boto_client):
        """Test putting metric data."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()
        
        dimensions = [
            {"Name": "Service", "Value": "ContentProcessing"},
            {"Name": "Operation", "Value": "ProcessPDF"},
        ]

        client.put_metric_data(
            namespace="AILearningAssistant",
            metric_name="ProcessingDuration",
            value=1234.5,
            unit="Milliseconds",
            dimensions=dimensions,
        )

        mock_metrics.put_metric_data.assert_called_once()
        call_args = mock_metrics.put_metric_data.call_args[1]
        assert call_args["Namespace"] == "AILearningAssistant"
        assert len(call_args["MetricData"]) == 1
        assert call_args["MetricData"][0]["MetricName"] == "ProcessingDuration"
        assert call_args["MetricData"][0]["Value"] == 1234.5
        assert call_args["MetricData"][0]["Unit"] == "Milliseconds"

    @patch("boto3.client")
    def test_put_metric_data_error(self, mock_boto_client):
        """Test error handling when putting metric data fails."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        error = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid metric"}},
            "put_metric_data",
        )
        mock_metrics.put_metric_data.side_effect = error

        client = CloudWatchClient()

        with pytest.raises(AWSServiceError) as exc_info:
            client.put_metric_data(
                namespace="Test",
                metric_name="TestMetric",
                value=100,
            )

        assert "Failed to put metric data" in str(exc_info.value)

    @patch("boto3.client")
    def test_log_error(self, mock_boto_client):
        """Test logging error to CloudWatch."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()
        
        client.log_error(
            error_id="ERR-123",
            error_type="ValidationError",
            error_message="Invalid input",
            severity="high",
            context={"user_id": "user123", "operation": "validate_input"},
        )

        mock_logs.put_log_events.assert_called_once()
        call_args = mock_logs.put_log_events.call_args[1]
        assert call_args["logStreamName"] == "errors"

    @patch("boto3.client")
    def test_log_operation(self, mock_boto_client):
        """Test logging operation to CloudWatch."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()
        
        client.log_operation(
            operation="process_content",
            status="success",
            duration_ms=1234.5,
            user_id="user123",
            metadata={"content_type": "pdf"},
        )

        # Verify log event was created
        mock_logs.put_log_events.assert_called_once()
        
        # Verify metric was created
        mock_metrics.put_metric_data.assert_called_once()
        call_args = mock_metrics.put_metric_data.call_args[1]
        assert call_args["Namespace"] == "AILearningAssistant/Operations"

    @patch("boto3.client")
    def test_query_logs(self, mock_boto_client):
        """Test querying CloudWatch logs."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        mock_logs.filter_log_events.return_value = {
            "events": [
                {"timestamp": 1234567890000, "message": "Log 1"},
                {"timestamp": 1234567891000, "message": "Log 2"},
            ]
        }

        client = CloudWatchClient()
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        results = client.query_logs(
            log_stream_name="test-stream",
            start_time=start_time,
            end_time=end_time,
            filter_pattern="ERROR",
            limit=50,
        )

        assert len(results) == 2
        mock_logs.filter_log_events.assert_called_once()

    @patch("boto3.client")
    def test_query_logs_error(self, mock_boto_client):
        """Test error handling when querying logs fails."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        error = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
            "filter_log_events",
        )
        mock_logs.filter_log_events.side_effect = error

        client = CloudWatchClient()

        with pytest.raises(AWSServiceError) as exc_info:
            client.query_logs("test-stream")

        assert "Failed to query logs" in str(exc_info.value)

    @patch("boto3.client")
    def test_get_metric_statistics(self, mock_boto_client):
        """Test getting metric statistics."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        mock_metrics.get_metric_statistics.return_value = {
            "Datapoints": [
                {"Timestamp": datetime.utcnow(), "Average": 123.45},
                {"Timestamp": datetime.utcnow(), "Average": 234.56},
            ]
        }

        client = CloudWatchClient()
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        results = client.get_metric_statistics(
            namespace="AILearningAssistant",
            metric_name="ProcessingDuration",
            start_time=start_time,
            end_time=end_time,
            period=300,
            statistics=["Average", "Maximum"],
        )

        assert len(results) == 2
        mock_metrics.get_metric_statistics.assert_called_once()

    @patch("boto3.client")
    def test_get_metric_statistics_error(self, mock_boto_client):
        """Test error handling when getting metric statistics fails."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        error = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid param"}},
            "get_metric_statistics",
        )
        mock_metrics.get_metric_statistics.side_effect = error

        client = CloudWatchClient()
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        with pytest.raises(AWSServiceError) as exc_info:
            client.get_metric_statistics(
                namespace="Test",
                metric_name="TestMetric",
                start_time=start_time,
                end_time=end_time,
            )

        assert "Failed to get metric statistics" in str(exc_info.value)

    @patch("boto3.client")
    def test_create_alarm(self, mock_boto_client):
        """Test creating CloudWatch alarm."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()
        
        dimensions = [{"Name": "Service", "Value": "ContentProcessing"}]
        alarm_actions = ["arn:aws:sns:us-east-1:123456789:alerts"]

        client.create_alarm(
            alarm_name="HighErrorRate",
            metric_name="ErrorCount",
            namespace="AILearningAssistant",
            threshold=10.0,
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=2,
            period=300,
            statistic="Sum",
            dimensions=dimensions,
            alarm_actions=alarm_actions,
        )

        mock_metrics.put_metric_alarm.assert_called_once()
        call_args = mock_metrics.put_metric_alarm.call_args[1]
        assert call_args["AlarmName"] == "HighErrorRate"
        assert call_args["Threshold"] == 10.0

    @patch("boto3.client")
    def test_create_alarm_error(self, mock_boto_client):
        """Test error handling when creating alarm fails."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        error = ClientError(
            {"Error": {"Code": "LimitExceededException", "Message": "Too many alarms"}},
            "put_metric_alarm",
        )
        mock_metrics.put_metric_alarm.side_effect = error

        client = CloudWatchClient()

        with pytest.raises(AWSServiceError) as exc_info:
            client.create_alarm(
                alarm_name="TestAlarm",
                metric_name="TestMetric",
                namespace="Test",
                threshold=100.0,
            )

        assert "Failed to create alarm" in str(exc_info.value)

    @patch("boto3.client")
    def test_log_events_sorting(self, mock_boto_client):
        """Test that log events are sorted by timestamp."""
        mock_logs = Mock()
        mock_metrics = Mock()
        mock_boto_client.side_effect = [mock_logs, mock_metrics]

        client = CloudWatchClient()
        
        # Events in wrong order
        events = [
            {"timestamp": 1234567892000, "message": "Third"},
            {"timestamp": 1234567890000, "message": "First"},
            {"timestamp": 1234567891000, "message": "Second"},
        ]

        client.put_log_events("test-stream", events)

        # Verify events were sorted
        call_args = mock_logs.put_log_events.call_args[1]
        log_events = call_args["logEvents"]
        assert log_events[0]["timestamp"] == 1234567890000
        assert log_events[1]["timestamp"] == 1234567891000
        assert log_events[2]["timestamp"] == 1234567892000
