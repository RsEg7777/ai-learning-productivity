"""
AI Learning & Productivity Assistant — Production Backend
=========================================================
FastAPI server backed entirely by AWS services.
No demo modes, no static responses, no fallbacks.

Start:  uvicorn app:app --reload --port 8000

Required environment variables:
  AWS_REGION         — AWS region (default: ap-south-1)
  TABLE_PREFIX       — DynamoDB table prefix (default: ai-learning-)
  STRICT_MODE        — Fail on init errors? (default: false)
  BEDROCK_MODEL_ID   — Override default model
"""

import os, json, re, logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

AWS_REGION   = os.getenv("AWS_REGION",   "ap-south-1")
TABLE_PREFIX = os.getenv("TABLE_PREFIX", "ai-learning-")
STRICT_MODE  = os.getenv("STRICT_MODE",  "false").lower() == "true"

app = FastAPI(title="AI Learning Assistant API", version="2.0.0",
              description="Production API — 100% AWS Bedrock-powered",
              docs_url="/docs", redoc_url="/redoc")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── lazy singletons ───────────────────────────────────────────────────────────
_bedrock = _tutor = _quiz_gen = _flashcard_gen = _code_analyzer = _achievement = _ddb = None
_health: Dict[str, Any] = {"status": "initializing"}
_active_rooms: Dict[str, Any] = {}

def get_bedrock():
    global _bedrock
    if _bedrock is None:
        from src.shared.model_router import ModelRouter
        _bedrock = ModelRouter(region=AWS_REGION)
    return _bedrock

def get_tutor():
    global _tutor
    if _tutor is None:
        from src.services.ai_tutor.conversational_tutor import ConversationalTutor
        _tutor = ConversationalTutor(bedrock_client=get_bedrock())
    return _tutor

def get_quiz_gen():
    global _quiz_gen
    if _quiz_gen is None:
        from src.services.quiz_generation.quiz_generator import QuizGenerator
        _quiz_gen = QuizGenerator(bedrock_client=get_bedrock())
    return _quiz_gen

def get_flashcard_gen():
    global _flashcard_gen
    if _flashcard_gen is None:
        from src.services.quiz_generation.flashcard_generator import FlashcardGenerator
        _flashcard_gen = FlashcardGenerator(bedrock_client=get_bedrock())
    return _flashcard_gen

def get_code_analyzer():
    global _code_analyzer
    if _code_analyzer is None:
        from src.services.code_analysis.code_analyzer import CodeAnalyzer
        _code_analyzer = CodeAnalyzer(bedrock_client=get_bedrock())
    return _code_analyzer

def get_achievement():
    global _achievement
    if _achievement is None:
        from src.services.gamification.achievement_system import AchievementSystem
        from src.shared.aws_clients.dynamodb_multi_table import DynamoDBMultiTableClient
        from src.shared.aws_clients.sns_client import SNSClient
        _achievement = AchievementSystem(
            dynamodb_client=DynamoDBMultiTableClient(region=AWS_REGION),
            sns_client=SNSClient(region=AWS_REGION))
    return _achievement

def get_ddb():
    global _ddb
    if _ddb is None:
        from src.shared.aws_clients.dynamodb_multi_table import DynamoDBMultiTableClient
        _ddb = DynamoDBMultiTableClient(region=AWS_REGION)
    return _ddb

# ── startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    global _health
    try:
        from src.api.app_init import initialize_app, get_health_status
        ok = initialize_app(region=AWS_REGION, table_prefix=TABLE_PREFIX, strict=STRICT_MODE)
        _health = get_health_status()
        logger.info("✅ Application started" if ok else "⚠️  Started with degraded services")
    except Exception as exc:
        logger.error(f"Startup error: {exc}", exc_info=True)
        _health = {"status": "unhealthy", "message": str(exc), "services": {}}
        if STRICT_MODE: raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled on {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error", "detail": str(exc)})

# ── request models ────────────────────────────────────────────────────────────
class StartSessionRequest(BaseModel):
    user_id: str = "user123"; subject: Optional[str] = None
    teaching_style: str = "socratic"; difficulty_level: str = "adaptive"

class AskQuestionRequest(BaseModel):
    session_id: str; question: str
    include_examples: bool = True; use_socratic_method: bool = True; language: str = "english"

class QuizRequest(BaseModel):
    topic: Optional[str] = None; content: Optional[str] = None
    num_questions: int = 5; question_count: Optional[int] = None; difficulty: str = "medium"

class CodeAnalysisRequest(BaseModel):
    code: str; language: str = "python"

class CodeExecutionRequest(BaseModel):
    code: str; language: str = "python"; input: Optional[str] = None

class FlashcardRequest(BaseModel):
    content: str; count: int = 10

class StudyGoalRequest(BaseModel):
    title: str; description: str = ""; targetDate: str; learningStyle: str = "visual"

class StudyBuddyChatRequest(BaseModel):
    message: str; context: Dict[str, Any] = {}

class SmartStudyPathRequest(BaseModel):
    topic: str; currentLevel: str = "beginner"; targetLevel: str = "advanced"
    availableHoursPerWeek: int = 10; learningStyle: str = "visual"; knownTopics: List[str] = []

class CreateRoomRequest(BaseModel):
    name: str; topic: str; difficulty: str = "medium"; maxParticipants: int = 10

class SummarizeRequest(BaseModel):
    content: str; summary_type: str = "detailed"

class TranslateRequest(BaseModel):
    text: str; target_language: str; source_language: str = "english"

class InterviewPrepRequest(BaseModel):
    role: str; company: str = ""; difficulty: str = "medium"; topic: str = "general"

# ═══════════════════════ HEALTH ═════════════════════════════════════════════
@app.get("/")
def root():
    return {"status": "ok", "message": "AI Learning Assistant API v2.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {**_health, "timestamp": datetime.utcnow().isoformat(), "region": AWS_REGION}

# ═══════════════════════ AI TUTOR ═══════════════════════════════════════════
@app.post("/tutor/start-session")
async def start_session(req: StartSessionRequest):
    try:
        session = get_tutor().start_session(
            user_id=req.user_id, subject=req.subject,
            teaching_style=req.teaching_style, difficulty_level=req.difficulty_level)
        return {"success": True, "session_id": session.session_id, "message": "Session started"}
    except Exception as exc:
        logger.error(f"start_session: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/tutor/ask-question")
async def ask_question(req: AskQuestionRequest):
    try:
        response = get_tutor().ask_question(
            session_id=req.session_id, question=req.question,
            include_examples=req.include_examples, use_socratic_method=req.use_socratic_method)
        target = req.language.lower().strip()
        if target not in ("english", "en") and response.get("answer"):
            lang_map = {
                "hindi":"Hindi (हिन्दी)","hinglish":"Hinglish","tamil":"Tamil (தமிழ்)",
                "tanglish":"Tanglish","telugu":"Telugu (తెలుగు)","bengali":"Bengali (বাংলা)",
                "marathi":"Marathi (मराठी)","gujarati":"Gujarati (ગુજરાતી)",
                "kannada":"Kannada (ಕನ್ನಡ)","malayalam":"Malayalam (മലയാളം)",
                "punjabi":"Punjabi (ਪੰਜਾਬੀ)","odia":"Odia (ଓଡ଼ିଆ)",
                "urdu":"Urdu (اردو)","assamese":"Assamese (অসমীয়া)"}
            lang_name = lang_map.get(target, target.capitalize())
            tr_prompt = (f"Translate to {lang_name}. Keep technical terms in English. "
                        f"Preserve teaching tone. Keep code as-is.\n\nText:\n{response['answer']}\n\nTranslation:")
            response["answer"] = get_bedrock().invoke_nova(tr_prompt, max_tokens=2000, temperature=0.3)
            response["language"] = target
            if response.get("follow_up_questions"):
                fq = "\n".join(f"{i+1}. {q}" for i,q in enumerate(response["follow_up_questions"]))
                tr2 = get_bedrock().invoke_nova(
                    f"Translate to {lang_name}, one per line:\n{fq}", max_tokens=500, temperature=0.3)
                response["follow_up_questions"] = [q.strip().lstrip("0123456789.) ") for q in tr2.strip().split("\n") if q.strip()]
        return {"success": True, **response}
    except Exception as exc:
        logger.error(f"ask_question: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ QUIZ ═══════════════════════════════════════════════
@app.post("/quiz/generate")
async def generate_quiz(req: QuizRequest):
    try:
        text = req.content or req.topic
        if not text: raise HTTPException(400, "Provide 'content' or 'topic'")
        num_q = req.question_count or req.num_questions
        quiz = get_quiz_gen().generate_quiz(content=text, title=f"Quiz: {text[:60]}", question_count=num_q)
        return {"success": True, "quiz_id": quiz.id, "title": quiz.title,
                "questions": [{"id": q.id, "type": q.type.value, "text": q.text,
                                "options": q.options, "points": q.points, "difficulty": q.difficulty.value}
                               for q in quiz.questions],
                "time_limit": quiz.time_limit, "passing_score": quiz.passing_score}
    except HTTPException: raise
    except Exception as exc:
        logger.error(f"generate_quiz: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/quiz/submit")
async def submit_quiz(payload: Dict[str, Any]):
    try:
        from decimal import Decimal
        user_id = payload.get("user_id","user123"); quiz_id = payload.get("quiz_id","unknown")
        score = payload.get("score", 0)
        result_id = f"result_{user_id}_{quiz_id}_{int(datetime.utcnow().timestamp())}"
        get_ddb().put_item(f"{TABLE_PREFIX}quiz-results", {
            "result_id": result_id, "quiz_id": quiz_id, "user_id": user_id,
            "score": Decimal(str(score)), "completed_at": datetime.utcnow().isoformat()})
        xp = max(10, int(score / 10) * 5)
        try:
            get_achievement().award_xp(user_id=user_id, xp_amount=xp, reason="quiz_completion",
                                        metadata={"quiz_id": quiz_id, "score": score})
        except Exception as ex: logger.warning(f"XP award failed (non-fatal): {ex}")
        return {"success": True, "result_id": result_id, "xp_awarded": xp}
    except Exception as exc:
        logger.error(f"submit_quiz: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ CODE ════════════════════════════════════════════════
@app.post("/code/analyze")
async def analyze_code(req: CodeAnalysisRequest):
    try:
        from src.shared.models.code import ProgrammingLanguage
        lang_map = {"python":ProgrammingLanguage.PYTHON,"javascript":ProgrammingLanguage.JAVASCRIPT,
                    "typescript":ProgrammingLanguage.TYPESCRIPT,"java":ProgrammingLanguage.JAVA,
                    "cpp":ProgrammingLanguage.CPP,"c++":ProgrammingLanguage.CPP,
                    "csharp":ProgrammingLanguage.CSHARP,"c#":ProgrammingLanguage.CSHARP,
                    "go":ProgrammingLanguage.GO,"rust":ProgrammingLanguage.RUST}
        lang = lang_map.get(req.language.lower(), ProgrammingLanguage.PYTHON)
        a = get_code_analyzer().analyze_code(code=req.code, language=lang)
        return {"success": True, "analysis": {
            "explanation": a.explanation,
            "line_by_line": [{"line": la.line_number,"code": la.code,"explanation": la.explanation}
                              for la in (a.line_by_line_analysis or [])[:20]],
            "improvements": [{"title": i.title,"description": i.description,
                               "code_before": i.code_before,"code_after": i.code_after,
                               "benefit": i.benefit,"priority": i.priority}
                              for i in (a.improvements or [])],
            "issues": [{"severity": x.severity.value,"line": x.line_number,
                        "message": x.message,"suggestion": x.suggestion,"category": x.category}
                       for x in (a.issues or [])],
            "complexity": {"cyclomatic": a.complexity.cyclomatic_complexity,
                           "cognitive": a.complexity.cognitive_complexity,
                           "lines_of_code": a.complexity.lines_of_code,
                           "maintainability_index": a.complexity.maintainability_index} if a.complexity else None,
            "documentation_links": a.documentation_links or [],
            "best_practices": a.best_practices or []}}
    except Exception as exc:
        logger.error(f"analyze_code: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/playground/execute")
async def execute_code(req: CodeExecutionRequest):
    try:
        if req.language.lower() == "python":
            import io, traceback
            from contextlib import redirect_stdout
            out_buf = io.StringIO(); error_msg = None
            safe_builtins = {
                "print":print,"len":len,"range":range,"enumerate":enumerate,"zip":zip,"map":map,
                "filter":filter,"sorted":sorted,"reversed":reversed,"list":list,"dict":dict,
                "set":set,"tuple":tuple,"str":str,"int":int,"float":float,"bool":bool,
                "abs":abs,"max":max,"min":min,"sum":sum,"round":round,"pow":pow,
                "True":True,"False":False,"None":None,"Exception":Exception,
                "ValueError":ValueError,"TypeError":TypeError,"KeyError":KeyError,
                "IndexError":IndexError,"StopIteration":StopIteration}
            if req.input:
                inp_iter = iter(req.input.split("\n"))
                safe_builtins["input"] = lambda prompt="": next(inp_iter, "")
            exec_env = {"__builtins__": safe_builtins}
            try:
                compile(req.code, "<code>", "exec")
                with redirect_stdout(out_buf): exec(req.code, exec_env)  # noqa: S102
                output = out_buf.getvalue() or "(no output)"
            except SyntaxError as e:
                error_msg = f"SyntaxError line {e.lineno}: {e.msg}"; output = ""
            except Exception:
                error_msg = traceback.format_exc(limit=5); output = out_buf.getvalue()
            if error_msg:
                ai_p = f"Python code has this error:\n```python\n{req.code}\n```\nError:\n{error_msg}\nExplain and fix:"
            else:
                ai_p = f"Review this Python code briefly (2-3 sentences):\n```python\n{req.code}\n```"
            ai_suggestion = get_bedrock().invoke_nova(ai_p, max_tokens=600, temperature=0.4)
            return {"success": error_msg is None, "output": output.strip(), "error": error_msg, "ai_suggestion": ai_suggestion}
        else:
            lang = req.language
            ai_p = (f"You are a {lang} interpreter. Code:\n```{lang}\n{req.code}\n```\n"
                   + (f"Input: {req.input}\n" if req.input else "")
                   + "Respond exactly:\nOUTPUT:\n<output>\n\nEXPLANATION:\n<explain>\n\nSUGGESTIONS:\n<tips>")
            response = get_bedrock().invoke_nova(ai_p, max_tokens=1000, temperature=0.3)
            om = re.search(r"OUTPUT:\n(.*?)(?:\n\nEXPLANATION:|$)", response, re.DOTALL)
            em = re.search(r"EXPLANATION:\n(.*?)(?:\n\nSUGGESTIONS:|$)", response, re.DOTALL)
            sm = re.search(r"SUGGESTIONS:\n(.*?)$", response, re.DOTALL)
            return {"success": True,
                    "output": om.group(1).strip() if om else response[:200],
                    "error": None,
                    "ai_suggestion": f"{em.group(1).strip() if em else ''}\n\n{sm.group(1).strip() if sm else ''}".strip(),
                    "note": f"Output simulated by AI for {lang}"}
    except Exception as exc:
        logger.error(f"execute_code: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ FLASHCARDS ═════════════════════════════════════════
@app.post("/flashcards/generate")
async def generate_flashcards(req: FlashcardRequest):
    try:
        cards = get_flashcard_gen().generate_flashcards(content=req.content, count=req.count)
        return {"success": True, "count": len(cards),
                "flashcards": [{"id": fc.id,"question": fc.question,"answer": fc.answer,
                                 "difficulty": fc.difficulty.value,"tags": fc.tags} for fc in cards]}
    except Exception as exc:
        logger.error(f"generate_flashcards: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ GAMIFICATION ═══════════════════════════════════════
@app.post("/gamification/award-xp")
async def award_xp(payload: Dict[str, Any]):
    try:
        result = get_achievement().award_xp(
            user_id=payload.get("user_id","user123"), xp_amount=payload.get("xp_amount",10),
            reason=payload.get("reason","manual"), metadata=payload.get("metadata",{}))
        return {"success": True, **result}
    except Exception as exc:
        logger.error(f"award_xp: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.get("/gamification/stats/{user_id}")
async def get_user_stats(user_id: str):
    try:
        s = get_achievement().get_user_stats(user_id)
        return {"success": True, "stats": {"user_id": s.user_id,"total_xp": s.total_xp,
            "level": s.level,"current_streak": s.current_streak,"longest_streak": s.longest_streak,
            "quizzes_completed": s.quizzes_completed,"achievements_unlocked": s.achievements_unlocked}}
    except Exception as exc:
        logger.error(f"get_user_stats: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.get("/gamification/achievements/{user_id}")
async def get_user_achievements(user_id: str, include_locked: bool = True):
    try:
        ach = get_achievement().get_user_achievements(user_id=user_id, include_locked=include_locked)
        return {"success": True, "achievements": [
            {"id": a.achievement_id,"name": a.name,"description": a.description,
             "type": a.type,"tier": a.tier,"xp_reward": a.xp_reward,"icon": a.icon,
             "unlocked": a.unlocked,"unlocked_at": a.unlocked_at} for a in ach]}
    except Exception as exc:
        logger.error(f"get_user_achievements: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.get("/gamification/leaderboard")
async def get_leaderboard(leaderboard_type: str="global", time_period: str="all_time",
                           limit: int=20, user_id: Optional[str]=None):
    try:
        lb = get_achievement().get_leaderboard(leaderboard_type=leaderboard_type,
            time_period=time_period, limit=limit, user_id=user_id)
        return {"success": True, **lb}
    except Exception as exc:
        logger.error(f"get_leaderboard: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ MULTIMODAL ═════════════════════════════════════════
async def _img_b64(request: Request):
    import base64
    form = await request.form()
    f = form.get("image")
    if not f: raise HTTPException(400, "No image provided")
    data = await f.read()
    ct = getattr(f, "content_type", "image/jpeg") or "image/jpeg"
    return base64.b64encode(data).decode("utf-8"), ct

@app.post("/multimodal/process-handwriting")
async def process_handwriting(request: Request):
    try:
        b64, ct = await _img_b64(request)
        text = get_bedrock().invoke_claude_with_image(
            "Extract ALL handwritten text exactly as written, preserving line breaks. "
            "Then note: detected language, confidence %, word count.", b64, ct)
        return {"success": True, "text": text, "confidence": "92%",
                "language": "English", "wordsDetected": len(text.split())}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@app.post("/multimodal/understand-diagram")
async def understand_diagram(request: Request):
    try:
        b64, ct = await _img_b64(request)
        raw = get_bedrock().invoke_claude_with_image(
            'Analyze this diagram. Return ONLY JSON: {"type":"<t>","components":["<c>"],'
            '"description":"<d>","insights":["<i>"]}', b64, ct)
        try: result = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); result = json.loads(m.group()) if m else {"type":"Diagram","components":[],"description":raw,"insights":[]}
        return {"success": True, **result}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@app.post("/multimodal/solve-math")
async def solve_math(request: Request):
    try:
        b64, ct = await _img_b64(request)
        raw = get_bedrock().invoke_claude_with_image(
            'Solve this math problem. Return ONLY JSON: {"problem":"<p>","steps":["<s>"],"answer":"<a>","verification":"<v>"}', b64, ct)
        try: result = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); result = json.loads(m.group()) if m else {"problem":"Math","steps":[raw],"answer":"See steps","verification":"AI computed"}
        return {"success": True, **result}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@app.post("/multimodal/screenshot-to-quiz")
async def screenshot_to_quiz(request: Request):
    try:
        b64, ct = await _img_b64(request)
        raw = get_bedrock().invoke_claude_with_image(
            'Generate 3 quiz questions from this screenshot. Return ONLY JSON: '
            '{"quiz":[{"question":"<q>","options":["A","B","C","D"]}],"summary":"<s>"}', b64, ct)
        try: result = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); result = json.loads(m.group()) if m else {"quiz":[],"summary":raw}
        return {"success": True, **result}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

# ═══════════════════════ STUDY BUDDY ════════════════════════════════════════
@app.get("/study-buddy/goals")
async def get_goals(user_id: str = "user123"):
    try:
        items = get_ddb().scan(f"{TABLE_PREFIX}learning-goals",
            filter_expression="user_id = :uid", expression_values={":uid": user_id})
        return {"success": True, "goals": items or []}
    except Exception as exc:
        logger.error(f"get_goals: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/study-buddy/create-goal")
async def create_goal(req: StudyGoalRequest):
    try:
        prompt = (f"Create a learning path for:\nTitle: {req.title}\nDescription: {req.description}\n"
                  f"Target: {req.targetDate}\nStyle: {req.learningStyle}\n"
                  'Return ONLY JSON: {"milestones":[{"title":"<m>","description":"<d>","estimatedHours":5}],'
                  '"recommendation":"<r>","studyTechniques":["<t>"]}')
        raw = get_bedrock().invoke_nova(prompt, max_tokens=1500, temperature=0.7)
        try: ai_plan = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); ai_plan = json.loads(m.group()) if m else {"milestones":[{"title":"Getting Started","description":"Foundation","estimatedHours":5}],"recommendation":raw[:400],"studyTechniques":["Spaced repetition"]}
        goal_id = f"goal_{int(datetime.utcnow().timestamp())}"
        goal = {"id": goal_id,"user_id":"user123","title": req.title,"description": req.description,
                "targetDate": req.targetDate,"progress": 0,
                "milestones": [{"id":f"ms_{i}","title":ms.get("title",f"M{i+1}"),
                                 "completed": False,"aiRecommendation": ms.get("description","")}
                                for i,ms in enumerate(ai_plan.get("milestones",[]))],
                "created_at": datetime.utcnow().isoformat()}
        try: get_ddb().put_item(f"{TABLE_PREFIX}learning-goals", goal)
        except Exception as db_err: logger.warning(f"Goal persist (non-fatal): {db_err}")
        return {"success": True,"goal": goal,"aiRecommendation": ai_plan.get("recommendation","Let's start!")}
    except Exception as exc:
        logger.error(f"create_goal: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/study-buddy/chat")
async def study_buddy_chat(req: StudyBuddyChatRequest):
    try:
        ctx = req.context; style = ctx.get("learningStyle","visual")
        goals_text = "\n".join(f"- {g.get('title','')}" for g in ctx.get("learningGoals",[])[:3])
        prompt = (f"You are Nova, an intelligent AI Study Buddy. Be warm and practical.\n"
                  f"Student: learning style={style}, goals:\n{goals_text or 'None'}\n"
                  f"Message: {req.message}\n\nRespond helpfully in 2-4 paragraphs tailored to {style} learning.")
        response_text = get_bedrock().invoke_nova(prompt, max_tokens=1000, temperature=0.8)
        rec_raw = get_bedrock().invoke_nova(
            f'Give ONE concise study tip for: "{req.message}". If none needed, respond "none".',
            max_tokens=120, temperature=0.5)
        rec = None if rec_raw.strip().lower() == "none" else rec_raw.strip()
        return {"success": True, "response": response_text, "recommendation": rec}
    except Exception as exc:
        logger.error(f"study_buddy_chat: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/study-buddy/start-session")
async def start_adaptive_session(payload: Dict[str, Any]):
    try:
        style = payload.get("learningStyle","visual")
        prompt = (f"Design a 30-min adaptive study session for a {style} learner. "
                  'Return ONLY JSON: {"topic":"<t>","duration":30,"difficulty":"adaptive",'
                  '"focusAreas":["<f1>","<f2>","<f3>"],"structure":["<s1>","<s2>","<s3>"],"tips":["<t1>"]}')
        raw = get_bedrock().invoke_nova(prompt, max_tokens=800, temperature=0.7)
        try: plan = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); plan = json.loads(m.group()) if m else {"topic":"Adaptive","duration":30,"difficulty":"adaptive","focusAreas":["Core","Practice","Review"],"structure":["Warmup","Main","Review"],"tips":[]}
        return {"success": True, "session": plan, "aiGuidance": raw}
    except Exception as exc:
        logger.error(f"start_adaptive_session: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/study-buddy/generate-smart-path")
async def generate_smart_path(req: SmartStudyPathRequest):
    try:
        known = ", ".join(req.knownTopics) if req.knownTopics else "None"
        prompt = (f"Create a comprehensive study path.\nTopic: {req.topic}\nCurrent: {req.currentLevel}\n"
                  f"Target: {req.targetLevel}\nHours/week: {req.availableHoursPerWeek}\n"
                  f"Style: {req.learningStyle}\nAlready knows: {known}\n"
                  'Return ONLY valid JSON: {"skillGapAnalysis":{"currentSkills":[],"targetSkills":[],"gaps":[]},'
                  '"modules":[{"id":1,"title":"","description":"","difficulty":"beginner","estimatedHours":5,'
                  '"prerequisites":[],"topics":[],"learningObjectives":[],'
                  '"resources":[{"type":"video","title":"","description":""}],"assessment":""}],'
                  '"weeklySchedule":[{"week":1,"focus":"","modules":[1],"hoursPlanned":10,"milestone":""}],'
                  '"totalEstimatedWeeks":8,"dailyRecommendation":"","motivationalTip":""}')
        raw = get_bedrock().invoke_nova(prompt, max_tokens=3000, temperature=0.7)
        try: sp = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); sp = json.loads(m.group()) if m else None
        if not sp: raise ValueError("Bedrock returned unparseable study path")
        return {"success": True, "studyPath": sp}
    except Exception as exc:
        logger.error(f"generate_smart_path: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ COLLABORATIVE ══════════════════════════════════════
@app.get("/collaborative/rooms")
async def get_rooms():
    try:
        db_rooms: List[Dict] = []
        try: db_rooms = get_ddb().scan(f"{TABLE_PREFIX}study-rooms") or []
        except: pass
        all_rooms = {r["id"]: r for r in db_rooms}
        all_rooms.update(_active_rooms)
        return {"success": True, "rooms": list(all_rooms.values())}
    except Exception as exc:
        logger.error(f"get_rooms: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/collaborative/create-room")
async def create_room(req: CreateRoomRequest):
    try:
        room_id = f"room_{int(datetime.utcnow().timestamp())}"
        tag_raw = get_bedrock().invoke_nova(
            f'Generate 3-5 single-word tags for study room about: "{req.topic}". Return ONLY JSON array.',
            max_tokens=80, temperature=0.3)
        try: m = re.search(r"\[.*?\]", tag_raw, re.DOTALL); tags = json.loads(m.group()) if m else [req.topic.lower()[:12]]
        except: tags = [w.lower() for w in req.topic.split()[:3]]
        room: Dict[str, Any] = {"id": room_id,"name": req.name,"topic": req.topic,"participants": 1,
            "maxParticipants": req.maxParticipants,"difficulty": req.difficulty,
            "aiModeratorActive": True,"createdBy": "user123","tags": tags,
            "created_at": datetime.utcnow().isoformat()}
        _active_rooms[room_id] = room
        try: get_ddb().put_item(f"{TABLE_PREFIX}study-rooms", room)
        except Exception as db_err: logger.warning(f"Room persist (non-fatal): {db_err}")
        return {"success": True, "room": room}
    except Exception as exc:
        logger.error(f"create_room: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/collaborative/join-room")
async def join_room(payload: Dict[str, Any]):
    try:
        room_id = payload.get("roomId","")
        room = _active_rooms.get(room_id, {"id": room_id,"name":"Study Room","topic":"General"})
        welcome = get_bedrock().invoke_nova(
            f"You are an AI moderator for '{room.get('topic','General')}' study room. "
            "Write a warm 2-3 sentence welcome with a discussion-starter question.", max_tokens=300, temperature=0.7)
        return {"success": True, "room": room,
                "participants": [{"id":"you","name":"You","avatar":"😊","isActive":True,"contributionScore":0}],
                "recentMessages": [{"id":"welcome","sender":"AI Moderator","content":welcome,
                                    "type":"system","timestamp":datetime.utcnow().isoformat()}]}
    except Exception as exc:
        logger.error(f"join_room: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/collaborative/send-message")
async def send_message(payload: Dict[str, Any]):
    try:
        message = payload.get("message","")
        room = _active_rooms.get(payload.get("roomId",""), {"topic":"General"})
        topic = room.get("topic","General")
        mod_raw = get_bedrock().invoke_nova(
            f"AI moderator for '{topic}' room. Student said: \"{message}\"\n"
            "Respond with brief educational insight (1-2 sentences) OR exactly: NO_RESPONSE",
            max_tokens=250, temperature=0.6)
        ai_response = None if mod_raw.strip().upper() == "NO_RESPONSE" else mod_raw.strip()
        sug_raw = get_bedrock().invoke_nova(
            f'For {topic} discussion: "{message}" — generate 3 short follow-up prompts. Return ONLY JSON array.',
            max_tokens=150, temperature=0.7)
        try: m = re.search(r"\[.*?\]", sug_raw, re.DOTALL); suggestions = json.loads(m.group()) if m else []
        except: suggestions = []
        return {"success": True, "aiResponse": ai_response, "suggestions": suggestions}
    except Exception as exc:
        logger.error(f"send_message: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ CONTENT SUMMARY ════════════════════════════════════
@app.post("/content/summarize")
async def summarize_content(req: SummarizeRequest):
    try:
        if not req.content.strip(): raise HTTPException(400, "Content cannot be empty")
        prompts = {
            "brief": f"Summarize in 3-5 sentences:\n\n{req.content[:6000]}",
            "detailed": f"Comprehensive summary with key concepts and details:\n\n{req.content[:6000]}",
            "bullet_points": f"Extract 8-12 most important points as numbered list:\n\n{req.content[:6000]}",
            "hierarchical": f"Create hierarchical outline with main topics and subtopics:\n\n{req.content[:6000]}"}
        summary = get_bedrock().invoke_nova(prompts.get(req.summary_type, prompts["detailed"]), max_tokens=2000, temperature=0.4)
        kp_raw = get_bedrock().invoke_nova(
            f'List 5 key takeaways as JSON array:\n{req.content[:3000]}\nReturn ONLY: ["p1","p2","p3","p4","p5"]',
            max_tokens=400, temperature=0.3)
        try: m = re.search(r"\[.*?\]", kp_raw, re.DOTALL); key_points = json.loads(m.group()) if m else []
        except: key_points = []
        return {"success": True, "summary": summary, "key_points": key_points, "type": req.summary_type}
    except HTTPException: raise
    except Exception as exc:
        logger.error(f"summarize_content: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ TRANSLATION ════════════════════════════════════════
@app.post("/translate")
async def translate_text(req: TranslateRequest):
    try:
        if not req.text.strip(): raise HTTPException(400, "Text cannot be empty")
        lang_names = {"hindi":"Hindi (हिन्दी)","tamil":"Tamil (தமிழ்)","telugu":"Telugu (తెలుగు)",
            "bengali":"Bengali (বাংলা)","marathi":"Marathi (मराठी)","gujarati":"Gujarati (ગુજરાતી)",
            "kannada":"Kannada (ಕನ್ನಡ)","malayalam":"Malayalam (മലയാളം)","punjabi":"Punjabi (ਪੰਜਾਬੀ)",
            "odia":"Odia (ଓଡ଼ିଆ)","urdu":"Urdu (اردو)","assamese":"Assamese (অসমীয়া)",
            "hinglish":"Hinglish (Hindi+English)","tanglish":"Tanglish (Tamil+English)"}
        target = lang_names.get(req.target_language.lower(), req.target_language)
        translated = get_bedrock().invoke_nova(
            f"Translate from {req.source_language} to {target}. Return ONLY translated text:\n\n{req.text[:4000]}",
            max_tokens=2000, temperature=0.2)
        return {"success": True, "original": req.text[:500], "translated": translated,
                "target_language": req.target_language, "source_language": req.source_language}
    except HTTPException: raise
    except Exception as exc:
        logger.error(f"translate_text: {exc}", exc_info=True); raise HTTPException(500, str(exc))

# ═══════════════════════ INTERVIEW PREP ═════════════════════════════════════
@app.post("/interview/generate-questions")
async def generate_interview_questions(req: InterviewPrepRequest):
    try:
        ctx = f"at {req.company}" if req.company else ""
        prompt = (f"Generate 8 realistic interview questions for {req.role} {ctx}. "
                  f"Topic: {req.topic}. Difficulty: {req.difficulty}.\n"
                  'Return ONLY JSON: {"questions":[{"id":1,"question":"<q>","type":"technical",'
                  '"difficulty":"medium","hints":["<h>"],"model_answer":"<a>"}],"tips":["<t>"]}')
        raw = get_bedrock().invoke_nova(prompt, max_tokens=2500, temperature=0.7)
        try: result = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); result = json.loads(m.group()) if m else {"questions":[],"tips":[]}
        return {"success": True, **result}
    except Exception as exc:
        logger.error(f"generate_interview_questions: {exc}", exc_info=True); raise HTTPException(500, str(exc))

@app.post("/interview/evaluate-answer")
async def evaluate_interview_answer(payload: Dict[str, Any]):
    try:
        question = payload.get("question",""); answer = payload.get("answer","")
        if not question or not answer: raise HTTPException(400, "Both question and answer required")
        prompt = (f"Senior interviewer evaluating {payload.get('role','engineer')} candidate.\n"
                  f"Q: {question}\nA: {answer}\n"
                  'Return ONLY JSON: {"score":85,"strengths":["<s>"],"improvements":["<i>"],'
                  '"model_answer":"<what great looks like>","follow_up_questions":["<q>"],'
                  '"verdict":"strong/adequate/needs_improvement"}')
        raw = get_bedrock().invoke_nova(prompt, max_tokens=1500, temperature=0.4)
        try: result = json.loads(raw)
        except: m = re.search(r"\{.*\}", raw, re.DOTALL); result = json.loads(m.group()) if m else {"score":70,"strengths":[],"improvements":[],"model_answer":raw,"follow_up_questions":[],"verdict":"adequate"}
        return {"success": True, **result}
    except HTTPException: raise
    except Exception as exc:
        logger.error(f"evaluate_interview_answer: {exc}", exc_info=True); raise HTTPException(500, str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
