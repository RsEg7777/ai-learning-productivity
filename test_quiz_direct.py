"""Direct test of quiz generation without API Gateway."""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.api.quiz_handler import QuizHandler

# Create test event
event = {
    "body": json.dumps({
        "content": "Python is a high-level programming language created by Guido van Rossum. It emphasizes code readability and uses significant indentation. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
        "question_count": 3
    })
}

# Create handler and test
handler = QuizHandler()
response = handler.handle_generate_quiz(event, None)

print("Response Status:", response["statusCode"])
print("\nResponse Body:")
body = json.loads(response["body"])
print(json.dumps(body, indent=2))

if "questions" in body:
    print(f"\nGenerated {len(body['questions'])} questions")
    for i, q in enumerate(body['questions'], 1):
        print(f"\nQ{i}: {q['text']}")
        print(f"Type: {q['type']}")
        if q.get('options'):
            for opt in q['options']:
                print(f"  - {opt}")
