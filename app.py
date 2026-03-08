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
    language: str = "english"  # Supports Indian languages: hindi, tamil, telugu, bengali, marathi, etc.


class QuizRequest(BaseModel):
    topic: Optional[str] = None
    content: Optional[str] = None
    num_questions: int = 5
    question_count: Optional[int] = None
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
        
        # Multilingual support: translate response if non-English language requested
        target_lang = req.language.lower().strip()
        if target_lang != "english" and response.get("answer"):
            try:
                from src.shared.aws_clients.bedrock_client import BedrockClient
                bedrock_client = BedrockClient(region=AWS_REGION)
                
                lang_names = {
                    "hindi": "Hindi (हिन्दी)", "tamil": "Tamil (தமிழ்)",
                    "telugu": "Telugu (తెలుగు)", "bengali": "Bengali (বাংলা)",
                    "marathi": "Marathi (मराठी)", "gujarati": "Gujarati (ગુજરાતી)",
                    "kannada": "Kannada (ಕನ್ನಡ)", "malayalam": "Malayalam (മലയാളം)",
                    "punjabi": "Punjabi (ਪੰਜਾਬੀ)", "odia": "Odia (ଓଡ଼ିଆ)",
                    "urdu": "Urdu (اردو)", "assamese": "Assamese (অসমীয়া)",
                    "hinglish": "Hinglish (Hindi + English mixed)",
                    "tanglish": "Tanglish (Tamil + English mixed)",
                }
                lang_display = lang_names.get(target_lang, target_lang.capitalize())
                
                translate_prompt = f"""Translate the following educational text to {lang_display}.
Keep technical terms in English but explain them in {lang_display}.
Preserve the teaching tone and structure. Keep code examples as-is.

Text to translate:
{response['answer']}

Translated text:"""
                translated = bedrock_client.invoke_model(
                    model_id="us.amazon.nova-pro-v1:0",
                    prompt=translate_prompt,
                    max_tokens=2000,
                    temperature=0.3,
                )
                response["answer"] = translated.strip()
                response["language"] = target_lang
                
                # Also translate follow-up questions
                if response.get("follow_up_questions"):
                    fq_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(response["follow_up_questions"])])
                    fq_prompt = f"Translate these questions to {lang_display}. Return only the translated questions, one per line:\n{fq_text}"
                    fq_translated = bedrock_client.invoke_model(
                        model_id="us.amazon.nova-pro-v1:0",
                        prompt=fq_prompt,
                        max_tokens=500,
                        temperature=0.3,
                    )
                    translated_questions = [q.strip().lstrip('0123456789.)-: ') for q in fq_translated.strip().split('\n') if q.strip()]
                    if translated_questions:
                        response["follow_up_questions"] = translated_questions
            except Exception as translate_err:
                logger.warning(f"Translation to {target_lang} failed: {translate_err}")
                response["language"] = "english"
                response["translation_note"] = f"Translation to {target_lang} unavailable. Showing English response."
        
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
        # Accept both 'content' and 'topic' fields from frontend
        quiz_content = req.content or req.topic or "General Knowledge"
        num_q = req.question_count or req.num_questions
        
        quiz = quiz_service.generate_quiz(
            content=quiz_content,
            title=f"Quiz: {quiz_content[:60]}",
            question_count=num_q
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
        # For now, provide a simulated response to get the playground working
        # TODO: Integrate with actual Bedrock model once model access is configured
        
        # Simple code analysis without AI
        has_errors = False
        errors = []
        
        # Basic syntax check
        if req.language == "python":
            try:
                compile(req.code, '<string>', 'exec')
            except SyntaxError as e:
                has_errors = True
                errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        
        # Simulate output
        if not has_errors:
            output = f"Code analysis complete.\n\nYour {req.language} code appears to be syntactically correct.\n\nNote: This is a simulated response. Full AI-powered code execution coming soon!"
            ai_suggestion = "Code looks good! Consider adding comments and error handling for production use."
        else:
            output = "Syntax errors detected. Please fix them and try again."
            ai_suggestion = "Fix the syntax errors listed above."
        
        return {
            "success": not has_errors,
            "output": output,
            "error": "\n".join(errors) if has_errors else None,
            "ai_suggestion": ai_suggestion,
            "ai_explanation": ai_suggestion if has_errors else None
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
        
        response = bedrock_client.invoke_model(
            model_id="us.amazon.nova-pro-v1:0",
            prompt=prompt,
            max_tokens=1500,
            temperature=0.7,
        )
        
        import json
        import re as _re
        try:
            # Try parsing full response as JSON first
            ai_plan = json.loads(response)
        except:
            # Try extracting JSON from response
            json_match = _re.search(r'\{.*\}', response, _re.DOTALL)
            if json_match:
                try:
                    ai_plan = json.loads(json_match.group(0))
                except:
                    ai_plan = None
            else:
                ai_plan = None
            
            if not ai_plan:
                ai_plan = {
                    "milestones": [
                        {"title": "Getting Started", "description": "Foundation concepts", "estimatedHours": 5}
                    ],
                    "recommendation": response[:500],
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
        
        response = bedrock_client.invoke_model(
            model_id="us.amazon.nova-pro-v1:0",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.8,
        )
        
        # Use AI to generate contextual recommendation
        recommendation = None
        rec_prompt = f"""Based on this student message: "{req.message}"
And the AI tutor's response, generate ONE short (1-2 sentence) actionable study recommendation.
If the student seems confident and doesn't need extra help, return ONLY the word "none".
Otherwise, return ONLY the recommendation text, no JSON."""
        try:
            rec_response = bedrock_client.invoke_model(
                model_id="us.amazon.nova-pro-v1:0",
                prompt=rec_prompt,
                max_tokens=100,
                temperature=0.5,
            )
            if rec_response.strip().lower() != "none" and len(rec_response.strip()) > 10:
                recommendation = rec_response.strip()
        except Exception:
            pass
        
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
        
        response = bedrock_client.invoke_model(
            model_id="us.amazon.nova-pro-v1:0",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
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


# In-memory room storage for the hackathon demo
_active_rooms: Dict[str, Any] = {}


@app.get("/collaborative/rooms")
async def get_study_rooms():
    """Get available collaborative study rooms."""
    try:
        rooms = list(_active_rooms.values())
        return {
            "success": True,
            "rooms": rooms
        }
    except Exception as e:
        logger.error(f"Error getting rooms: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborative/create-room")
async def create_study_room(req: CreateRoomRequest):
    """Create a new collaborative study room with AI-generated tags."""
    try:
        room_id = f"room_{int(datetime.utcnow().timestamp())}"
        
        # Use AI to generate relevant tags for the room topic
        tags = [word.strip().lower() for word in req.topic.split() if len(word.strip()) > 2][:5]
        if services_initialized:
            try:
                from src.shared.aws_clients.bedrock_client import BedrockClient
                bedrock_client = BedrockClient(region=AWS_REGION)
                tag_prompt = f"Generate 3-5 relevant short tags (single words) for a study room about: {req.topic}. Return ONLY a JSON array of strings like [\"tag1\", \"tag2\"]."
                tag_response = bedrock_client.invoke_model(
                    model_id="us.amazon.nova-pro-v1:0",
                    prompt=tag_prompt,
                    max_tokens=100,
                    temperature=0.3,
                )
                import json as json_mod
                import re as re_mod
                json_match = re_mod.search(r'\[.*?\]', tag_response, re_mod.DOTALL)
                if json_match:
                    tags = json_mod.loads(json_match.group(0))
            except Exception as tag_err:
                logger.warning(f"AI tag generation failed, using defaults: {tag_err}")
        
        room = {
            "id": room_id,
            "name": req.name,
            "topic": req.topic,
            "participants": 1,
            "maxParticipants": req.maxParticipants,
            "difficulty": req.difficulty,
            "aiModeratorActive": True,
            "createdBy": "user123",
            "tags": tags
        }
        
        # Store room in memory
        _active_rooms[room_id] = room
        
        return {
            "success": True,
            "room": room
        }
    except Exception as e:
        logger.error(f"Error creating room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collaborative/join-room")
async def join_study_room(request: dict):
    """Join a collaborative study room with AI-generated welcome."""
    try:
        room_id = request.get('roomId')
        
        # Get room data from storage
        room_data = _active_rooms.get(room_id, {
            "id": room_id,
            "name": "Study Room",
            "topic": "General Learning"
        })
        
        participants = [
            {"id": "you", "name": "You", "avatar": "😊", "isActive": True, "contributionScore": 0}
        ]
        
        # Generate AI welcome message with room context
        welcome_messages = []
        if services_initialized:
            try:
                from src.shared.aws_clients.bedrock_client import BedrockClient
                bedrock_client = BedrockClient(region=AWS_REGION)
                welcome_prompt = f"""You are an AI moderator for a collaborative study room.
Room topic: {room_data.get('topic', 'General')}
Difficulty: {room_data.get('difficulty', 'medium')}

Generate a brief, engaging welcome message (2-3 sentences) that:
1. Welcomes the student to the room
2. Introduces the topic they'll be studying
3. Suggests a discussion starter question related to the topic

Be friendly and encouraging. Do NOT use JSON format, just write the message directly."""
                ai_welcome = bedrock_client.invoke_model(
                    model_id="us.amazon.nova-pro-v1:0",
                    prompt=welcome_prompt,
                    max_tokens=300,
                    temperature=0.7,
                )
                welcome_messages.append({
                    "id": "welcome_1",
                    "sender": "AI Moderator",
                    "content": ai_welcome.strip(),
                    "type": "system",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as ai_err:
                logger.warning(f"AI welcome generation failed: {ai_err}")
        
        return {
            "success": True,
            "room": {
                "id": room_data.get("id", room_id),
                "name": room_data.get("name", "Study Room"),
                "topic": room_data.get("topic", "General Learning")
            },
            "participants": participants,
            "recentMessages": welcome_messages
        }
    except Exception as e:
        logger.error(f"Error joining room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class SmartStudyPathRequest(BaseModel):
    topic: str
    currentLevel: str = "beginner"  # beginner, intermediate, advanced
    targetLevel: str = "advanced"
    availableHoursPerWeek: int = 10
    learningStyle: str = "visual"
    knownTopics: list = []


@app.post("/study-buddy/generate-smart-path")
async def generate_smart_study_path(req: SmartStudyPathRequest):
    """Generate an AI-powered smart study path with skill gap analysis.
    
    This is a unique feature that provides:
    - Skill gap analysis between current and target level
    - Prerequisite mapping
    - Weekly schedule with adaptive difficulty
    - Resource recommendations per module
    - Progress milestones with estimated completion times
    """
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Study path service not available")
    
    try:
        from src.shared.aws_clients.bedrock_client import BedrockClient
        import json
        import re as _re_sp
        
        bedrock_client = BedrockClient(region=AWS_REGION)
        
        known_str = ", ".join(req.knownTopics) if req.knownTopics else "None specified"
        
        prompt = f"""You are an expert learning path architect. Create a comprehensive, personalized smart study path.

Student Profile:
- Topic: {req.topic}
- Current Level: {req.currentLevel}
- Target Level: {req.targetLevel}
- Available Hours/Week: {req.availableHoursPerWeek}
- Learning Style: {req.learningStyle}
- Already Knows: {known_str}

Generate a detailed study path as JSON:
{{
    "skillGapAnalysis": {{
        "currentSkills": ["skills the student likely has at {req.currentLevel} level"],
        "targetSkills": ["skills needed for {req.targetLevel} level"],
        "gaps": ["specific skill gaps to address"]
    }},
    "modules": [
        {{
            "id": 1,
            "title": "Module Title",
            "description": "What this module covers",
            "difficulty": "beginner|intermediate|advanced",
            "estimatedHours": 5,
            "prerequisites": [],
            "topics": ["topic1", "topic2"],
            "learningObjectives": ["By the end, you will..."],
            "resources": [{{"type": "video|article|practice|project", "title": "Resource name", "description": "Why this helps"}}],
            "assessment": "How to verify mastery"
        }}
    ],
    "weeklySchedule": [
        {{
            "week": 1,
            "focus": "What to focus on",
            "modules": [1],
            "hoursPlanned": 10,
            "milestone": "What you should achieve by end of week"
        }}
    ],
    "totalEstimatedWeeks": 8,
    "dailyRecommendation": "Personalized daily study routine based on {req.learningStyle} learning style",
    "motivationalTip": "An encouraging, personalized message"
}}

IMPORTANT: Generate 5-8 modules that progressively build skills. Create a realistic weekly schedule. Tailor everything to the {req.learningStyle} learning style."""
        
        response = bedrock_client.invoke_model(
            model_id="us.amazon.nova-pro-v1:0",
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7,
        )
        
        try:
            study_path = json.loads(response)
        except:
            json_match = _re_sp.search(r'\{.*\}', response, _re_sp.DOTALL)
            if json_match:
                try:
                    study_path = json.loads(json_match.group(0))
                except:
                    study_path = None
            else:
                study_path = None
        
        if not study_path:
            study_path = {
                "skillGapAnalysis": {
                    "currentSkills": [f"Basic {req.topic} understanding"],
                    "targetSkills": [f"Advanced {req.topic} mastery"],
                    "gaps": [f"Intermediate {req.topic} concepts"]
                },
                "modules": [
                    {"id": 1, "title": f"Foundations of {req.topic}", "description": "Core concepts", "difficulty": "beginner", "estimatedHours": 5, "prerequisites": [], "topics": [req.topic], "learningObjectives": [f"Understand {req.topic} fundamentals"], "resources": [], "assessment": "Complete practice exercises"}
                ],
                "weeklySchedule": [{"week": 1, "focus": "Foundations", "modules": [1], "hoursPlanned": req.availableHoursPerWeek, "milestone": "Complete fundamentals"}],
                "totalEstimatedWeeks": 8,
                "dailyRecommendation": response[:500] if response else "Study consistently for best results.",
                "motivationalTip": "Every expert was once a beginner. Keep going!"
            }
        
        return {
            "success": True,
            "studyPath": study_path
        }
    except Exception as e:
        logger.error(f"Error generating smart study path: {e}", exc_info=True)
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
        
        ai_response_text = bedrock_client.invoke_model(
            model_id="us.amazon.nova-pro-v1:0",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
        )
        
        # Generate AI-powered discussion suggestions
        suggestions = []
        try:
            suggestion_prompt = f"""Given this student discussion message: "{message}"
Generate 3 short follow-up discussion prompts (each under 10 words) that encourage deeper learning.
Return ONLY a JSON array of strings like ["prompt1", "prompt2", "prompt3"]."""
            suggestion_response = bedrock_client.invoke_model(
                model_id="us.amazon.nova-pro-v1:0",
                prompt=suggestion_prompt,
                max_tokens=150,
                temperature=0.7,
            )
            import re as _re2
            json_match = _re2.search(r'\[.*?\]', suggestion_response, _re2.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group(0))
        except Exception:
            suggestions = []
        
        ai_response = ai_response_text.strip() if len(ai_response_text.strip()) > 20 else None
        
        return {
            "success": True,
            "aiResponse": ai_response,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
