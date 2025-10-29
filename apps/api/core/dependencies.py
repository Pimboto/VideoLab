"""
Dependency injection for FastAPI
"""
from functools import lru_cache
from typing import Dict, Any
from fastapi import Header, Depends
from supabase import Client

from core.config import Settings, get_settings
from core.security import verify_clerk_token, extract_user_info
from core.exceptions import UnauthorizedError
from services.file_service import FileService
from services.job_service import JobService
from services.processing_service import ProcessingService
from services.storage_service import StorageService
from services.user_service import UserService
from services.video_render_service import VideoRenderService
from services.media_upload_service import MediaUploadService
from services.csv_service import CSVService
from services.folder_service import FolderService
from utils.supabase_client import get_supabase_client


@lru_cache
def get_storage_service() -> StorageService:
    """Get storage service instance"""
    settings = get_settings()
    return StorageService(settings)


@lru_cache
def get_job_service() -> JobService:
    """Get job service instance with Supabase"""
    return JobService()


@lru_cache
def get_file_service() -> FileService:
    """Get file service instance"""
    settings = get_settings()
    storage_service = get_storage_service()
    return FileService(settings, storage_service)


@lru_cache
def get_video_render_service() -> VideoRenderService:
    """Get video render service instance"""
    settings = get_settings()
    return VideoRenderService(settings)


@lru_cache
def get_processing_service() -> ProcessingService:
    """Get processing service instance"""
    settings = get_settings()
    job_service = get_job_service()
    video_render_service = get_video_render_service()
    storage_service = get_storage_service()
    return ProcessingService(settings, job_service, video_render_service, storage_service)


@lru_cache
def get_media_upload_service() -> MediaUploadService:
    """Get media upload service instance (videos and audios)"""
    settings = get_settings()
    storage_service = get_storage_service()
    supabase = get_supabase_client()
    return MediaUploadService(settings, storage_service, supabase)


@lru_cache
def get_csv_service() -> CSVService:
    """Get CSV service instance"""
    settings = get_settings()
    storage_service = get_storage_service()
    supabase = get_supabase_client()
    return CSVService(settings, storage_service, supabase)


@lru_cache
def get_folder_service() -> FolderService:
    """Get folder service instance"""
    storage_service = get_storage_service()
    supabase = get_supabase_client()
    return FolderService(storage_service, supabase)


# ========================================
# Authentication & User Management
# ========================================


def get_supabase() -> Client:
    """
    Get Supabase client instance.

    Returns:
        Supabase Client instance
    """
    return get_supabase_client()


@lru_cache
def get_user_service(supabase: Client = Depends(get_supabase)) -> UserService:
    """
    Get user service instance.

    Args:
        supabase: Supabase client (injected)

    Returns:
        UserService instance
    """
    return UserService(supabase)


async def get_current_user(
    authorization: str = Header(..., description="Bearer token from Clerk"),
    supabase: Client = Depends(get_supabase),
) -> Dict[str, Any]:
    """
    Extract and verify current user from Clerk JWT token.

    This dependency should be used on all protected endpoints to ensure
    the user is authenticated and exists in the database.

    Args:
        authorization: Authorization header with Bearer token
        supabase: Supabase client (injected)

    Returns:
        Dict containing user information from database with keys:
        - id: UUID from database
        - clerk_id: Clerk user ID
        - email: User email
        - first_name: User first name (optional)
        - last_name: User last name (optional)
        - avatar_url: User avatar URL (optional)
        - created_at: Account creation timestamp
        - updated_at: Last update timestamp

    Raises:
        UnauthorizedError: If token is invalid, expired, or user not found

    Example:
        ```python
        @router.get("/protected")
        async def protected_route(
            current_user: dict = Depends(get_current_user)
        ):
            user_id = current_user["id"]
            clerk_id = current_user["clerk_id"]
            # ... your logic
        ```
    """
    # Validate authorization header format
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError(
            "Invalid authorization header format. Expected 'Bearer <token>'"
        )

    # Extract token
    token = authorization.replace("Bearer ", "").strip()

    if not token:
        raise UnauthorizedError("No token provided")

    # Verify Clerk JWT and extract user info
    try:
        payload = verify_clerk_token(token)
        user_info = extract_user_info(payload)
    except UnauthorizedError:
        raise
    except Exception as e:
        raise UnauthorizedError(f"Failed to verify token: {str(e)}")

    clerk_id = user_info.get("clerk_id")
    if not clerk_id:
        raise UnauthorizedError("Invalid user ID in token")

    # Get user from Supabase (must exist via webhook)
    user_service = UserService(supabase)

    try:
        user = user_service.get_user_by_clerk_id(clerk_id)
    except Exception as e:
        raise UnauthorizedError(f"Failed to retrieve user from database: {str(e)}")

    if not user:
        raise UnauthorizedError(
            "User not found in database. Please contact support.",
            {"clerk_id": clerk_id, "hint": "User should be created via Clerk webhook"}
        )

    return user


async def get_optional_user(
    authorization: str = Header(None, description="Optional Bearer token"),
    supabase: Client = Depends(get_supabase),
) -> Dict[str, Any] | None:
    """
    Optional authentication dependency.

    Similar to get_current_user but returns None if no token is provided
    instead of raising an error. Useful for endpoints that work differently
    for authenticated vs unauthenticated users.

    Args:
        authorization: Optional authorization header
        supabase: Supabase client (injected)

    Returns:
        User dict if authenticated, None otherwise

    Example:
        ```python
        @router.get("/public-or-private")
        async def mixed_route(
            current_user: dict | None = Depends(get_optional_user)
        ):
            if current_user:
                # Authenticated logic
                user_id = current_user["id"]
            else:
                # Public logic
                pass
        ```
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization, supabase)
    except UnauthorizedError:
        return None
