"""
Vercel Serverless Function Entry Point for FastAPI.
Exposes 'app' for Vercel's native Python ASGI runtime.
Includes diagnostic error capturing to catch and display startup failures.
"""

import os
import sys
import traceback

# Ensure root directory of backend is in Python search path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

startup_error = None
app = None

try:
    from app.main import app as actual_app
    app = actual_app
except Exception:
    startup_error = traceback.format_exc()

if startup_error:
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    err_app = FastAPI()

    @err_app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def show_error(full_path: str = ""):
        return PlainTextResponse(
            f"=== VOXORA BACKEND STARTUP ERROR ===\n\n{startup_error}",
            status_code=500,
        )

    app = err_app
