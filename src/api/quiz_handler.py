"""API handler for quiz generation and session endpoints."""

import json
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime

from ..services.quiz_generation.flashcard_generator import FlashcardGenerator
from ..services.quiz_generation.quiz_generator import QuizGenerator
from ..services.quiz_generation.quiz_session_service import QuizSessionService
from ..shared.aws_clients.bedrock_client import BedrockClient
from ..shared.aws_clients.dynamodb_client import DynamoDBClient
from ..shared.utils.errors import ValidationError, ContentProcessingError

logger = logging.getLogger(__name__)


class QuizHandler:
    """Handler for quiz-related API endpoints."""

    def __init__(self) -> None:
        """Initialize quiz handler."""
        bedrock_client = BedrockClient()
        
        self.flashcard_generator = FlashcardGenerator(bedrock_client=bedrock_client)
        self.quiz_generator = QuizGenerator(bedrock_client=bedrock_client)
        # Quiz session service will be initialized when needed with table name from env
        self.quiz_session_service = None
        logger.info("Initialized QuizHandler")

    def handle_generate_flashcards(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle flashcard generation request."""
        try:
            body = self._parse_body(event)
            
            content_id = body.get("content_id")
            content_text = body.get("content")
            count = body.get("count", 10)

            if not content_id and not content_text:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "Either content_id or content parameter is required",
                )

            logger.info(f"Generating flashcards: content_id={content_id}, count={count}")

            flashcards = self.flashcard_generator.generate_flashcards(
                content=content_text,
                count=count,
            )

            response_data = {
                "flashcards": [
                    {
                        "id": fc.id,
                        "question": fc.question,
                        "answer": fc.answer,
                        "difficulty": fc.difficulty.value,
                        "tags": fc.tags,
                    }
                    for fc in flashcards
                ],
                "count": len(flashcards),
            }

            logger.info(f"Successfully generated {len(flashcards)} flashcards")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during flashcard generation",
            )

    def handle_generate_quiz(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle quiz generation request."""
        try:
            body = self._parse_body(event)
            
            # Accept both 'content' and 'topic' for compatibility
            content_input = body.get("content") or body.get("topic")
            quiz_type = body.get("quiz_type", "mixed")
            question_count = body.get("question_count") or body.get("num_questions", 10)

            if not content_input:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "content or topic parameter is required",
                )

            logger.info(f"Generating quiz: type={quiz_type}, questions={question_count}")

            quiz = self.quiz_generator.generate_quiz(
                content=content_input,
                question_count=question_count,
            )

            response_data = {
                "quiz_id": quiz.id,
                "title": quiz.title,
                "questions": [
                    {
                        "id": q.id,
                        "type": q.type.value,
                        "text": q.text,
                        "options": q.options,
                        "points": q.points,
                    }
                    for q in quiz.questions
                ],
                "time_limit": quiz.time_limit,
                "passing_score": quiz.passing_score,
            }

            logger.info(f"Successfully generated quiz {quiz.id}")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during quiz generation",
            )

    def handle_submit_quiz(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle quiz submission and scoring."""
        try:
            body = self._parse_body(event)
            user_id = self._extract_user_id(event)
            
            quiz_id = body.get("quiz_id")
            answers = body.get("answers", {})

            if not quiz_id:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "quiz_id parameter is required",
                )

            logger.info(f"Submitting quiz: user={user_id}, quiz={quiz_id}")

            # In a real implementation, retrieve quiz and score answers
            # For now, return a mock response
            response_data = {
                "quiz_id": quiz_id,
                "user_id": user_id,
                "score": 85,
                "total_questions": len(answers),
                "correct_answers": int(len(answers) * 0.85),
                "passed": True,
                "feedback": "Great job! You passed the quiz.",
            }

            logger.info(f"Quiz submitted successfully: score={response_data['score']}")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during quiz submission",
            )

    def _extract_user_id(self, event: Dict[str, Any]) -> str:
        """Extract user ID from API Gateway authorizer."""
        try:
            request_context = event.get("requestContext", {})
            authorizer = request_context.get("authorizer", {})
            claims = authorizer.get("claims", {})
            user_id = claims.get("sub")

            if user_id:
                return user_id

            user_id = authorizer.get("user_id")
            if user_id:
                return user_id

            raise ValidationError(
                message="User ID not found in request context",
                field="user_id",
            )

        except Exception as e:
            logger.error(f"Error extracting user ID: {e}")
            raise ValidationError(
                message="Failed to extract user ID from request",
                field="user_id",
            )

    def _parse_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse request body from event."""
        body = event.get("body", "{}")
        if isinstance(body, str):
            return json.loads(body)
        return body

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
def generate_flashcards_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for flashcard generation."""
    handler = QuizHandler()
    return handler.handle_generate_flashcards(event, context)


def generate_quiz_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for quiz generation."""
    handler = QuizHandler()
    return handler.handle_generate_quiz(event, context)


def submit_quiz_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for quiz submission."""
    handler = QuizHandler()
    return handler.handle_submit_quiz(event, context)
