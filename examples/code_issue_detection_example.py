"""
Example demonstrating enhanced code issue detection and suggestions.

This example shows how the code analyzer detects anti-patterns, provides
corrective suggestions with explanations, and includes relevant documentation
links and examples.

Task 8.3: Implement code issue detection and suggestions
Requirements: 3.3, 3.4
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.code_analysis.code_analyzer import CodeAnalyzer
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.code import ProgrammingLanguage


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_issues(issues):
    """Print detected issues with suggestions."""
    if not issues:
        print("✓ No issues detected!")
        return
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. [{issue.severity.value.upper()}] {issue.message}")
        if issue.line_number:
            print(f"   Line: {issue.line_number}")
        print(f"   Category: {issue.category}")
        
        if issue.suggestion:
            print(f"\n   💡 Suggestion:")
            # Print suggestion with proper indentation
            for line in issue.suggestion.split('\n'):
                print(f"      {line}")


def print_improvements(improvements):
    """Print improvement suggestions."""
    if not improvements:
        print("No improvements suggested.")
        return
    
    for i, imp in enumerate(improvements, 1):
        print(f"\n{i}. {imp.title} [Priority: {imp.priority}]")
        print(f"   {imp.description}")
        
        if imp.code_before:
            print(f"\n   Before:")
            for line in imp.code_before.split('\n'):
                print(f"      {line}")
        
        if imp.code_after:
            print(f"\n   After:")
            for line in imp.code_after.split('\n'):
                print(f"      {line}")
        
        print(f"\n   Benefit: {imp.benefit}")


def example_security_vulnerability():
    """Example 1: Detecting security vulnerabilities with corrective suggestions."""
    print_section("Example 1: Security Vulnerability Detection")
    
    code = """def process_user_input(user_data):
    # Dangerous: Using eval with user input
    result = eval(user_data)
    return result

def execute_query(user_id):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute(query)
"""
    
    print("Code to analyze:")
    print(code)
    
    # Note: In a real scenario, this would call the actual Bedrock service
    print("\n📊 Analysis Results:")
    print("\nThis code would be analyzed for:")
    print("- Security vulnerabilities (eval() usage, SQL injection)")
    print("- Corrective suggestions with explanations")
    print("- Code examples showing the fix")
    print("- Links to security documentation")
    
    print("\n💡 Expected Issues:")
    print("\n1. [CRITICAL] Using eval() with user input is a security vulnerability")
    print("   Line: 3")
    print("   Category: security")
    print("\n   Suggestion:")
    print("      Replace eval() with ast.literal_eval() to safely evaluate user input.")
    print("      The eval() function can execute arbitrary code, creating a security")
    print("      vulnerability. ast.literal_eval() only evaluates literals and is safe")
    print("      for untrusted input.")
    print("\n      Example:")
    print("      # Before:")
    print("      result = eval(user_data)")
    print("\n      # After:")
    print("      import ast")
    print("      result = ast.literal_eval(user_data)")
    print("\n      Relevant documentation: https://docs.python.org/3/library/security_warnings.html")


def example_performance_issues():
    """Example 2: Detecting performance issues with optimization suggestions."""
    print_section("Example 2: Performance Issue Detection")
    
    code = """def process_large_list(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result

def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates
"""
    
    print("Code to analyze:")
    print(code)
    
    print("\n📊 Analysis Results:")
    print("\nThis code would be analyzed for:")
    print("- Inefficient loop patterns")
    print("- Algorithm complexity issues")
    print("- Better alternatives with examples")
    
    print("\n💡 Expected Issues:")
    print("\n1. [WARNING] Inefficient loop pattern")
    print("   Line: 3")
    print("   Category: performance")
    print("\n   Suggestion:")
    print("      Use list comprehension for better performance and readability.")
    print("      List comprehensions are optimized at the C level and typically")
    print("      20-30% faster than traditional for loops with append operations.")
    print("\n      Example:")
    print("      # Before:")
    print("      result = []")
    print("      for i in range(len(data)):")
    print("          if data[i] > 0:")
    print("              result.append(data[i] * 2)")
    print("\n      # After:")
    print("      result = [item * 2 for item in data if item > 0]")
    print("\n      Relevant documentation: https://docs.python.org/3/library/profile.html")


def example_error_handling():
    """Example 3: Detecting missing error handling."""
    print_section("Example 3: Error Handling Detection")
    
    code = """def divide_numbers(a, b):
    return a / b

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def parse_json(data):
    import json
    return json.loads(data)
"""
    
    print("Code to analyze:")
    print(code)
    
    print("\n📊 Analysis Results:")
    print("\nThis code would be analyzed for:")
    print("- Missing error handling")
    print("- Potential runtime exceptions")
    print("- Best practices for exception handling")
    
    print("\n💡 Expected Issues:")
    print("\n1. [ERROR] Division by zero not handled")
    print("   Line: 2")
    print("   Category: error-handling")
    print("\n   Suggestion:")
    print("      Add error handling to catch ZeroDivisionError. This prevents the")
    print("      program from crashing when b is zero. Use try-except or validate")
    print("      input before division.")
    print("\n      Example:")
    print("      # Before:")
    print("      def divide_numbers(a, b):")
    print("          return a / b")
    print("\n      # After:")
    print("      def divide_numbers(a, b):")
    print("          if b == 0:")
    print("              raise ValueError('Cannot divide by zero')")
    print("          return a / b")
    print("\n      Relevant documentation: https://docs.python.org/3/tutorial/errors.html")


def example_code_improvements():
    """Example 4: Suggesting code improvements with documentation."""
    print_section("Example 4: Code Improvement Suggestions")
    
    code = """def calculate_total(items):
    total = 0
    for item in items:
        total = total + item
    return total

def get_user_name(user):
    return user['name']
"""
    
    print("Code to analyze:")
    print(code)
    
    print("\n📊 Analysis Results:")
    print("\nThis code would receive improvement suggestions for:")
    print("- Using built-in functions")
    print("- Adding type hints")
    print("- Error handling for dictionary access")
    
    print("\n💡 Expected Improvements:")
    print("\n1. Use built-in sum() function [Priority: medium]")
    print("   Description:")
    print("      The built-in sum() function is more efficient and Pythonic than")
    print("      manually accumulating values in a loop. It's optimized in C and")
    print("      clearly expresses the intent of summing values.")
    print("\n   Before:")
    print("      total = 0")
    print("      for item in items:")
    print("          total = total + item")
    print("\n   After:")
    print("      total = sum(items)")
    print("\n   Benefit: Improves performance and readability")
    print("   Learn more: https://docs.python.org/3/library/functions.html#sum")
    
    print("\n2. Add type hints [Priority: high]")
    print("   Description:")
    print("      Type hints improve code documentation and enable static type checking")
    print("      with tools like mypy. They make the code more maintainable and help")
    print("      catch type-related bugs early in development.")
    print("\n   Before:")
    print("      def calculate_total(items):")
    print("\n   After:")
    print("      def calculate_total(items: List[float]) -> float:")
    print("\n   Benefit: Enables static type checking and improves code documentation")
    print("   Learn more: https://docs.python.org/3/library/typing.html")


def example_javascript_issues():
    """Example 5: JavaScript-specific issue detection."""
    print_section("Example 5: JavaScript-Specific Issues")
    
    code = """function fetchUserData(userId) {
    fetch(`/api/users/${userId}`)
        .then(response => response.json())
        .then(data => console.log(data));
}

function processArray(arr) {
    for (var i = 0; i < arr.length; i++) {
        setTimeout(() => console.log(arr[i]), 100);
    }
}
"""
    
    print("Code to analyze:")
    print(code)
    
    print("\n📊 Analysis Results:")
    print("\nThis code would be analyzed for:")
    print("- Missing promise error handling")
    print("- Variable scoping issues (var vs let/const)")
    print("- Modern JavaScript best practices")
    
    print("\n💡 Expected Issues:")
    print("\n1. [WARNING] Missing error handling for promise")
    print("   Line: 2")
    print("   Category: error-handling")
    print("\n   Suggestion:")
    print("      Add .catch() to handle promise rejections. Unhandled promise")
    print("      rejections can cause silent failures and make debugging difficult.")
    print("\n      Example:")
    print("      # Before:")
    print("      fetch(`/api/users/${userId}`)")
    print("          .then(response => response.json())")
    print("          .then(data => console.log(data));")
    print("\n      # After:")
    print("      fetch(`/api/users/${userId}`)")
    print("          .then(response => response.json())")
    print("          .then(data => console.log(data))")
    print("          .catch(error => console.error('Error:', error));")
    print("\n      Relevant documentation: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Control_flow_and_error_handling")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  Code Issue Detection and Suggestions - Examples")
    print("  Task 8.3: Requirements 3.3, 3.4")
    print("=" * 80)
    
    print("\nThis example demonstrates the enhanced code analysis features:")
    print("✓ Anti-pattern and error detection")
    print("✓ Corrective suggestions with detailed explanations")
    print("✓ Code examples showing before/after")
    print("✓ Relevant documentation links")
    print("✓ Multiple severity levels and categories")
    
    # Run examples
    example_security_vulnerability()
    example_performance_issues()
    example_error_handling()
    example_code_improvements()
    example_javascript_issues()
    
    print_section("Summary")
    print("The enhanced code analyzer provides:")
    print("\n1. Comprehensive Issue Detection:")
    print("   - Security vulnerabilities")
    print("   - Performance problems")
    print("   - Error handling gaps")
    print("   - Style violations")
    print("   - Maintainability concerns")
    
    print("\n2. Detailed Corrective Suggestions:")
    print("   - Clear explanation of the problem")
    print("   - Why the fix is needed")
    print("   - How to implement the fix")
    print("   - Code examples (before/after)")
    
    print("\n3. Educational Resources:")
    print("   - Language-specific documentation links")
    print("   - Category-specific guides")
    print("   - Best practices references")
    
    print("\n4. Prioritized Improvements:")
    print("   - High priority: Security and critical bugs")
    print("   - Medium priority: Performance and maintainability")
    print("   - Low priority: Style and minor improvements")
    
    print("\n" + "=" * 80)
    print("  For actual analysis, use the CodeAnalyzer with AWS Bedrock")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
