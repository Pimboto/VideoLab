"""
File service for core file management operations with AWS S3 Storage and DB

This service handles:
- File listing (videos, audios)
- File deletion (single and bulk)
- File renaming
- File moving (bulk)
- Output file listing

Upload operations have been moved to specialized services:
- MediaUploadService: video and audio uploads
- CSVService: CSV uploads and parsing
- FolderService: folder management
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from supabase import Client

from core.config import Settings
from core.exceptions import (
    FileNotFoundError,
    StorageError
)
from models.file import FileCreate
from schemas.file_schemas import (
    FileBulkDeleteResponse,
    FileBulkMoveResponse,
    FileDeleteResponse,
    FileInfo,
    FileListResponse,
    FileRenameResponse,
)
from services.storage_service import StorageService
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class FileService:
    """Service for core file management operations with AWS S3"""

    def __init__(self, settings: Settings, storage_service: StorageService):
        self.settings = settings
        self.storage = storage_service
        self.supabase: Client = get_supabase_client()

    async def _sync_folder_metadata(
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

    async def _create_file_metadata(
        self,
        user_id: str,
        filename: str,
        filepath: str,
        file_type: str,
        size_bytes: int,
        mime_type: Optional[str] = None,
        subfolder: Optional[str] = None,
        original_filename: Optional[str] = None,
        additional_metadata: Optional[dict] = None
    ) -> dict:
        """Create file metadata record in database"""
        try:
            # Store original filename and any additional metadata
            metadata = {}
            if original_filename:
                metadata["original_filename"] = original_filename

            # Merge additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)

            # Only set metadata if we have any
            file_metadata = metadata if metadata else None

            file_data = FileCreate(
                user_id=user_id,
                filename=filename,
                filepath=filepath,
                file_type=file_type,
                size_bytes=size_bytes,
                mime_type=mime_type,
                subfolder=subfolder,
                metadata=file_metadata
            )

            result = self.supabase.table("files").insert(file_data.model_dump()).execute()

            if not result.data or len(result.data) == 0:
                raise StorageError("Failed to create file metadata in database")

            return result.data[0]
        except Exception as e:
            raise StorageError(f"Failed to save file metadata: {str(e)}")

    async def list_files(
        self,
        user_id: str,
        file_type: str,
        subfolder: Optional[str] = None
    ) -> FileListResponse:
        """
        List all files for a user by file type.

        Unified method that works for videos, audios, and CSVs.

        Args:
            user_id: User ID
            file_type: File type (video, audio, csv)
            subfolder: Optional subfolder filter

        Returns:
            FileListResponse with list of files
        """
        try:
            query = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("file_type", file_type)

            if subfolder:
                query = query.eq("subfolder", subfolder)

            result = query.order("created_at", desc=True).execute()

            files = []
            for file_data in result.data:
                # Parse metadata if it's a JSON string
                metadata = file_data.get("metadata")
                if metadata and isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = None

                files.append(FileInfo(
                    filename=file_data["filename"],
                    filepath=file_data["filepath"],
                    size=file_data["size_bytes"],
                    modified=file_data["created_at"],
                    file_type=file_type,
                    metadata=metadata
                ))

            return FileListResponse(files=files, count=len(files))
        except Exception as e:
            raise StorageError(f"Failed to list {file_type} files: {str(e)}")

    async def list_videos(
        self,
        user_id: str,
        subfolder: Optional[str] = None
    ) -> FileListResponse:
        """List all video files for a user from database"""
        return await self.list_files(user_id, "video", subfolder)

    async def list_audios(
        self,
        user_id: str,
        subfolder: Optional[str] = None
    ) -> FileListResponse:
        """List all audio files for a user from database"""
        return await self.list_files(user_id, "audio", subfolder)

    async def delete_file(
        self,
        user_id: str,
        file_id: str
    ) -> FileDeleteResponse:
        """Delete a file by ID (from storage and database)"""
        try:
            # Get file metadata
            result = self.supabase.table("files") \
                .select("*") \
                .eq("id", file_id) \
                .eq("user_id", user_id) \
                .execute()

            if not result.data or len(result.data) == 0:
                raise FileNotFoundError(f"File not found or access denied")

            file_data = result.data[0]
            subfolder = file_data.get("subfolder")
            file_size = file_data.get("size_bytes", 0)
            file_type = file_data.get("file_type", "")

            # Delete from storage
            await self.storage.delete_file(
                category=file_type + "s",  # video -> videos
                storage_path=file_data["filepath"]
            )

            # Delete metadata from database
            self.supabase.table("files").delete().eq("id", file_id).execute()

            # Update folder stats (decrement count and size)
            if subfolder:
                await self._sync_folder_metadata(
                    user_id=user_id,
                    category=file_type,
                    subfolder=subfolder,
                    file_size_delta=-file_size,
                    file_count_delta=-1
                )

            return FileDeleteResponse(
                message="File deleted successfully",
                filepath=file_data["filepath"]
            )
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}")

    async def delete_file_by_path(
        self,
        user_id: str,
        filepath: str
    ) -> FileDeleteResponse:
        """Delete a file by filepath (from storage and database)"""
        try:
            # Get file metadata by filepath
            result = self.supabase.table("files") \
                .select("*") \
                .eq("filepath", filepath) \
                .eq("user_id", user_id) \
                .execute()

            if not result.data or len(result.data) == 0:
                raise FileNotFoundError(f"File not found or access denied")

            file_data = result.data[0]

            # Map file_type to storage category
            file_type = file_data["file_type"]
            category_map = {
                "video": "videos",
                "audio": "audios",
                "csv": "csv",
                "output": "output"
            }
            category = category_map.get(file_type, file_type)

            # Delete from storage
            await self.storage.delete_file(
                category=category,
                storage_path=file_data["filepath"]
            )

            # Delete metadata from database
            self.supabase.table("files").delete().eq("id", file_data["id"]).execute()

            # Sync folder metadata (decrement count and size)
            if file_data.get("subfolder") and file_data["file_type"] in ["video", "audio"]:
                await self._sync_folder_metadata(
                    user_id=user_id,
                    category=file_data["file_type"],
                    subfolder=file_data["subfolder"],
                    file_size_delta=-file_data["size_bytes"]  # Negative for deletion
                )

            return FileDeleteResponse(
                message="File deleted successfully",
                filepath=file_data["filepath"]
            )
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}")

    async def bulk_delete_files(
        self,
        user_id: str,
        filepaths: list[str]
    ):
        """
        Delete multiple files efficiently.

        Best practice for bulk operations:
        - Process all files in a single operation when possible
        - Track successes and failures separately
        - Update folder metadata once per folder (not per file)
        - Return detailed results for UI feedback
        """
        deleted_count = 0
        failed_count = 0
        failed_files = []

        # Track folder updates (folder_key -> size_delta)
        folder_updates = {}

        try:
            # Get all file metadata in a single query
            result = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .in_("filepath", filepaths) \
                .execute()

            files_to_delete = result.data or []

            # Create a map for quick lookup
            files_map = {f["filepath"]: f for f in files_to_delete}

            # Process each file
            for filepath in filepaths:
                file_data = files_map.get(filepath)

                if not file_data:
                    failed_count += 1
                    failed_files.append(filepath)
                    continue

                try:
                    # Map file_type to storage category
                    file_type = file_data["file_type"]
                    category_map = {
                        "video": "videos",
                        "audio": "audios",
                        "csv": "csv",
                        "output": "output"
                    }
                    category = category_map.get(file_type, file_type)

                    # Delete from storage
                    await self.storage.delete_file(
                        category=category,
                        storage_path=file_data["filepath"]
                    )

                    # Delete from database
                    self.supabase.table("files").delete().eq("id", file_data["id"]).execute()

                    # Track folder update (accumulate deltas)
                    if file_data.get("subfolder") and file_data["file_type"] in ["video", "audio"]:
                        folder_key = f"{user_id}:{file_data['file_type']}:{file_data['subfolder']}"
                        if folder_key not in folder_updates:
                            folder_updates[folder_key] = {
                                "user_id": user_id,
                                "category": file_data["file_type"],
                                "subfolder": file_data["subfolder"],
                                "size_delta": 0,
                                "count_delta": 0
                            }
                        folder_updates[folder_key]["size_delta"] -= file_data["size_bytes"]
                        folder_updates[folder_key]["count_delta"] -= 1

                    deleted_count += 1

                except Exception as e:
                    logger.error(
                        f"Error deleting file: {str(e)}",
                        extra={"filepath": filepath},
                        exc_info=True
                    )
                    failed_count += 1
                    failed_files.append(filepath)

            # Update all affected folders in batch
            for folder_update in folder_updates.values():
                try:
                    await self._sync_folder_metadata(
                        user_id=folder_update["user_id"],
                        category=folder_update["category"],
                        subfolder=folder_update["subfolder"],
                        file_size_delta=folder_update["size_delta"],
                        file_count_delta=folder_update["count_delta"]
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to sync folder metadata after bulk delete: {str(e)}",
                        extra=folder_update
                    )

            # Build response message
            if deleted_count == len(filepaths):
                message = f"Successfully deleted all {deleted_count} files"
            elif deleted_count > 0:
                message = f"Deleted {deleted_count} files, {failed_count} failed"
            else:
                message = "Failed to delete any files"

            return FileBulkDeleteResponse(
                message=message,
                deleted_count=deleted_count,
                failed_count=failed_count,
                failed_files=failed_files
            )

        except Exception as e:
            raise StorageError(f"Bulk delete operation failed: {str(e)}")

    async def get_file_download_url(
        self,
        user_id: str,
        file_id: str
    ) -> str:
        """Get signed download URL for a file"""
        try:
            # Get file metadata
            result = self.supabase.table("files") \
                .select("*") \
                .eq("id", file_id) \
                .eq("user_id", user_id) \
                .execute()

            if not result.data or len(result.data) == 0:
                raise FileNotFoundError(f"File not found or access denied")

            file_data = result.data[0]

            # Get signed URL
            url = self.storage.get_public_url(
                category=file_data["file_type"] + "s",
                storage_path=file_data["filepath"]
            )

            return url
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get download URL: {str(e)}")

    async def rename_file(
        self,
        user_id: str,
        filepath: str,
        new_display_name: str
    ):
        """
        Rename file (REAL rename in S3 + database update).

        NEW: Actually renames the file in S3 (copy + delete), not just metadata.
        Handles duplicate names by adding (1), (2), etc.

        Args:
            user_id: User ID
            filepath: Current file path (full S3 path)
            new_display_name: New filename (can include extension)

        Returns:
            FileRenameResponse with new filepath

        Examples:
            If renaming "video.mp4" to "my_video.mp4":
            - S3: copies users/.../video.mp4 -> users/.../my_video.mp4, deletes old
            - DB: updates filename and filepath columns
        """
        try:
            # Get file from database
            result = self.supabase.table("files") \
                .select("*") \
                .eq("filepath", filepath) \
                .eq("user_id", user_id) \
                .single() \
                .execute()

            if not result.data:
                raise HTTPException(status_code=404, detail="File not found")

            file_data = result.data

            # Extract category and subfolder from current filepath
            # Format: users/{user_id}/{category}/{subfolder?}/{filename}
            parts = filepath.split("/")
            if len(parts) < 4:
                raise StorageError("Invalid filepath format")

            category = parts[2]  # "videos", "audios", "csv"
            # Determine if there's a subfolder
            if len(parts) == 5:
                subfolder = parts[3]
            elif len(parts) > 5:
                # Handle nested subfolders
                subfolder = "/".join(parts[3:-1])
            else:
                subfolder = None

            # Rename file in S3 (REAL rename with copy + delete)
            # Note: storage service expects plural categories (videos, audios, csv, output)
            new_filepath = await self.storage.rename_file_s3(
                user_id=user_id,
                category=category,  # Keep plural: "videos", "audios", "csv"
                old_filepath=filepath,
                new_filename=new_display_name,
                subfolder=subfolder,
                is_library=False
            )

            # Extract new filename from new_filepath
            new_filename = new_filepath.split("/")[-1]

            # Update database with NEW filename and filepath
            self.supabase.table("files") \
                .update({
                    "filename": new_filename,
                    "filepath": new_filepath,
                    "updated_at": "now()"
                }) \
                .eq("filepath", filepath) \
                .eq("user_id", user_id) \
                .execute()

            logger.info(
                f"File renamed successfully: {filepath} → {new_filepath}",
                extra={
                    "user_id": user_id,
                    "old": filepath.split("/")[-1],
                    "new": new_filename
                }
            )

            return FileRenameResponse(
                message="File renamed successfully",
                filepath=new_filepath,
                new_display_name=new_filename
            )

        except Exception as e:
            logger.error(f"Failed to rename file: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to rename file: {str(e)}")

    async def bulk_move_files(
        self,
        user_id: str,
        filepaths: list[str],
        destination_folder: str
    ):
        """
        Move multiple files to a destination folder in a single operation.

        Updates both storage paths and database records.
        Optimized for batch operations with minimal database calls.

        Args:
            user_id: User ID
            filepaths: List of file paths to move
            destination_folder: Destination folder name

        Returns:
            FileBulkMoveResponse with success/failure counts
        """
        moved_count = 0
        failed_count = 0
        failed_files = []

        # Track folder updates (source and destination)
        folder_updates = {}

        try:
            for filepath in filepaths:
                try:
                    # Get file metadata
                    result = self.supabase.table("files") \
                        .select("*") \
                        .eq("filepath", filepath) \
                        .eq("user_id", user_id) \
                        .single() \
                        .execute()

                    if not result.data:
                        failed_count += 1
                        failed_files.append(filepath)
                        continue

                    file_data = result.data
                    file_type = file_data["file_type"]
                    current_subfolder = file_data.get("subfolder", "")
                    file_size = file_data["size_bytes"]

                    # Determine category from file_type
                    category = f"{file_type}s"  # video -> videos, audio -> audios
                    category_folder = category  # videos, audios, etc.

                    # Build new storage path with correct prefix
                    filename = filepath.split("/")[-1]
                    new_filepath = f"users/{user_id}/{category_folder}/{destination_folder}/{filename}"

                    # Move file in AWS S3
                    await self.storage.move_file(
                        category=category,
                        source_path=filepath,
                        destination_path=new_filepath
                    )

                    # Update database record
                    self.supabase.table("files") \
                        .update({
                            "filepath": new_filepath,
                            "subfolder": destination_folder
                        }) \
                        .eq("filepath", filepath) \
                        .eq("user_id", user_id) \
                        .execute()

                    # Track folder updates for batch metadata sync
                    # Source folder (decrease)
                    if current_subfolder:
                        source_key = f"{user_id}_{file_type}_{current_subfolder}"
                        if source_key not in folder_updates:
                            folder_updates[source_key] = {
                                "user_id": user_id,
                                "category": file_type,  # Use singular: "video", "audio"
                                "subfolder": current_subfolder,
                                "size_delta": 0,
                                "count_delta": 0
                            }
                        folder_updates[source_key]["size_delta"] -= file_size
                        folder_updates[source_key]["count_delta"] -= 1

                    # Destination folder (increase)
                    dest_key = f"{user_id}_{file_type}_{destination_folder}"
                    if dest_key not in folder_updates:
                        folder_updates[dest_key] = {
                            "user_id": user_id,
                            "category": file_type,  # Use singular: "video", "audio"
                            "subfolder": destination_folder,
                            "size_delta": 0,
                            "count_delta": 0
                        }
                    folder_updates[dest_key]["size_delta"] += file_size
                    folder_updates[dest_key]["count_delta"] += 1

                    moved_count += 1

                except Exception as e:
                    logger.error(
                        f"Error moving file: {str(e)}",
                        extra={"filepath": filepath},
                        exc_info=True
                    )
                    failed_count += 1
                    failed_files.append(filepath)

            # Update all affected folders in batch
            for folder_update in folder_updates.values():
                try:
                    await self._sync_folder_metadata(
                        user_id=folder_update["user_id"],
                        category=folder_update["category"],
                        subfolder=folder_update["subfolder"],
                        file_size_delta=folder_update["size_delta"],
                        file_count_delta=folder_update["count_delta"]
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to sync folder metadata after bulk move: {str(e)}",
                        extra=folder_update
                    )

            # Build response message
            if moved_count == len(filepaths):
                message = f"Successfully moved all {moved_count} files"
            elif moved_count > 0:
                message = f"Moved {moved_count} files, {failed_count} failed"
            else:
                message = "Failed to move any files"

            return FileBulkMoveResponse(
                message=message,
                moved_count=moved_count,
                failed_count=failed_count,
                failed_files=failed_files,
                destination_folder=destination_folder
            )

        except Exception as e:
            raise StorageError(f"Bulk move operation failed: {str(e)}")

    def list_output_files(self, user_id: str) -> FileListResponse:
        """
        List all processed/output video files from AWS S3.

        Note: Output files are stored in S3 with tag purpose=temporary
        and automatically deleted after 24h by S3 lifecycle rule.

        Args:
            user_id: User ID to filter outputs

        Returns:
            FileListResponse with output files from S3
        """
        try:
            # List all files in user's output folder on S3
            prefix = f"users/{user_id}/output/"
            s3_files = self.storage.s3_client.list_files(prefix=prefix)

            files_list = []
            for s3_file in s3_files:
                # Extract filename from S3 key
                # Format: users/{user_id}/output/{project_name}/{filename}.mp4
                key = s3_file.get('key', '') or s3_file.get('Key', '')  # Handle both cases
                if not key:
                    continue
                    
                filename = key.split('/')[-1]

                # Extract project_name (folder name in S3)
                key_parts = key.split('/')
                project_name = key_parts[3] if len(key_parts) > 3 else ""

                # Get file metadata from S3
                size_bytes = s3_file.get('size', 0) or s3_file.get('Size', 0)
                last_modified = s3_file.get('last_modified') or s3_file.get('LastModified')

                # Convert datetime to ISO string
                if last_modified:
                    if isinstance(last_modified, datetime):
                        modified_str = last_modified.isoformat()
                    else:
                        modified_str = last_modified
                else:
                    modified_str = datetime.now().isoformat()

                files_list.append({
                    "filename": filename,
                    "filepath": key,  # Full S3 key
                    "size": size_bytes,
                    "size_bytes": size_bytes,  # For compatibility
                    "modified": modified_str,
                    "file_type": "output",
                    "folder": project_name,  # Project name as folder
                    "metadata": {
                        "storage_type": "s3",
                        "temporary": True,
                        "expires_in": "24 hours",
                    }
                })

            # Sort by modified date, newest first
            files_list.sort(key=lambda x: x["modified"], reverse=True)

            logger.info(f"Listed {len(files_list)} output files for user {user_id} from S3")
            return FileListResponse(files=files_list, count=len(files_list))

        except Exception as e:
            logger.error(f"Error listing output files from S3: {str(e)}", exc_info=True)
            # Return empty list on error instead of failing
            return FileListResponse(files=[], count=0)
