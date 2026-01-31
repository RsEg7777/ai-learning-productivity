"""API handler for code analysis endpoints."""

import json
import logging
from typing import Dict, Any, Optional

from ..services.code_analysis.code_analyzer import CodeAnalyzer
from ..shared.aws_clients.bedrock_client import BedrockClient
from ..shared.utils.errors import ValidationError, ContentProcessingError

logger = logging.getLogger(__name__)


class CodeAnalysisHandler:
    """Handler for code analysis API endpoints."""

    def __init__(self) -> None:
        """Initialize code analysis handler."""
        bedrock_client = BedrockClient()
        self.code_analyzer = CodeAnalyzer(bedrock_client=bedrock_client)
        logger.info("Initialized CodeAnalysisHandler")

    def handle_analyze_code(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle code analysis request.

        Expected event structure:
        {
            "body": {
                "code": "code to analyze",
                "language": "python"
            }
        }

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with code analysis
        """
        try:
            body = self._parse_body(event)
            
            code = body.get("code")
            language = body.get("language", "python")

            if not code:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "code parameter is required",
                )

            logger.info(f"Analyzing code: language={language}")

            # Analyze code
            analysis = self.code_analyzer.analyze_code(
                code=code,
                language=language,
            )

            response_data = {
                "explanation": analysis.explanation,
                "line_by_line_analysis": [
                    {
                        "line_number": la.line_number,
                        "code": la.code,
                        "explanation": la.explanation,
                    }
                    for la in analysis.line_by_line_analysis
                ],
                "improvements": [
                    {
                        "type": imp.type,
                        "description": imp.description,
                        "suggested_code": imp.suggested_code,
                        "priority": imp.priority,
                    }
                    for imp in analysis.improvements
                ],
                "issues": [
                    {
                        "severity": issue.severity,
                        "type": issue.type,
                        "description": issue.description,
                        "line_number": issue.line_number,
                        "suggestion": issue.suggestion,
                    }
                    for issue in analysis.issues
                ],
                "complexity": {
                    "cyclomatic_complexity": analysis.complexity.cyclomatic_complexity,
                    "cognitive_complexity": analysis.complexity.cognitive_complexity,
                    "lines_of_code": analysis.complexity.lines_of_code,
                },
            }

            logger.info("Successfully analyzed code")
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
                "An unexpected error occurred during code analysis",
            )

    def handle_explain_algorithm(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle complex algorithm explanation request."""
        try:
            body = self._parse_body(event)
            
            code = body.get("code")
            language = body.get("language", "python")

            if not code:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "code parameter is required",
                )

            logger.info(f"Explaining algorithm: language={language}")

            # Explain algorithm
            explanation = self.code_analyzer.explain_complex_algorithm(
                code=code,
                language=language,
            )

            response_data = {
                "overview": explanation.overview,
                "steps": [
                    {
                        "step_number": step.step_number,
                        "description": step.description,
                        "code_snippet": step.code_snippet,
                    }
                    for step in explanation.steps
                ],
                "complexity_analysis": explanation.complexity_analysis,
                "optimization_suggestions": explanation.optimization_suggestions,
            }

            logger.info("Successfully explained algorithm")
            return self._success_response(200, response_data)

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return self._error_response(400, e.error_code, e.message, e.details)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred during algorithm explanation",
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
def analyze_code_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for code analysis."""
    handler = CodeAnalysisHandler()
    return handler.handle_analyze_code(event, context)


def explain_algorithm_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for algorithm explanation."""
    handler = CodeAnalysisHandler()
    return handler.handle_explain_algorithm(event, context)
