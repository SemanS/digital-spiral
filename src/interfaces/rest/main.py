"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infrastructure.observability.logger import configure_logging
from src.interfaces.rest.error_handlers import register_error_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Digital Spiral API...")
    configure_logging()
    logger.info("Digital Spiral API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Digital Spiral API...")
    logger.info("Digital Spiral API shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Digital Spiral API",
    description="REST API for Digital Spiral - Jira Analytics Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure from environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "digital-spiral-api",
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.
    
    Returns:
        API information
    """
    return {
        "name": "Digital Spiral API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Import and include routers
from src.interfaces.rest.ai import router as ai_router
from src.interfaces.rest.issues import router as issues_router
from src.interfaces.rest.sync import router as sync_router
from src.interfaces.rest.webhooks import router as webhooks_router
from src.interfaces.rest.routers.instances import router as instances_router
from src.interfaces.rest.routers.oauth import router as oauth_router

app.include_router(ai_router)
app.include_router(issues_router)
app.include_router(sync_router)
app.include_router(webhooks_router)
app.include_router(instances_router)
app.include_router(oauth_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.interfaces.rest.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

