"""Code analysis data models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProgrammingLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"


class IssueSeverity(str, Enum):
    """Severity levels for code issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LineAnalysis(BaseModel):
    """Analysis of a single line of code."""
    line_number: int = Field(..., ge=1, description="Line number")
    code: str = Field(..., description="Code content")
    explanation: str = Field(..., description="Explanation of what the line does")


class CodeIssue(BaseModel):
    """An issue detected in code."""
    severity: IssueSeverity = Field(..., description="Issue severity")
    line_number: Optional[int] = Field(None, description="Line number where issue occurs")
    message: str = Field(..., description="Issue description")
    suggestion: Optional[str] = Field(None, description="Suggested fix")
    category: str = Field(..., description="Issue category (e.g., 'performance', 'security')")


class Improvement(BaseModel):
    """A suggested improvement for code."""
    title: str = Field(..., description="Improvement title")
    description: str = Field(..., description="Detailed description")
    code_before: Optional[str] = Field(None, description="Original code")
    code_after: Optional[str] = Field(None, description="Improved code")
    benefit: str = Field(..., description="Benefit of applying this improvement")
    priority: str = Field(default="medium", description="Priority level")


class ComplexityMetrics(BaseModel):
    """Code complexity metrics."""
    cyclomatic_complexity: Optional[int] = Field(None, description="Cyclomatic complexity")
    cognitive_complexity: Optional[int] = Field(None, description="Cognitive complexity")
    lines_of_code: int = Field(..., ge=0, description="Total lines of code")
    comment_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="Comment to code ratio")


class CodeAnalysis(BaseModel):
    """Complete analysis of a code snippet."""
    explanation: str = Field(..., description="Overall code explanation")
    line_by_line_analysis: List[LineAnalysis] = Field(
        default_factory=list,
        description="Line-by-line analysis"
    )
    improvements: List[Improvement] = Field(
        default_factory=list,
        description="Suggested improvements"
    )
    issues: List[CodeIssue] = Field(
        default_factory=list,
        description="Detected issues"
    )
    complexity: ComplexityMetrics = Field(..., description="Complexity metrics")
    documentation_links: List[str] = Field(
        default_factory=list,
        description="Relevant documentation links"
    )
    best_practices: List[str] = Field(
        default_factory=list,
        description="Best practices recommendations"
    )


class CodeSnippet(BaseModel):
    """A code snippet submitted for analysis."""
    id: str = Field(..., description="Unique snippet identifier")
    user_id: str = Field(..., description="User who submitted the code")
    code: str = Field(..., description="Code content")
    language: ProgrammingLanguage = Field(..., description="Programming language")
    analysis: Optional[CodeAnalysis] = Field(None, description="Analysis results")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeExplanation(BaseModel):
    """Detailed explanation of code."""
    summary: str = Field(..., description="High-level summary")
    detailed_explanation: str = Field(..., description="Detailed explanation")
    line_by_line: List[LineAnalysis] = Field(
        default_factory=list,
        description="Line-by-line breakdown"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Key programming concepts used"
    )
    algorithm_steps: Optional[List[str]] = Field(
        None,
        description="Step-by-step algorithm breakdown for complex code"
    )
