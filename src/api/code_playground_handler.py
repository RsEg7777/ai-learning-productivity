"""API handler for Code Playground service."""

import json
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..services.code_execution.code_playground import CodePlayground
from ..shared.utils.error_handler import handle_errors
from ..shared.utils.response_formatter import format_success_response, format_error_response
from ..shared.utils.validators import validate_required_fields

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()


@app.post("/playground/execute")
@tracer.capture_method
@handle_errors
def execute_code() -> Dict[str, Any]:
    """Execute code in the playground."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["code", "language"])
    
    playground = CodePlayground()
    result = playground.execute_code(
        code=body["code"],
        language=body["language"],
        stdin=body.get("stdin"),
        timeout=body.get("timeout"),
    )
    
    return format_success_response({
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "execution_time_ms": result.execution_time_ms,
        "memory_used_mb": result.memory_used_mb,
        "exit_code": result.exit_code,
    })


@app.post("/playground/complete")
@tracer.capture_method
@handle_errors
def get_code_completion() -> Dict[str, Any]:
    """Get AI-powered code completion suggestions."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["code", "language", "cursor_position"])
    
    playground = CodePlayground()
    suggestions = playground.get_code_completion(
        code=body["code"],
        language=body["language"],
        cursor_position=body["cursor_position"],
    )
    
    return format_success_response({
        "suggestions": suggestions,
    })


@app.post("/playground/explain-error")
@tracer.capture_method
@handle_errors
def explain_error() -> Dict[str, Any]:
    """Get AI explanation of code error."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["code", "language", "error_message"])
    
    playground = CodePlayground()
    explanation = playground.explain_error(
        code=body["code"],
        language=body["language"],
        error_message=body["error_message"],
    )
    
    return format_success_response(explanation)


@app.post("/playground/visualize")
@tracer.capture_method
@handle_errors
def visualize_code() -> Dict[str, Any]:
    """Generate code visualization."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["code", "language"])
    
    playground = CodePlayground()
    visualization = playground.visualize_code(
        code=body["code"],
        language=body["language"],
    )
    
    return format_success_response(visualization)


@app.post("/playground/share")
@tracer.capture_method
@handle_errors
def share_code() -> Dict[str, Any]:
    """Share code snippet."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["code", "language", "user_id"])
    
    playground = CodePlayground()
    share_info = playground.share_code(
        code=body["code"],
        language=body["language"],
        user_id=body["user_id"],
        title=body.get("title"),
    )
    
    return format_success_response(share_info)


@app.get("/playground/languages")
@tracer.capture_method
@handle_errors
def get_supported_languages() -> Dict[str, Any]:
    """Get list of supported programming languages."""
    playground = CodePlayground()
    
    return format_success_response({
        "languages": list(playground.SUPPORTED_LANGUAGES.keys()),
        "details": {
            lang: {
                "extension": config["extension"],
                "timeout": config["timeout"],
                "requires_compilation": "compile" in config,
            }
            for lang, config in playground.SUPPORTED_LANGUAGES.items()
        },
    })


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for code playground endpoints."""
    return app.resolve(event, context)
