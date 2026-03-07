"""
Quick API Test Script
Tests all major endpoints to verify functionality.

Usage: python test_api.py
"""

import requests
import json
import sys
from typing import Dict, Any

API_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(success: bool, message: str):
    """Print test result."""
    icon = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{icon}{reset} {message}")

def test_health() -> bool:
    """Test health endpoint."""
    print_section("Testing Health Endpoint")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json()
        
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        
        if data.get('services'):
            print("\nServices:")
            for service, status in data['services'].items():
                print_result(status, service)
        
        if data.get('errors'):
            print("\nErrors:")
            for error in data['errors']:
                print(f"  - {error}")
        
        if data.get('warnings'):
            print("\nWarnings:")
            for warning in data['warnings']:
                print(f"  - {warning}")
        
        success = data.get('status') in ['healthy', 'degraded']
        print_result(success, "Health check")
        return success
    except Exception as e:
        print_result(False, f"Health check failed: {e}")
        return False

def test_tutor() -> bool:
    """Test AI tutor endpoints."""
    print_section("Testing AI Tutor")
    
    try:
        # Start session
        print("\n1. Starting tutor session...")
        response = requests.post(
            f"{API_URL}/tutor/start-session",
            json={
                "user_id": "test_user",
                "subject": "Python",
                "teaching_style": "socratic",
                "difficulty_level": "adaptive"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_result(False, f"Start session failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        session_id = data.get('session_id')
        print_result(True, f"Session started: {session_id}")
        
        # Ask question
        print("\n2. Asking question...")
        response = requests.post(
            f"{API_URL}/tutor/ask-question",
            json={
                "session_id": session_id,
                "question": "What is a Python decorator?",
                "include_examples": True,
                "use_socratic_method": True
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_result(False, f"Ask question failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        answer = data.get('answer', '')
        print_result(True, "Question answered")
        print(f"\nAnswer preview: {answer[:200]}...")
        
        if data.get('follow_up_questions'):
            print("\nFollow-up questions:")
            for q in data['follow_up_questions'][:3]:
                print(f"  - {q}")
        
        return True
        
    except Exception as e:
        print_result(False, f"Tutor test failed: {e}")
        return False

def test_quiz() -> bool:
    """Test quiz generation."""
    print_section("Testing Quiz Generation")
    
    try:
        print("\nGenerating quiz...")
        response = requests.post(
            f"{API_URL}/quiz/generate",
            json={
                "topic": "Python basics",
                "num_questions": 5,
                "difficulty": "medium"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_result(False, f"Quiz generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        questions = data.get('questions', [])
        
        print_result(True, f"Quiz generated with {len(questions)} questions")
        
        if questions:
            print("\nSample question:")
            q = questions[0]
            print(f"  Type: {q.get('type')}")
            print(f"  Text: {q.get('text')}")
            if q.get('options'):
                print(f"  Options: {len(q.get('options'))} choices")
        
        return True
        
    except Exception as e:
        print_result(False, f"Quiz test failed: {e}")
        return False

def test_code_analysis() -> bool:
    """Test code analysis."""
    print_section("Testing Code Analysis")
    
    sample_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total

result = calculate_sum([1, 2, 3, 4, 5])
print(result)
"""
    
    try:
        print("\nAnalyzing code...")
        response = requests.post(
            f"{API_URL}/code/analyze",
            json={
                "code": sample_code,
                "language": "python"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_result(False, f"Code analysis failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        analysis = data.get('analysis', {})
        
        print_result(True, "Code analyzed")
        
        print(f"\nExplanation: {analysis.get('explanation', '')[:200]}...")
        
        improvements = analysis.get('improvements', [])
        if improvements:
            print(f"\nImprovements found: {len(improvements)}")
            for imp in improvements[:2]:
                print(f"  - {imp.get('title')}")
        
        issues = analysis.get('issues', [])
        if issues:
            print(f"\nIssues found: {len(issues)}")
            for issue in issues[:2]:
                print(f"  - [{issue.get('severity')}] {issue.get('message')}")
        
        return True
        
    except Exception as e:
        print_result(False, f"Code analysis test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  AI Learning Assistant - API Test Suite")
    print("=" * 60)
    print(f"\nTesting API at: {API_URL}")
    
    results = {
        "Health Check": test_health(),
        "AI Tutor": test_tutor(),
        "Quiz Generation": test_quiz(),
        "Code Analysis": test_code_analysis(),
    }
    
    print_section("Test Summary")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        print_result(result, test_name)
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The API is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
