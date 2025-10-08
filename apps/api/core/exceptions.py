"""
Custom exceptions for the application
"""
from typing import Any


class VideoProcessorException(Exception):
    """Base exception for video processor"""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class FileNotFoundError(VideoProcessorException):
    """Raised when a file is not found"""

    pass


class InvalidFileTypeError(VideoProcessorException):
    """Raised when file type is not allowed"""

    pass


class FileSizeLimitError(VideoProcessorException):
    """Raised when file exceeds size limit"""

    pass


class FolderNotFoundError(VideoProcessorException):
    """Raised when a folder is not found"""

    pass


class FolderAlreadyExistsError(VideoProcessorException):
    """Raised when attempting to create an existing folder"""

    pass


class InvalidCategoryError(VideoProcessorException):
    """Raised when storage category is invalid"""

    pass


class JobNotFoundError(VideoProcessorException):
    """Raised when a job is not found"""

    pass


class ProcessingError(VideoProcessorException):
    """Raised when video processing fails"""

    pass


class ValidationError(VideoProcessorException):
    """Raised when validation fails"""

    pass


class StorageError(VideoProcessorException):
    """Raised when storage operation fails"""

    pass
