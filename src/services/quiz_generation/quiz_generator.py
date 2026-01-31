"""Quiz generation service with multiple question types using Amazon Bedrock."""

import logging
import uuid
import re
import random
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.models.quiz import Quiz, Question, QuestionType, DifficultyLevel
from ...shared.models.content import ProcessedContent
from ...shared.utils.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class QuizGenerator:
    """Service for generating quizzes with multiple question types from content."""

    # Default number of questions per quiz
    DEFAULT_QUESTION_COUNT = 10

    # Maximum tokens for quiz generation
    MAX_TOKENS = 4000

    # Question type distribution for balanced quizzes
    QUESTION_TYPE_DISTRIBUTION = {
        QuestionType.MULTIPLE_CHOICE: 0.5,  # 50% multiple choice
        QuestionType.TRUE_FALSE: 0.3,       # 30% true/false
        QuestionType.FILL_IN_BLANK: 0.2,    # 20% fill-in-blank
    }

    # Difficulty distribution for balanced quizzes
    DIFFICULTY_DISTRIBUTION = {
        DifficultyLevel.EASY: 0.3,    # 30% easy
        DifficultyLevel.MEDIUM: 0.5,  # 50% medium
        DifficultyLevel.HARD: 0.2,    # 20% hard
    }

    def __init__(self, bedrock_client: BedrockClient) -> None:
        """
        Initialize quiz generator.

        Args:
            bedrock_client: Bedrock client for LLM operations
        """
        self.bedrock_client = bedrock_client
        logger.info("Initialized QuizGenerator")

    def generate_quiz(
        self,
        content: ProcessedContent,
        title: Optional[str] = None,
        question_count: Optional[int] = None,
        time_limit: Optional[int] = None,
        passing_score: int = 70,
    ) -> Quiz:
        """
        Generate a quiz with multiple question types from processed content.

        This method:
        1. Validates the content
        2. Generates varied question types (multiple choice, true/false, fill-in-blank)
        3. Balances question difficulty levels
        4. Creates a complete quiz with metadata

        Args:
            content: Processed content to generate quiz from
            title: Quiz title (defaults to content-based title)
            question_count: Number of questions (default: DEFAULT_QUESTION_COUNT)
            time_limit: Time limit in seconds (optional)
            passing_score: Passing score percentage (default: 70)

        Returns:
            Quiz object with varied question types

        Raises:
            ContentProcessingError: If quiz generation fails
        """
        try:
            # Handle both string and Content object inputs
            if isinstance(content, str):
                content_text = content
                content_id = f"content_{hash(content)}"
                content_language = "en"
                quiz_title = title or "Generated Quiz"
            else:
                # Validate content object
                if not content or not content.original_content:
                    raise ContentProcessingError(
                        message="Content cannot be empty for quiz generation",
                        content_type="quiz",
                    )
                content_text = content.original_content
                content_id = content.id
                content_language = content.language
                quiz_title = title or f"Quiz: {content.summary.text[:50]}..." if content.summary else "Generated Quiz"

            # Set defaults
            target_count = question_count or self.DEFAULT_QUESTION_COUNT

            logger.info(
                f"Generating quiz with {target_count} questions from content "
                f"(id: {content_id}, language: {content_language})"
            )

            # Generate questions with varied types
            questions = self._generate_questions(
                content_text=content_text,
                count=target_count,
            )
            
            logger.info(f"Generated {len(questions)} questions total")

            # Create quiz object
            quiz = Quiz(
                id=str(uuid.uuid4()),
                content_id=content_id,
                title=quiz_title,
                questions=questions,
                time_limit=time_limit,
                passing_score=passing_score,
                created_at=datetime.utcnow(),
            )

            # Log question type and difficulty distribution
            self._log_quiz_statistics(quiz)

            return quiz

        except ContentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise ContentProcessingError(
                message=f"Failed to generate quiz: {str(e)}",
                content_type="quiz",
            )

    def _generate_questions(
        self,
        content_text: str,
        count: int,
    ) -> List[Question]:
        """
        Generate questions with varied types and balanced difficulty.

        Args:
            content: Processed content
            count: Number of questions to generate

        Returns:
            List of Question objects with varied types
        """
        try:
            # Calculate question type distribution
            type_counts = self._calculate_question_type_counts(count)
            
            # Calculate difficulty distribution
            difficulty_counts = self._calculate_difficulty_counts(count)

            logger.info(
                f"Generating questions - Types: {type_counts}, Difficulties: {difficulty_counts}"
            )

            # Generate questions for each type
            all_questions = []

            # Generate multiple choice questions
            if type_counts[QuestionType.MULTIPLE_CHOICE] > 0:
                mc_questions = self._generate_multiple_choice_questions(
                    content_text=content_text,
                    count=type_counts[QuestionType.MULTIPLE_CHOICE],
                )
                all_questions.extend(mc_questions)

            # Generate true/false questions
            if type_counts[QuestionType.TRUE_FALSE] > 0:
                tf_questions = self._generate_true_false_questions(
                    content_text=content_text,
                    count=type_counts[QuestionType.TRUE_FALSE],
                )
                all_questions.extend(tf_questions)

            # Generate fill-in-blank questions
            if type_counts[QuestionType.FILL_IN_BLANK] > 0:
                fib_questions = self._generate_fill_in_blank_questions(
                    content_text=content_text,
                    count=type_counts[QuestionType.FILL_IN_BLANK],
                )
                all_questions.extend(fib_questions)

            # Balance difficulty levels
            all_questions = self._balance_difficulty(all_questions, difficulty_counts)

            # Ensure we have the requested count
            if len(all_questions) < count:
                logger.warning(
                    f"Generated only {len(all_questions)} questions, expected {count}. "
                    f"Will return available questions."
                )

            # Shuffle questions for variety
            random.shuffle(all_questions)

            return all_questions[:count]

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            raise

    def _calculate_question_type_counts(self, total_count: int) -> Dict[QuestionType, int]:
        """
        Calculate how many questions of each type to generate.

        Args:
            total_count: Total number of questions

        Returns:
            Dictionary mapping question types to counts
        """
        counts = {}
        remaining = total_count

        # Calculate counts based on distribution
        for q_type, ratio in self.QUESTION_TYPE_DISTRIBUTION.items():
            count = int(total_count * ratio)
            counts[q_type] = count
            remaining -= count

        # Distribute remaining questions
        if remaining > 0:
            # Add remaining to multiple choice (most versatile)
            counts[QuestionType.MULTIPLE_CHOICE] += remaining

        return counts

    def _calculate_difficulty_counts(self, total_count: int) -> Dict[DifficultyLevel, int]:
        """
        Calculate how many questions of each difficulty to generate.

        Args:
            total_count: Total number of questions

        Returns:
            Dictionary mapping difficulty levels to counts
        """
        counts = {}
        remaining = total_count

        # Calculate counts based on distribution
        for difficulty, ratio in self.DIFFICULTY_DISTRIBUTION.items():
            count = int(total_count * ratio)
            counts[difficulty] = count
            remaining -= count

        # Distribute remaining questions
        if remaining > 0:
            # Add remaining to medium difficulty
            counts[DifficultyLevel.MEDIUM] += remaining

        return counts

    def _generate_multiple_choice_questions(
        self,
        content_text: str,
        count: int,
    ) -> List[Question]:
        """
        Generate multiple choice questions.

        Args:
            content_text: Content text to generate questions from
            count: Number of questions to generate

        Returns:
            List of multiple choice Question objects
        """
        try:
            # Prepare content for prompt
            if len(content_text) > 6000:
                content_text = content_text[:6000]

            # Create prompt
            prompt = f"""Generate exactly {count} multiple choice questions from the following content.

Content:
{content_text}

For each question, provide:
1. Question text
2. Four answer options (A, B, C, D)
3. Correct answer (letter)
4. Explanation of why the answer is correct
5. Difficulty level (easy, medium, or hard)

Format your response EXACTLY as follows:

QUESTION 1
Text: [question text]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Correct: [A/B/C/D]
Explanation: [explanation]
Difficulty: [easy/medium/hard]

Continue this pattern for all {count} questions.

Guidelines:
- Make questions clear and unambiguous
- Ensure all options are plausible
- Vary difficulty levels
- Test understanding, not just memorization"""

            # Invoke Bedrock
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=self.MAX_TOKENS,
                temperature=0.7,
            )

            # Parse questions
            questions = self._parse_multiple_choice_questions(response)

            # Ensure we have enough questions
            if len(questions) < count:
                logger.warning(
                    f"Generated only {len(questions)} multiple choice questions, expected {count}"
                )

            return questions[:count]

        except Exception as e:
            logger.error(f"Error generating multiple choice questions: {e}")
            return []

    def _generate_true_false_questions(
        self,
        content_text: str,
        count: int,
    ) -> List[Question]:
        """
        Generate true/false questions.

        Args:
            content_text: Content text to generate questions from
            count: Number of questions to generate

        Returns:
            List of true/false Question objects
        """
        try:
            # Prepare content for prompt
            if len(content_text) > 6000:
                content_text = content_text[:6000]

            # Create prompt
            prompt = f"""Generate exactly {count} true/false questions from the following content.

Content:
{content_text}

For each question, provide:
1. A statement that is either true or false
2. The correct answer (True or False)
3. Explanation of why the statement is true or false
4. Difficulty level (easy, medium, or hard)

Format your response EXACTLY as follows:

QUESTION 1
Statement: [statement]
Answer: [True/False]
Explanation: [explanation]
Difficulty: [easy/medium/hard]

Continue this pattern for all {count} questions.

Guidelines:
- Make statements clear and specific
- Avoid ambiguous or trick questions
- Balance true and false answers
- Vary difficulty levels"""

            # Invoke Bedrock
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=self.MAX_TOKENS,
                temperature=0.7,
            )

            # Parse questions
            questions = self._parse_true_false_questions(response)

            # Ensure we have enough questions
            if len(questions) < count:
                logger.warning(
                    f"Generated only {len(questions)} true/false questions, expected {count}"
                )

            return questions[:count]

        except Exception as e:
            logger.error(f"Error generating true/false questions: {e}")
            return []

    def _generate_fill_in_blank_questions(
        self,
        content_text: str,
        count: int,
    ) -> List[Question]:
        """
        Generate fill-in-the-blank questions.

        Args:
            content_text: Content text to generate questions from
            count: Number of questions to generate

        Returns:
            List of fill-in-blank Question objects
        """
        try:
            # Prepare content for prompt
            if len(content_text) > 6000:
                content_text = content_text[:6000]

            # Create prompt
            prompt = f"""Generate exactly {count} fill-in-the-blank questions from the following content.

Content:
{content_text}

For each question, provide:
1. A sentence with a blank (use _____ for the blank)
2. The correct answer to fill in the blank
3. Explanation of the answer
4. Difficulty level (easy, medium, or hard)

Format your response EXACTLY as follows:

QUESTION 1
Text: [sentence with _____ for blank]
Answer: [correct answer]
Explanation: [explanation]
Difficulty: [easy/medium/hard]

Continue this pattern for all {count} questions.

Guidelines:
- Make the blank test key concepts or terms
- Ensure only one correct answer fits naturally
- The sentence should make sense with the answer filled in
- Vary difficulty levels"""

            # Invoke Bedrock
            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=self.MAX_TOKENS,
                temperature=0.7,
            )

            # Parse questions
            questions = self._parse_fill_in_blank_questions(response)

            # Ensure we have enough questions
            if len(questions) < count:
                logger.warning(
                    f"Generated only {len(questions)} fill-in-blank questions, expected {count}"
                )

            return questions[:count]

        except Exception as e:
            logger.error(f"Error generating fill-in-blank questions: {e}")
            return []

    def _parse_multiple_choice_questions(self, response: str) -> List[Question]:
        """
        Parse multiple choice questions from LLM response.

        Args:
            response: LLM response text

        Returns:
            List of Question objects
        """
        questions = []
        question_blocks = re.split(r'QUESTION\s+\d+', response)

        for block in question_blocks:
            if not block.strip():
                continue

            try:
                # Extract question text
                text_match = re.search(r'Text:\s*(.+?)(?=\n[A-D]\))', block, re.DOTALL)
                if not text_match:
                    continue
                question_text = text_match.group(1).strip()

                # Extract options
                options = []
                for letter in ['A', 'B', 'C', 'D']:
                    option_match = re.search(rf'{letter}\)\s*(.+?)(?=\n(?:[A-D]\)|Correct:|$))', block, re.DOTALL)
                    if option_match:
                        options.append(option_match.group(1).strip())

                if len(options) != 4:
                    continue

                # Extract correct answer
                correct_match = re.search(r'Correct:\s*([A-D])', block, re.IGNORECASE)
                if not correct_match:
                    continue
                correct_letter = correct_match.group(1).upper()
                correct_index = ord(correct_letter) - ord('A')
                correct_answer = options[correct_index]

                # Extract explanation
                explanation_match = re.search(r'Explanation:\s*(.+?)(?=\nDifficulty:|$)', block, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."

                # Extract difficulty
                difficulty_match = re.search(r'Difficulty:\s*(easy|medium|hard)', block, re.IGNORECASE)
                difficulty_str = difficulty_match.group(1).lower() if difficulty_match else "medium"
                difficulty = self._parse_difficulty(difficulty_str)

                # Create question
                question = Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.MULTIPLE_CHOICE,
                    text=question_text,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    points=1,
                    difficulty=difficulty,
                )

                questions.append(question)

            except Exception as e:
                logger.warning(f"Error parsing multiple choice question block: {e}")
                continue

        logger.debug(f"Parsed {len(questions)} multiple choice questions")
        return questions

    def _parse_true_false_questions(self, response: str) -> List[Question]:
        """
        Parse true/false questions from LLM response.

        Args:
            response: LLM response text

        Returns:
            List of Question objects
        """
        questions = []
        question_blocks = re.split(r'QUESTION\s+\d+', response)

        for block in question_blocks:
            if not block.strip():
                continue

            try:
                # Extract statement
                statement_match = re.search(r'Statement:\s*(.+?)(?=\nAnswer:|$)', block, re.DOTALL)
                if not statement_match:
                    continue
                statement = statement_match.group(1).strip()

                # Extract answer
                answer_match = re.search(r'Answer:\s*(True|False)', block, re.IGNORECASE)
                if not answer_match:
                    continue
                correct_answer = answer_match.group(1).capitalize()

                # Extract explanation
                explanation_match = re.search(r'Explanation:\s*(.+?)(?=\nDifficulty:|$)', block, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."

                # Extract difficulty
                difficulty_match = re.search(r'Difficulty:\s*(easy|medium|hard)', block, re.IGNORECASE)
                difficulty_str = difficulty_match.group(1).lower() if difficulty_match else "medium"
                difficulty = self._parse_difficulty(difficulty_str)

                # Create question
                question = Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.TRUE_FALSE,
                    text=statement,
                    options=["True", "False"],
                    correct_answer=correct_answer,
                    explanation=explanation,
                    points=1,
                    difficulty=difficulty,
                )

                questions.append(question)

            except Exception as e:
                logger.warning(f"Error parsing true/false question block: {e}")
                continue

        logger.debug(f"Parsed {len(questions)} true/false questions")
        return questions

    def _parse_fill_in_blank_questions(self, response: str) -> List[Question]:
        """
        Parse fill-in-blank questions from LLM response.

        Args:
            response: LLM response text

        Returns:
            List of Question objects
        """
        questions = []
        question_blocks = re.split(r'QUESTION\s+\d+', response)

        for block in question_blocks:
            if not block.strip():
                continue

            try:
                # Extract question text
                text_match = re.search(r'Text:\s*(.+?)(?=\nAnswer:|$)', block, re.DOTALL)
                if not text_match:
                    continue
                question_text = text_match.group(1).strip()

                # Ensure it has a blank
                if '_____' not in question_text and '____' not in question_text and '___' not in question_text:
                    continue

                # Extract answer
                answer_match = re.search(r'Answer:\s*(.+?)(?=\nExplanation:|$)', block, re.DOTALL)
                if not answer_match:
                    continue
                correct_answer = answer_match.group(1).strip()

                # Extract explanation
                explanation_match = re.search(r'Explanation:\s*(.+?)(?=\nDifficulty:|$)', block, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."

                # Extract difficulty
                difficulty_match = re.search(r'Difficulty:\s*(easy|medium|hard)', block, re.IGNORECASE)
                difficulty_str = difficulty_match.group(1).lower() if difficulty_match else "medium"
                difficulty = self._parse_difficulty(difficulty_str)

                # Create question
                question = Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.FILL_IN_BLANK,
                    text=question_text,
                    options=None,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    points=1,
                    difficulty=difficulty,
                )

                questions.append(question)

            except Exception as e:
                logger.warning(f"Error parsing fill-in-blank question block: {e}")
                continue

        logger.debug(f"Parsed {len(questions)} fill-in-blank questions")
        return questions

    def _balance_difficulty(
        self,
        questions: List[Question],
        target_counts: Dict[DifficultyLevel, int],
    ) -> List[Question]:
        """
        Balance question difficulty levels to match target distribution.

        Args:
            questions: List of questions
            target_counts: Target counts for each difficulty level

        Returns:
            Balanced list of questions
        """
        # Group questions by difficulty
        by_difficulty = {
            DifficultyLevel.EASY: [],
            DifficultyLevel.MEDIUM: [],
            DifficultyLevel.HARD: [],
        }

        for question in questions:
            by_difficulty[question.difficulty].append(question)

        # Select questions to match target distribution
        balanced = []

        for difficulty, target_count in target_counts.items():
            available = by_difficulty[difficulty]
            
            if len(available) >= target_count:
                # We have enough, select randomly
                selected = random.sample(available, target_count)
            else:
                # Not enough, take all and adjust others
                selected = available
                shortage = target_count - len(available)
                
                # Try to fill from medium difficulty first
                if difficulty != DifficultyLevel.MEDIUM and by_difficulty[DifficultyLevel.MEDIUM]:
                    extra = by_difficulty[DifficultyLevel.MEDIUM][:shortage]
                    selected.extend(extra)
                    by_difficulty[DifficultyLevel.MEDIUM] = by_difficulty[DifficultyLevel.MEDIUM][shortage:]

            balanced.extend(selected)

        return balanced

    def _generate_fallback_questions(
        self,
        content: ProcessedContent,
        count: int,
    ) -> List[Question]:
        """
        Generate simple fallback questions when other methods fail.

        Args:
            content: Processed content
            count: Number of questions to generate

        Returns:
            List of Question objects
        """
        questions = []

        # Generate simple true/false questions from key points
        if content.key_points:
            for i, key_point in enumerate(content.key_points):
                if len(questions) >= count:
                    break

                question = Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.TRUE_FALSE,
                    text=f"The content states: {key_point}",
                    options=["True", "False"],
                    correct_answer="True",
                    explanation=f"This is a key point from the content: {key_point}",
                    points=1,
                    difficulty=DifficultyLevel.EASY,
                )
                questions.append(question)

        # If still need more, generate from concepts
        if len(questions) < count and content.concepts:
            for concept in content.concepts:
                if len(questions) >= count:
                    break

                question = Question(
                    id=str(uuid.uuid4()),
                    type=QuestionType.FILL_IN_BLANK,
                    text=f"_____ is defined as: {concept.description}",
                    options=None,
                    correct_answer=concept.name,
                    explanation=f"The concept {concept.name} is defined in the content.",
                    points=1,
                    difficulty=DifficultyLevel.MEDIUM,
                )
                questions.append(question)

        return questions[:count]

    def _parse_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """
        Parse difficulty level from string.

        Args:
            difficulty_str: Difficulty string

        Returns:
            DifficultyLevel enum value
        """
        difficulty_map = {
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
        }
        return difficulty_map.get(difficulty_str.lower(), DifficultyLevel.MEDIUM)

    def _log_quiz_statistics(self, quiz: Quiz) -> None:
        """
        Log statistics about the generated quiz.

        Args:
            quiz: Generated quiz
        """
        # Count question types
        type_counts = {
            QuestionType.MULTIPLE_CHOICE: 0,
            QuestionType.TRUE_FALSE: 0,
            QuestionType.FILL_IN_BLANK: 0,
        }

        # Count difficulty levels
        difficulty_counts = {
            DifficultyLevel.EASY: 0,
            DifficultyLevel.MEDIUM: 0,
            DifficultyLevel.HARD: 0,
        }

        for question in quiz.questions:
            type_counts[question.type] += 1
            difficulty_counts[question.difficulty] += 1

        logger.info(
            f"Generated quiz '{quiz.title}' with {len(quiz.questions)} questions - "
            f"Types: MC={type_counts[QuestionType.MULTIPLE_CHOICE]}, "
            f"TF={type_counts[QuestionType.TRUE_FALSE]}, "
            f"FIB={type_counts[QuestionType.FILL_IN_BLANK]} | "
            f"Difficulty: Easy={difficulty_counts[DifficultyLevel.EASY]}, "
            f"Medium={difficulty_counts[DifficultyLevel.MEDIUM]}, "
            f"Hard={difficulty_counts[DifficultyLevel.HARD]}"
        )
