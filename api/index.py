"""
Vercel Serverless Function for FastAPI backend
This file handles all API requests and routes them to FastAPI app
"""
import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change to backend directory for relative imports
os.chdir(backend_path)

# Import FastAPI app from backend
from main import app

# Vercel supports ASGI apps natively, so we can export app directly
# The app will be automatically wrapped by Vercel's Python runtime

