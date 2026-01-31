"""Integration tests for service wiring and communication."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.api.service_orchestrator import ServiceOrchestrator, get_orchestrator
from src.api.health_check_handler import HealthCheckHandler
from src.shared.utils.errors import ServiceCommunicationError


class TestServiceOrchestrator:
    """Test service orchestrator functionality."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return ServiceOrchestrator()

    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes all services."""
        assert orchestrator.text_processor is not None
        assert orchestrator.pdf_processor is not None
        assert orchestrator.video_processor is not None
        assert orchestrator.flashcard_generator is not None
        assert orchestrator.quiz_generator is not None
        assert orchestrator.code_analyzer is not None
        assert orchestrator.voice_service is not None
        assert orchestrator.multilingual_service is not None

    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns singleton instance."""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        assert orchestrator1 is orchestrator2

    @patch('src.api.service_orchestrator.TextProcessor')
    @patch('src.api.service_orchestrator.FlashcardGenerator')
    @patch('src.api.service_orchestrator.QuizGenerator')
    def test_process_content_end_to_end(
        self,
        mock_quiz_gen,
        mock_flashcard_gen,
        mock_text_proc,
        orchestrator,
    ):
        """Test end-to-end content processing workflow."""
        # Mock processed content
        mock_processed = Mock()
        mock_processed.id = "content-123"
        mock_processed.summary.text = "Test summary"
        mock_processed.key_points = ["Point 1", "Point 2"]
        mock_processed.concepts = [
            Mock(name="Concept 1", description="Description 1")
        ]
        mock_text_proc.return_value.process_text.return_value = mock_processed

        # Mock quiz
        mock_quiz = Mock()
        mock_quiz.id = "quiz-123"
        mock_quiz.title = "Test Quiz"
        mock_quiz.questions = [Mock(), Mock()]
        mock_quiz_gen.return_value.generate_quiz.return_value = mock_quiz

        # Mock flashcards
        mock_flashcards = [
            Mock(id="fc-1", question="Q1", answer="A1"),
            Mock(id="fc-2", question="Q2", answer="A2"),
        ]
        mock_flashcard_gen.return_value.generate_flashcards.return_value = mock_flashcards

        # Execute workflow
        result = orchestrator.process_content_end_to_end(
            content="Test content",
            content_type="text",
            language="en",
            generate_quiz=True,
            generate_flashcards=True,
        )

        # Verify result structure
        assert "processed_content" in result
        assert "quiz" in result
        assert "flashcards" in result
        assert "processing_time" in result

        # Verify processed content
        assert result["processed_content"]["id"] == "content-123"
        assert result["processed_content"]["summary"] == "Test summary"

        # Verify quiz
        assert result["quiz"]["id"] == "quiz-123"
        assert result["quiz"]["question_count"] == 2

        # Verify flashcards
        assert result["flashcards"]["count"] == 2

    def test_process_content_unsupported_type(self, orchestrator):
        """Test that unsupported content type raises error."""
        with pytest.raises(ServiceCommunicationError) as exc_info:
            orchestrator.process_content_end_to_end(
                content="Test content",
                content_type="unsupported",
                language="en",
            )
        
        assert "Unsupported content type" in str(exc_info.value)

    @patch('src.api.service_orchestrator.VoiceInterfaceService')
    @patch('src.api.service_orchestrator.TextProcessor')
    @patch('src.api.service_orchestrator.FlashcardGenerator')
    def test_process_voice_to_learning_materials(
        self,
        mock_flashcard_gen,
        mock_text_proc,
        mock_voice_service,
        orchestrator,
    ):
        """Test voice-to-learning-materials workflow."""
        # Mock transcription
        mock_transcription = Mock()
        mock_transcription.text = "Transcribed text"
        mock_transcription.confidence = 0.95
        mock_voice_service.return_value.process_voice_input.return_value = mock_transcription

        # Mock processed content
        mock_processed = Mock()
        mock_processed.summary.text = "Summary"
        mock_processed.key_points = ["Point 1"]
        mock_text_proc.return_value.process_text.return_value = mock_processed

        # Mock flashcards
        mock_flashcards = [Mock(question="Q1", answer="A1")]
        mock_flashcard_gen.return_value.generate_flashcards.return_value = mock_flashcards

        # Execute workflow
        result = orchestrator.process_voice_to_learning_materials(
            audio_data=b"audio data",
            language_code="en-US",
        )

        # Verify result
        assert "transcription" in result
        assert result["transcription"]["text"] == "Transcribed text"
        assert "summary" in result
        assert "flashcards" in result

    @patch('src.api.service_orchestrator.CodeAnalyzer')
    @patch('src.api.service_orchestrator.VoiceInterfaceService')
    def test_analyze_code_with_explanation(
        self,
        mock_voice_service,
        mock_code_analyzer,
        orchestrator,
    ):
        """Test code analysis with audio explanation workflow."""
        # Mock code analysis
        mock_analysis = Mock()
        mock_analysis.explanation = "Code explanation"
        mock_analysis.improvements = [Mock(), Mock()]
        mock_analysis.issues = [Mock()]
        mock_analysis.complexity.cyclomatic_complexity = 5
        mock_analysis.complexity.cognitive_complexity = 3
        mock_code_analyzer.return_value.analyze_code.return_value = mock_analysis

        # Mock audio generation
        mock_audio = Mock()
        mock_audio.audio_data = b"audio data"
        mock_voice_service.return_value.generate_audio_response.return_value = mock_audio

        # Execute workflow with audio
        result = orchestrator.analyze_code_with_explanation(
            code="def test(): pass",
            language="python",
            generate_audio=True,
            audio_language="en-US",
        )

        # Verify result
        assert result["explanation"] == "Code explanation"
        assert result["improvements_count"] == 2
        assert result["issues_count"] == 1
        assert "audio_explanation" in result
        assert result["audio_explanation"]["available"] is True

    def test_get_service_status(self, orchestrator):
        """Test service status retrieval."""
        status = orchestrator.get_service_status()

        # Verify status structure
        assert "timestamp" in status
        assert "services" in status

        # Verify all services are reported
        expected_services = [
            "text_processor",
            "pdf_processor",
            "video_processor",
            "flashcard_generator",
            "quiz_generator",
            "code_analyzer",
            "voice_service",
            "multilingual_service",
        ]

        for service_name in expected_services:
            assert service_name in status["services"]
            assert "status" in status["services"][service_name]
            assert "initialized" in status["services"][service_name]


class TestHealthCheckHandler:
    """Test health check handler functionality."""

    @pytest.fixture
    def handler(self):
        """Create health check handler instance."""
        return HealthCheckHandler()

    @pytest.fixture
    def mock_event(self):
        """Create mock API Gateway event."""
        return {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {},
            "queryStringParameters": None,
            "body": None,
        }

    @pytest.fixture
    def mock_context(self):
        """Create mock Lambda context."""
        context = Mock()
        context.function_name = "test-function"
        context.memory_limit_in_mb = 512
        context.get_remaining_time_in_millis = Mock(return_value=30000)
        return context

    def test_health_check_handler_initialization(self, handler):
        """Test that health check handler initializes properly."""
        assert handler.orchestrator is not None

    def test_handle_health_check_success(self, handler, mock_event, mock_context):
        """Test successful health check."""
        response = handler.handle_health_check(mock_event, mock_context)

        # Verify response structure
        assert response["statusCode"] == 200
        assert "body" in response
        
        import json
        body = json.loads(response["body"])
        
        assert body["status"] == "healthy"
        assert "timestamp" in body
        assert body["service"] == "ai-learning-assistant"

    def test_handle_detailed_health_check(self, handler, mock_event, mock_context):
        """Test detailed health check."""
        response = handler.handle_detailed_health_check(mock_event, mock_context)

        # Verify response
        assert response["statusCode"] in [200, 503]
        assert "body" in response
        
        import json
        body = json.loads(response["body"])
        
        assert "status" in body
        assert "services" in body
        assert "aws_services" in body
        assert "lambda_context" in body

    def test_handle_readiness_check(self, handler, mock_event, mock_context):
        """Test readiness check."""
        response = handler.handle_readiness_check(mock_event, mock_context)

        # Verify response
        assert response["statusCode"] in [200, 503]
        assert "body" in response
        
        import json
        body = json.loads(response["body"])
        
        assert "ready" in body
        assert "checks" in body

    def test_handle_metrics(self, handler, mock_event, mock_context):
        """Test metrics collection."""
        response = handler.handle_metrics(mock_event, mock_context)

        # Verify response
        assert response["statusCode"] == 200
        assert "body" in response
        
        import json
        body = json.loads(response["body"])
        
        assert "timestamp" in body
        assert "service" in body
        assert "lambda" in body

    @patch('src.api.health_check_handler.BedrockClient')
    @patch('src.api.health_check_handler.S3Client')
    @patch('src.api.health_check_handler.DynamoDBClient')
    def test_check_aws_services(
        self,
        mock_dynamodb,
        mock_s3,
        mock_bedrock,
        handler,
    ):
        """Test AWS services health check."""
        # Mock successful initialization
        mock_bedrock.return_value = Mock()
        mock_s3.return_value = Mock()
        mock_dynamodb.return_value = Mock()

        aws_services = handler._check_aws_services()

        # Verify all services are checked
        assert "bedrock" in aws_services
        assert "s3" in aws_services
        assert "dynamodb" in aws_services

        # Verify status
        for service_status in aws_services.values():
            assert "status" in service_status

    def test_check_orchestrator(self, handler):
        """Test orchestrator health check."""
        result = handler._check_orchestrator()

        assert "ready" in result
        assert result["ready"] is True

    def test_check_aws_clients(self, handler):
        """Test AWS clients health check."""
        result = handler._check_aws_clients()

        assert "ready" in result


class TestServiceIntegration:
    """Test overall service integration."""

    def test_all_services_accessible_through_orchestrator(self):
        """Test that all services are accessible through orchestrator."""
        orchestrator = get_orchestrator()

        # Verify all services are initialized
        services = [
            orchestrator.text_processor,
            orchestrator.pdf_processor,
            orchestrator.video_processor,
            orchestrator.flashcard_generator,
            orchestrator.quiz_generator,
            orchestrator.code_analyzer,
            orchestrator.voice_service,
            orchestrator.multilingual_service,
        ]

        for service in services:
            assert service is not None

    def test_health_check_reports_all_services(self):
        """Test that health check reports status of all services."""
        handler = HealthCheckHandler()
        orchestrator = handler.orchestrator

        status = orchestrator.get_service_status()

        # Verify all expected services are in status
        expected_services = [
            "text_processor",
            "pdf_processor",
            "video_processor",
            "flashcard_generator",
            "quiz_generator",
            "code_analyzer",
            "voice_service",
            "multilingual_service",
        ]

        for service_name in expected_services:
            assert service_name in status["services"]

    @patch('src.api.service_orchestrator.BedrockClient')
    def test_services_share_aws_clients(self, mock_bedrock):
        """Test that services can share AWS client instances."""
        # Create orchestrator
        orchestrator = ServiceOrchestrator()

        # Verify Bedrock client is used by multiple services
        assert orchestrator.bedrock_client is not None
        assert orchestrator.text_processor is not None
        assert orchestrator.quiz_generator is not None
        assert orchestrator.code_analyzer is not None
