"""Example usage of the code analysis service."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.code_analysis.code_analyzer import CodeAnalyzer
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.code import ProgrammingLanguage


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def example_python_analysis():
    """Example: Analyze Python code."""
    print_section("Example 1: Python Code Analysis")

    # Initialize services
    bedrock_client = BedrockClient()
    analyzer = CodeAnalyzer(bedrock_client)

    # Sample Python code
    code = """def calculate_fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# Calculate first 10 Fibonacci numbers
result = calculate_fibonacci(10)
print(result)"""

    print("Code to analyze:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    try:
        # Analyze the code
        print("\nAnalyzing code...")
        analysis = analyzer.analyze_code(code, ProgrammingLanguage.PYTHON)

        # Display results
        print("\n📝 Overall Explanation:")
        print(analysis.explanation)

        print("\n📊 Complexity Metrics:")
        print(f"  - Lines of Code: {analysis.complexity.lines_of_code}")
        print(f"  - Cyclomatic Complexity: {analysis.complexity.cyclomatic_complexity}")
        print(f"  - Comment Ratio: {analysis.complexity.comment_ratio:.2%}")

        if analysis.line_by_line_analysis:
            print("\n🔍 Line-by-Line Analysis (sample):")
            for line_analysis in analysis.line_by_line_analysis[:3]:
                print(f"  Line {line_analysis.line_number}: {line_analysis.code}")
                print(f"    → {line_analysis.explanation}")

        if analysis.issues:
            print(f"\n⚠️  Issues Found ({len(analysis.issues)}):")
            for issue in analysis.issues:
                print(f"  [{issue.severity.value.upper()}] Line {issue.line_number}: {issue.message}")
                if issue.suggestion:
                    print(f"    💡 Suggestion: {issue.suggestion}")

        if analysis.improvements:
            print(f"\n✨ Improvement Suggestions ({len(analysis.improvements)}):")
            for imp in analysis.improvements[:3]:
                print(f"  • {imp.title} (Priority: {imp.priority})")
                print(f"    {imp.description[:100]}...")

        if analysis.best_practices:
            print(f"\n📚 Best Practices:")
            for practice in analysis.best_practices[:3]:
                print(f"  • {practice}")

        if analysis.documentation_links:
            print(f"\n🔗 Documentation Links:")
            for link in analysis.documentation_links[:2]:
                print(f"  • {link}")

        print("\n✅ Analysis completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")


def example_javascript_analysis():
    """Example: Analyze JavaScript code."""
    print_section("Example 2: JavaScript Code Analysis")

    bedrock_client = BedrockClient()
    analyzer = CodeAnalyzer(bedrock_client)

    code = """function fetchUserData(userId) {
    return fetch(`/api/users/${userId}`)
        .then(response => response.json())
        .then(data => {
            console.log('User data:', data);
            return data;
        })
        .catch(error => {
            console.error('Error fetching user:', error);
        });
}

// Usage
fetchUserData(123);"""

    print("Code to analyze:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    try:
        print("\nAnalyzing JavaScript code...")
        analysis = analyzer.analyze_code(code, ProgrammingLanguage.JAVASCRIPT)

        print("\n📝 Overall Explanation:")
        print(analysis.explanation)

        print("\n📊 Complexity:")
        print(f"  - Lines: {analysis.complexity.lines_of_code}")
        print(f"  - Cyclomatic Complexity: {analysis.complexity.cyclomatic_complexity}")

        if analysis.improvements:
            print(f"\n✨ Suggestions ({len(analysis.improvements)}):")
            for imp in analysis.improvements[:2]:
                print(f"  • {imp.title}")

        print("\n✅ JavaScript analysis completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def example_code_explanation():
    """Example: Get detailed code explanation."""
    print_section("Example 3: Detailed Code Explanation")

    bedrock_client = BedrockClient()
    analyzer = CodeAnalyzer(bedrock_client)

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

    print("Code to explain:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    try:
        print("\nGenerating detailed explanation...")
        explanation = analyzer.explain_code(code, ProgrammingLanguage.PYTHON)

        print("\n📝 Summary:")
        print(explanation.summary)

        print("\n📖 Detailed Explanation:")
        print(explanation.detailed_explanation)

        if explanation.key_concepts:
            print("\n🔑 Key Concepts:")
            for concept in explanation.key_concepts[:5]:
                print(f"  • {concept}")

        if explanation.algorithm_steps:
            print("\n📋 Algorithm Steps:")
            for i, step in enumerate(explanation.algorithm_steps, 1):
                print(f"  {i}. {step}")

        print("\n✅ Explanation generated successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def example_issue_detection():
    """Example: Detect code issues."""
    print_section("Example 4: Issue Detection")

    bedrock_client = BedrockClient()
    analyzer = CodeAnalyzer(bedrock_client)

    # Code with potential issues
    code = """def process_user_input(user_input):
    # Dangerous: using eval with user input
    result = eval(user_input)
    
    # Missing error handling
    data = fetch_data()
    value = data['key']
    
    # Inefficient loop
    numbers = []
    for i in range(1000000):
        numbers.append(i * 2)
    
    return result"""

    print("Code to check for issues:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    try:
        print("\nDetecting issues...")
        issues = analyzer.detect_issues(code, ProgrammingLanguage.PYTHON)

        if issues:
            print(f"\n⚠️  Found {len(issues)} issue(s):")
            for issue in issues:
                severity_emoji = {
                    'critical': '🔴',
                    'error': '🟠',
                    'warning': '🟡',
                    'info': '🔵'
                }
                emoji = severity_emoji.get(issue.severity.value, '⚪')
                
                print(f"\n{emoji} [{issue.severity.value.upper()}] {issue.category}")
                if issue.line_number:
                    print(f"  Line: {issue.line_number}")
                print(f"  Issue: {issue.message}")
                if issue.suggestion:
                    print(f"  💡 Fix: {issue.suggestion}")
        else:
            print("\n✅ No issues detected!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def example_improvement_suggestions():
    """Example: Get improvement suggestions."""
    print_section("Example 5: Improvement Suggestions")

    bedrock_client = BedrockClient()
    analyzer = CodeAnalyzer(bedrock_client)

    code = """def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price']
    return total

def get_user_name(user):
    if user:
        if 'name' in user:
            return user['name']
    return 'Unknown'"""

    print("Code to improve:")
    print("-" * 80)
    print(code)
    print("-" * 80)

    try:
        print("\nGenerating improvement suggestions...")
        improvements = analyzer.suggest_improvements(code, ProgrammingLanguage.PYTHON)

        if improvements:
            print(f"\n✨ Found {len(improvements)} improvement(s):")
            for i, imp in enumerate(improvements, 1):
                print(f"\n{i}. {imp.title} (Priority: {imp.priority})")
                print(f"   {imp.description}")
                print(f"   💪 Benefit: {imp.benefit}")
                
                if imp.code_before and imp.code_after:
                    print(f"\n   Before:")
                    print(f"   {imp.code_before[:100]}...")
                    print(f"\n   After:")
                    print(f"   {imp.code_after[:100]}...")
        else:
            print("\n✅ Code looks good! No major improvements needed.")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  CODE ANALYSIS SERVICE - EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates the code analysis capabilities:")
    print("  • Multi-language code parsing")
    print("  • Line-by-line explanations")
    print("  • Issue detection")
    print("  • Improvement suggestions")
    print("  • Best practices recommendations")
    print("\nNote: These examples use Amazon Bedrock. Ensure AWS credentials are configured.")
    print("=" * 80)

    try:
        # Run examples
        example_python_analysis()
        example_javascript_analysis()
        example_code_explanation()
        example_issue_detection()
        example_improvement_suggestions()

        print("\n" + "=" * 80)
        print("  ALL EXAMPLES COMPLETED")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
