"""Multimodal AI processor for images, handwriting, diagrams, and more."""

import json
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
import io

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.aws_clients.s3_client import S3Client
from ...shared.utils.logger import get_logger
from ...shared.utils.errors import ServiceError

logger = get_logger(__name__)


class MultimodalProcessor:
    """
    Process images, diagrams, handwritten notes, and screenshots.
    
    Features:
    - OCR for handwritten notes
    - Diagram understanding and explanation
    - Math equation recognition and solving
    - Screenshot-to-quiz generation
    - Image-based flashcard creation
    - Visual concept mapping
    """

    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        s3_client: Optional[S3Client] = None,
    ):
        """Initialize multimodal processor."""
        self.bedrock_client = bedrock_client or BedrockClient()
        self.s3_client = s3_client or S3Client()
        logger.info("MultimodalProcessor initialized")

    def process_handwritten_notes(
        self,
        image_data: bytes,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Process handwritten notes with OCR.
        
        Args:
            image_data: Image bytes
            language: Language code
            
        Returns:
            Dictionary with extracted text and analysis
        """
        try:
            logger.info("Processing handwritten notes")
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Use Bedrock with vision capabilities
            prompt = f"""Analyze this handwritten note image and extract the text.

Instructions:
1. Perform OCR on the handwritten text
2. Correct any spelling errors
3. Format the text properly
4. Identify key concepts
5. Generate a summary

Provide response in JSON format:
{{
    "extracted_text": "Full extracted text",
    "corrected_text": "Corrected and formatted text",
    "key_concepts": ["concept1", "concept2"],
    "summary": "Brief summary",
    "confidence": 0-100,
    "language_detected": "language code"
}}"""

            # In production, use Bedrock's vision model
            # For now, simulate with text-based analysis
            response = self._analyze_with_vision(prompt, image_base64)
            
            try:
                data = json.loads(response)
                
                # Generate flashcards from notes
                flashcards = self._generate_flashcards_from_text(
                    data.get("corrected_text", "")
                )
                
                # Generate quiz questions
                quiz_questions = self._generate_quiz_from_text(
                    data.get("corrected_text", "")
                )
                
                return {
                    "extracted_text": data.get("extracted_text", ""),
                    "corrected_text": data.get("corrected_text", ""),
                    "key_concepts": data.get("key_concepts", []),
                    "summary": data.get("summary", ""),
                    "confidence": data.get("confidence", 0),
                    "language": data.get("language_detected", language),
                    "flashcards": flashcards,
                    "quiz_questions": quiz_questions,
                    "processed_at": datetime.now().isoformat(),
                }
            except json.JSONDecodeError:
                return {
                    "extracted_text": response,
                    "error": "Failed to parse response",
                }
                
        except Exception as e:
            logger.error(f"Error processing handwritten notes: {e}", exc_info=True)
            raise ServiceError(f"Failed to process handwritten notes: {str(e)}")

    def understand_diagram(
        self,
        image_data: bytes,
        diagram_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Understand and explain diagrams.
        
        Args:
            image_data: Image bytes
            diagram_type: Type of diagram (flowchart, uml, architecture, etc.)
            
        Returns:
            Dictionary with diagram analysis
        """
        try:
            logger.info(f"Understanding diagram: {diagram_type}")
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = f"""Analyze this diagram image and provide a detailed explanation.

Diagram Type: {diagram_type or 'Unknown'}

Instructions:
1. Identify the type of diagram
2. Describe all components and their relationships
3. Explain the flow or structure
4. Identify key concepts
5. Provide a step-by-step explanation
6. Suggest improvements if applicable

Provide response in JSON format:
{{
    "diagram_type": "identified type",
    "components": [
        {{"name": "component", "description": "desc", "connections": ["other components"]}}
    ],
    "flow_description": "How it works",
    "key_concepts": ["concept1", "concept2"],
    "step_by_step": ["step1", "step2"],
    "improvements": ["suggestion1", "suggestion2"],
    "complexity": "simple|moderate|complex"
}}"""

            response = self._analyze_with_vision(prompt, image_base64)
            
            try:
                data = json.loads(response)
                
                # Generate quiz about the diagram
                quiz = self._generate_diagram_quiz(data)
                
                return {
                    **data,
                    "quiz_questions": quiz,
                    "processed_at": datetime.now().isoformat(),
                }
            except json.JSONDecodeError:
                return {
                    "explanation": response,
                    "error": "Failed to parse response",
                }
                
        except Exception as e:
            logger.error(f"Error understanding diagram: {e}", exc_info=True)
            raise ServiceError(f"Failed to understand diagram: {str(e)}")

    def solve_math_equation(
        self,
        image_data: bytes,
        show_steps: bool = True,
    ) -> Dict[str, Any]:
        """
        Recognize and solve math equations from images.
        
        Args:
            image_data: Image bytes
            show_steps: Whether to show step-by-step solution
            
        Returns:
            Dictionary with equation and solution
        """
        try:
            logger.info("Solving math equation from image")
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = f"""Analyze this image containing a math equation and solve it.

Instructions:
1. Extract the mathematical equation
2. Identify the type of problem
3. Solve step-by-step
4. Provide the final answer
5. Explain the concepts used

Provide response in JSON format:
{{
    "equation": "extracted equation in LaTeX",
    "equation_type": "algebra|calculus|geometry|etc",
    "steps": [
        {{"step_number": 1, "description": "desc", "equation": "equation at this step"}}
    ],
    "final_answer": "answer",
    "concepts_used": ["concept1", "concept2"],
    "difficulty": "easy|medium|hard",
    "explanation": "Why this approach works"
}}"""

            response = self._analyze_with_vision(prompt, image_base64)
            
            try:
                data = json.loads(response)
                
                # Generate similar practice problems
                practice_problems = self._generate_similar_problems(
                    data.get("equation_type", ""),
                    data.get("difficulty", "medium")
                )
                
                return {
                    **data,
                    "practice_problems": practice_problems,
                    "processed_at": datetime.now().isoformat(),
                }
            except json.JSONDecodeError:
                return {
                    "solution": response,
                    "error": "Failed to parse response",
                }
                
        except Exception as e:
            logger.error(f"Error solving math equation: {e}", exc_info=True)
            raise ServiceError(f"Failed to solve math equation: {str(e)}")

    def screenshot_to_quiz(
        self,
        image_data: bytes,
        question_count: int = 5,
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        """
        Generate quiz questions from screenshot.
        
        Args:
            image_data: Image bytes
            question_count: Number of questions to generate
            difficulty: Difficulty level
            
        Returns:
            Dictionary with quiz questions
        """
        try:
            logger.info(f"Generating {question_count} quiz questions from screenshot")
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = f"""Analyze this screenshot and generate quiz questions.

Instructions:
1. Extract all text and visual information
2. Identify key concepts and facts
3. Generate {question_count} quiz questions
4. Include multiple choice, true/false, and short answer
5. Provide correct answers and explanations

Difficulty: {difficulty}

Provide response in JSON format:
{{
    "content_summary": "What the screenshot contains",
    "key_topics": ["topic1", "topic2"],
    "questions": [
        {{
            "question": "Question text",
            "type": "multiple_choice|true_false|short_answer",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "answer",
            "explanation": "Why this is correct",
            "difficulty": "easy|medium|hard"
        }}
    ]
}}"""

            response = self._analyze_with_vision(prompt, image_base64)
            
            try:
                data = json.loads(response)
                return {
                    **data,
                    "question_count": len(data.get("questions", [])),
                    "processed_at": datetime.now().isoformat(),
                }
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse response",
                    "raw_response": response,
                }
                
        except Exception as e:
            logger.error(f"Error generating quiz from screenshot: {e}", exc_info=True)
            raise ServiceError(f"Failed to generate quiz: {str(e)}")

    def create_visual_flashcards(
        self,
        image_data: bytes,
        card_count: int = 10,
    ) -> Dict[str, Any]:
        """
        Create flashcards from image content.
        
        Args:
            image_data: Image bytes
            card_count: Number of flashcards to create
            
        Returns:
            Dictionary with flashcards
        """
        try:
            logger.info(f"Creating {card_count} flashcards from image")
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = f"""Analyze this image and create flashcards for learning.

Instructions:
1. Extract key information
2. Create {card_count} flashcards
3. Each card should have a question and answer
4. Include visual descriptions where relevant
5. Order by importance

Provide response in JSON format:
{{
    "flashcards": [
        {{
            "front": "Question or term",
            "back": "Answer or definition",
            "hint": "Optional hint",
            "category": "category",
            "difficulty": "easy|medium|hard"
        }}
    ]
}}"""

            response = self._analyze_with_vision(prompt, image_base64)
            
            try:
                data = json.loads(response)
                return {
                    "flashcards": data.get("flashcards", []),
                    "card_count": len(data.get("flashcards", [])),
                    "processed_at": datetime.now().isoformat(),
                }
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse response",
                }
                
        except Exception as e:
            logger.error(f"Error creating flashcards: {e}", exc_info=True)
            raise ServiceError(f"Failed to create flashcards: {str(e)}")

    def analyze_code_screenshot(
        self,
        image_data: bytes,
    ) -> Dict[str, Any]:
        """
        Analyze code from screenshot.
        
        Args:
            image_data: Image bytes
            
        Returns:
            Dictionary with code analysis
        """
        try:
            logger.info("Analyzing code from screenshot")
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            prompt = """Analyze this code screenshot.

Instructions:
1. Extract the code
2. Identify the programming language
3. Explain what the code does
4. Identify any issues or improvements
5. Suggest best practices

Provide response in JSON format:
{
    "code": "extracted code",
    "language": "programming language",
    "explanation": "what it does",
    "issues": ["issue1", "issue2"],
    "improvements": ["improvement1", "improvement2"],
    "best_practices": ["practice1", "practice2"],
    "complexity": "simple|moderate|complex"
}"""

            response = self._analyze_with_vision(prompt, image_base64)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "analysis": response,
                    "error": "Failed to parse response",
                }
                
        except Exception as e:
            logger.error(f"Error analyzing code screenshot: {e}", exc_info=True)
            raise ServiceError(f"Failed to analyze code: {str(e)}")

    def _analyze_with_vision(self, prompt: str, image_base64: str) -> str:
        """Analyze image with vision-capable model."""
        # In production, use Bedrock's Claude with vision
        # For now, simulate with text-based model
        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.5,
        )
        return response

    def _generate_flashcards_from_text(self, text: str) -> List[Dict[str, str]]:
        """Generate flashcards from extracted text."""
        if not text:
            return []
        
        prompt = f"""Create 5 flashcards from this text:

{text}

Provide in JSON format:
{{
    "flashcards": [
        {{"front": "question", "back": "answer"}}
    ]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
        try:
            data = json.loads(response)
            return data.get("flashcards", [])
        except json.JSONDecodeError:
            return []

    def _generate_quiz_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Generate quiz questions from text."""
        if not text:
            return []
        
        prompt = f"""Create 3 quiz questions from this text:

{text}

Provide in JSON format:
{{
    "questions": [
        {{
            "question": "question text",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "answer"
        }}
    ]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
        try:
            data = json.loads(response)
            return data.get("questions", [])
        except json.JSONDecodeError:
            return []

    def _generate_diagram_quiz(self, diagram_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate quiz about diagram."""
        prompt = f"""Create 3 quiz questions about this diagram:

Type: {diagram_data.get('diagram_type', 'Unknown')}
Components: {', '.join([c.get('name', '') for c in diagram_data.get('components', [])])}
Key Concepts: {', '.join(diagram_data.get('key_concepts', []))}

Provide in JSON format:
{{
    "questions": [
        {{
            "question": "question",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "answer"
        }}
    ]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        
        try:
            data = json.loads(response)
            return data.get("questions", [])
        except json.JSONDecodeError:
            return []

    def _generate_similar_problems(
        self,
        equation_type: str,
        difficulty: str,
    ) -> List[Dict[str, str]]:
        """Generate similar practice problems."""
        prompt = f"""Generate 3 similar {equation_type} problems at {difficulty} difficulty.

Provide in JSON format:
{{
    "problems": [
        {{
            "problem": "problem statement",
            "answer": "answer",
            "hint": "hint"
        }}
    ]
}}"""

        response = self.bedrock_client.invoke_model(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.8,
        )
        
        try:
            data = json.loads(response)
            return data.get("problems", [])
        except json.JSONDecodeError:
            return []
