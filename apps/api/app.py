"""
Video Processor API - Main application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.dependencies import get_job_service
from middleware.error_handler import ErrorHandlerMiddleware, exception_handlers
from routers import files, folders, processing, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Ensure storage directories exist
    settings.ensure_storage_directories()
    logger.info("Storage directories initialized")

    # Initialize job service
    job_service = get_job_service()
    logger.info("Job service initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Professional API for batch video processing with text and audio",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add error handling middleware
    app.add_middleware(ErrorHandlerMiddleware)

    # Register exception handlers
    for exc_class, handler in exception_handlers.items():
        app.add_exception_handler(exc_class, handler)

    # Include routers
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(files.router, prefix=settings.api_prefix)
    app.include_router(folders.router, prefix=settings.api_prefix)
    app.include_router(processing.router, prefix=settings.api_prefix)

    # Health check endpoint
    @app.get("/health")
    def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "message": "API is running",
            "version": settings.app_version,
        }

    @app.get("/")
    def root():
        """Root endpoint"""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
