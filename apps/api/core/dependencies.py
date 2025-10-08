"""
Dependency injection for FastAPI
"""
from functools import lru_cache

from core.config import Settings, get_settings
from services.file_service import FileService
from services.job_service import JobService
from services.processing_service import ProcessingService
from services.storage_service import StorageService


# Singleton instances
_job_service_instance: JobService | None = None


@lru_cache
def get_storage_service() -> StorageService:
    """Get storage service instance"""
    settings = get_settings()
    return StorageService(settings)


def get_job_service() -> JobService:
    """Get job service singleton instance"""
    global _job_service_instance
    if _job_service_instance is None:
        _job_service_instance = JobService()
    return _job_service_instance


@lru_cache
def get_file_service() -> FileService:
    """Get file service instance"""
    settings = get_settings()
    storage_service = get_storage_service()
    return FileService(settings, storage_service)


@lru_cache
def get_processing_service() -> ProcessingService:
    """Get processing service instance"""
    settings = get_settings()
    job_service = get_job_service()
    return ProcessingService(settings, job_service)
