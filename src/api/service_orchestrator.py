"""Service orchestrator for inter-service communication and coordination."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..services.content_processing.text_processor import TextProcessor
from ..services.content_processing.pdf_processor import PDFProcessor
from ..services.content_processing.video_processor import VideoProcessor
from ..services.quiz_generation.flashcard_generator import FlashcardGenerator
from ..services.quiz_generation.quiz_generator import QuizGenerator
from ..services.code_analysis.code_analyzer import CodeAnalyzer
from ..services.voice_interface.voice_interface_service import VoiceInterfaceService
from ..services.multilingual.multilingual_service import MultilingualService
from ..shared.aws_clients.bedrock_client import BedrockClient
from ..shared.aws_clients.transcribe_client import TranscribeClient
from ..shared.aws_clients.polly_client import PollyClient
from ..shared.aws_clients.s3_client import S3Client
from ..shared.utils.errors import ServiceCommunicationError
from ..shared.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceOrchestrator:
    """
    Orchestrates communication between microservices.
    
    This class provides a centralized way for services to communicate
    with each other, enabling complex workflows that span multiple services.
    """

    def __init__(self) -> None:
        """Initialize service orchestrator with all service instances."""
        # Initialize AWS clients
        self.bedrock_client = BedrockClient()
        self.transcribe_client = TranscribeClient()
        self.polly_client = PollyClient()
        self.s3_client = S3Client()

        # Initialize services
        self.text_processor = TextProcessor(bedrock_client=self.bedrock_client)
        self.pdf_processor = PDFProcessor(text_processor=self.text_processor)
        self.video_processor = VideoProcessor(
            text_processor=self.text_processor,
            transcribe_client=self.transcribe_client,
            s3_client=self.s3_client,
        )
        self.flashcard_generator = FlashcardGenerator(bedrock_client=self.bedrock_client)
        self.quiz_generator = QuizGenerator(bedrock_client=self.bedrock_client)
        self.code_analyzer = CodeAnalyzer(bedrock_client=self.bedrock_client)
        self.voice_service = VoiceInterfaceService(
            transcribe_client=self.transcribe_client,
            polly_client=self.polly_client,
        )
        self.multilingual_service = MultilingualService()

        logger.info("ServiceOrchestrator initialized with all services")

    def process_content_end_to_end(
        self,
        content: str,
        content_type: str,
        language: str = "en",
        generate_quiz: bool = True,
        generate_flashcards: bool = True,
    ) -> Dict[str, Any]:
        """
        Process content through multiple services in a coordinated workflow.

        This method demonstrates service-to-service communication by:
        1. Processing the content (text/PDF/video)
        2. Optionally generating quiz questions
        3. Optionally generating flashcards
        4. Returning a comprehensive result

        Args:
            content: Content to process
            content_type: Type of content (text, pdf, video)
            language: Language code
            generate_quiz: Whether to generate quiz
            generate_flashcards: Whether to generate flashcards

        Returns:
            Dictionary with processed content, quiz, and flashcards

        Raises:
            ServiceCommunicationError: If service communication fails
        """
        try:
            logger.info(
                f"Starting end-to-end content processing: "
                f"type={content_type}, language={language}"
            )

            result = {
                "processed_content": None,
                "quiz": None,
                "flashcards": None,
                "processing_time": 0,
            }

            start_time = datetime.now()

            # Step 1: Process content based on type
            if content_type == "text":
                processed = self.text_processor.process_text(content, language)
                result["processed_content"] = {
                    "id": processed.id,
                    "summary": processed.summary.text,
                    "key_points": processed.key_points,
                    "concepts": [
                        {"name": c.name, "description": c.description}
                        for c in processed.concepts
                    ],
                }
            else:
                raise ServiceCommunicationError(
                    message=f"Unsupported content type: {content_type}",
                    service="content_processing",
                )

            # Step 2: Generate quiz if requested
            if generate_quiz:
                logger.info("Generating quiz from processed content")
                quiz = self.quiz_generator.generate_quiz(
                    content=content,
                    question_count=10,
                )
                result["quiz"] = {
                    "id": quiz.id,
                    "title": quiz.title,
                    "question_count": len(quiz.questions),
                }

            # Step 3: Generate flashcards if requested
            if generate_flashcards:
                logger.info("Generating flashcards from processed content")
                flashcards = self.flashcard_generator.generate_flashcards(
                    content=content,
                    count=10,
                )
                result["flashcards"] = {
                    "count": len(flashcards),
                    "cards": [
                        {
                            "id": fc.id,
                            "question": fc.question,
                            "answer": fc.answer,
                        }
                        for fc in flashcards[:3]  # Return first 3 as preview
                    ],
                }

            # Calculate total processing time
            end_time = datetime.now()
            result["processing_time"] = (end_time - start_time).total_seconds()

            logger.info(
                f"End-to-end processing completed in {result['processing_time']:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Error in end-to-end processing: {e}", exc_info=True)
            raise ServiceCommunicationError(
                message=f"Failed to complete end-to-end processing: {str(e)}",
                service="orchestrator",
            )

    def process_voice_to_learning_materials(
        self,
        audio_data: bytes,
        language_code: str = "en-US",
    ) -> Dict[str, Any]:
        """
        Process voice input and generate learning materials.

        This workflow demonstrates:
        1. Voice transcription
        2. Content processing
        3. Learning material generation

        Args:
            audio_data: Audio data bytes
            language_code: Language code for transcription

        Returns:
            Dictionary with transcription and learning materials
        """
        try:
            logger.info("Starting voice-to-learning-materials workflow")

            # Step 1: Transcribe audio
            transcription = self.voice_service.process_voice_input(
                audio_data=audio_data,
                language_code=language_code,
            )

            # Step 2: Process transcribed text
            processed = self.text_processor.process_text(
                content=transcription.text,
                language=language_code.split("-")[0],  # Extract language code
            )

            # Step 3: Generate flashcards
            flashcards = self.flashcard_generator.generate_flashcards(
                content=transcription.text,
                count=5,
            )

            result = {
                "transcription": {
                    "text": transcription.text,
                    "confidence": transcription.confidence,
                },
                "summary": processed.summary.text,
                "key_points": processed.key_points,
                "flashcards": [
                    {
                        "question": fc.question,
                        "answer": fc.answer,
                    }
                    for fc in flashcards
                ],
            }

            logger.info("Voice-to-learning-materials workflow completed")
            return result

        except Exception as e:
            logger.error(f"Error in voice workflow: {e}", exc_info=True)
            raise ServiceCommunicationError(
                message=f"Failed to process voice to learning materials: {str(e)}",
                service="orchestrator",
            )

    def analyze_code_with_explanation(
        self,
        code: str,
        language: str,
        generate_audio: bool = False,
        audio_language: str = "en-US",
    ) -> Dict[str, Any]:
        """
        Analyze code and optionally generate audio explanation.

        This workflow demonstrates:
        1. Code analysis
        2. Text-to-speech synthesis for explanations

        Args:
            code: Code to analyze
            language: Programming language
            generate_audio: Whether to generate audio explanation
            audio_language: Language for audio synthesis

        Returns:
            Dictionary with code analysis and optional audio
        """
        try:
            logger.info(f"Analyzing code with language={language}")

            # Step 1: Analyze code
            analysis = self.code_analyzer.analyze_code(
                code=code,
                language=language,
            )

            result = {
                "explanation": analysis.explanation,
                "improvements_count": len(analysis.improvements),
                "issues_count": len(analysis.issues),
                "complexity": {
                    "cyclomatic": analysis.complexity.cyclomatic_complexity,
                    "cognitive": analysis.complexity.cognitive_complexity,
                },
            }

            # Step 2: Generate audio explanation if requested
            if generate_audio:
                logger.info("Generating audio explanation")
                audio_result = self.voice_service.generate_audio_response(
                    text=analysis.explanation,
                    language_code=audio_language,
                )
                result["audio_explanation"] = {
                    "available": True,
                    "format": "mp3",
                    "size": len(audio_result.audio_data),
                }

            logger.info("Code analysis with explanation completed")
            return result

        except Exception as e:
            logger.error(f"Error in code analysis workflow: {e}", exc_info=True)
            raise ServiceCommunicationError(
                message=f"Failed to analyze code with explanation: {str(e)}",
                service="orchestrator",
            )

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of all services.

        Returns:
            Dictionary with service health status
        """
        services = {
            "text_processor": self.text_processor,
            "pdf_processor": self.pdf_processor,
            "video_processor": self.video_processor,
            "flashcard_generator": self.flashcard_generator,
            "quiz_generator": self.quiz_generator,
            "code_analyzer": self.code_analyzer,
            "voice_service": self.voice_service,
            "multilingual_service": self.multilingual_service,
        }

        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
        }

        for service_name, service in services.items():
            try:
                # Check if service is initialized
                status["services"][service_name] = {
                    "status": "healthy",
                    "initialized": service is not None,
                }
            except Exception as e:
                status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return status


# Singleton instance
_orchestrator_instance: Optional[ServiceOrchestrator] = None


def get_orchestrator() -> ServiceOrchestrator:
    """
    Get singleton instance of ServiceOrchestrator.

    Returns:
        ServiceOrchestrator instance
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ServiceOrchestrator()
    return _orchestrator_instance
