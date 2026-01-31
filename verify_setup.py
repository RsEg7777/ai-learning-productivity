#!/usr/bin/env python3
"""Verify project setup and structure."""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()


def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists."""
    return Path(dirpath).is_dir()


def main():
    """Run setup verification."""
    print("=" * 60)
    print("AI Learning Assistant - Setup Verification")
    print("=" * 60)
    print()

    checks = {
        "Project Files": [
            "README.md",
            "requirements.txt",
            "requirements-dev.txt",
            "setup.py",
            "pytest.ini",
            "pyproject.toml",
            ".gitignore",
        ],
        "Source Directories": [
            "src",
            "src/shared",
            "src/shared/models",
            "src/shared/aws_clients",
            "src/shared/utils",
            "src/services",
            "src/services/content_processing",
            "src/services/quiz_generation",
            "src/services/code_analysis",
            "src/services/voice_interface",
            "src/services/user_management",
            "src/services/multilingual",
            "src/api",
        ],
        "Model Files": [
            "src/shared/models/__init__.py",
            "src/shared/models/content.py",
            "src/shared/models/quiz.py",
            "src/shared/models/code.py",
            "src/shared/models/user.py",
        ],
        "AWS Client Files": [
            "src/shared/aws_clients/__init__.py",
            "src/shared/aws_clients/s3_client.py",
            "src/shared/aws_clients/dynamodb_client.py",
            "src/shared/aws_clients/bedrock_client.py",
            "src/shared/aws_clients/transcribe_client.py",
            "src/shared/aws_clients/polly_client.py",
            "src/shared/aws_clients/translate_client.py",
            "src/shared/aws_clients/comprehend_client.py",
            "src/shared/aws_clients/cognito_client.py",
        ],
        "Utility Files": [
            "src/shared/utils/__init__.py",
            "src/shared/utils/errors.py",
            "src/shared/utils/logger.py",
            "src/shared/utils/validators.py",
        ],
        "Test Directories": [
            "tests",
            "tests/unit",
            "tests/property",
            "tests/integration",
        ],
        "Test Files": [
            "tests/conftest.py",
            "tests/unit/test_models.py",
            "tests/unit/test_validators.py",
        ],
        "Infrastructure Files": [
            "infrastructure/package.json",
            "infrastructure/tsconfig.json",
            "infrastructure/cdk.json",
            "infrastructure/app.ts",
            "infrastructure/lib/ai-learning-assistant-stack.ts",
            "infrastructure/README.md",
        ],
        "Configuration Files": [
            "config/config.example.yaml",
        ],
        "Documentation": [
            "docs/DEVELOPMENT.md",
        ],
    }

    all_passed = True
    total_checks = 0
    passed_checks = 0

    for category, items in checks.items():
        print(f"\n{category}:")
        print("-" * 60)

        for item in items:
            total_checks += 1
            if check_file_exists(item) or check_directory_exists(item):
                print(f"  ✓ {item}")
                passed_checks += 1
            else:
                print(f"  ✗ {item} (MISSING)")
                all_passed = False

    print()
    print("=" * 60)
    print(f"Results: {passed_checks}/{total_checks} checks passed")
    print("=" * 60)

    if all_passed:
        print("\n✓ All checks passed! Project structure is complete.")
        print("\nNext steps:")
        print("1. Create and activate virtual environment:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("\n2. Install dependencies:")
        print("   pip install -r requirements.txt")
        print("   pip install -r requirements-dev.txt")
        print("\n3. Install CDK dependencies:")
        print("   cd infrastructure && npm install")
        print("\n4. Run tests:")
        print("   pytest")
        print("\n5. Deploy infrastructure:")
        print("   cd infrastructure && cdk deploy")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the missing items above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
