"""
Vercel Serverless Function Entry Point for FastAPI.
Exposes 'app' for Vercel's Python runtime.
"""

import os
import sys

# Ensure root directory of backend is in Python search path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.main import app
