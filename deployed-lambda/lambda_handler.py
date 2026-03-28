"""
Lambda handler for FastAPI application using Mangum.
This file serves as the entry point for AWS Lambda.
"""

from mangum import Mangum
from app import app

# Wrap FastAPI app with Mangum adapter for Lambda
# lifespan="on" to ensure startup events run and services are initialized
lambda_handler = Mangum(app, lifespan="on")
