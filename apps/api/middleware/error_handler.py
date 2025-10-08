"""
Error handling middleware and exception handlers
"""
import logging
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.exceptions import (
    FileNotFoundError,
    FileSizeLimitError,
    FolderAlreadyExistsError,
    FolderNotFoundError,
    InvalidCategoryError,
    InvalidFileTypeError,
    JobNotFoundError,
    ProcessingError,
    StorageError,
    ValidationError,
    VideoProcessorException,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and logging"""

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and handle errors"""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "message": str(exc),
                },
            )


def create_exception_handler(
    status_code: int,
) -> Callable[[Request, VideoProcessorException], JSONResponse]:
    """Create exception handler for VideoProcessorException subclasses"""

    async def handler(request: Request, exc: VideoProcessorException) -> JSONResponse:
        """Handle VideoProcessorException"""
        logger.warning(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"details": exc.details},
        )

        content = {"detail": exc.message}
        if exc.details:
            content["details"] = exc.details

        return JSONResponse(status_code=status_code, content=content)

    return handler


# Exception handlers mapping
exception_handlers = {
    FileNotFoundError: create_exception_handler(status.HTTP_404_NOT_FOUND),
    FolderNotFoundError: create_exception_handler(status.HTTP_404_NOT_FOUND),
    JobNotFoundError: create_exception_handler(status.HTTP_404_NOT_FOUND),
    InvalidFileTypeError: create_exception_handler(status.HTTP_400_BAD_REQUEST),
    FileSizeLimitError: create_exception_handler(status.HTTP_400_BAD_REQUEST),
    FolderAlreadyExistsError: create_exception_handler(status.HTTP_400_BAD_REQUEST),
    InvalidCategoryError: create_exception_handler(status.HTTP_400_BAD_REQUEST),
    ValidationError: create_exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY),
    ProcessingError: create_exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
    StorageError: create_exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
}
