"""Unit tests for complex algorithm explanation functionality."""

import pytest
import json
from unittest.mock import Mock

from src.services.code_analysis.code_analyzer import CodeAnalyzer
from src.shared.models.code import ProgrammingLanguage
from src.shared.utils.errors import ContentProcessingError


@pytest.fixture
def mock_bedrock_client():
    """Create mock Bedrock client."""
    client = Mock()
    return client


@pytest.fixture
def code_analyzer(mock_bedrock_client):
    """Create CodeAnalyzer instance with mock client."""
    return CodeAnalyzer(mock_bedrock_client)


class TestComplexAlgorithmExplanation:
    """Test suite for complex algorithm explanation (Task 8.4)."""

    def test_explain_complex_algorithm_bubble_sort(self, code_analyzer, mock_bedrock_client):
        """Test complex algorithm explanation for bubble sort."""
        code = """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr"""

        # Mock responses for each component
        mock_bedrock_client.invoke_claude.side_effect = [
            # Detailed algorithm steps
            json.dumps([
                {
                    "step_number": 1,
                    "title": "Initialize outer loop",
                    "description": "Start iterating through the array",
                    "code_snippet": "for i in range(n):"
                },
                {
                    "step_number": 2,
                    "title": "Compare adjacent elements",
                    "description": "Compare each pair of adjacent elements",
                    "code_snippet": "if arr[j] > arr[j+1]:"
                },
                {
                    "step_number": 3,
                    "title": "Swap elements",
                    "description": "Swap if they are in wrong order",
                    "code_snippet": "arr[j], arr[j+1] = arr[j+1], arr[j]"
                }
            ]),
            # Flow diagram
            """```mermaid
graph TD
    A([Start]) --> B[Get array length]
    B --> C{{i < n?}}
    C -->|Yes| D{{j < n-i-1?}}
    C -->|No| H([End])
    D -->|Yes| E{{arr[j] > arr[j+1]?}}
    D -->|No| C
    E -->|Yes| F[Swap elements]
    E -->|No| G[Continue]
    F --> D
    G --> D
```""",
            # Complexity analysis
            json.dumps({
                "time_complexity": "O(n^2)",
                "time_explanation": "Nested loops iterate through array, resulting in quadratic time",
                "space_complexity": "O(1)",
                "space_explanation": "Only uses constant extra space for swapping",
                "best_case": "O(n)",
                "average_case": "O(n^2)",
                "worst_case": "O(n^2)",
                "complexity_factors": ["Array size", "Initial order"]
            }),
            # Optimization suggestions
            json.dumps([
                {
                    "title": "Add early termination flag",
                    "description": "Track if any swaps occurred in a pass",
                    "expected_improvement": "Best case becomes O(n) for sorted arrays",
                    "implementation": "Add a flag to detect when no swaps occur",
                    "tradeoffs": "Minimal overhead, significant improvement for nearly sorted data"
                },
                {
                    "title": "Use more efficient sorting algorithm",
                    "description": "Replace with quicksort or mergesort",
                    "expected_improvement": "Reduce to O(n log n) average case",
                    "implementation": "Implement divide-and-conquer sorting",
                    "tradeoffs": "More complex implementation, better for large datasets"
                }
            ])
        ]

        result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        # Verify structure
        assert 'algorithm_steps' in result
        assert 'flow_diagram' in result
        assert 'complexity_analysis' in result
        assert 'optimization_suggestions' in result

        # Verify algorithm steps
        steps = result['algorithm_steps']
        assert isinstance(steps, list)
        assert len(steps) > 0
        assert all('step_number' in step for step in steps)
        assert all('title' in step for step in steps)
        assert all('description' in step for step in steps)

        # Verify flow diagram
        diagram = result['flow_diagram']
        assert isinstance(diagram, str)
        assert 'graph TD' in diagram or 'graph LR' in diagram

        # Verify complexity analysis
        complexity = result['complexity_analysis']
        assert 'time_complexity' in complexity
        assert 'space_complexity' in complexity
        assert 'O(n^2)' in complexity['time_complexity']

        # Verify optimization suggestions
        optimizations = result['optimization_suggestions']
        assert isinstance(optimizations, list)
        assert len(optimizations) > 0
        assert all('title' in opt for opt in optimizations)

    def test_explain_complex_algorithm_binary_search(self, code_analyzer, mock_bedrock_client):
        """Test complex algorithm explanation for binary search."""
        code = """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1"""

        mock_bedrock_client.invoke_claude.side_effect = [
            json.dumps([
                {"step_number": 1, "title": "Initialize pointers", "description": "Set left and right boundaries"}
            ]),
            "graph TD\n    A([Start]) --> B[Initialize pointers]\n    B --> C([End])",
            json.dumps({
                "time_complexity": "O(log n)",
                "time_explanation": "Divides search space in half each iteration",
                "space_complexity": "O(1)",
                "space_explanation": "Uses constant space"
            }),
            json.dumps([
                {"title": "Use recursive approach", "description": "Alternative implementation"}
            ])
        ]

        result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        assert result['complexity_analysis']['time_complexity'] == 'O(log n)'
        # Check for logarithmic complexity explanation (log, divide, half, binary)
        explanation = result['complexity_analysis']['time_explanation'].lower()
        assert any(word in explanation for word in ['log', 'divide', 'half', 'binary'])

    def test_explain_complex_algorithm_recursive_fibonacci(self, code_analyzer, mock_bedrock_client):
        """Test complex algorithm explanation for recursive Fibonacci."""
        code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""

        mock_bedrock_client.invoke_claude.side_effect = [
            json.dumps([
                {"step_number": 1, "title": "Base case", "description": "Return n if n <= 1"},
                {"step_number": 2, "title": "Recursive calls", "description": "Sum of fib(n-1) and fib(n-2)"}
            ]),
            "graph TD\n    A([Start]) --> B{{n <= 1?}}\n    B -->|Yes| C[Return n]\n    B -->|No| D[Recursive calls]",
            json.dumps({
                "time_complexity": "O(2^n)",
                "time_explanation": "Exponential due to redundant calculations",
                "space_complexity": "O(n)",
                "space_explanation": "Call stack depth"
            }),
            json.dumps([
                {
                    "title": "Use memoization",
                    "description": "Cache computed values to avoid redundant calculations",
                    "expected_improvement": "Reduce from O(2^n) to O(n)",
                    "implementation": "Use dictionary to store computed fibonacci values",
                    "tradeoffs": "Increases space complexity to O(n)"
                }
            ])
        ]

        result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        # Should identify exponential complexity
        assert '2^n' in result['complexity_analysis']['time_complexity']
        
        # Should suggest memoization
        optimizations = result['optimization_suggestions']
        assert any('memoization' in opt['title'].lower() or 'memoization' in opt['description'].lower() 
                   for opt in optimizations)

    def test_generate_detailed_algorithm_steps(self, code_analyzer, mock_bedrock_client):
        """Test detailed algorithm step generation."""
        code = """def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)"""

        mock_bedrock_client.invoke_claude.return_value = json.dumps([
            {
                "step_number": 1,
                "title": "Check base case",
                "description": "If array has 1 or fewer elements, it's already sorted",
                "code_snippet": "if len(arr) <= 1: return arr"
            },
            {
                "step_number": 2,
                "title": "Select pivot",
                "description": "Choose middle element as pivot for partitioning",
                "code_snippet": "pivot = arr[len(arr) // 2]"
            },
            {
                "step_number": 3,
                "title": "Partition array",
                "description": "Divide array into elements less than, equal to, and greater than pivot",
                "code_snippet": "left = [x for x in arr if x < pivot]"
            }
        ])

        result = code_analyzer._generate_detailed_algorithm_steps(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, list)
        assert len(result) >= 3
        assert result[0]['step_number'] == 1
        assert 'base case' in result[0]['title'].lower()
        assert 'pivot' in result[1]['title'].lower()

    def test_generate_algorithm_flow_diagram(self, code_analyzer, mock_bedrock_client):
        """Test flow diagram generation."""
        code = """def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1"""

        mock_bedrock_client.invoke_claude.return_value = """```mermaid
graph TD
    A([Start]) --> B[Initialize index i=0]
    B --> C{{i < len(arr)?}}
    C -->|Yes| D{{arr[i] == target?}}
    C -->|No| F[Return -1]
    D -->|Yes| E[Return i]
    D -->|No| G[Increment i]
    G --> C
    E --> H([End])
    F --> H
```"""

        result = code_analyzer._generate_algorithm_flow_diagram(code, ProgrammingLanguage.PYTHON)

        assert isinstance(result, str)
        assert 'graph TD' in result or 'graph LR' in result
        assert 'Start' in result or 'End' in result

    def test_generate_algorithm_flow_diagram_fallback(self, code_analyzer, mock_bedrock_client):
        """Test flow diagram generation with fallback."""
        code = """def simple_func():
    x = 1
    if x > 0:
        return True
    return False"""

        # Return invalid response to trigger fallback
        mock_bedrock_client.invoke_claude.return_value = "Invalid response"

        result = code_analyzer._generate_algorithm_flow_diagram(code, ProgrammingLanguage.PYTHON)

        # Should generate simple fallback diagram
        assert isinstance(result, str)
        assert 'graph TD' in result
        assert 'Start' in result or 'Initialize' in result

    def test_analyze_algorithm_complexity(self, code_analyzer, mock_bedrock_client):
        """Test complexity analysis."""
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

        mock_bedrock_client.invoke_claude.return_value = json.dumps({
            "time_complexity": "O(n^3)",
            "time_explanation": "Three nested loops, each iterating n times",
            "space_complexity": "O(n^2)",
            "space_explanation": "Result matrix requires n^2 space",
            "best_case": "O(n^3)",
            "average_case": "O(n^3)",
            "worst_case": "O(n^3)",
            "complexity_factors": ["Matrix dimensions", "Number of operations"]
        })

        result = code_analyzer._analyze_algorithm_complexity(code, ProgrammingLanguage.PYTHON)

        assert result['time_complexity'] == 'O(n^3)'
        assert result['space_complexity'] == 'O(n^2)'
        assert 'nested' in result['time_explanation'].lower() or 'loop' in result['time_explanation'].lower()

    def test_analyze_algorithm_complexity_fallback(self, code_analyzer, mock_bedrock_client):
        """Test complexity analysis with text fallback."""
        code = """def simple_loop(arr):
    for item in arr:
        print(item)"""

        # Return text response instead of JSON
        mock_bedrock_client.invoke_claude.return_value = """
        Time complexity: O(n) - iterates through array once
        Space complexity: O(1) - uses constant space
        """

        result = code_analyzer._analyze_algorithm_complexity(code, ProgrammingLanguage.PYTHON)

        assert 'time_complexity' in result
        assert 'space_complexity' in result
        assert 'O(n)' in result['time_complexity']
        assert 'O(1)' in result['space_complexity']

    def test_generate_optimization_suggestions(self, code_analyzer, mock_bedrock_client):
        """Test optimization suggestion generation."""
        code = """def find_duplicates(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates"""

        complexity_analysis = {
            'time_complexity': 'O(n^2)',
            'space_complexity': 'O(n)'
        }

        mock_bedrock_client.invoke_claude.return_value = json.dumps([
            {
                "title": "Use hash set for tracking",
                "description": "Replace nested loop with hash set to track seen elements",
                "expected_improvement": "Reduce time complexity from O(n^2) to O(n)",
                "implementation": "Use a set to track seen elements and another for duplicates",
                "tradeoffs": "Slightly higher space complexity but much better time complexity"
            },
            {
                "title": "Sort array first",
                "description": "Sort the array and then find duplicates in single pass",
                "expected_improvement": "Reduce to O(n log n) time complexity",
                "implementation": "Sort array, then iterate once comparing adjacent elements",
                "tradeoffs": "Modifies original array unless copied first"
            }
        ])

        result = code_analyzer._generate_optimization_suggestions(
            code, ProgrammingLanguage.PYTHON, complexity_analysis
        )

        assert isinstance(result, list)
        assert len(result) >= 2
        assert all('title' in opt for opt in result)
        assert all('expected_improvement' in opt for opt in result)
        assert any('hash' in opt['title'].lower() or 'set' in opt['title'].lower() 
                   for opt in result)

    def test_parse_algorithm_steps_text(self, code_analyzer):
        """Test parsing algorithm steps from text."""
        response = """1. Initialize variables
        Set up the initial state
        
        2. Process input
        Validate and prepare data
        
        3. Execute algorithm
        Perform main computation"""

        result = code_analyzer._parse_algorithm_steps_text(response)

        assert isinstance(result, list)
        assert len(result) >= 3
        assert result[0]['step_number'] == 1
        assert 'initialize' in result[0]['title'].lower()

    def test_parse_complexity_text(self, code_analyzer):
        """Test parsing complexity from text."""
        response = """
        The time complexity is O(n log n) because of the sorting operation.
        The space complexity is O(n) for storing the sorted array.
        """

        result = code_analyzer._parse_complexity_text(response)

        assert 'O(n log n)' in result['time_complexity'] or 'O(n)' in result['time_complexity']
        assert 'O(n)' in result['space_complexity'] or 'O(1)' in result['space_complexity']

    def test_parse_optimization_text(self, code_analyzer):
        """Test parsing optimization suggestions from text."""
        response = """1. Use dynamic programming to cache results
        2. Implement early termination for better average case
        3. Consider using a more efficient data structure"""

        result = code_analyzer._parse_optimization_text(response)

        assert isinstance(result, list)
        assert len(result) >= 3
        assert all('title' in opt for opt in result)
        assert any('dynamic programming' in opt['title'].lower() for opt in result)

    def test_explain_complex_algorithm_error_handling(self, code_analyzer, mock_bedrock_client):
        """Test error handling in complex algorithm explanation."""
        code = "def test(): pass"

        # Simulate error
        mock_bedrock_client.invoke_claude.side_effect = Exception("API error")

        with pytest.raises(ContentProcessingError) as exc_info:
            code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)

        assert "Failed to explain complex algorithm" in str(exc_info.value)

    def test_explain_complex_algorithm_different_languages(self, code_analyzer, mock_bedrock_client):
        """Test complex algorithm explanation works with different languages."""
        languages = [
            (ProgrammingLanguage.PYTHON, "def sort(arr): pass"),
            (ProgrammingLanguage.JAVASCRIPT, "function sort(arr) {}"),
            (ProgrammingLanguage.JAVA, "public void sort(int[] arr) {}"),
        ]

        for lang, code in languages:
            mock_bedrock_client.invoke_claude.side_effect = [
                json.dumps([{"step_number": 1, "title": "Step 1", "description": "Description"}]),
                "graph TD\n    A([Start]) --> B([End])",
                json.dumps({"time_complexity": "O(n)", "space_complexity": "O(1)"}),
                json.dumps([{"title": "Optimization", "description": "Details"}])
            ]

            result = code_analyzer.explain_complex_algorithm(code, lang)

            assert 'algorithm_steps' in result
            assert 'flow_diagram' in result
            assert 'complexity_analysis' in result
            assert 'optimization_suggestions' in result

            mock_bedrock_client.invoke_claude.reset_mock()

    def test_generate_simple_flow_diagram_with_loop(self, code_analyzer):
        """Test simple flow diagram generation for code with loops."""
        code = """for i in range(10):
    print(i)"""

        result = code_analyzer._generate_simple_flow_diagram(code, ProgrammingLanguage.PYTHON)

        assert 'graph TD' in result
        assert 'Loop' in result or 'loop' in result

    def test_generate_simple_flow_diagram_with_condition(self, code_analyzer):
        """Test simple flow diagram generation for code with conditions."""
        code = """if x > 0:
    print("positive")
else:
    print("negative")"""

        result = code_analyzer._generate_simple_flow_diagram(code, ProgrammingLanguage.PYTHON)

        assert 'graph TD' in result
        assert 'condition' in result.lower() or 'check' in result.lower()

    def test_complexity_analysis_includes_all_cases(self, code_analyzer, mock_bedrock_client):
        """Test that complexity analysis includes best, average, and worst cases."""
        code = """def quicksort(arr):
    # implementation
    pass"""

        mock_bedrock_client.invoke_claude.return_value = json.dumps({
            "time_complexity": "O(n log n)",
            "time_explanation": "Average case for quicksort",
            "space_complexity": "O(log n)",
            "space_explanation": "Recursion stack",
            "best_case": "O(n log n)",
            "average_case": "O(n log n)",
            "worst_case": "O(n^2)",
            "complexity_factors": ["Pivot selection", "Input distribution"]
        })

        result = code_analyzer._analyze_algorithm_complexity(code, ProgrammingLanguage.PYTHON)

        assert 'best_case' in result
        assert 'average_case' in result
        assert 'worst_case' in result
        assert 'complexity_factors' in result

    def test_optimization_suggestions_include_tradeoffs(self, code_analyzer, mock_bedrock_client):
        """Test that optimization suggestions include trade-off analysis."""
        code = "def test(): pass"
        complexity_analysis = {'time_complexity': 'O(n)'}

        mock_bedrock_client.invoke_claude.return_value = json.dumps([
            {
                "title": "Use caching",
                "description": "Cache results for repeated calls",
                "expected_improvement": "O(1) for cached results",
                "implementation": "Use functools.lru_cache decorator",
                "tradeoffs": "Increases memory usage proportional to cache size"
            }
        ])

        result = code_analyzer._generate_optimization_suggestions(
            code, ProgrammingLanguage.PYTHON, complexity_analysis
        )

        assert len(result) > 0
        assert 'tradeoffs' in result[0]
        assert result[0]['tradeoffs']  # Should not be empty

