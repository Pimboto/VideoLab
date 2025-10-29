"""
Supabase Client Singleton

This module provides a singleton instance of the Supabase client
for database and storage operations.
"""
import logging
from functools import lru_cache
from supabase import create_client, Client
from core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase_client() -> Client:
    """
    Get a singleton Supabase client instance.

    Uses the service role key for backend operations, which bypasses RLS.
    For user-specific operations, we'll manually enforce user isolation.

    Returns:
        Client: Supabase client instance
    """
    settings = get_settings()

    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key
    )


def update_folder_stats(
    user_id: str,
    category: str,
    folder_name: str,
    file_count_delta: int = 0,
    size_delta: int = 0
) -> bool:
    """
    Update folder statistics (file_count and total_size) atomically.

    Uses PostgreSQL RPC function for atomic updates (same as _sync_folder_metadata).
    Creates folder if it doesn't exist.

    Args:
        user_id: User ID
        category: Category (video, audio)
        folder_name: Folder name
        file_count_delta: Change in file count (+1 for add, -1 for delete)
        size_delta: Change in total size in bytes (+ for add, - for delete)

    Returns:
        True if successful, False otherwise

    Examples:
        >>> update_folder_stats("user123", "video", "my-videos", +1, +1024000)  # Add file
        >>> update_folder_stats("user123", "video", "my-videos", -1, -1024000)  # Delete file
    """
    if not folder_name:
        return True  # No folder to update

    try:
        supabase = get_supabase_client()

        # Use PostgreSQL RPC function for atomic updates
        # This function handles creating folder if it doesn't exist
        supabase.rpc(
            "sync_folder_metadata",
            {
                "p_user_id": user_id,
                "p_category": category,
                "p_folder_name": folder_name,
                "p_file_count_delta": file_count_delta,
                "p_size_delta": size_delta
            }
        ).execute()

        logger.info(
            f"Updated folder stats: {folder_name}",
            extra={
                "user_id": user_id,
                "category": category,
                "folder": folder_name,
                "file_count_delta": file_count_delta,
                "size_delta": size_delta
            }
        )

        return True

    except Exception as e:
        logger.warning(
            f"Failed to update folder stats: {str(e)}",
            extra={"user_id": user_id, "category": category, "folder": folder_name}
        )
        return False
