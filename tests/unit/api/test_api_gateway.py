"""Unit tests for API Gateway handlers."""

import json
import base64
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.api.content_upload_handler import ContentUploadHandler
from src.api.text_processing_handler import TextProcessingHandler
from src.api.quiz_handler import QuizHandler
from src.api.code_analysis_handler import CodeAnalysisHandler
from src.api.voice_interface_handler import VoiceInterfaceHandler


class TestContentUploadHandler:
    """Test content upload API handler."""

    def test_handle_upload_success(self):
        """Test successful content upload."""
        handler = ContentUploadHandler(bucket_name="test-bucket")
        
        # Mock the upload service
        with patch.object(handler.upload_service, 'upload_content') as mock_upload, \
             patch.object(handler.upload_service, 'get_presigned_url') as mock_url:
            
            # Setup mocks
            mock_content = Mock()
            mock_content.id = "test-id"
            mock_content.title = "Test Document"
            mock_content.type.value = "pdf"
            mock_content.language = "en"
            mock_content.uploaded_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_content.s3_location = "s3://bucket/path"
            mock_content.metadata.file_size = 1024
            mock_content.metadata.mime_type = "application/pdf"
            
            mock_upload.return_value = mock_content
            mock_url.return_value = "https://presigned-url"
            
            # Create test event
            event = {
                "body": base64.b64encode(b"test content").decode(),
                "isBase64Encoded": True,
                "queryStringParameters": {
                    "filename": "test.pdf",
                    "title": "Test Document",
                    "language": "en"
                },
                "requestContext": {
                    "authorizer": {
                        "claims": {
                            "sub": "user-123"
                        }
                    }
                }
            }
            
            # Call handler
            response = handler.handle_upload(event, None)
            
            # Verify response
            assert response["statusCode"] == 201
            body = json.loads(response["body"])
            assert body["status"] == "success"
            assert "data" in body
            assert body["data"]["content_id"] == "test-id"
            assert body["data"]["title"] == "Test Document"
            assert body["data"]["type"] == "pdf"
            assert "presigned_url" in body["data"]

    def test_handle_upload_missing_filename(self):
        """Test upload with missing filename."""
        handler = ContentUploadHandler(bucket_name="test-bucket")
        
        event = {
            "body": base64.b64encode(b"test content").decode(),
            "isBase64Encoded": True,
            "queryStringParameters": {},
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123"
                    }
                }
            }
        }
        
        response = handler.handle_upload(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_PARAMETER"

    def test_handle_upload_missing_user_id(self):
        """Test upload with missing user ID."""
        handler = ContentUploadHandler(bucket_name="test-bucket")
        
        event = {
            "body": base64.b64encode(b"test content").decode(),
            "isBase64Encoded": True,
            "queryStringParameters": {
                "filename": "test.pdf"
            },
            "requestContext": {}
        }
        
        response = handler.handle_upload(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["status"] == "error"
        assert "user" in body["error"]["message"].lower() or "User" in body["error"]["message"]


class TestTextProcessingHandler:
    """Test text processing API handler."""

    def test_handle_process_text_success(self):
        """Test successful text processing."""
        handler = TextProcessingHandler()
        
        with patch.object(handler.text_processor, 'process_text') as mock_process:
            # Setup mock
            mock_result = Mock()
            mock_result.id = "content-123"
            mock_result.summary.text = "Summary text"
            mock_result.key_points = ["Point 1", "Point 2"]
            mock_result.concepts = []
            mock_result.language = "en"
            mock_result.processing_time = 2.5
            
            mock_process.return_value = mock_result
            
            # Create test event
            event = {
                "body": json.dumps({
                    "content": "Text to process",
                    "language": "en"
                })
            }
            
            # Call handler
            response = handler.handle_process_text(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["content_id"] == "content-123"
            assert body["summary"] == "Summary text"
            assert len(body["key_points"]) == 2

    def test_handle_process_text_missing_content(self):
        """Test text processing with missing content."""
        handler = TextProcessingHandler()
        
        event = {
            "body": json.dumps({
                "language": "en"
            })
        }
        
        response = handler.handle_process_text(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_PARAMETER"


class TestQuizHandler:
    """Test quiz API handler."""

    def test_handle_generate_flashcards_success(self):
        """Test successful flashcard generation."""
        handler = QuizHandler()
        
        with patch.object(handler.flashcard_generator, 'generate_flashcards') as mock_gen:
            # Setup mock
            mock_flashcard = Mock()
            mock_flashcard.id = "fc-1"
            mock_flashcard.question = "Question?"
            mock_flashcard.answer = "Answer"
            mock_flashcard.difficulty.value = "medium"
            mock_flashcard.tags = ["tag1"]
            
            mock_gen.return_value = [mock_flashcard] * 10
            
            # Create test event
            event = {
                "body": json.dumps({
                    "content": "Content for flashcards",
                    "count": 10
                })
            }
            
            # Call handler
            response = handler.handle_generate_flashcards(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["count"] == 10
            assert len(body["flashcards"]) == 10

    def test_handle_generate_quiz_success(self):
        """Test successful quiz generation."""
        handler = QuizHandler()
        
        with patch.object(handler.quiz_generator, 'generate_quiz') as mock_gen:
            # Setup mock
            mock_quiz = Mock()
            mock_quiz.id = "quiz-1"
            mock_quiz.title = "Test Quiz"
            mock_quiz.questions = []
            mock_quiz.time_limit = 600
            mock_quiz.passing_score = 70
            
            mock_gen.return_value = mock_quiz
            
            # Create test event
            event = {
                "body": json.dumps({
                    "content": "Content for quiz",
                    "question_count": 10
                })
            }
            
            # Call handler
            response = handler.handle_generate_quiz(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["quiz_id"] == "quiz-1"
            assert body["title"] == "Test Quiz"

    def test_handle_submit_quiz_success(self):
        """Test successful quiz submission."""
        handler = QuizHandler()
        
        # Create test event
        event = {
            "body": json.dumps({
                "quiz_id": "quiz-1",
                "answers": {
                    "q1": "a1",
                    "q2": "a2"
                }
            }),
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123"
                    }
                }
            }
        }
        
        # Call handler
        response = handler.handle_submit_quiz(event, None)
        
        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["quiz_id"] == "quiz-1"
        assert "score" in body


class TestCodeAnalysisHandler:
    """Test code analysis API handler."""

    def test_handle_analyze_code_success(self):
        """Test successful code analysis."""
        handler = CodeAnalysisHandler()
        
        with patch.object(handler.code_analyzer, 'analyze_code') as mock_analyze:
            # Setup mock
            mock_analysis = Mock()
            mock_analysis.explanation = "Code explanation"
            mock_analysis.line_by_line_analysis = []
            mock_analysis.improvements = []
            mock_analysis.issues = []
            mock_analysis.complexity.cyclomatic_complexity = 1
            mock_analysis.complexity.cognitive_complexity = 1
            mock_analysis.complexity.lines_of_code = 10
            
            mock_analyze.return_value = mock_analysis
            
            # Create test event
            event = {
                "body": json.dumps({
                    "code": "def hello(): pass",
                    "language": "python"
                })
            }
            
            # Call handler
            response = handler.handle_analyze_code(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["explanation"] == "Code explanation"
            assert "complexity" in body

    def test_handle_explain_algorithm_success(self):
        """Test successful algorithm explanation."""
        handler = CodeAnalysisHandler()
        
        with patch.object(handler.code_analyzer, 'explain_complex_algorithm') as mock_explain:
            # Setup mock
            mock_explanation = Mock()
            mock_explanation.overview = "Algorithm overview"
            mock_explanation.steps = []
            mock_explanation.complexity_analysis = "O(n)"
            mock_explanation.optimization_suggestions = []
            
            mock_explain.return_value = mock_explanation
            
            # Create test event
            event = {
                "body": json.dumps({
                    "code": "def quicksort(arr): pass",
                    "language": "python"
                })
            }
            
            # Call handler
            response = handler.handle_explain_algorithm(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["overview"] == "Algorithm overview"


class TestVoiceInterfaceHandler:
    """Test voice interface API handler."""

    def test_handle_transcribe_audio_success(self):
        """Test successful audio transcription."""
        handler = VoiceInterfaceHandler()
        
        with patch.object(handler.voice_service, 'process_voice_input') as mock_transcribe:
            # Setup mock
            mock_result = Mock()
            mock_result.text = "Transcribed text"
            mock_result.confidence = 0.95
            mock_result.language = "en-US"
            mock_result.timestamps = []
            
            mock_transcribe.return_value = mock_result
            
            # Create test event
            audio_data = b"fake audio data"
            event = {
                "body": json.dumps({
                    "audio_data": base64.b64encode(audio_data).decode(),
                    "language": "en-US"
                })
            }
            
            # Call handler
            response = handler.handle_transcribe_audio(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["text"] == "Transcribed text"
            assert body["confidence"] == 0.95

    def test_handle_synthesize_speech_success(self):
        """Test successful speech synthesis."""
        handler = VoiceInterfaceHandler()
        
        with patch.object(handler.voice_service, 'generate_audio_response') as mock_synthesize:
            # Setup mock
            mock_result = Mock()
            mock_result.audio_data = b"fake audio data"
            mock_result.language_code = "en-US"
            mock_result.voice_id = "Joanna"
            
            mock_synthesize.return_value = mock_result
            
            # Create test event
            event = {
                "body": json.dumps({
                    "text": "Text to synthesize",
                    "language": "en-US",
                    "voice_id": "Joanna"
                })
            }
            
            # Call handler
            response = handler.handle_synthesize_speech(event, None)
            
            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "audio_data" in body
            assert body["format"] == "mp3"


class TestRateLimiting:
    """Test rate limiting behavior."""

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in responses."""
        handler = TextProcessingHandler()
        
        with patch.object(handler.text_processor, 'process_text') as mock_process:
            mock_result = Mock()
            mock_result.id = "content-123"
            mock_result.summary.text = "Summary"
            mock_result.key_points = []
            mock_result.concepts = []
            mock_result.language = "en"
            mock_result.processing_time = 1.0
            
            mock_process.return_value = mock_result
            
            event = {
                "body": json.dumps({
                    "content": "Test content",
                    "language": "en"
                })
            }
            
            response = handler.handle_process_text(event, None)
            
            # Verify CORS headers are present
            assert "Access-Control-Allow-Origin" in response["headers"]
            assert "Access-Control-Allow-Methods" in response["headers"]


class TestCORSSupport:
    """Test CORS support."""

    def test_cors_headers_in_success_response(self):
        """Test CORS headers in successful responses."""
        handler = TextProcessingHandler()
        
        response = handler._success_response(200, {"data": "test"})
        
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET,POST,PUT,DELETE,OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]
        assert "Content-Type,Authorization" in response["headers"]["Access-Control-Allow-Headers"]

    def test_cors_headers_in_error_response(self):
        """Test CORS headers in error responses."""
        handler = TextProcessingHandler()
        
        response = handler._error_response(400, "ERROR", "Error message")
        
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET,POST,PUT,DELETE,OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]


class TestRequestValidation:
    """Test request validation."""

    def test_missing_required_parameter(self):
        """Test validation of missing required parameters."""
        handler = TextProcessingHandler()
        
        event = {
            "body": json.dumps({
                "language": "en"
                # Missing 'content' parameter
            })
        }
        
        response = handler.handle_process_text(event, None)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_PARAMETER"
        assert "content" in body["message"]

    def test_invalid_json_body(self):
        """Test handling of invalid JSON in request body."""
        handler = TextProcessingHandler()
        
        event = {
            "body": "invalid json {"
        }
        
        response = handler.handle_process_text(event, None)
        
        # Should handle gracefully
        assert response["statusCode"] in [400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
