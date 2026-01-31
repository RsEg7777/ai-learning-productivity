"""Unit tests for code issue detection and suggestions (Task 8.3)."""

import pytest
from unittest.mock import Mock
import json

from src.services.code_analysis.code_analyzer import CodeAnalyzer
from src.shared.models.code import (
    CodeIssue,
    Improvement,
    ProgrammingLanguage,
    IssueSeverity,
)


@pytest.fixture
def mock_bedrock_client():
    """Create mock Bedrock client."""
    return Mock()


@pytest.fixture
def code_analyzer(mock_bedrock_client):
    """Create CodeAnalyzer instance with mock client."""
    return CodeAnalyzer(mock_bedrock_client)


class TestCodeIssueDetection:
    """Test suite for code issue detection and suggestions (Requirements 3.3, 3.4)."""

    def test_detect_issues_with_suggestions_and_examples(self, code_analyzer, mock_bedrock_client):
        """Test that detected issues include corrective suggestions with explanations and examples."""
        code = """def unsafe_eval(user_input):
    return eval(user_input)"""

        # Mock response with detailed suggestions and examples
        mock_response = json.dumps([
            {
                "severity": "critical",
                "line": 2,
                "message": "Using eval() with user input is a security vulnerability",
                "suggestion": "Replace eval() with ast.literal_eval() to safely evaluate user input. The eval() function can execute arbitrary code, creating a security vulnerability. ast.literal_eval() only evaluates literals and is safe for untrusted input.",
                "category": "security",
                "example": "# Before:\nresult = eval(user_input)\n\n# After:\nimport ast\nresult = ast.literal_eval(user_input)"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        issues = code_analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        assert len(issues) == 1
        issue = issues[0]
        
        # Verify issue has all required fields
        assert issue.severity == IssueSeverity.CRITICAL
        assert issue.line_number == 2
        assert "eval()" in issue.message
        assert "security" in issue.category
        
        # Verify suggestion includes explanation
        assert issue.suggestion is not None
        assert "ast.literal_eval()" in issue.suggestion
        assert "security vulnerability" in issue.suggestion.lower()
        
        # Verify suggestion includes example
        assert "# Before:" in issue.suggestion or "Before:" in issue.suggestion
        assert "# After:" in issue.suggestion or "After:" in issue.suggestion
        
        # Verify documentation link is included
        assert "https://" in issue.suggestion

    def test_detect_issues_multiple_categories(self, code_analyzer, mock_bedrock_client):
        """Test detection of issues across multiple categories."""
        code = """def process_data(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result"""

        mock_response = json.dumps([
            {
                "severity": "warning",
                "line": 3,
                "message": "Inefficient loop pattern",
                "suggestion": "Use list comprehension or enumerate() for better performance and readability.",
                "category": "performance",
                "example": "result = [item * 2 for item in data]"
            },
            {
                "severity": "info",
                "line": 1,
                "message": "Missing type hints",
                "suggestion": "Add type hints to improve code documentation and enable static type checking.",
                "category": "style",
                "example": "def process_data(data: List[int]) -> List[int]:"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        issues = code_analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        assert len(issues) == 2
        
        # Check performance issue
        perf_issue = next(i for i in issues if i.category == "performance")
        assert perf_issue.severity == IssueSeverity.WARNING
        assert "performance" in perf_issue.suggestion.lower() or "comprehension" in perf_issue.suggestion.lower()
        
        # Check style issue
        style_issue = next(i for i in issues if i.category == "style")
        assert style_issue.severity == IssueSeverity.INFO
        assert "type" in style_issue.suggestion.lower()

    def test_detect_issues_with_error_handling_category(self, code_analyzer, mock_bedrock_client):
        """Test detection of error handling issues."""
        code = """def divide(a, b):
    return a / b"""

        mock_response = json.dumps([
            {
                "severity": "error",
                "line": 2,
                "message": "Division by zero not handled",
                "suggestion": "Add error handling to catch ZeroDivisionError. This prevents the program from crashing when b is zero. Use try-except or validate input before division.",
                "category": "error-handling",
                "example": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        issues = code_analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.category == "error-handling"
        assert issue.severity == IssueSeverity.ERROR
        assert "zero" in issue.message.lower()
        assert issue.suggestion is not None
        assert "error" in issue.suggestion.lower() or "exception" in issue.suggestion.lower()

    def test_detect_issues_fallback_text_parsing(self, code_analyzer, mock_bedrock_client):
        """Test fallback text parsing when JSON parsing fails."""
        code = """def bad_code():
    pass"""

        # Mock response with text format (not JSON)
        mock_response = """1. Critical security issue on line 5: SQL injection vulnerability
Suggestion: Use parameterized queries instead of string concatenation

2. Error on line 10: Potential null pointer exception
Fix: Add null check before accessing object properties

3. Warning: Performance issue with nested loops
Consider: Optimize algorithm complexity"""

        mock_bedrock_client.invoke_claude.return_value = mock_response

        issues = code_analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        assert len(issues) > 0
        
        # Check that suggestions were extracted
        issues_with_suggestions = [i for i in issues if i.suggestion is not None]
        assert len(issues_with_suggestions) > 0

    def test_suggest_improvements_with_documentation_links(self, code_analyzer, mock_bedrock_client):
        """Test that improvement suggestions include documentation links."""
        code = """def process_list(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result"""

        mock_response = json.dumps([
            {
                "title": "Use list comprehension",
                "description": "List comprehensions are more Pythonic and typically faster than traditional for loops with append operations. They are optimized at the C level and create the list in a single pass.",
                "code_before": "result = []\nfor item in items:\n    result.append(item * 2)",
                "code_after": "result = [item * 2 for item in items]",
                "benefit": "Improves performance by 20-30% and makes code more readable",
                "priority": "medium"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        improvements = code_analyzer.suggest_improvements(code, ProgrammingLanguage.PYTHON)

        assert len(improvements) == 1
        improvement = improvements[0]
        
        # Verify improvement has detailed description
        assert "Pythonic" in improvement.description or "faster" in improvement.description
        
        # Verify code examples are present
        assert improvement.code_before is not None
        assert improvement.code_after is not None
        assert "for item in items" in improvement.code_before
        assert "item * 2 for item in items" in improvement.code_after
        
        # Verify benefit includes documentation link
        assert improvement.benefit is not None
        assert "https://" in improvement.benefit

    def test_suggest_improvements_multiple_priorities(self, code_analyzer, mock_bedrock_client):
        """Test that improvements are categorized by priority."""
        code = """def example():
    pass"""

        mock_response = json.dumps([
            {
                "title": "Critical security fix",
                "description": "Fix security vulnerability",
                "benefit": "Prevents security breach",
                "priority": "high"
            },
            {
                "title": "Minor style improvement",
                "description": "Improve code style",
                "benefit": "Better readability",
                "priority": "low"
            },
            {
                "title": "Performance optimization",
                "description": "Optimize performance",
                "benefit": "Faster execution",
                "priority": "medium"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        improvements = code_analyzer.suggest_improvements(code, ProgrammingLanguage.PYTHON)

        assert len(improvements) == 3
        
        # Check priorities
        priorities = [imp.priority for imp in improvements]
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities

    def test_get_issue_documentation_link_python(self, code_analyzer):
        """Test documentation link generation for Python issues."""
        # Test various categories
        security_link = code_analyzer._get_issue_documentation_link("security", ProgrammingLanguage.PYTHON)
        assert security_link is not None
        assert "python" in security_link.lower()
        assert "security" in security_link.lower()
        
        performance_link = code_analyzer._get_issue_documentation_link("performance", ProgrammingLanguage.PYTHON)
        assert performance_link is not None
        assert "python" in performance_link.lower()
        
        error_link = code_analyzer._get_issue_documentation_link("error-handling", ProgrammingLanguage.PYTHON)
        assert error_link is not None
        assert "python" in error_link.lower()

    def test_get_issue_documentation_link_javascript(self, code_analyzer):
        """Test documentation link generation for JavaScript issues."""
        security_link = code_analyzer._get_issue_documentation_link("security", ProgrammingLanguage.JAVASCRIPT)
        assert security_link is not None
        assert "mozilla" in security_link.lower() or "mdn" in security_link.lower()
        
        async_link = code_analyzer._get_issue_documentation_link("async", ProgrammingLanguage.JAVASCRIPT)
        assert async_link is not None

    def test_get_issue_documentation_link_fallback(self, code_analyzer):
        """Test fallback to general documentation for unknown categories."""
        unknown_link = code_analyzer._get_issue_documentation_link("unknown-category", ProgrammingLanguage.PYTHON)
        assert unknown_link is not None
        assert "python" in unknown_link.lower()

    def test_categorize_improvement(self, code_analyzer):
        """Test improvement categorization based on title."""
        # Test type safety
        assert code_analyzer._categorize_improvement("Add type hints") == "type-safety"
        assert code_analyzer._categorize_improvement("Use type annotations") == "type-safety"
        
        # Test error handling
        assert code_analyzer._categorize_improvement("Add error handling") == "error-handling"
        assert code_analyzer._categorize_improvement("Handle exceptions") == "error-handling"
        
        # Test performance
        assert code_analyzer._categorize_improvement("Optimize performance") == "performance"
        assert code_analyzer._categorize_improvement("Improve speed") == "performance"
        
        # Test security
        assert code_analyzer._categorize_improvement("Fix security vulnerability") == "security"
        assert code_analyzer._categorize_improvement("Make code safer") == "security"
        
        # Test concurrency
        assert code_analyzer._categorize_improvement("Use async/await") == "concurrency"
        assert code_analyzer._categorize_improvement("Add concurrent processing") == "concurrency"
        
        # Test style
        assert code_analyzer._categorize_improvement("Follow naming conventions") == "style"
        assert code_analyzer._categorize_improvement("Format code properly") == "style"
        
        # Test default
        assert code_analyzer._categorize_improvement("Refactor code") == "maintainability"

    def test_analyze_code_includes_enhanced_issues(self, code_analyzer, mock_bedrock_client):
        """Test that analyze_code includes enhanced issue detection."""
        code = """def unsafe_function(user_input):
    return eval(user_input)"""

        # Mock all responses needed for analyze_code
        mock_bedrock_client.invoke_claude.side_effect = [
            "This function evaluates user input",  # explanation
            '[]',  # line-by-line
            json.dumps([{  # issues with enhanced suggestions
                "severity": "critical",
                "line": 2,
                "message": "Security vulnerability: eval() with user input",
                "suggestion": "Use ast.literal_eval() instead. This prevents arbitrary code execution.",
                "category": "security",
                "example": "import ast\nresult = ast.literal_eval(user_input)"
            }]),
            '[]',  # improvements
            "Best practices",  # best practices
        ]

        analysis = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert len(analysis.issues) == 1
        issue = analysis.issues[0]
        
        # Verify enhanced suggestion
        assert issue.suggestion is not None
        assert "ast.literal_eval()" in issue.suggestion
        assert "https://" in issue.suggestion  # Documentation link included

    def test_analyze_code_includes_enhanced_improvements(self, code_analyzer, mock_bedrock_client):
        """Test that analyze_code includes enhanced improvements with documentation."""
        code = """def process(data):
    result = []
    for item in data:
        result.append(item)
    return result"""

        mock_bedrock_client.invoke_claude.side_effect = [
            "This function processes data",
            '[]',
            '[]',  # no issues
            json.dumps([{  # improvements with documentation
                "title": "Use list comprehension",
                "description": "More Pythonic and efficient",
                "code_before": "result = []\nfor item in data:\n    result.append(item)",
                "code_after": "result = [item for item in data]",
                "benefit": "Better performance",
                "priority": "medium"
            }]),
            "Best practices",
        ]

        analysis = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert len(analysis.improvements) == 1
        improvement = analysis.improvements[0]
        
        # Verify enhanced benefit with documentation link
        assert improvement.benefit is not None
        assert "https://" in improvement.benefit

    def test_detect_issues_with_all_severity_levels(self, code_analyzer, mock_bedrock_client):
        """Test detection of issues with all severity levels."""
        code = """def example():
    pass"""

        mock_response = json.dumps([
            {
                "severity": "critical",
                "message": "Critical security issue",
                "suggestion": "Fix immediately",
                "category": "security"
            },
            {
                "severity": "error",
                "message": "Error in logic",
                "suggestion": "Correct the logic",
                "category": "error-handling"
            },
            {
                "severity": "warning",
                "message": "Potential issue",
                "suggestion": "Consider fixing",
                "category": "performance"
            },
            {
                "severity": "info",
                "message": "Style suggestion",
                "suggestion": "Optional improvement",
                "category": "style"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        issues = code_analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        assert len(issues) == 4
        
        severities = {issue.severity for issue in issues}
        assert IssueSeverity.CRITICAL in severities
        assert IssueSeverity.ERROR in severities
        assert IssueSeverity.WARNING in severities
        assert IssueSeverity.INFO in severities

    def test_detect_issues_javascript_specific(self, code_analyzer, mock_bedrock_client):
        """Test issue detection for JavaScript-specific patterns."""
        code = """function fetchData() {
    fetch(url).then(response => response.json())
}"""

        mock_response = json.dumps([
            {
                "severity": "warning",
                "line": 2,
                "message": "Missing error handling for promise",
                "suggestion": "Add .catch() to handle promise rejections. Unhandled promise rejections can cause silent failures.",
                "category": "error-handling",
                "example": "fetch(url)\n  .then(response => response.json())\n  .catch(error => console.error(error))"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        issues = code_analyzer.detect_issues(code, ProgrammingLanguage.JAVASCRIPT)

        assert len(issues) == 1
        issue = issues[0]
        assert "promise" in issue.message.lower()
        assert ".catch()" in issue.suggestion

    def test_suggest_improvements_with_detailed_explanations(self, code_analyzer, mock_bedrock_client):
        """Test that improvements include detailed explanations of WHY."""
        code = """def calculate(x, y):
    return x + y"""

        mock_response = json.dumps([
            {
                "title": "Add type hints",
                "description": "Type hints improve code documentation and enable static type checking with tools like mypy. They make the code more maintainable and help catch type-related bugs early in development. Modern Python projects should use type hints for better code quality.",
                "code_before": "def calculate(x, y):",
                "code_after": "def calculate(x: int, y: int) -> int:",
                "benefit": "Enables static type checking and improves code documentation",
                "priority": "high"
            }
        ])

        mock_bedrock_client.invoke_claude.return_value = mock_response

        improvements = code_analyzer.suggest_improvements(code, ProgrammingLanguage.PYTHON)

        assert len(improvements) == 1
        improvement = improvements[0]
        
        # Verify detailed explanation
        assert len(improvement.description) > 50  # Should be detailed
        assert "why" in improvement.description.lower() or "improve" in improvement.description.lower()
        
        # Verify code examples
        assert improvement.code_before is not None
        assert improvement.code_after is not None
        assert "int" in improvement.code_after  # Type hints added

    def test_parse_issues_text_extracts_suggestions(self, code_analyzer):
        """Test that text parsing extracts suggestions from various formats."""
        response = """1. Critical issue on line 5
Suggestion: Use parameterized queries
Fix: Replace string concatenation with prepared statements

2. Error on line 10
Instead: Add null check before accessing properties
Recommend: Validate input before processing"""

        issues = code_analyzer._parse_issues_text(response)

        assert len(issues) >= 2
        
        # Check that suggestions were extracted
        issues_with_suggestions = [i for i in issues if i.suggestion]
        assert len(issues_with_suggestions) >= 1
