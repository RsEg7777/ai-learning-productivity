"""Pytest configuration and shared fixtures."""

import pytest
import os
from hypothesis import settings, Verbosity

# Configure Hypothesis
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=1000, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.verbose)

# Load profile from environment
profile = os.getenv("HYPOTHESIS_PROFILE", "default")
settings.load_profile(profile)


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return """
    Machine learning is a subset of artificial intelligence that focuses on 
    developing algorithms and statistical models that enable computers to 
    learn from and make predictions or decisions based on data. Unlike 
    traditional programming where explicit instructions are provided, machine 
    learning systems improve their performance through experience.
    """


@pytest.fixture
def sample_code_snippet():
    """Sample code snippet for testing."""
    return """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "preferred_language": "en",
    }
