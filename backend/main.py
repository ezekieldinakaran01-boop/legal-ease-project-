"""LegalEase FastAPI backend entrypoint."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Ensure parent directory is on sys.path for relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("legalease.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("Starting LegalEase API Service...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "your_" in api_key.lower():
        logger.warning(
            "GEMINI_API_KEY is not configured! Document generation requests will fail until "
            "a valid Google Gemini API key is set in .env or the system environment."
        )
    else:
        # Mask the key for safe logging
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        logger.info("Google Gemini API key detected (%s). Ready to process requests.", masked)
    yield
    logger.info("Shutting down LegalEase API Service...")


app = FastAPI(
    title="LegalEase API – AI-Powered Legal Document Generator",
    version="1.0.0",
    description=(
        "Production-ready backend API for generating structured, jurisdiction-aware legal documents "
        "using Google Gemini AI with high-fidelity DOCX, PDF, and TXT export pipelines."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing request %s %s: %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred while processing your request. Please check the logs for details."
        },
    )

# Include API routes
from backend.routes import router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("BACKEND_PORT", 8000))
    logger.info("Launching server on http://%s:%d", host, port)
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
