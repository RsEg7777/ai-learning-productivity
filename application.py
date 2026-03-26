"""
Elastic Beanstalk entry point.
EB expects a WSGI 'application' callable in application.py.
We use Mangum to wrap FastAPI for WSGI compatibility.
"""
from app import app as fastapi_app

# For Elastic Beanstalk with gunicorn/uvicorn
# EB runs: gunicorn application:application
# We expose the ASGI app under this name
application = fastapi_app

# Also keep 'app' for direct uvicorn usage
app = fastapi_app
