"""API handler for text processing endpoints."""

import json
import logging
from typing import Dict, Any, Optional
import os

from ..services.content_processing.text_processor import TextProcessor
from ..shared.aws_clients.bedrock_client import BedrockClient
from ..shared.utils.errors import ValidationError, ContentProcessingError

logger = logging.getLogger(__name__)


class TextProcessingHandler:
    """Handler for text processing API endpoints."""

    def __init__(self) -> None:
        """Initialize text processing handler."""
        bedrock_client = BedrockClient()
        self.text_processor = TextProcessor(bedrock_client=bedrock_client)
        logger.info("Initialized TextProcessingHandler")

    def handle_process_text(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle text processing request.

        Expected event structure:
        {
            "body": {
                "content": "text to process",
                "language": "en",
                "summary_type": "brief"
            }
        }

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with processed content
        """
        try:
            # Parse request body
            body = self._parse_body(event)
            
            content = body.get("content")
            language = body.get("language", "en")
            summary_type = body.get("summary_type", "brief")

            if not content:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "content parameter is required",
                )

            # DEMO MODE: Return pre-generated summary if Bedrock is unavailable
            if os.getenv("DEMO_MODE") == "true":
                logger.info("Demo mode enabled - returning sample text processing")
                return self._success_response(200, {
                    "content_id": "demo-content-123",
                    "summary": f"Summary: {content[:100]}..." if len(content) > 100 else content,
                    "key_points": [
                        "Key point 1 from the content",
                        "Key point 2 from the content",
                        "Key point 3 from the content"
                    ],
                    "concepts": [
                        {"name": "Main Concept", "description": "Primary topic discussed in the content"}
                    ],
                    "language": language,
                    "processing_time": 0.5
                })

            logger.info(f"Processing text: language={language}, summary_type={summary_type}")

            # Process text
            result = self.text_processor.process_text(
                content=content,
                language=language,
            )

            response_data = {
                "content_id": result.id,
                "summary": result.summary.text,
                "key_points": result.key_points,
                "concepts": [
                    {"name": c.name, "description": c.description}
                    for c in result.concepts
                ],
                "language": result.language,
                "processing_time": result.processing_time,
            }

            logger.info(f"Successfully processed text content {result.id}")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except ContentProcessingError as e:
            logger.error(f"Content processing error: {e.message}")
            return self._error_response(500, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during text processing",
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


def process_text_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for text processing."""
    handler = TextProcessingHandler()
    return handler.handle_process_text(event, context)
