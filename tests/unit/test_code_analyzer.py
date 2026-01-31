"""Unit tests for code analyzer service."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.services.code_analysis.code_analyzer import CodeAnalyzer
from src.shared.models.code import (
    CodeAnalysis,
    CodeExplanation,
    LineAnalysis,
    CodeIssue,
    Improvement,
    ComplexityMetrics,
    ProgrammingLanguage,
    IssueSeverity,
)
from src.shared.utils.errors import ContentProcessingError, ProcessingTimeoutError


@pytest.fixture
def mock_bedrock_client():
    """Create mock Bedrock client."""
    client = Mock()
    return client


@pytest.fixture
def code_analyzer(mock_bedrock_client):
    """Create CodeAnalyzer instance with mock client."""
    return CodeAnalyzer(mock_bedrock_client)


class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer."""

    def test_initialization(self, mock_bedrock_client):
        """Test CodeAnalyzer initialization."""
        analyzer = CodeAnalyzer(mock_bedrock_client)
        assert analyzer.bedrock_client == mock_bedrock_client
        assert analyzer.CODE_ANALYSIS_TIMEOUT == 15
        assert analyzer.MAX_LINES_FOR_DETAILED_ANALYSIS == 100

    def test_analyze_code_empty_input(self, code_analyzer):
        """Test analyze_code with empty input raises error."""
        with pytest.raises(ContentProcessingError) as exc_info:
            code_analyzer.analyze_code("", ProgrammingLanguage.PYTHON)

        assert "Code cannot be empty" in str(exc_info.value)

    def test_analyze_code_python_simple(self, code_analyzer, mock_bedrock_client):
        """Test analyze_code with simple Python code."""
        code = """def add(a, b):
    return a + b"""

        # Mock Bedrock responses
        mock_bedrock_client.invoke_claude.side_effect = [
            "This function adds two numbers",  # explanation
            '[{"line": 1, "code": "def add(a, b):", "explanation": "Function definition"}]',  # line-by-line
            '[]',  # issues
            '[{"title": "Add type hints", "description": "Add type annotations", "benefit": "Better type safety", "priority": "medium"}]',  # improvements
            "Use descriptive function names",  # best practices
        ]

        result = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, CodeAnalysis)
        assert "adds two numbers" in result.explanation.lower()
        assert len(result.line_by_line_analysis) >= 0
        assert isinstance(result.complexity, ComplexityMetrics)
        assert result.complexity.lines_of_code > 0

    def test_analyze_code_with_issues(self, code_analyzer, mock_bedrock_client):
        """Test analyze_code detects issues."""
        code = """def divide(a, b):
    return a / b"""

        mock_bedrock_client.invoke_claude.side_effect = [
            "This function divides two numbers",
            '[]',  # line-by-line
            '[{"severity": "error", "line": 2, "message": "Division by zero not handled", "category": "error-handling"}]',  # issues
            '[]',  # improvements
            "Handle edge cases",  # best practices
        ]

        result = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert len(result.issues) > 0
        assert any("division" in issue.message.lower() for issue in result.issues)

    def test_analyze_code_javascript(self, code_analyzer, mock_bedrock_client):
        """Test analyze_code with JavaScript code."""
        code = """function greet(name) {
    console.log("Hello, " + name);
}"""

        mock_bedrock_client.invoke_claude.side_effect = [
            "This function greets a user",
            '[]',
            '[]',
            '[{"title": "Use template literals", "description": "Use modern syntax", "benefit": "More readable", "priority": "low"}]',
            "Use modern ES6+ syntax",
        ]

        result = code_analyzer.analyze_code(code, ProgrammingLanguage.JAVASCRIPT)

        assert isinstance(result, CodeAnalysis)
        assert "greet" in result.explanation.lower() or "hello" in result.explanation.lower()

    def test_explain_code(self, code_analyzer, mock_bedrock_client):
        """Test explain_code method."""
        code = """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)"""

        mock_bedrock_client.invoke_claude.side_effect = [
            "Calculates factorial recursively",  # summary
            "This is a recursive implementation of factorial",  # detailed
            '[]',  # line-by-line
            "Recursion, base case, mathematical function",  # key concepts
            "1. Check base case\n2. Recursive call\n3. Multiply result",  # algorithm steps
        ]

        result = code_analyzer.explain_code(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, CodeExplanation)
        assert "factorial" in result.summary.lower() or "recursive" in result.summary.lower()
        assert result.detailed_explanation
        assert result.key_concepts

    def test_suggest_improvements(self, code_analyzer, mock_bedrock_client):
        """Test suggest_improvements method."""
        code = """def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result"""

        mock_bedrock_client.invoke_claude.return_value = '''[
            {
                "title": "Use list comprehension",
                "description": "Replace loop with list comprehension",
                "code_before": "for item in data:\\n    result.append(item * 2)",
                "code_after": "result = [item * 2 for item in data]",
                "benefit": "More Pythonic and concise",
                "priority": "medium"
            }
        ]'''

        result = code_analyzer.suggest_improvements(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(imp, Improvement) for imp in result)

    def test_detect_issues(self, code_analyzer, mock_bedrock_client):
        """Test detect_issues method."""
        code = """def unsafe_eval(user_input):
    return eval(user_input)"""

        mock_bedrock_client.invoke_claude.return_value = '''[
            {
                "severity": "critical",
                "line": 2,
                "message": "Using eval() with user input is a security vulnerability",
                "suggestion": "Use ast.literal_eval() or validate input",
                "category": "security"
            }
        ]'''

        result = code_analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(issue, CodeIssue) for issue in result)
        assert any(issue.severity == IssueSeverity.CRITICAL for issue in result)

    def test_calculate_complexity_simple(self, code_analyzer):
        """Test complexity calculation for simple code."""
        code = """def add(a, b):
    # Add two numbers
    return a + b"""

        complexity = code_analyzer._calculate_complexity(code, ProgrammingLanguage.PYTHON)

        assert isinstance(complexity, ComplexityMetrics)
        assert complexity.lines_of_code > 0
        assert complexity.cyclomatic_complexity >= 1
        assert 0.0 <= complexity.comment_ratio <= 1.0

    def test_calculate_complexity_with_branches(self, code_analyzer):
        """Test complexity calculation with conditional branches."""
        code = """def check_value(x):
    if x > 0:
        if x > 10:
            return "large"
        return "small"
    elif x < 0:
        return "negative"
    else:
        return "zero"
"""

        complexity = code_analyzer._calculate_complexity(code, ProgrammingLanguage.PYTHON)

        assert complexity.cyclomatic_complexity > 1
        assert complexity.lines_of_code > 0

    def test_extract_libraries_python(self, code_analyzer):
        """Test library extraction from Python code."""
        code = """import numpy as np
from pandas import DataFrame
import requests"""

        libraries = code_analyzer._extract_libraries(code, ProgrammingLanguage.PYTHON)

        assert 'numpy' in libraries or 'pandas' in libraries or 'requests' in libraries

    def test_extract_libraries_javascript(self, code_analyzer):
        """Test library extraction from JavaScript code."""
        code = """const express = require('express');
import React from 'react';"""

        libraries = code_analyzer._extract_libraries(code, ProgrammingLanguage.JAVASCRIPT)

        assert 'express' in libraries or 'react' in libraries.lower()

    def test_is_complex_algorithm_simple(self, code_analyzer):
        """Test complex algorithm detection for simple code."""
        code = """def add(a, b):
    return a + b"""

        is_complex = code_analyzer._is_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        assert not is_complex

    def test_is_complex_algorithm_nested_loops(self, code_analyzer):
        """Test complex algorithm detection with nested loops."""
        code = """def matrix_multiply(a, b):
    result = []
    for i in range(len(a)):
        row = []
        for j in range(len(b[0])):
            sum_val = 0
            for k in range(len(b)):
                sum_val += a[i][k] * b[k][j]
            row.append(sum_val)
        result.append(row)
    return result"""

        is_complex = code_analyzer._is_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        assert is_complex

    def test_is_complex_algorithm_recursion(self, code_analyzer):
        """Test complex algorithm detection with recursion."""
        code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""

        is_complex = code_analyzer._is_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        assert is_complex

    def test_get_documentation_links(self, code_analyzer):
        """Test documentation link generation."""
        code = """import numpy as np
def process():
    pass"""

        links = code_analyzer._get_documentation_links(code, ProgrammingLanguage.PYTHON)

        assert isinstance(links, list)
        assert len(links) > 0
        assert any('python' in link.lower() for link in links)

    def test_parse_line_analysis_text(self, code_analyzer):
        """Test parsing line analysis from text."""
        response = """Line 1: This is the first line
Line 2: This is the second line
Line 3: This is the third line"""

        lines = ["line 1 code", "line 2 code", "line 3 code"]

        result = code_analyzer._parse_line_analysis_text(response, lines)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, LineAnalysis) for item in result)

    def test_parse_issues_text(self, code_analyzer):
        """Test parsing issues from text."""
        response = """1. Critical security issue on line 5: SQL injection vulnerability
2. Error on line 10: Potential null pointer exception
3. Warning: Performance issue with nested loops"""

        result = code_analyzer._parse_issues_text(response)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(issue, CodeIssue) for issue in result)

    def test_parse_improvements_text(self, code_analyzer):
        """Test parsing improvements from text."""
        response = """1. Use list comprehension instead of loops for better performance
2. Add error handling to prevent crashes
3. Consider using type hints for better code documentation"""

        result = code_analyzer._parse_improvements_text(response)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(imp, Improvement) for imp in result)

    def test_analyze_code_large_file(self, code_analyzer, mock_bedrock_client):
        """Test analyze_code with large file (>100 lines)."""
        # Create code with 150 lines
        code = "\n".join([f"# Line {i}" for i in range(150)])

        mock_bedrock_client.invoke_claude.side_effect = [
            "This is a large file",
            "Key sections analysis",  # key sections instead of line-by-line
            '[]',
            '[]',
            "Best practices",
        ]

        result = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, CodeAnalysis)
        # Should use key sections analysis for large files
        assert mock_bedrock_client.invoke_claude.call_count >= 3

    def test_analyze_code_with_timeout_check(self, code_analyzer, mock_bedrock_client):
        """Test that analyze_code completes within timeout."""
        code = """def simple_function():
    return "Hello, World!" """

        mock_bedrock_client.invoke_claude.side_effect = [
            "Simple function",
            '[]',
            '[]',
            '[]',
            "Best practices",
        ]

        import time
        start = time.time()
        result = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)
        elapsed = time.time() - start

        assert isinstance(result, CodeAnalysis)
        # Should complete well within timeout (allowing some overhead for test execution)
        assert elapsed < code_analyzer.CODE_ANALYSIS_TIMEOUT + 5

    def test_extract_key_concepts(self, code_analyzer, mock_bedrock_client):
        """Test key concept extraction."""
        code = """class BinaryTree:
    def __init__(self):
        self.root = None"""

        mock_bedrock_client.invoke_claude.return_value = """1. Object-oriented programming
2. Data structures
3. Binary tree implementation
4. Constructor method"""

        result = code_analyzer._extract_key_concepts(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_algorithm_steps(self, code_analyzer, mock_bedrock_client):
        """Test algorithm step generation."""
        code = """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]"""

        mock_bedrock_client.invoke_claude.return_value = """1. Get array length
2. Iterate through array
3. Compare adjacent elements
4. Swap if out of order
5. Repeat until sorted"""

        result = code_analyzer._generate_algorithm_steps(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_analyze_code_multiple_languages(self, code_analyzer, mock_bedrock_client):
        """Test analyze_code works with different programming languages."""
        languages = [
            ProgrammingLanguage.PYTHON,
            ProgrammingLanguage.JAVASCRIPT,
            ProgrammingLanguage.JAVA,
            ProgrammingLanguage.CPP,
        ]

        for lang in languages:
            mock_bedrock_client.invoke_claude.side_effect = [
                f"Code in {lang.value}",
                '[]',
                '[]',
                '[]',
                "Best practices",
            ]

            code = "// Simple code"
            result = code_analyzer.analyze_code(code, lang)

            assert isinstance(result, CodeAnalysis)
            mock_bedrock_client.invoke_claude.reset_mock()

    def test_complexity_metrics_comment_ratio(self, code_analyzer):
        """Test comment ratio calculation."""
        code = """# Comment 1
# Comment 2
def func():
    # Comment 3
    return 1"""

        complexity = code_analyzer._calculate_complexity(code, ProgrammingLanguage.PYTHON)

        assert complexity.comment_ratio > 0
        assert complexity.comment_ratio <= 1.0

    def test_analyze_code_with_best_practices(self, code_analyzer, mock_bedrock_client):
        """Test that best practices are included in analysis."""
        code = """def calculate(x, y):
    return x + y"""

        mock_bedrock_client.invoke_claude.side_effect = [
            "Simple calculation",
            '[]',
            '[]',
            '[]',
            "1. Use type hints\n2. Add docstrings\n3. Handle edge cases",
        ]

        result = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert len(result.best_practices) > 0

    def test_analyze_code_with_documentation_links(self, code_analyzer, mock_bedrock_client):
        """Test that documentation links are included."""
        code = """import requests
def fetch_data():
    pass"""

        mock_bedrock_client.invoke_claude.side_effect = [
            "Fetches data",
            '[]',
            '[]',
            '[]',
            "Best practices",
        ]

        result = code_analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        assert len(result.documentation_links) > 0
        assert any('python' in link.lower() for link in result.documentation_links)
