"""
AI Learning & Productivity Assistant - Production Backend
==========================================================
FastAPI server with real AWS services and proper error handling.

Run:  uvicorn app:app --reload --port 8000

Environment Variables:
- AWS_REGION : AWS region (default: us-east-1)
- TABLE_PREFIX : DynamoDB table prefix (default: ai-learning-)
- STRICT_MODE : Fail on initialization errors (default: false)
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
TABLE_PREFIX = os.getenv('TABLE_PREFIX', 'ai-learning-')
STRICT_MODE = os.getenv('STRICT_MODE', 'false').lower() == 'true'

app = FastAPI(
    title="AI Learning Assistant API",
    version="2.0.0",
    description="Production API with AWS Bedrock integration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
services_initialized = False
tutor_service = None
quiz_service = None
code_analyzer = None
health_status = {"status": "initializing"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global services_initialized, tutor_service, quiz_service, code_analyzer, health_status
    
    try:
        from src.api.app_init import initialize_app, get_health_status
        from src.services.ai_tutor.conversational_tutor import ConversationalTutor
        from src.services.quiz_generation.quiz_generator import QuizGenerator
        from src.services.code_analysis.code_analyzer import CodeAnalyzer
        from src.shared.aws_clients.bedrock_client import BedrockClient
        from src.shared.models.code import ProgrammingLanguage
        
        logger.info("Initializing application...")
        
        if initialize_app(region=AWS_REGION, table_prefix=TABLE_PREFIX, strict=STRICT_MODE):
            # Initialize service instances
            bedrock_client = BedrockClient(region=AWS_REGION)
            tutor_service = ConversationalTutor(bedrock_client=bedrock_client)
            quiz_service = QuizGenerator(bedrock_client=bedrock_client)
            code_analyzer = CodeAnalyzer(bedrock_client=bedrock_client)
            
            services_initialized = True
            health_status = get_health_status()
            logger.info("✅ Application initialized successfully")
        else:
            health_status = get_health_status()
            logger.error("❌ Application initialization failed")
            if STRICT_MODE:
                raise RuntimeError("Initialization failed in strict mode")
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        health_status = {
            "status": "unhealthy",
            "message": str(e),
            "services": {}
        }
        if STRICT_MODE:
            raise


# Request/Response Models
class StartSessionRequest(BaseModel):
    user_id: str = "user123"
    subject: Optional[str] = None
    teaching_style: str = "socratic"
    difficulty_level: str = "adaptive"


class AskQuestionRequest(BaseModel):
    session_id: str
    question: str
    include_examples: bool = True
    use_socratic_method: bool = True


class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"


class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc),
            "path": str(request.url)
        }
    )


# Health and Status Endpoints
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "message": "AI Learning Assistant API",
        "version": "2.0.0",
        "services_initialized": services_initialized
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        **health_status,
        "timestamp": datetime.utcnow().isoformat()
    }


# AI Tutor Endpoints
@app.post("/tutor/start-session")
async def start_session(req: StartSessionRequest):
    """Start a new tutoring session."""
    if not services_initialized or not tutor_service:
        raise HTTPException(
            status_code=503,
            detail="Tutor service not available. Check /health for details."
        )
    
    try:
        session = tutor_service.start_session(
            user_id=req.user_id,
            subject=req.subject,
            teaching_style=req.teaching_style,
            difficulty_level=req.difficulty_level
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "message": "Session started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tutor/ask-question")
async def ask_question(req: AskQuestionRequest):
    """Ask a question to the AI tutor."""
    if not services_initialized or not tutor_service:
        raise HTTPException(
            status_code=503,
            detail="Tutor service not available. Check /health for details."
        )
    
    try:
        response = tutor_service.ask_question(
            session_id=req.session_id,
            question=req.question,
            include_examples=req.include_examples,
            use_socratic_method=req.use_socratic_method
        )
        
        return {
            "success": True,
            **response
        }
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Quiz Endpoints
@app.post("/quiz/generate")
async def generate_quiz(req: QuizRequest):
    """Generate a quiz from a topic."""
    if not services_initialized or not quiz_service:
        raise HTTPException(
            status_code=503,
            detail="Quiz service not available. Check /health for details."
        )
    
    try:
        # Generate quiz from topic text
        quiz = quiz_service.generate_quiz(
            content=f"Topic: {req.topic}\n\nGenerate questions about {req.topic} at {req.difficulty} difficulty level.",
            title=f"Quiz: {req.topic}",
            question_count=req.num_questions
        )
        
        return {
            "success": True,
            "quiz_id": quiz.id,
            "title": quiz.title,
            "questions": [
                {
                    "id": q.id,
                    "type": q.type.value,
                    "text": q.text,
                    "options": q.options,
                    "points": q.points,
                    "difficulty": q.difficulty.value
                }
                for q in quiz.questions
            ],
            "time_limit": quiz.time_limit,
            "passing_score": quiz.passing_score
        }
    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Code Analysis Endpoints
@app.post("/code/analyze")
async def analyze_code(req: CodeAnalysisRequest):
    """Analyze code and provide suggestions."""
    if not services_initialized or not code_analyzer:
        raise HTTPException(
            status_code=503,
            detail="Code analyzer not available. Check /health for details."
        )
    
    try:
        from src.shared.models.code import ProgrammingLanguage
        
        # Map language string to enum
        lang_map = {
            "python": ProgrammingLanguage.PYTHON,
            "javascript": ProgrammingLanguage.JAVASCRIPT,
            "typescript": ProgrammingLanguage.TYPESCRIPT,
            "java": ProgrammingLanguage.JAVA,
            "cpp": ProgrammingLanguage.CPP,
            "c++": ProgrammingLanguage.CPP,
            "csharp": ProgrammingLanguage.CSHARP,
            "c#": ProgrammingLanguage.CSHARP,
            "go": ProgrammingLanguage.GO,
            "rust": ProgrammingLanguage.RUST,
        }
        
        language = lang_map.get(req.language.lower(), ProgrammingLanguage.PYTHON)
        
        analysis = code_analyzer.analyze_code(
            code=req.code,
            language=language
        )
        
        return {
            "success": True,
            "analysis": {
                "explanation": analysis.explanation,
                "line_by_line": [
                    {
                        "line": la.line_number,
                        "code": la.code,
                        "explanation": la.explanation
                    }
                    for la in analysis.line_by_line_analysis[:20]  # Limit to first 20
                ],
                "improvements": [
                    {
                        "title": imp.title,
                        "description": imp.description,
                        "code_before": imp.code_before,
                        "code_after": imp.code_after,
                        "benefit": imp.benefit,
                        "priority": imp.priority
                    }
                    for imp in analysis.improvements
                ],
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "line": issue.line_number,
                        "message": issue.message,
                        "suggestion": issue.suggestion,
                        "category": issue.category
                    }
                    for issue in analysis.issues
                ],
                "complexity": {
                    "cyclomatic": analysis.complexity.cyclomatic_complexity,
                    "cognitive": analysis.complexity.cognitive_complexity,
                    "lines_of_code": analysis.complexity.lines_of_code,
                    "maintainability_index": analysis.complexity.maintainability_index
                } if analysis.complexity else None,
                "documentation_links": analysis.documentation_links,
                "best_practices": analysis.best_practices
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Gamification Endpoints
@app.post("/gamification/award-xp")
async def award_xp(request: dict):
    """Award XP to a user."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Gamification service not available"
        )
    
    try:
        from src.services.gamification.achievement_system import AchievementSystem
        from src.shared.aws_clients.dynamodb_client import DynamoDBClient
        
        achievement_system = AchievementSystem(
            dynamodb_client=DynamoDBClient()
        )
        
        result = achievement_system.award_xp(
            user_id=request.get('user_id'),
            xp_amount=request.get('xp_amount'),
            reason=request.get('reason'),
            metadata=request.get('metadata')
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Error awarding XP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gamification/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get user gamification stats."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Gamification service not available"
        )
    
    try:
        from src.services.gamification.achievement_system import AchievementSystem
        from src.shared.aws_clients.dynamodb_client import DynamoDBClient
        
        achievement_system = AchievementSystem(
            dynamodb_client=DynamoDBClient()
        )
        
        stats = achievement_system.get_user_stats(user_id)
        
        return {
            "success": True,
            "stats": {
                "user_id": stats.user_id,
                "total_xp": stats.total_xp,
                "level": stats.level,
                "current_streak": stats.current_streak,
                "longest_streak": stats.longest_streak,
                "quizzes_completed": stats.quizzes_completed,
                "achievements_unlocked": stats.achievements_unlocked,
            }
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gamification/leaderboard")
async def get_leaderboard(
    leaderboard_type: str = "global",
    time_period: str = "all_time",
    limit: int = 100,
    user_id: Optional[str] = None
):
    """Get leaderboard rankings."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Gamification service not available"
        )
    
    try:
        from src.services.gamification.achievement_system import AchievementSystem
        from src.shared.aws_clients.dynamodb_client import DynamoDBClient
        
        achievement_system = AchievementSystem(
            dynamodb_client=DynamoDBClient()
        )
        
        leaderboard = achievement_system.get_leaderboard(
            leaderboard_type=leaderboard_type,
            time_period=time_period,
            limit=limit,
            user_id=user_id
        )
        
        return {
            "success": True,
            **leaderboard
        }
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gamification/achievements/{user_id}")
async def get_user_achievements(user_id: str, include_locked: bool = True):
    """Get user's achievements."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Gamification service not available"
        )
    
    try:
        from src.services.gamification.achievement_system import AchievementSystem
        from src.shared.aws_clients.dynamodb_client import DynamoDBClient
        
        achievement_system = AchievementSystem(
            dynamodb_client=DynamoDBClient()
        )
        
        achievements = achievement_system.get_user_achievements(
            user_id=user_id,
            include_locked=include_locked
        )
        
        return {
            "success": True,
            "achievements": [
                {
                    "id": a.achievement_id,
                    "name": a.name,
                    "description": a.description,
                    "type": a.type,
                    "tier": a.tier,
                    "xp_reward": a.xp_reward,
                    "icon": a.icon,
                    "unlocked": a.unlocked,
                    "unlocked_at": a.unlocked_at,
                }
                for a in achievements
            ]
        }
    except Exception as e:
        logger.error(f"Error getting achievements: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
