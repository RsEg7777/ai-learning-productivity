"""Flashcard generation service using Amazon Bedrock."""

import logging
import uuid
import re
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.models.quiz import Flashcard, DifficultyLevel, SpacedRepetitionData
from ...shared.models.content import ProcessedContent
from ...shared.utils.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Service for generating flashcards from processed content."""

    # Minimum number of flashcards to generate per content piece
    MIN_FLASHCARDS = 10

    # Maximum tokens for flashcard generation
    MAX_TOKENS = 3000

    def __init__(self, bedrock_client: BedrockClient) -> None:
        """
        Initialize flashcard generator.

        Args:
            bedrock_client: Bedrock client for LLM operations
        """
        self.bedrock_client = bedrock_client
        logger.info("Initialized FlashcardGenerator")

    def generate_flashcards(
        self,
        content: ProcessedContent,
        count: Optional[int] = None,
    ) -> List[Flashcard]:
        """
        Generate flashcards from processed content.

        This method:
        1. Validates the content
        2. Generates at least MIN_FLASHCARDS (10) question-answer pairs
        3. Assigns difficulty levels based on complexity
        4. Adds relevant tags for categorization
        5. Initializes spaced repetition data

        Args:
            content: Processed content or string to generate flashcards from
            count: Number of flashcards to generate (minimum MIN_FLASHCARDS)

        Returns:
            List of Flashcard objects

        Raises:
            ContentProcessingError: If flashcard generation fails
        """
        try:
            # Handle both string and Content object inputs
            if isinstance(content, str):
                content_text = content
                content_id = f"content_{hash(content)}"
                content_language = "en"
            else:
                # Validate content object
                if not content or not content.original_content:
                    raise ContentProcessingError(
                        message="Content cannot be empty for flashcard generation",
                        content_type="flashcard",
                    )
                content_text = content.original_content
                content_id = content.id
                content_language = content.language

            # Ensure minimum count
            target_count = max(count or self.MIN_FLASHCARDS, self.MIN_FLASHCARDS)

            logger.info(
                f"Generating {target_count} flashcards from content "
                f"(id: {content_id}, language: {content_language})"
            )

            # Generate flashcards using Bedrock
            flashcard_data = self._generate_flashcard_data(
                content_text=content_text,
                count=target_count,
            )

            # Create Flashcard objects
            flashcards = []
            for data in flashcard_data:
                flashcard = Flashcard(
                    id=str(uuid.uuid4()),
                    content_id=content_id,
                    question=data["question"],
                    answer=data["answer"],
                    difficulty=data["difficulty"],
                    tags=data["tags"],
                    repetition_data=SpacedRepetitionData(),
                    created_at=datetime.utcnow(),
                )
                flashcards.append(flashcard)

            logger.info(
                f"Successfully generated {len(flashcards)} flashcards "
                f"(easy: {sum(1 for f in flashcards if f.difficulty == DifficultyLevel.EASY)}, "
                f"medium: {sum(1 for f in flashcards if f.difficulty == DifficultyLevel.MEDIUM)}, "
                f"hard: {sum(1 for f in flashcards if f.difficulty == DifficultyLevel.HARD)})"
            )

            return flashcards

        except ContentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise ContentProcessingError(
                message=f"Failed to generate flashcards: {str(e)}",
                content_type="flashcard",
            )

    def _generate_flashcard_data(
        self,
        content_text: str,
        count: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcard data using Bedrock.

        Args:
            content_text: Content text to generate flashcards from
            count: Number of flashcards to generate

        Returns:
            List of dictionaries with flashcard data
        """
        try:
            # Limit content length to avoid token limits
            if len(content_text) > 8000:
                content_text = content_text[:8000]

            # Create prompt for flashcard generation
            prompt = f"""Generate exactly {count} flashcards from the following content. 
Each flashcard should have a clear question and a concise answer.

Content:
{content_text}

For each flashcard, provide:
1. Question: A clear, specific question
2. Answer: A concise, accurate answer (2-4 sentences)
3. Difficulty: easy, medium, or hard
4. Tags: 2-3 relevant tags (comma-separated)

Format your response EXACTLY as follows for each flashcard:

FLASHCARD 1
Question: [question text]
Answer: [answer text]
Difficulty: [easy/medium/hard]
Tags: [tag1, tag2, tag3]

FLASHCARD 2
Question: [question text]
Answer: [answer text]
Difficulty: [easy/medium/hard]
Tags: [tag1, tag2, tag3]

Continue this pattern for all {count} flashcards.

Guidelines:
- Questions should test understanding, not just memorization
- Vary difficulty levels (mix of easy, medium, and hard)
- Include factual recall, conceptual understanding, and application questions
- Keep answers clear and concise
- Use relevant tags that categorize the content"""

            # Invoke Bedrock to generate flashcards
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=self.MAX_TOKENS,
                temperature=0.7,
            )

            # Parse flashcards from response
            flashcard_data = self._parse_flashcards(response)

            # Ensure we have at least the minimum number
            if len(flashcard_data) < count:
                logger.warning(
                    f"Generated only {len(flashcard_data)} flashcards, "
                    f"expected at least {count}"
                )
                
                # If we didn't get enough, generate additional using simple method
                additional_needed = count - len(flashcard_data)
                additional_flashcards = self._generate_simple_flashcards(
                    content=content_text,
                    count=additional_needed,
                )
                flashcard_data.extend(additional_flashcards)

            return flashcard_data[:count]  # Return exactly the requested count

        except Exception as e:
            logger.error(f"Error generating flashcard data: {e}")
            raise

    def _parse_flashcards(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse flashcards from LLM response.

        Args:
            response: LLM response text

        Returns:
            List of dictionaries with flashcard data
        """
        flashcards = []

        # Split by FLASHCARD markers
        flashcard_blocks = re.split(r'FLASHCARD\s+\d+', response)

        for block in flashcard_blocks:
            if not block.strip():
                continue

            try:
                # Extract question
                question_match = re.search(r'Question:\s*(.+?)(?=\n(?:Answer:|$))', block, re.DOTALL)
                if not question_match:
                    continue
                question = question_match.group(1).strip()

                # Extract answer
                answer_match = re.search(r'Answer:\s*(.+?)(?=\n(?:Difficulty:|$))', block, re.DOTALL)
                if not answer_match:
                    continue
                answer = answer_match.group(1).strip()

                # Extract difficulty
                difficulty_match = re.search(r'Difficulty:\s*(easy|medium|hard)', block, re.IGNORECASE)
                difficulty_str = difficulty_match.group(1).lower() if difficulty_match else "medium"
                difficulty = self._parse_difficulty(difficulty_str)

                # Extract tags
                tags_match = re.search(r'Tags:\s*(.+?)(?=\n|$)', block)
                tags = []
                if tags_match:
                    tags_str = tags_match.group(1).strip()
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]

                # Ensure we have at least some tags
                if not tags:
                    tags = ["general"]

                flashcard_data = {
                    "question": question,
                    "answer": answer,
                    "difficulty": difficulty,
                    "tags": tags[:3],  # Limit to 3 tags
                }

                flashcards.append(flashcard_data)

            except Exception as e:
                logger.warning(f"Error parsing flashcard block: {e}")
                continue

        logger.debug(f"Parsed {len(flashcards)} flashcards from response")
        return flashcards

    def _generate_simple_flashcards(
        self,
        content: Any,
        count: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate simple flashcards as fallback.

        Uses key points and concepts to create basic flashcards.
        If not enough key points/concepts, creates generic flashcards from summary.

        Args:
            content: Processed content
            count: Number of flashcards to generate

        Returns:
            List of dictionaries with flashcard data
        """
        flashcards = []

        # If a plain string was provided, construct a minimal ProcessedContent
        if isinstance(content, str):
            from ...shared.models.content import Summary, SummaryType

            summary = Summary(
                id=str(uuid.uuid4()),
                content_id="fallback",
                type=SummaryType.BRIEF,
                text=content[:2000] if len(content) > 2000 else content,
                key_points=[],
                hierarchical_structure=[],
                generated_at=datetime.utcnow(),
            )

            content = ProcessedContent(
                id="fallback",
                original_content=content,
                summary=summary,
                key_points=[],
                concepts=[],
                language="en",
                processing_time=0.0,
                metadata={},
            )

        # Generate from key points
        if content.key_points:
            for i, key_point in enumerate(content.key_points):
                if len(flashcards) >= count:
                    break
                flashcard = {
                    "question": f"What is important to know about: {key_point[:50]}...?",
                    "answer": key_point,
                    "difficulty": DifficultyLevel.EASY,
                    "tags": ["key-point", "summary"],
                }
                flashcards.append(flashcard)

        # Generate from concepts
        if content.concepts and len(flashcards) < count:
            for concept in content.concepts:
                if len(flashcards) >= count:
                    break
                flashcard = {
                    "question": f"What is {concept.name}?",
                    "answer": concept.description,
                    "difficulty": self._determine_difficulty_from_importance(concept.importance),
                    "tags": ["concept", concept.name.lower().replace(" ", "-")],
                }
                flashcards.append(flashcard)

        # If still not enough, generate generic flashcards from summary
        if len(flashcards) < count and content.summary:
            summary_text = content.summary.text
            # Split summary into sentences
            sentences = [s.strip() for s in summary_text.split('.') if s.strip() and len(s.strip()) > 20]
            
            for i, sentence in enumerate(sentences):
                if len(flashcards) >= count:
                    break
                # Create a simple Q&A from the sentence
                flashcard = {
                    "question": f"What does the content say about topic {len(flashcards) + 1}?",
                    "answer": sentence + ".",
                    "difficulty": DifficultyLevel.EASY,
                    "tags": ["summary", "general"],
                }
                flashcards.append(flashcard)

        # If still not enough, create very basic flashcards
        while len(flashcards) < count:
            flashcard = {
                "question": f"What is a key concept from this content? (Question {len(flashcards) + 1})",
                "answer": content.summary.text[:200] if content.summary else content.original_content[:200],
                "difficulty": DifficultyLevel.EASY,
                "tags": ["general", "fallback"],
            }
            flashcards.append(flashcard)

        return flashcards[:count]

    def _parse_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """
        Parse difficulty level from string.

        Args:
            difficulty_str: Difficulty string (easy, medium, hard)

        Returns:
            DifficultyLevel enum value
        """
        difficulty_map = {
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
        }
        return difficulty_map.get(difficulty_str.lower(), DifficultyLevel.MEDIUM)

    def _determine_difficulty_from_importance(self, importance: float) -> DifficultyLevel:
        """
        Determine difficulty level based on concept importance.

        Args:
            importance: Importance score (0.0 to 1.0)

        Returns:
            DifficultyLevel enum value
        """
        if importance >= 0.8:
            return DifficultyLevel.HARD
        elif importance >= 0.5:
            return DifficultyLevel.MEDIUM
        else:
            return DifficultyLevel.EASY

    def generate_flashcards_from_text(
        self,
        text: str,
        content_id: str,
        language: str = "en",
        count: Optional[int] = None,
    ) -> List[Flashcard]:
        """
        Generate flashcards directly from text content.

        Convenience method that doesn't require ProcessedContent.

        Args:
            text: Text content
            content_id: Content identifier
            language: Language code
            count: Number of flashcards to generate

        Returns:
            List of Flashcard objects

        Raises:
            ContentProcessingError: If flashcard generation fails
        """
        try:
            # Create a minimal ProcessedContent object
            from ...shared.models.content import Summary, SummaryType

            summary = Summary(
                id=str(uuid.uuid4()),
                content_id=content_id,
                type=SummaryType.BRIEF,
                text=text[:2000] if len(text) > 2000 else text,
                key_points=[],
                hierarchical_structure=[],
                generated_at=datetime.utcnow(),
            )

            processed_content = ProcessedContent(
                id=content_id,
                original_content=text,
                summary=summary,
                key_points=[],
                concepts=[],
                language=language,
                processing_time=0.0,
                metadata={},
            )

            return self.generate_flashcards(
                content=processed_content,
                count=count,
            )

        except Exception as e:
            logger.error(f"Error generating flashcards from text: {e}")
            raise ContentProcessingError(
                message=f"Failed to generate flashcards from text: {str(e)}",
                content_type="flashcard",
            )
