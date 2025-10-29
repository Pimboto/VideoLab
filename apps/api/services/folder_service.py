"""
Folder Service

Handles folder management operations:
- Folder creation and deletion
- Folder listing with metadata
- Atomic folder stats synchronization
"""
import logging
from typing import Optional

from core.exceptions import StorageError
from schemas.file_schemas import (
    FolderCreateResponse,
    FolderDeleteResponse,
    FolderInfo,
    FolderListResponse,
)
from services.storage_service import StorageService
from supabase import Client


logger = logging.getLogger(__name__)


class FolderService:
    """Service for folder operations"""

    def __init__(
        self,
        storage_service: StorageService,
        supabase: Client
    ):
        self.storage = storage_service
        self.supabase = supabase

    async def sync_folder_metadata(
        self,
        user_id: str,
        category: str,
        subfolder: str,
        file_size_delta: int,
        file_count_delta: Optional[int] = None
    ) -> None:
        """
        Atomically update folder metadata (file_count and total_size).

        Uses a PostgreSQL function for true atomic updates.

        Args:
            user_id: User ID
            category: File category (video, audio)
            subfolder: Folder name
            file_size_delta: Change in size (positive for add, negative for delete)
            file_count_delta: Change in file count (optional, auto-calculated if not provided)
        """
        if not subfolder:
            return  # No folder to update

        try:
            # Calculate count delta if not provided (for single file operations)
            if file_count_delta is None:
                file_count_delta = 1 if file_size_delta > 0 else -1

            self.supabase.rpc(
                "sync_folder_metadata",
                {
                    "p_user_id": user_id,
                    "p_category": category,
                    "p_folder_name": subfolder,
                    "p_file_count_delta": file_count_delta,
                    "p_size_delta": file_size_delta
                }
            ).execute()

        except Exception as e:
            # Log but don't fail the operation - folder metadata is cached
            # If folder doesn't exist, the function handles it gracefully
            logger.warning(
                f"Failed to sync folder metadata: {str(e)}",
                extra={"user_id": user_id, "category": category, "subfolder": subfolder}
            )

    async def list_folders(
        self,
        user_id: str,
        category: str
    ) -> FolderListResponse:
        """
        List all folders for a user in a category.

        Queries the dedicated folders table with pre-calculated metadata.

        Args:
            user_id: User ID
            category: Category (videos, audios, csv)

        Returns:
            FolderListResponse with list of folders and their metadata
        """
        try:
            # Query folders table directly (fast, single query)
            result = self.supabase.table("folders") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("category", category.rstrip("s")) \
                .order("created_at", desc=False) \
                .execute()

            if not result.data:
                return FolderListResponse(folders=[], count=0)

            # Map to response schema
            folders = [
                FolderInfo(
                    name=row["folder_name"],
                    path=row["folder_path"],
                    file_count=row["file_count"],
                    total_size=row["total_size"]
                )
                for row in result.data
            ]

            return FolderListResponse(folders=folders, count=len(folders))

        except Exception as e:
            raise StorageError(f"Failed to list folders: {str(e)}")

    async def create_folder(
        self,
        user_id: str,
        category: str,
        folder_name: str
    ) -> FolderCreateResponse:
        """
        Create a new folder.

        Inserts into folders table. The actual AWS S3 folder
        is created implicitly when first file is uploaded.

        Args:
            user_id: User ID
            category: Category (videos, audios, csv)
            folder_name: Name of the folder to create

        Returns:
            FolderCreateResponse with success message and folder metadata
        """
        try:
            # Validate and build folder path
            folder_path = await self.storage.create_folder(
                category=category,
                user_id=user_id,
                folder_name=folder_name
            )

            # Insert into folders table
            from models.folder import FolderCreate
            folder_data = FolderCreate(
                user_id=user_id,
                category=category.rstrip("s"),  # "videos" → "video"
                folder_name=folder_name,
                folder_path=folder_path
            )

            result = self.supabase.table("folders").insert(folder_data.model_dump()).execute()

            if not result.data or len(result.data) == 0:
                raise StorageError("Failed to create folder in database")

            return FolderCreateResponse(
                message="Folder created successfully",
                folder_name=folder_name,
                folder_path=folder_path,
            )

        except Exception as e:
            raise StorageError(f"Failed to create folder: {str(e)}")

    async def delete_folder(
        self,
        user_id: str,
        category: str,
        folder_name: str
    ) -> FolderDeleteResponse:
        """
        Delete a folder and all its files.

        Deletes all files in the folder from both S3 storage and database,
        then removes the folder record from the folders table.

        Args:
            user_id: User ID
            category: Category (videos, audios)
            folder_name: Folder name

        Returns:
            FolderDeleteResponse with deletion details
        """
        try:
            # Get all files in the folder
            result = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("file_type", category.rstrip("s")) \
                .eq("subfolder", folder_name) \
                .execute()

            files_to_delete = result.data or []
            files_deleted = 0

            # Delete each file (from storage and database)
            for file_data in files_to_delete:
                try:
                    # Delete from AWS S3
                    await self.storage.delete_file(
                        category=category,
                        storage_path=file_data["filepath"]
                    )

                    # Delete from database
                    self.supabase.table("files").delete().eq("id", file_data["id"]).execute()
                    files_deleted += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to delete file from folder: {str(e)}",
                        extra={"filepath": file_data['filepath']}
                    )
                    continue

            # Delete folder from folders table
            self.supabase.table("folders").delete() \
                .eq("user_id", user_id) \
                .eq("category", category.rstrip("s")) \
                .eq("folder_name", folder_name) \
                .execute()

            return FolderDeleteResponse(
                message=f"Folder '{folder_name}' deleted successfully",
                folder_name=folder_name,
                files_deleted=files_deleted
            )

        except Exception as e:
            raise StorageError(f"Failed to delete folder: {str(e)}")
