"""
Voxora Backend — FastAPI application entry point.

Creates and configures the FastAPI application with all middleware,
routes, and event handlers.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    # Startup
    settings = get_settings()
    print(f"🚀 Voxora Backend starting in {settings.app_env} mode")
    print(f"📡 API prefix: {settings.api_v1_prefix}")

    yield

    # Shutdown
    print("👋 Voxora Backend shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Voxora AI",
        description="Conversational Business Intelligence API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_v1_router)

    # Health check & Root
    @app.get("/", tags=["System"])
    async def root():
        return {
            "status": "healthy",
            "service": "voxora-backend",
            "version": "0.1.0",
            "message": "Voxora AI Backend is operational on Vercel"
        }

    @app.get("/health", tags=["System"])
    async def health_check():
        import os
        from app.integrations.gcp import get_gcp_credentials
        creds = get_gcp_credentials()
        detected_gcp = [k for k in os.environ.keys() if any(x in k.upper() for x in ("GCP", "GOOGLE", "BIGQUERY"))]
        detected_llm = [k for k in os.environ.keys() if any(x in k.upper() for x in ("GROQ", "GEMINI", "OPENAI", "LLM"))]

        llm_status = "untested"
        llm_error = None
        try:
            from app.services.llm_service import llm_service
            resp, prov = await llm_service.generate_response([{"role": "user", "content": "ping"}])
            llm_status = f"ok ({prov})"
        except Exception as e:
            llm_status = "failed"
            llm_error = str(e)

        return {
            "status": "healthy",
            "service": "voxora-backend",
            "version": "0.1.0",
            "gcp_credentials_loaded": bool(creds),
            "detected_gcp_env_keys": detected_gcp,
            "detected_llm_env_keys": detected_llm,
            "llm_test": {
                "status": llm_status,
                "error": llm_error,
            },
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        import logging
        import traceback
        logging.getLogger(__name__).error("Unhandled exception: %s", traceback.format_exc())
        origin = request.headers.get("origin", "*")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error: {str(exc)}"},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            },
        )

    return app


app = create_app()
