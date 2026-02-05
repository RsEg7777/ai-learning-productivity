"""Conversational AI Tutor with context-aware dialogue and Socratic teaching."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.aws_clients.dynamodb_client import DynamoDBClient
from ...shared.utils.logger import get_logger
from ...shared.utils.errors import ServiceError

logger = get_logger(__name__)


@dataclass
class TutorMessage:
    """Represents a message in the tutor conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TutorSession:
    """Represents a tutoring session."""
    session_id: str
    user_id: str
    subject: Optional[str]
    messages: List[TutorMessage]
    created_at: str
    updated_at: str
    context: Dict[str, Any]


class ConversationalTutor:
    """
    AI-powered conversational tutor with context awareness and Socratic teaching.
    
    Features:
    - Multi-turn dialogue with context retention
    - Socratic method teaching (asking guiding questions)
    - Subject matter expertise across domains
    - Personalized teaching style
    - Follow-up question handling
    - Learning progress tracking
    """

    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        dynamodb_client: Optional[DynamoDBClient] = None,
    ):
        """Initialize the conversational tutor."""
        self.bedrock_client = bedrock_client or BedrockClient()
        self.dynamodb_client = dynamodb_client or DynamoDBClient()
        self.table_name = "tutor_sessions"
        logger.info("ConversationalTutor initialized")

    def start_session(
        self,
        user_id: str,
        subject: Optional[str] = None,
        teaching_style: str = "socratic",
        difficulty_level: str = "adaptive",
    ) -> TutorSession:
        """
        Start a new tutoring session.
        
        Args:
            user_id: User identifier
            subject: Subject area (e.g., "python", "mathematics", "physics")
            teaching_style: Teaching approach ("socratic", "direct", "exploratory")
            difficulty_level: Difficulty level ("beginner", "intermediate", "advanced", "adaptive")
            
        Returns:
            TutorSession object
        """
        session_id = f"tutor_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TutorSession(
            session_id=session_id,
            user_id=user_id,
            subject=subject,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            context={
                "teaching_style": teaching_style,
                "difficulty_level": difficulty_level,
                "topics_covered": [],
                "misconceptions_identified": [],
                "learning_progress": {},
            }
        )
        
        # Save session to DynamoDB
        self._save_session(session)
        
        logger.info(f"Started tutor session: {session_id}")
        return session

    def ask_question(
        self,
        session_id: str,
        question: str,
        include_examples: bool = True,
        use_socratic_method: bool = True,
    ) -> Dict[str, Any]:
        """
        Ask a question to the AI tutor.
        
        Args:
            session_id: Session identifier
            question: User's question
            include_examples: Whether to include examples in response
            use_socratic_method: Whether to use Socratic teaching (ask guiding questions)
            
        Returns:
            Dictionary with tutor's response and metadata
        """
        try:
            # Load session
            session = self._load_session(session_id)
            
            # Add user message to session
            user_message = TutorMessage(
                role="user",
                content=question,
                timestamp=datetime.now().isoformat(),
            )
            session.messages.append(user_message)
            
            # Build conversation context
            conversation_history = self._build_conversation_context(session)
            
            # Generate tutor response
            response = self._generate_tutor_response(
                question=question,
                conversation_history=conversation_history,
                context=session.context,
                include_examples=include_examples,
                use_socratic_method=use_socratic_method,
            )
            
            # Add assistant message to session
            assistant_message = TutorMessage(
                role="assistant",
                content=response["answer"],
                timestamp=datetime.now().isoformat(),
                metadata=response.get("metadata", {}),
            )
            session.messages.append(assistant_message)
            
            # Update session context
            self._update_session_context(session, question, response)
            
            # Save updated session
            session.updated_at = datetime.now().isoformat()
            self._save_session(session)
            
            logger.info(f"Processed question in session {session_id}")
            
            return {
                "session_id": session_id,
                "answer": response["answer"],
                "follow_up_questions": response.get("follow_up_questions", []),
                "concepts_covered": response.get("concepts_covered", []),
                "difficulty_assessment": response.get("difficulty_assessment"),
                "learning_tips": response.get("learning_tips", []),
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            raise ServiceError(f"Failed to process question: {str(e)}")

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the tutoring session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session summary
        """
        try:
            session = self._load_session(session_id)
            
            # Generate summary using AI
            summary_prompt = self._build_summary_prompt(session)
            summary_response = self.bedrock_client.invoke_model(
                prompt=summary_prompt,
                max_tokens=1000,
            )
            
            summary_data = json.loads(summary_response)
            
            return {
                "session_id": session_id,
                "duration_minutes": self._calculate_session_duration(session),
                "message_count": len(session.messages),
                "topics_covered": session.context.get("topics_covered", []),
                "key_learnings": summary_data.get("key_learnings", []),
                "areas_for_improvement": summary_data.get("areas_for_improvement", []),
                "recommended_next_topics": summary_data.get("recommended_next_topics", []),
                "overall_progress": summary_data.get("overall_progress", ""),
            }
            
        except Exception as e:
            logger.error(f"Error generating session summary: {e}", exc_info=True)
            raise ServiceError(f"Failed to generate session summary: {str(e)}")

    def _generate_tutor_response(
        self,
        question: str,
        conversation_history: str,
        context: Dict[str, Any],
        include_examples: bool,
        use_socratic_method: bool,
    ) -> Dict[str, Any]:
        """Generate AI tutor response using Bedrock."""
        teaching_style = context.get("teaching_style", "socratic")
        difficulty_level = context.get("difficulty_level", "adaptive")
        subject = context.get("subject", "general")
        
        prompt = f"""You are an expert AI tutor with deep knowledge across multiple subjects. Your goal is to help students learn effectively through thoughtful guidance.

Teaching Context:
- Subject: {subject}
- Teaching Style: {teaching_style}
- Difficulty Level: {difficulty_level}
- Topics Previously Covered: {', '.join(context.get('topics_covered', [])[:5])}

Conversation History:
{conversation_history}

Current Question: {question}

Instructions:
1. Provide a clear, accurate answer to the student's question
2. {"Use the Socratic method - ask 2-3 guiding questions to help them think deeper" if use_socratic_method else "Provide direct explanations"}
3. {"Include relevant examples to illustrate concepts" if include_examples else "Focus on conceptual understanding"}
4. Identify any misconceptions in the question
5. Assess the difficulty level of the question
6. Suggest related concepts to explore
7. Provide practical learning tips

Respond in JSON format:
{{
    "answer": "Your detailed answer here",
    "follow_up_questions": ["Question 1?", "Question 2?"],
    "concepts_covered": ["concept1", "concept2"],
    "difficulty_assessment": "beginner|intermediate|advanced",
    "misconceptions_identified": ["misconception1"],
    "learning_tips": ["tip1", "tip2"],
    "related_topics": ["topic1", "topic2"]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if response is not valid JSON
            return {
                "answer": response,
                "follow_up_questions": [],
                "concepts_covered": [],
                "difficulty_assessment": "unknown",
                "learning_tips": [],
            }

    def _build_conversation_context(self, session: TutorSession) -> str:
        """Build conversation context from session messages."""
        # Include last 10 messages for context
        recent_messages = session.messages[-10:]
        
        context_lines = []
        for msg in recent_messages:
            role = "Student" if msg.role == "user" else "Tutor"
            context_lines.append(f"{role}: {msg.content}")
        
        return "\n".join(context_lines) if context_lines else "No previous conversation"

    def _update_session_context(
        self,
        session: TutorSession,
        question: str,
        response: Dict[str, Any],
    ) -> None:
        """Update session context with new information."""
        # Add new concepts covered
        new_concepts = response.get("concepts_covered", [])
        existing_concepts = session.context.get("topics_covered", [])
        session.context["topics_covered"] = list(set(existing_concepts + new_concepts))
        
        # Track misconceptions
        misconceptions = response.get("misconceptions_identified", [])
        if misconceptions:
            existing_misconceptions = session.context.get("misconceptions_identified", [])
            session.context["misconceptions_identified"] = existing_misconceptions + misconceptions
        
        # Update difficulty level if adaptive
        if session.context.get("difficulty_level") == "adaptive":
            assessed_difficulty = response.get("difficulty_assessment")
            if assessed_difficulty:
                session.context["current_difficulty"] = assessed_difficulty

    def _build_summary_prompt(self, session: TutorSession) -> str:
        """Build prompt for session summary generation."""
        messages_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in session.messages
        ])
        
        return f"""Analyze this tutoring session and provide a comprehensive summary.

Session Details:
- Subject: {session.subject or 'General'}
- Duration: {self._calculate_session_duration(session)} minutes
- Messages: {len(session.messages)}

Conversation:
{messages_text}

Provide a summary in JSON format:
{{
    "key_learnings": ["learning1", "learning2"],
    "areas_for_improvement": ["area1", "area2"],
    "recommended_next_topics": ["topic1", "topic2"],
    "overall_progress": "Brief assessment of student's progress"
}}"""

    def _calculate_session_duration(self, session: TutorSession) -> int:
        """Calculate session duration in minutes."""
        if not session.messages:
            return 0
        
        start_time = datetime.fromisoformat(session.created_at)
        end_time = datetime.fromisoformat(session.updated_at)
        duration = (end_time - start_time).total_seconds() / 60
        
        return int(duration)

    def _save_session(self, session: TutorSession) -> None:
        """Save session to DynamoDB."""
        try:
            item = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "subject": session.subject,
                "messages": [asdict(msg) for msg in session.messages],
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "context": session.context,
            }
            self.dynamodb_client.put_item(self.table_name, item)
        except Exception as e:
            logger.warning(f"Failed to save session to DynamoDB: {e}")

    def _load_session(self, session_id: str) -> TutorSession:
        """Load session from DynamoDB."""
        try:
            item = self.dynamodb_client.get_item(
                self.table_name,
                {"session_id": session_id}
            )
            
            if not item:
                raise ServiceError(f"Session not found: {session_id}")
            
            messages = [
                TutorMessage(**msg) for msg in item.get("messages", [])
            ]
            
            return TutorSession(
                session_id=item["session_id"],
                user_id=item["user_id"],
                subject=item.get("subject"),
                messages=messages,
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                context=item.get("context", {}),
            )
        except Exception as e:
            logger.error(f"Failed to load session: {e}", exc_info=True)
            raise ServiceError(f"Failed to load session: {str(e)}")
