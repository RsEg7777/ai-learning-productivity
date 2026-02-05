"""API handler for AI Tutor service."""

import json
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..services.ai_tutor.conversational_tutor import ConversationalTutor
from ..shared.utils.error_handler import handle_errors
from ..shared.utils.response_formatter import format_success_response, format_error_response
from ..shared.utils.validators import validate_required_fields

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()


@app.post("/tutor/start-session")
@tracer.capture_method
@handle_errors
def start_tutor_session() -> Dict[str, Any]:
    """Start a new AI tutor session."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["user_id"])
    
    tutor = ConversationalTutor()
    session = tutor.start_session(
        user_id=body["user_id"],
        subject=body.get("subject"),
        teaching_style=body.get("teaching_style", "socratic"),
        difficulty_level=body.get("difficulty_level", "adaptive"),
    )
    
    return format_success_response({
        "session_id": session.session_id,
        "user_id": session.user_id,
        "subject": session.subject,
        "created_at": session.created_at,
        "context": session.context,
    })


@app.post("/tutor/ask-question")
@tracer.capture_method
@handle_errors
def ask_tutor_question() -> Dict[str, Any]:
    """Ask a question to the AI tutor."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["session_id", "question"])
    
    tutor = ConversationalTutor()
    response = tutor.ask_question(
        session_id=body["session_id"],
        question=body["question"],
        include_examples=body.get("include_examples", True),
        use_socratic_method=body.get("use_socratic_method", True),
    )
    
    return format_success_response(response)


@app.get("/tutor/session-summary/<session_id>")
@tracer.capture_method
@handle_errors
def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get summary of a tutor session."""
    tutor = ConversationalTutor()
    summary = tutor.get_session_summary(session_id)
    
    return format_success_response(summary)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for AI tutor endpoints."""
    return app.resolve(event, context)
