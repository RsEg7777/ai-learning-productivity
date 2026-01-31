"""Text content processing service using Amazon Bedrock."""

import logging
import time
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ...shared.aws_clients.bedrock_client import BedrockClient
from ...shared.models.content import (
    ProcessedContent,
    Summary,
    SummaryType,
    SummaryNode,
    Concept,
)
from ...shared.utils.errors import ContentProcessingError, ProcessingTimeoutError

logger = logging.getLogger(__name__)


class TextProcessor:
    """Service for processing text content with Amazon Bedrock."""

    # Processing time limits (in seconds)
    TEXT_PROCESSING_TIMEOUT = 30

    # Word count threshold for hierarchical summaries
    HIERARCHICAL_THRESHOLD = 10000

    # Chunk size for processing large content
    CHUNK_SIZE = 8000  # words per chunk

    def __init__(self, bedrock_client: BedrockClient) -> None:
        """
        Initialize text processor.

        Args:
            bedrock_client: Bedrock client for LLM operations
        """
        self.bedrock_client = bedrock_client
        logger.info("Initialized TextProcessor")

    def process_text(
        self,
        text: str,
        language: str = "en",
        summary_type: Optional[SummaryType] = None,
    ) -> ProcessedContent:
        """
        Process text content with analysis and summarization.

        This method:
        1. Validates input and checks word count
        2. Determines appropriate summary type based on content length
        3. Generates summary (hierarchical for large content)
        4. Extracts key points and concepts
        5. Returns ProcessedContent within 30-second timeout

        Args:
            text: Text content to process
            language: Language code (default: "en")
            summary_type: Type of summary to generate (auto-detected if None)

        Returns:
            ProcessedContent with summary, key points, and concepts

        Raises:
            ContentProcessingError: If processing fails
            ProcessingTimeoutError: If processing exceeds 30 seconds
        """
        start_time = time.time()

        try:
            # Validate input
            if not text or not text.strip():
                raise ContentProcessingError(
                    message="Text content cannot be empty",
                    content_type="text",
                )

            # Count words
            word_count = self._count_words(text)
            logger.info(f"Processing text content: {word_count} words, language: {language}")

            # Determine summary type based on content length
            if summary_type is None:
                if word_count > self.HIERARCHICAL_THRESHOLD:
                    summary_type = SummaryType.HIERARCHICAL
                elif word_count > 2000:
                    summary_type = SummaryType.DETAILED
                else:
                    summary_type = SummaryType.BRIEF

            # Generate summary based on type
            if summary_type == SummaryType.HIERARCHICAL:
                summary = self._generate_hierarchical_summary(text, language)
            else:
                summary = self._generate_standard_summary(text, summary_type, language)

            # Check timeout after summary generation
            elapsed_time = time.time() - start_time
            if elapsed_time > self.TEXT_PROCESSING_TIMEOUT:
                raise ProcessingTimeoutError(
                    content_type="text",
                    time_limit=self.TEXT_PROCESSING_TIMEOUT,
                    time_elapsed=int(elapsed_time),
                )

            # Extract key points (if not already in summary)
            key_points = summary.key_points if summary.key_points else self._extract_key_points(text)

            # Extract concepts
            concepts = self._extract_concepts(text, language)

            # Calculate final processing time
            processing_time = time.time() - start_time

            # Create ProcessedContent
            processed_content = ProcessedContent(
                id=str(uuid.uuid4()),
                original_content=text,
                summary=summary,
                key_points=key_points,
                concepts=concepts,
                language=language,
                processing_time=processing_time,
                metadata={
                    "word_count": word_count,
                    "summary_type": summary_type.value,
                },
            )

            logger.info(
                f"Successfully processed text content in {processing_time:.2f}s "
                f"(word_count: {word_count}, summary_type: {summary_type.value})"
            )

            return processed_content

        except ProcessingTimeoutError:
            raise
        except ContentProcessingError:
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error processing text content: {e}")
            raise ContentProcessingError(
                message=f"Failed to process text content: {str(e)}",
                content_type="text",
                details={"elapsed_time": elapsed_time},
            )

    def _generate_standard_summary(
        self,
        text: str,
        summary_type: SummaryType,
        language: str,
    ) -> Summary:
        """
        Generate a standard (non-hierarchical) summary.

        Args:
            text: Text to summarize
            summary_type: Type of summary (brief, detailed, bullet_points)
            language: Language code

        Returns:
            Summary object
        """
        try:
            # Generate summary using Bedrock
            summary_text = self.bedrock_client.generate_summary(
                text=text,
                summary_type=summary_type.value,
                max_tokens=1024 if summary_type == SummaryType.BRIEF else 2048,
            )

            # Extract key points from summary
            key_points = self._extract_key_points_from_summary(summary_text)

            summary = Summary(
                id=str(uuid.uuid4()),
                content_id="",  # Will be set by caller
                type=summary_type,
                text=summary_text,
                key_points=key_points,
                hierarchical_structure=[],
                generated_at=datetime.utcnow(),
            )

            return summary

        except Exception as e:
            logger.error(f"Error generating standard summary: {e}")
            raise ContentProcessingError(
                message=f"Failed to generate summary: {str(e)}",
                content_type="text",
            )

    def _generate_hierarchical_summary(
        self,
        text: str,
        language: str,
    ) -> Summary:
        """
        Generate a hierarchical summary for large content (>10,000 words).

        This method:
        1. Splits content into manageable chunks
        2. Generates summaries for each chunk
        3. Creates hierarchical structure with main points and sub-points
        4. Combines into final hierarchical summary

        Args:
            text: Text to summarize
            language: Language code

        Returns:
            Summary object with hierarchical structure
        """
        try:
            logger.info("Generating hierarchical summary for large content")

            # Split text into chunks
            chunks = self._split_into_chunks(text, self.CHUNK_SIZE)
            logger.info(f"Split content into {len(chunks)} chunks")

            # Generate summaries for each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                chunk_summary = self.bedrock_client.generate_summary(
                    text=chunk,
                    summary_type="detailed",
                    max_tokens=1024,
                )
                chunk_summaries.append(chunk_summary)
                logger.debug(f"Generated summary for chunk {i+1}/{len(chunks)}")

            # Create hierarchical structure
            hierarchical_structure = self._build_hierarchical_structure(chunk_summaries)

            # Generate overall summary from chunk summaries
            combined_text = "\n\n".join(chunk_summaries)
            overall_summary = self.bedrock_client.generate_summary(
                text=combined_text,
                summary_type="hierarchical",
                max_tokens=2048,
            )

            # Extract key points from overall summary
            key_points = self._extract_key_points_from_summary(overall_summary)

            summary = Summary(
                id=str(uuid.uuid4()),
                content_id="",  # Will be set by caller
                type=SummaryType.HIERARCHICAL,
                text=overall_summary,
                key_points=key_points,
                hierarchical_structure=hierarchical_structure,
                generated_at=datetime.utcnow(),
            )

            logger.info("Successfully generated hierarchical summary")
            return summary

        except Exception as e:
            logger.error(f"Error generating hierarchical summary: {e}")
            raise ContentProcessingError(
                message=f"Failed to generate hierarchical summary: {str(e)}",
                content_type="text",
            )

    def _build_hierarchical_structure(
        self,
        chunk_summaries: List[str],
    ) -> List[SummaryNode]:
        """
        Build hierarchical structure from chunk summaries.

        Args:
            chunk_summaries: List of summaries for each chunk

        Returns:
            List of SummaryNode objects representing hierarchy
        """
        hierarchical_structure = []

        for i, chunk_summary in enumerate(chunk_summaries):
            # Create main node for this chunk
            main_node = SummaryNode(
                level=0,
                text=f"Section {i+1}",
                children=[],
            )

            # Extract sub-points from chunk summary
            sub_points = self._extract_sub_points(chunk_summary)

            # Create child nodes for sub-points
            for sub_point in sub_points:
                child_node = SummaryNode(
                    level=1,
                    text=sub_point,
                    children=[],
                )
                main_node.children.append(child_node)

            hierarchical_structure.append(main_node)

        return hierarchical_structure

    def _extract_sub_points(self, text: str) -> List[str]:
        """
        Extract sub-points from text.

        Looks for bullet points, numbered lists, or sentences.

        Args:
            text: Text to extract sub-points from

        Returns:
            List of sub-points
        """
        sub_points = []

        # Try to find bullet points or numbered lists
        bullet_pattern = r'^[\s]*[-•*]\s+(.+)$'
        numbered_pattern = r'^[\s]*\d+\.\s+(.+)$'

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for bullet points
            bullet_match = re.match(bullet_pattern, line)
            if bullet_match:
                sub_points.append(bullet_match.group(1))
                continue

            # Check for numbered lists
            numbered_match = re.match(numbered_pattern, line)
            if numbered_match:
                sub_points.append(numbered_match.group(1))
                continue

        # If no structured points found, split into sentences
        if not sub_points:
            sentences = re.split(r'[.!?]+', text)
            sub_points = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        # Limit to top 5 sub-points
        return sub_points[:5]

    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text using Bedrock.

        Args:
            text: Text to extract key points from

        Returns:
            List of key points
        """
        try:
            # Limit text length for key point extraction
            text_sample = text[:5000] if len(text) > 5000 else text

            prompt = f"""Extract the 5-7 most important key points from the following text. 
Return only the key points as a numbered list.

Text:
{text_sample}

Key Points:"""

            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=512,
                temperature=0.3,
            )

            # Parse key points from response
            key_points = self._parse_key_points(response)

            return key_points

        except Exception as e:
            logger.warning(f"Error extracting key points: {e}")
            return []

    def _extract_key_points_from_summary(self, summary_text: str) -> List[str]:
        """
        Extract key points from a summary text.

        Args:
            summary_text: Summary text

        Returns:
            List of key points
        """
        key_points = []

        # Look for bullet points or numbered lists
        bullet_pattern = r'^[\s]*[-•*]\s+(.+)$'
        numbered_pattern = r'^[\s]*\d+\.\s+(.+)$'

        lines = summary_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for bullet points
            bullet_match = re.match(bullet_pattern, line)
            if bullet_match:
                key_points.append(bullet_match.group(1))
                continue

            # Check for numbered lists
            numbered_match = re.match(numbered_pattern, line)
            if numbered_match:
                key_points.append(numbered_match.group(1))

        # If no structured points found, extract from summary
        if not key_points:
            key_points = self._extract_key_points(summary_text)

        return key_points[:7]  # Limit to 7 key points

    def _parse_key_points(self, text: str) -> List[str]:
        """
        Parse key points from LLM response.

        Args:
            text: LLM response text

        Returns:
            List of key points
        """
        key_points = []

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering and bullet points
            cleaned = re.sub(r'^[\d]+\.\s*', '', line)
            cleaned = re.sub(r'^[-•*]\s*', '', cleaned)

            if cleaned and len(cleaned) > 10:
                key_points.append(cleaned)

        return key_points

    def _extract_concepts(self, text: str, language: str) -> List[Concept]:
        """
        Extract key concepts from text using Bedrock.

        Args:
            text: Text to extract concepts from
            language: Language code

        Returns:
            List of Concept objects
        """
        try:
            # Limit text length for concept extraction
            text_sample = text[:5000] if len(text) > 5000 else text

            prompt = f"""Analyze the following text and extract the 5 most important concepts.
For each concept, provide:
1. Name (2-4 words)
2. Brief description (1 sentence)
3. Importance score (0.0 to 1.0)

Format your response as:
Concept: [name]
Description: [description]
Importance: [score]

Text:
{text_sample}"""

            response = self.bedrock_client.invoke_claude(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.3,
            )

            # Parse concepts from response
            concepts = self._parse_concepts(response)

            return concepts

        except Exception as e:
            logger.warning(f"Error extracting concepts: {e}")
            return []

    def _parse_concepts(self, text: str) -> List[Concept]:
        """
        Parse concepts from LLM response.

        Args:
            text: LLM response text

        Returns:
            List of Concept objects
        """
        concepts = []

        # Split by concept blocks
        concept_blocks = re.split(r'Concept:', text)

        for block in concept_blocks[1:]:  # Skip first empty block
            try:
                # Extract name
                name_match = re.search(r'^(.+?)(?:\n|Description:)', block)
                if not name_match:
                    continue
                name = name_match.group(1).strip()

                # Extract description
                desc_match = re.search(r'Description:\s*(.+?)(?:\n|Importance:)', block, re.DOTALL)
                description = desc_match.group(1).strip() if desc_match else ""

                # Extract importance
                imp_match = re.search(r'Importance:\s*([\d.]+)', block)
                importance = float(imp_match.group(1)) if imp_match else 0.5

                # Ensure importance is in valid range
                importance = max(0.0, min(1.0, importance))

                concept = Concept(
                    name=name,
                    description=description,
                    importance=importance,
                    related_concepts=[],
                )

                concepts.append(concept)

            except Exception as e:
                logger.warning(f"Error parsing concept block: {e}")
                continue

        return concepts[:5]  # Limit to 5 concepts

    def _count_words(self, text: str) -> int:
        """
        Count words in text.

        Args:
            text: Text to count words in

        Returns:
            Word count
        """
        # Split by whitespace and count non-empty tokens
        words = text.split()
        return len([w for w in words if w.strip()])

    def _split_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """
        Split text into chunks of approximately equal size.

        Tries to split at paragraph or sentence boundaries.

        Args:
            text: Text to split
            chunk_size: Target chunk size in words

        Returns:
            List of text chunks
        """
        words = text.split()
        total_words = len(words)

        if total_words <= chunk_size:
            return [text]

        chunks = []
        current_chunk = []
        current_size = 0

        # Split into paragraphs first
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            para_words = paragraph.split()
            para_size = len(para_words)

            # If adding this paragraph exceeds chunk size, start new chunk
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.extend(para_words)
            current_size += para_size

        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        logger.debug(f"Split {total_words} words into {len(chunks)} chunks")
        return chunks
