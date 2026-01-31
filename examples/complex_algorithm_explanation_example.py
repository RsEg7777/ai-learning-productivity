"""
Example demonstrating complex algorithm explanation functionality.

This example shows how to use the CodeAnalyzer to get comprehensive
explanations of complex algorithms including:
- Step-by-step breakdown
- Visual flow diagrams (Mermaid)
- Complexity analysis
- Optimization suggestions
"""

import json
from src.services.code_analysis.code_analyzer import CodeAnalyzer
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.code import ProgrammingLanguage


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_bubble_sort():
    """Example: Explain bubble sort algorithm."""
    print_section("Example 1: Bubble Sort Algorithm")
    
    # Initialize services
    bedrock_client = BedrockClient()
    code_analyzer = CodeAnalyzer(bedrock_client)
    
    # Bubble sort implementation
    code = """def bubble_sort(arr):
    \"\"\"Sort array using bubble sort algorithm.\"\"\"
    n = len(arr)
    
    # Traverse through all array elements
    for i in range(n):
        # Last i elements are already in place
        for j in range(0, n-i-1):
            # Swap if element found is greater than next element
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    
    return arr"""
    
    print("Code to analyze:")
    print(code)
    print()
    
    # Get complex algorithm explanation
    result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)
    
    # Display algorithm steps
    print("📋 Algorithm Steps:")
    print("-" * 80)
    for step in result['algorithm_steps']:
        print(f"\nStep {step['step_number']}: {step['title']}")
        print(f"  {step['description']}")
        if step.get('code_snippet'):
            print(f"  Code: {step['code_snippet']}")
    
    # Display flow diagram
    print("\n\n📊 Algorithm Flow Diagram (Mermaid):")
    print("-" * 80)
    print(result['flow_diagram'])
    
    # Display complexity analysis
    print("\n\n⚡ Complexity Analysis:")
    print("-" * 80)
    complexity = result['complexity_analysis']
    print(f"Time Complexity: {complexity['time_complexity']}")
    print(f"  {complexity['time_explanation']}")
    print(f"\nSpace Complexity: {complexity['space_complexity']}")
    print(f"  {complexity['space_explanation']}")
    print(f"\nBest Case: {complexity.get('best_case', 'N/A')}")
    print(f"Average Case: {complexity.get('average_case', 'N/A')}")
    print(f"Worst Case: {complexity.get('worst_case', 'N/A')}")
    
    # Display optimization suggestions
    print("\n\n💡 Optimization Suggestions:")
    print("-" * 80)
    for i, opt in enumerate(result['optimization_suggestions'], 1):
        print(f"\n{i}. {opt['title']}")
        print(f"   Description: {opt['description']}")
        print(f"   Expected Improvement: {opt['expected_improvement']}")
        print(f"   Implementation: {opt['implementation']}")
        print(f"   Trade-offs: {opt['tradeoffs']}")


def example_recursive_fibonacci():
    """Example: Explain recursive Fibonacci algorithm."""
    print_section("Example 2: Recursive Fibonacci Algorithm")
    
    bedrock_client = BedrockClient()
    code_analyzer = CodeAnalyzer(bedrock_client)
    
    code = """def fibonacci(n):
    \"\"\"Calculate nth Fibonacci number recursively.\"\"\"
    # Base cases
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    # Recursive case
    return fibonacci(n-1) + fibonacci(n-2)"""
    
    print("Code to analyze:")
    print(code)
    print()
    
    result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)
    
    # Display key information
    print("⚡ Complexity Analysis:")
    complexity = result['complexity_analysis']
    print(f"Time Complexity: {complexity['time_complexity']}")
    print(f"Space Complexity: {complexity['space_complexity']}")
    
    print("\n\n💡 Top Optimization Suggestions:")
    for i, opt in enumerate(result['optimization_suggestions'][:3], 1):
        print(f"\n{i}. {opt['title']}")
        print(f"   Expected Improvement: {opt['expected_improvement']}")


def example_binary_search():
    """Example: Explain binary search algorithm."""
    print_section("Example 3: Binary Search Algorithm")
    
    bedrock_client = BedrockClient()
    code_analyzer = CodeAnalyzer(bedrock_client)
    
    code = """def binary_search(arr, target):
    \"\"\"Search for target in sorted array using binary search.\"\"\"
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        # Check if target is at mid
        if arr[mid] == target:
            return mid
        
        # If target is greater, ignore left half
        elif arr[mid] < target:
            left = mid + 1
        
        # If target is smaller, ignore right half
        else:
            right = mid - 1
    
    # Target not found
    return -1"""
    
    print("Code to analyze:")
    print(code)
    print()
    
    result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)
    
    # Display algorithm steps
    print("📋 Algorithm Steps:")
    for step in result['algorithm_steps']:
        print(f"\n{step['step_number']}. {step['title']}")
        print(f"   {step['description']}")
    
    # Display complexity
    print("\n\n⚡ Complexity Analysis:")
    complexity = result['complexity_analysis']
    print(f"Time Complexity: {complexity['time_complexity']}")
    print(f"Space Complexity: {complexity['space_complexity']}")
    print(f"\nThis is highly efficient for searching in sorted arrays!")


def example_quicksort():
    """Example: Explain quicksort algorithm."""
    print_section("Example 4: Quicksort Algorithm")
    
    bedrock_client = BedrockClient()
    code_analyzer = CodeAnalyzer(bedrock_client)
    
    code = """def quicksort(arr):
    \"\"\"Sort array using quicksort algorithm.\"\"\"
    # Base case
    if len(arr) <= 1:
        return arr
    
    # Choose pivot (middle element)
    pivot = arr[len(arr) // 2]
    
    # Partition array
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    # Recursively sort and combine
    return quicksort(left) + middle + quicksort(right)"""
    
    print("Code to analyze:")
    print(code)
    print()
    
    result = code_analyzer.explain_complex_algorithm(code, ProgrammingLanguage.PYTHON)
    
    # Display flow diagram
    print("📊 Algorithm Flow Diagram:")
    print(result['flow_diagram'])
    
    # Display complexity with all cases
    print("\n\n⚡ Complexity Analysis:")
    complexity = result['complexity_analysis']
    print(f"Time Complexity: {complexity['time_complexity']}")
    print(f"Best Case: {complexity.get('best_case', 'N/A')}")
    print(f"Average Case: {complexity.get('average_case', 'N/A')}")
    print(f"Worst Case: {complexity.get('worst_case', 'N/A')}")
    
    print("\n\n💡 Optimization Suggestions:")
    for opt in result['optimization_suggestions']:
        print(f"\n• {opt['title']}")
        print(f"  {opt['expected_improvement']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  COMPLEX ALGORITHM EXPLANATION EXAMPLES")
    print("  Demonstrating Task 8.4 Implementation")
    print("=" * 80)
    
    try:
        # Run examples
        example_bubble_sort()
        example_recursive_fibonacci()
        example_binary_search()
        example_quicksort()
        
        print("\n\n" + "=" * 80)
        print("  All examples completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nNote: These examples require AWS credentials and Bedrock access.")
        print("Set up your AWS credentials to run these examples.")


if __name__ == "__main__":
    main()
