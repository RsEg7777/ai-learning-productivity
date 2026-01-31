"""Content-related data models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Supported content types."""
    TEXT = "text"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"


class SummaryType(str, Enum):
    """Types of summaries that can be generated."""
    BRIEF = "brief"
    DETAILED = "detailed"
    HIERARCHICAL = "hierarchical"
    BULLET_POINTS = "bullet_points"


class SummaryNode(BaseModel):
    """Node in a hierarchical summary structure."""
    level: int = Field(..., description="Hierarchy level (0 = top level)")
    text: str = Field(..., description="Summary text for this node")
    children: List["SummaryNode"] = Field(default_factory=list, description="Child nodes")


class Summary(BaseModel):
    """Summary of processed content."""
    id: str = Field(..., description="Unique summary identifier")
    content_id: str = Field(..., description="ID of the source content")
    type: SummaryType = Field(..., description="Type of summary")
    text: str = Field(..., description="Summary text")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    hierarchical_structure: List[SummaryNode] = Field(
        default_factory=list, 
        description="Hierarchical structure for large content"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class Concept(BaseModel):
    """A concept extracted from content."""
    name: str = Field(..., description="Concept name")
    description: str = Field(..., description="Concept description")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance score (0-1)")
    related_concepts: List[str] = Field(default_factory=list, description="Related concept names")


class ContentMetadata(BaseModel):
    """Metadata for uploaded content."""
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    duration: Optional[float] = Field(None, description="Duration in seconds (for audio/video)")
    page_count: Optional[int] = Field(None, description="Number of pages (for PDFs)")
    word_count: Optional[int] = Field(None, description="Word count")
    language_detected: Optional[str] = Field(None, description="Detected language code")


class Content(BaseModel):
    """Content uploaded by users."""
    id: str = Field(..., description="Unique content identifier")
    user_id: str = Field(..., description="User who uploaded the content")
    title: str = Field(..., description="Content title")
    type: ContentType = Field(..., description="Content type")
    original_text: str = Field(..., description="Original text content")
    processed_summary: Optional[str] = Field(None, description="Processed summary")
    language: str = Field(default="en", description="Content language code")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    s3_location: Optional[str] = Field(None, description="S3 storage location")
    metadata: ContentMetadata = Field(default_factory=ContentMetadata, description="Content metadata")


class ProcessedContent(BaseModel):
    """Result of content processing."""
    id: str = Field(..., description="Unique identifier")
    original_content: str = Field(..., description="Original content text")
    summary: Summary = Field(..., description="Generated summary")
    key_points: List[str] = Field(default_factory=list, description="Extracted key points")
    concepts: List[Concept] = Field(default_factory=list, description="Extracted concepts")
    language: str = Field(..., description="Content language")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
