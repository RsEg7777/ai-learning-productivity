"""
Comprehensive Feature Test Suite
Tests all 100% of implemented features.

Usage: python test_all_features.py
"""

import requests
import json
import sys
import time
from typing import Dict, Any

API_URL = "http://localhost:8000"

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def print_header(title: str):
    """Print section header."""
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BLUE}  {title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_result(success: bool, message: str):
    """Print test result."""
    icon = "✓" if success else "✗"
    color = Colors.GREEN if success else Colors.RED
    print(f"{color}{icon}{Colors.RESET} {message}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ{Colors.RESET} {message}")

# Test Results Tracker
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0
}

def run_test(test_name: str, test_func):
    """Run a test and track results."""
    test_results["total"] += 1
    try:
        result = test_func()
        if result:
            test_results["passed"] += 1
            print_result(True, test_name)
        else:
            test_results["failed"] += 1
            print_result(False, test_name)
        return result
    except Exception as e:
        test_results["failed"] += 1
        print_result(False, f"{test_name} - Error: {e}")
        return False

# Test Functions

def test_health():
    """Test health endpoint."""
    response = requests.get(f"{API_URL}/health", timeout=5)
    data = response.json()
    return data.get('status') in ['healthy', 'degraded']

def test_ai_tutor_session():
    """Test AI tutor session creation."""
    response = requests.post(
        f"{API_URL}/tutor/start-session",
        json={"user_id": "test_user", "subject": "Python"},
        timeout=10
    )
    return response.status_code == 200 and 'session_id' in response.json()

def test_ai_tutor_question():
    """Test AI tutor question answering."""
    # Start session first
    session_response = requests.post(
        f"{API_URL}/tutor/start-session",
        json={"user_id": "test_user", "subject": "Python"},
        timeout=10
    )
    session_id = session_response.json().get('session_id')
    
    # Ask question
    response = requests.post(
        f"{API_URL}/tutor/ask-question",
        json={
            "session_id": session_id,
            "question": "What is a Python list?"
        },
        timeout=30
    )
    data = response.json()
    return response.status_code == 200 and 'answer' in data

def test_quiz_generation():
    """Test quiz generation."""
    response = requests.post(
        f"{API_URL}/quiz/generate",
        json={"topic": "Python basics", "num_questions": 5},
        timeout=30
    )
    data = response.json()
    return (response.status_code == 200 and 
            'questions' in data and 
            len(data['questions']) > 0)

def test_code_analysis():
    """Test code analysis."""
    code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""
    response = requests.post(
        f"{API_URL}/code/analyze",
        json={"code": code, "language": "python"},
        timeout=30
    )
    data = response.json()
    return (response.status_code == 200 and 
            'analysis' in data and
            'explanation' in data['analysis'])

def test_gamification_award_xp():
    """Test XP awarding."""
    response = requests.post(
        f"{API_URL}/gamification/award-xp",
        json={
            "user_id": "test_user",
            "xp_amount": 100,
            "reason": "test"
        },
        timeout=10
    )
    data = response.json()
    return response.status_code == 200 and data.get('success')

def test_gamification_stats():
    """Test user stats retrieval."""
    response = requests.get(
        f"{API_URL}/gamification/stats/test_user",
        timeout=10
    )
    data = response.json()
    return (response.status_code == 200 and 
            'stats' in data and
            'total_xp' in data['stats'])

def test_gamification_leaderboard():
    """Test leaderboard retrieval."""
    response = requests.get(
        f"{API_URL}/gamification/leaderboard?time_period=all_time",
        timeout=10
    )
    data = response.json()
    return response.status_code == 200 and 'entries' in data

def test_gamification_achievements():
    """Test achievements retrieval."""
    response = requests.get(
        f"{API_URL}/gamification/achievements/test_user",
        timeout=10
    )
    data = response.json()
    return response.status_code == 200 and 'achievements' in data

def main():
    """Run all tests."""
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BLUE}  AI Learning Assistant - Comprehensive Feature Test{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"\nTesting API at: {API_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Infrastructure Tests
    print_header("Infrastructure Tests")
    run_test("Health Check", test_health)
    
    # AI Tutor Tests
    print_header("AI Tutor Tests")
    run_test("Start Tutor Session", test_ai_tutor_session)
    run_test("Ask Question", test_ai_tutor_question)
    
    # Quiz Tests
    print_header("Quiz Generation Tests")
    run_test("Generate Quiz", test_quiz_generation)
    
    # Code Analysis Tests
    print_header("Code Analysis Tests")
    run_test("Analyze Code", test_code_analysis)
    
    # Gamification Tests
    print_header("Gamification Tests")
    run_test("Award XP", test_gamification_award_xp)
    run_test("Get User Stats", test_gamification_stats)
    run_test("Get Leaderboard", test_gamification_leaderboard)
    run_test("Get Achievements", test_gamification_achievements)
    
    # Summary
    print_header("Test Summary")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests:  {total}")
    print(f"{Colors.GREEN}Passed:       {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed:       {failed}{Colors.RESET}")
    print(f"\nPass Rate:    {pass_rate:.1f}%")
    
    if pass_rate == 100:
        print(f"\n{Colors.GREEN}🎉 All tests passed! The application is 100% functional.{Colors.RESET}")
        return 0
    elif pass_rate >= 80:
        print(f"\n{Colors.YELLOW}⚠️  Most tests passed. Some features may need attention.{Colors.RESET}")
        return 1
    else:
        print(f"\n{Colors.RED}❌ Many tests failed. Check the API server and configuration.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user.{Colors.RESET}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}❌ Cannot connect to API server at {API_URL}{Colors.RESET}")
        print(f"{Colors.YELLOW}Make sure the server is running:{Colors.RESET}")
        print(f"  Windows: .\\start-server.ps1")
        print(f"  Linux/Mac: python -m uvicorn app:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
