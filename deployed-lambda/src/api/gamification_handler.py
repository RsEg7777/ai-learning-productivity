"""API handler for Gamification service."""

import json
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..services.gamification.achievement_system import AchievementSystem
from ..shared.utils.error_handler import handle_errors
from ..shared.utils.response_formatter import format_success_response, format_error_response
from ..shared.utils.validators import validate_required_fields

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()


@app.get("/gamification/stats/<user_id>")
@tracer.capture_method
@handle_errors
def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get user gamification statistics."""
    achievement_system = AchievementSystem()
    stats = achievement_system.get_user_stats(user_id)
    
    return format_success_response({
        "user_id": stats.user_id,
        "total_xp": stats.total_xp,
        "level": stats.level,
        "current_streak": stats.current_streak,
        "longest_streak": stats.longest_streak,
        "quizzes_completed": stats.quizzes_completed,
        "perfect_scores": stats.perfect_scores,
        "code_analyzed": stats.code_analyzed,
        "flashcards_reviewed": stats.flashcards_reviewed,
        "study_time_minutes": stats.study_time_minutes,
        "achievements_unlocked": stats.achievements_unlocked,
        "badges": stats.badges,
        "last_activity": stats.last_activity,
    })


@app.post("/gamification/award-xp")
@tracer.capture_method
@handle_errors
def award_xp() -> Dict[str, Any]:
    """Award XP to a user."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["user_id", "xp_amount", "reason"])
    
    achievement_system = AchievementSystem()
    result = achievement_system.award_xp(
        user_id=body["user_id"],
        xp_amount=body["xp_amount"],
        reason=body["reason"],
        metadata=body.get("metadata"),
    )
    
    return format_success_response(result)


@app.post("/gamification/update-streak")
@tracer.capture_method
@handle_errors
def update_streak() -> Dict[str, Any]:
    """Update user's daily streak."""
    body = app.current_event.json_body
    
    # Validate required fields
    validate_required_fields(body, ["user_id"])
    
    achievement_system = AchievementSystem()
    result = achievement_system.update_streak(body["user_id"])
    
    return format_success_response(result)


@app.get("/gamification/leaderboard")
@tracer.capture_method
@handle_errors
def get_leaderboard() -> Dict[str, Any]:
    """Get leaderboard rankings."""
    query_params = app.current_event.query_string_parameters or {}
    
    achievement_system = AchievementSystem()
    leaderboard = achievement_system.get_leaderboard(
        leaderboard_type=query_params.get("type", "global"),
        time_period=query_params.get("period", "all_time"),
        limit=int(query_params.get("limit", 100)),
        user_id=query_params.get("user_id"),
    )
    
    return format_success_response(leaderboard)


@app.get("/gamification/achievements/<user_id>")
@tracer.capture_method
@handle_errors
def get_achievements(user_id: str) -> Dict[str, Any]:
    """Get user's achievements."""
    query_params = app.current_event.query_string_parameters or {}
    include_locked = query_params.get("include_locked", "true").lower() == "true"
    
    achievement_system = AchievementSystem()
    achievements = achievement_system.get_user_achievements(
        user_id=user_id,
        include_locked=include_locked,
    )
    
    return format_success_response({
        "user_id": user_id,
        "achievements": [
            {
                "achievement_id": a.achievement_id,
                "name": a.name,
                "description": a.description,
                "type": a.type,
                "tier": a.tier,
                "xp_reward": a.xp_reward,
                "icon": a.icon,
                "unlocked": a.unlocked,
                "unlocked_at": a.unlocked_at,
                "progress": a.progress,
            }
            for a in achievements
        ],
    })


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for gamification endpoints."""
    return app.resolve(event, context)
