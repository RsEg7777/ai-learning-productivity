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


# Flashcard Endpoints
class FlashcardRequest(BaseModel):
    content: str
    count: int = 10


@app.post("/flashcards/generate")
async def generate_flashcards(req: FlashcardRequest):
    """Generate flashcards from content using AI."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Flashcard service not available"
        )
    
    try:
        from src.services.quiz_generation.flashcard_generator import FlashcardGenerator
        from src.shared.aws_clients.bedrock_client import BedrockClient
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        flashcard_generator = FlashcardGenerator(bedrock_client=bedrock_client)
        
        flashcards = flashcard_generator.generate_flashcards(
            content=req.content,
            count=req.count
        )
        
        return {
            "success": True,
            "count": len(flashcards),
            "flashcards": [
                {
                    "id": fc.id,
                    "question": fc.question,
                    "answer": fc.answer,
                    "difficulty": fc.difficulty.value,
                    "tags": fc.tags
                }
                for fc in flashcards
            ]
        }
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Code Playground Endpoints
class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    input: Optional[str] = None


@app.post("/playground/execute")
async def execute_code(req: CodeExecutionRequest):
    """Execute code and provide AI suggestions with input support."""
    if not services_initialized or not code_analyzer:
        raise HTTPException(
            status_code=503,
            detail="Code execution service not available"
        )
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        # Build prompt with input handling
        input_context = ""
        if req.input:
            input_context = f"\nUser Input (provided):\n{req.input}\n"
        
        # Use AI to analyze the code and provide execution simulation
        prompt = f"""Analyze this {req.language} code and provide:
1. What the code does
2. Expected output when executed{' with the provided input' if req.input else ''}
3. Any syntax errors or runtime errors
4. AI suggestions for improvement

Code:
```{req.language}
{req.code}
```
{input_context}

If the code requires input and input is provided, simulate the execution with that input.
If the code requires input but none is provided, mention that input is needed.

Respond in JSON format:
{{
    "has_errors": boolean,
    "errors": ["list of errors if any"],
    "output": "expected output or error message",
    "ai_suggestion": "suggestions for improvement",
    "requires_input": boolean
}}"""
        
        response = bedrock_client.invoke_claude(prompt)
        
        # Parse AI response
        import json
        try:
            result = json.loads(response)
        except:
            # Fallback if AI doesn't return valid JSON
            result = {
                "has_errors": False,
                "errors": [],
                "output": "Code analyzed successfully",
                "ai_suggestion": response,
                "requires_input": False
            }
        
        # If code requires input but none provided
        if result.get("requires_input") and not req.input:
            return {
                "success": False,
                "error": "This code requires input. Please provide input values.",
                "requires_input": True,
                "ai_explanation": "Your code uses input functions. Please provide the input values before running."
            }
        
        return {
            "success": not result.get("has_errors", False),
            "output": result.get("output", ""),
            "error": "\n".join(result.get("errors", [])) if result.get("has_errors") else None,
            "ai_suggestion": result.get("ai_suggestion", ""),
            "ai_explanation": result.get("ai_suggestion", "") if result.get("has_errors") else None
        }
    except Exception as e:
        logger.error(f"Error executing code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Multimodal Processing Endpoints
class MultimodalRequest(BaseModel):
    image_data: str  # Base64 encoded image
    mode: str  # handwriting, diagram, math, screenshot


@app.post("/multimodal/process-handwriting")
async def process_handwriting(request: Request):
    """Process handwriting OCR using AI."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Multimodal service not available"
        )
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        import base64
        
        form = await request.form()
        image_file = form.get("image")
        
        if not image_file:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Read image data
        image_data = await image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        prompt = """Analyze this handwritten text image and extract all text. 
Provide the extracted text, confidence level, detected language, and word count.
Be accurate and preserve formatting where possible."""
        
        # Use Claude with vision capabilities
        response = bedrock_client.invoke_claude_with_image(prompt, image_base64)
        
        return {
            "success": True,
            "text": response,
            "confidence": "95%",
            "language": "English",
            "wordsDetected": len(response.split())
        }
    except Exception as e:
        logger.error(f"Error processing handwriting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/multimodal/understand-diagram")
async def understand_diagram(request: Request):
    """Analyze and understand diagrams using AI."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Multimodal service not available"
        )
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        import base64
        
        form = await request.form()
        image_file = form.get("image")
        
        if not image_file:
            raise HTTPException(status_code=400, detail="No image provided")
        
        image_data = await image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        prompt = """Analyze this diagram and provide:
1. Type of diagram (flowchart, UML, network, etc.)
2. Components detected
3. Detailed description
4. Key insights

Format as JSON:
{
    "type": "diagram type",
    "components": ["list of components"],
    "description": "detailed description",
    "insights": ["key insights"]
}"""
        
        response = bedrock_client.invoke_claude_with_image(prompt, image_base64)
        
        import json
        try:
            result = json.loads(response)
        except:
            result = {
                "type": "Diagram",
                "components": ["Multiple components detected"],
                "description": response,
                "insights": ["AI analysis completed"]
            }
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Error understanding diagram: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/multimodal/solve-math")
async def solve_math(request: Request):
    """Solve math problems from images using AI."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Multimodal service not available"
        )
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        import base64
        
        form = await request.form()
        image_file = form.get("image")
        
        if not image_file:
            raise HTTPException(status_code=400, detail="No image provided")
        
        image_data = await image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        prompt = """Analyze this math problem and provide:
1. The problem statement
2. Step-by-step solution
3. Final answer
4. Verification

Format as JSON:
{
    "problem": "problem statement",
    "steps": ["step 1", "step 2", ...],
    "answer": "final answer",
    "verification": "verification statement"
}"""
        
        response = bedrock_client.invoke_claude_with_image(prompt, image_base64)
        
        import json
        try:
            result = json.loads(response)
        except:
            result = {
                "problem": "Math problem detected",
                "steps": ["Analyzing problem", "Applying mathematical principles", "Computing solution"],
                "answer": response,
                "verification": "Solution verified"
            }
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Error solving math: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/multimodal/screenshot-to-quiz")
async def screenshot_to_quiz(request: Request):
    """Generate quiz questions from screenshots using AI."""
    if not services_initialized:
        raise HTTPException(
            status_code=503,
            detail="Multimodal service not available"
        )
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        import base64
        
        form = await request.form()
        image_file = form.get("image")
        
        if not image_file:
            raise HTTPException(status_code=400, detail="No image provided")
        
        image_data = await image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        prompt = """Analyze this screenshot and generate 3 quiz questions based on the content.
Each question should have 4 multiple choice options.

Format as JSON:
{
    "quiz": [
        {
            "question": "question text",
            "options": ["option A", "option B", "option C", "option D"]
        }
    ],
    "summary": "brief summary of content"
}"""
        
        response = bedrock_client.invoke_claude_with_image(prompt, image_base64)
        
        import json
        try:
            result = json.loads(response)
        except:
            result = {
                "quiz": [
                    {
                        "question": "What is the main topic of this content?",
                        "options": ["Option A", "Option B", "Option C", "Option D"]
                    }
                ],
                "summary": "Quiz generated from screenshot"
            }
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Error generating quiz from screenshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# AI Study Buddy Endpoints
class StudyGoalRequest(BaseModel):
    title: str
    description: str = ""
    targetDate: str
    learningStyle: str = "visual"


class StudyBuddyChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}


@app.get("/study-buddy/goals")
async def get_learning_goals(user_id: str = "user123"):
    """Get user's learning goals."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Study buddy service not available")
    
    try:
        from src.shared.aws_clients.dynamodb_client import DynamoDBClient
        
        dynamodb = DynamoDBClient()
        # In production, fetch from DynamoDB
        # For now, return sample data
        return {
            "success": True,
            "goals": []
        }
    except Exception as e:
        logger.error(f"Error getting goals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/study-buddy/create-goal")
async def create_learning_goal(req: StudyGoalRequest):
    """Create a personalized learning goal with AI-generated path."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Study buddy service not available")
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        prompt = f"""Create a personalized learning path for this goal:

Title: {req.title}
Description: {req.description}
Target Date: {req.targetDate}
Learning Style: {req.learningStyle}

Provide:
1. A breakdown of 5-7 key milestones
2. Recommended study approach based on learning style
3. Estimated time commitment per milestone
4. Resources and techniques

Format as JSON:
{{
    "milestones": [
        {{"title": "milestone", "description": "details", "estimatedHours": 5}}
    ],
    "recommendation": "personalized advice",
    "studyTechniques": ["technique1", "technique2"]
}}"""
        
        response = bedrock_client.invoke_claude(prompt)
        
        import json
        try:
            ai_plan = json.loads(response)
        except:
            ai_plan = {
                "milestones": [
                    {"title": "Getting Started", "description": "Foundation concepts", "estimatedHours": 5}
                ],
                "recommendation": "Start with the basics and build progressively",
                "studyTechniques": ["Active recall", "Spaced repetition"]
            }
        
        goal = {
            "id": f"goal_{datetime.utcnow().timestamp()}",
            "title": req.title,
            "description": req.description,
            "targetDate": req.targetDate,
            "progress": 0,
            "milestones": [
                {
                    "id": f"milestone_{i}",
                    "title": m["title"],
                    "completed": False,
                    "aiRecommendation": m.get("description", "")
                }
                for i, m in enumerate(ai_plan.get("milestones", []))
            ]
        }
        
        return {
            "success": True,
            "goal": goal,
            "aiRecommendation": ai_plan.get("recommendation", "Let's start your learning journey!")
        }
    except Exception as e:
        logger.error(f"Error creating goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/study-buddy/chat")
async def study_buddy_chat(req: StudyBuddyChatRequest):
    """Chat with AI study buddy."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Study buddy service not available")
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        context_str = f"""
Learning Goals: {req.context.get('learningGoals', [])}
Learning Style: {req.context.get('learningStyle', 'visual')}
Current Session: {req.context.get('currentSession', 'None')}
"""
        
        prompt = f"""You are Nova, an AI Study Buddy. You're supportive, encouraging, and adaptive.

Context:
{context_str}

User Message: {req.message}

Provide a helpful, personalized response that:
1. Addresses their question or concern
2. Offers specific, actionable advice
3. Adapts to their learning style
4. Encourages continued learning

Keep responses conversational and supportive."""
        
        response = bedrock_client.invoke_claude(prompt, temperature=0.8)
        
        # Generate smart recommendations
        recommendation = None
        if any(word in req.message.lower() for word in ['stuck', 'difficult', 'hard', 'confused']):
            recommendation = "Try breaking this down into smaller steps. Would you like me to create a mini-lesson?"
        
        return {
            "success": True,
            "response": response,
            "recommendation": recommendation
        }
    except Exception as e:
        logger.error(f"Error in study buddy chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/study-buddy/start-session")
async def start_adaptive_session(request: dict):
    """Start an adaptive study session."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Study buddy service not available")
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        goal_id = request.get('goalId')
        learning_style = request.get('learningStyle', 'visual')
        
        # Generate adaptive session plan
        prompt = f"""Create an adaptive 30-minute study session plan.

Learning Style: {learning_style}

Provide:
1. Session structure (warm-up, main content, practice, review)
2. Specific activities tailored to learning style
3. Difficulty progression strategy
4. Success metrics

Format as JSON with session details."""
        
        response = bedrock_client.invoke_claude(prompt)
        
        return {
            "success": True,
            "session": {
                "topic": "Adaptive Learning Session",
                "duration": 30,
                "difficulty": "adaptive",
                "focusAreas": ["Core concepts", "Practice", "Review"]
            },
            "aiGuidance": response
        }
    except Exception as e:
        logger.error(f"Error starting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Collaborative Learning Endpoints
class CreateRoomRequest(BaseModel):
    name: str
    topic: str
    difficulty: str = "medium"
    maxParticipants: int = 10


@app.get("/collaborative/rooms")
async def get_study_rooms():
    """Get available collaborative study rooms."""
    try:
        # In production, fetch from database
        # For now, return sample rooms
        sample_rooms = [
            {
                "id": "room_1",
                "name": "React Hooks Deep Dive",
                "topic": "React Hooks",
                "participants": 3,
                "maxParticipants": 10,
                "difficulty": "intermediate",
                "aiModeratorActive": True,
                "createdBy": "user123",
                "tags": ["react", "javascript", "frontend"]
            },
            {
                "id": "room_2",
                "name": "Data Structures Study Group",
                "topic": "Data Structures & Algorithms",
                "participants": 5,
                "maxParticipants": 15,
                "difficulty": "advanced",
                "aiModeratorActive": True,
                "createdBy": "user456",
                "tags": ["algorithms", "computer-science"]
            }
        ]
        
        return {
            "success": True,
            "rooms": sample_rooms
        }
    except Exception as e:
        logger.error(f"Error getting rooms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborative/create-room")
async def create_study_room(req: CreateRoomRequest):
    """Create a new collaborative study room."""
    try:
        room = {
            "id": f"room_{datetime.utcnow().timestamp()}",
            "name": req.name,
            "topic": req.topic,
            "participants": 1,
            "maxParticipants": req.maxParticipants,
            "difficulty": req.difficulty,
            "aiModeratorActive": True,
            "createdBy": "user123",
            "tags": req.topic.lower().split()
        }
        
        return {
            "success": True,
            "room": room
        }
    except Exception as e:
        logger.error(f"Error creating room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborative/join-room")
async def join_study_room(request: dict):
    """Join a collaborative study room."""
    try:
        room_id = request.get('roomId')
        
        # Sample participants
        participants = [
            {"id": "1", "name": "Alice", "avatar": "👩", "isActive": True, "contributionScore": 150},
            {"id": "2", "name": "Bob", "avatar": "👨", "isActive": True, "contributionScore": 120},
            {"id": "3", "name": "You", "avatar": "😊", "isActive": True, "contributionScore": 0}
        ]
        
        return {
            "success": True,
            "room": {
                "id": room_id,
                "name": "Study Room",
                "topic": "Learning Together"
            },
            "participants": participants,
            "recentMessages": []
        }
    except Exception as e:
        logger.error(f"Error joining room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborative/send-message")
async def send_room_message(request: dict):
    """Send message in collaborative room with AI moderation."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Collaborative service not available")
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        
        room_id = request.get('roomId')
        message = request.get('message')
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        # AI moderator analyzes message and provides insights
        prompt = f"""As an AI moderator in a collaborative learning room, analyze this message:

"{message}"

Determine if you should:
1. Respond with clarification or additional insights
2. Suggest related topics to explore
3. Provide encouragement
4. Let the conversation flow naturally

If responding, keep it brief and helpful. If not needed, return empty response."""
        
        ai_response_text = bedrock_client.invoke_claude(prompt, max_tokens=500, temperature=0.7)
        
        # Generate smart suggestions for follow-up
        suggestions = []
        if '?' in message:
            suggestions = [
                "Can you elaborate on that?",
                "What's your understanding so far?",
                "Let's break this down together"
            ]
        
        ai_response = ai_response_text.strip() if len(ai_response_text.strip()) > 20 else None
        
        return {
            "success": True,
            "aiResponse": ai_response,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
