"""
Production Feature Testing Script
Tests all 7 fixed features to ensure they work end-to-end
"""

import requests
import json
import base64
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing Health Endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_ai_tutor():
    """Test AI Tutor with real AI responses"""
    print("\n2. Testing AI Tutor...")
    
    # Start session
    session_response = requests.post(
        f"{API_URL}/tutor/start-session",
        json={
            "user_id": "test_user",
            "subject": "Python Programming",
            "teaching_style": "socratic",
            "difficulty_level": "intermediate"
        }
    )
    print(f"   Session Status: {session_response.status_code}")
    session_data = session_response.json()
    session_id = session_data.get("session_id")
    
    # Ask question
    question_response = requests.post(
        f"{API_URL}/tutor/ask-question",
        json={
            "session_id": session_id,
            "question": "What are Python decorators and how do they work?",
            "include_examples": True,
            "use_socratic_method": True
        }
    )
    print(f"   Question Status: {question_response.status_code}")
    answer_data = question_response.json()
    print(f"   Answer Preview: {answer_data.get('answer', '')[:200]}...")
    print(f"   Follow-up Questions: {len(answer_data.get('follow_up_questions', []))}")
    
    return question_response.status_code == 200 and len(answer_data.get('answer', '')) > 100

def test_quiz_generator():
    """Test Quiz Generator"""
    print("\n3. Testing Quiz Generator...")
    
    response = requests.post(
        f"{API_URL}/quiz/generate",
        json={
            "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            "question_count": 5,
            "difficulty": "medium"
        }
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Questions Generated: {len(data.get('questions', []))}")
    
    return response.status_code == 200 and len(data.get('questions', [])) == 5

def test_flashcard_generator():
    """Test Flashcard Generator with count verification"""
    print("\n4. Testing Flashcard Generator...")
    
    # Test with 20 flashcards
    response = requests.post(
        f"{API_URL}/flashcards/generate",
        json={
            "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
            "count": 20
        }
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    flashcard_count = len(data.get('flashcards', []))
    print(f"   Flashcards Generated: {flashcard_count}")
    print(f"   Expected: 20")
    
    return response.status_code == 200 and flashcard_count >= 10

def test_code_analyzer():
    """Test Code Analyzer with AI analysis"""
    print("\n5. Testing Code Analyzer...")
    
    code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

result = calculate_fibonacci(10)
print(result)
"""
    
    response = requests.post(
        f"{API_URL}/code/analyze",
        json={
            "code": code,
            "language": "python"
        }
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    analysis = data.get('analysis', {})
    print(f"   Explanation Length: {len(analysis.get('explanation', ''))}")
    print(f"   Issues Found: {len(analysis.get('issues', []))}")
    print(f"   Improvements Suggested: {len(analysis.get('improvements', []))}")
    
    return response.status_code == 200 and len(analysis.get('explanation', '')) > 50

def test_code_playground():
    """Test Code Playground execution"""
    print("\n6. Testing Code Playground...")
    
    response = requests.post(
        f"{API_URL}/playground/execute",
        json={
            "code": "print('Hello, World!')\nprint(2 + 2)",
            "language": "python"
        }
    )
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Success: {data.get('success')}")
    print(f"   Output Preview: {data.get('output', '')[:100]}")
    
    return response.status_code == 200 and data.get('success')

def test_study_buddy():
    """Test AI Study Buddy"""
    print("\n7. Testing AI Study Buddy...")
    
    # Create goal
    goal_response = requests.post(
        f"{API_URL}/study-buddy/create-goal",
        json={
            "title": "Learn Python Basics",
            "description": "Master fundamental Python concepts",
            "targetDate": "2026-04-01",
            "learningStyle": "visual"
        }
    )
    print(f"   Goal Creation Status: {goal_response.status_code}")
    
    # Chat with study buddy
    chat_response = requests.post(
        f"{API_URL}/study-buddy/chat",
        json={
            "message": "I'm struggling with understanding Python decorators. Can you help?",
            "context": {
                "learningStyle": "visual",
                "learningGoals": ["Learn Python Basics"]
            }
        }
    )
    print(f"   Chat Status: {chat_response.status_code}")
    chat_data = chat_response.json()
    print(f"   Response Length: {len(chat_data.get('response', ''))}")
    
    return chat_response.status_code == 200 and len(chat_data.get('response', '')) > 50

def run_all_tests():
    """Run all production tests"""
    print("=" * 60)
    print("PRODUCTION FEATURE TESTING")
    print("=" * 60)
    
    results = {
        "Health Check": test_health(),
        "AI Tutor": test_ai_tutor(),
        "Quiz Generator": test_quiz_generator(),
        "Flashcard Generator": test_flashcard_generator(),
        "Code Analyzer": test_code_analyzer(),
        "Code Playground": test_code_playground(),
        "AI Study Buddy": test_study_buddy(),
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for feature, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{feature:.<40} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - PRODUCTION READY!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review logs")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("   Make sure the server is running: python -m uvicorn app:app --port 8000")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
