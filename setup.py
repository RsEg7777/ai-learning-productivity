"""Setup configuration for AI Learning Assistant."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-learning-assistant",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered learning platform with multilingual support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-learning-assistant",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "boto3>=1.34.0",
        "pydantic>=2.5.0",
        "aws-lambda-powertools>=2.30.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.92.0",
            "black>=23.12.0",
            "mypy>=1.7.1",
        ],
    },
)
