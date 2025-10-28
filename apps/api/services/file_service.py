"""
File service for file management operations with Supabase Storage and DB
"""
import csv
import io
import logging
import os
import subprocess
import tempfile
from typing import List, Optional
from pathlib import Path

from fastapi import UploadFile
from supabase import Client

from core.config import Settings
from core.exceptions import (
    FileSizeLimitError,
    InvalidFileTypeError,
    FileNotFoundError,
    StorageError
)
from models.file import FileCreate, File
from schemas.file_schemas import (
    FileDeleteResponse,
    FileInfo,
    FileListResponse,
    FileMoveResponse,
    FileUploadResponse,
    FolderCreateResponse,
    FolderListResponse,
)
from schemas.processing_schemas import TextCombinationsResponse
from services.storage_service import StorageService
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class FileService:
    """Service for file management operations with Supabase"""

    def __init__(self, settings: Settings, storage_service: StorageService):
        self.settings = settings
        self.storage = storage_service
        self.supabase: Client = get_supabase_client()

    async def _generate_video_thumbnail(
        self,
        video_content: bytes,
        output_path: str
    ) -> bool:
        """
        Generate ultra-optimized thumbnail from video using ffmpeg.

        Creates a 100x56 WebP thumbnail at 1 second mark with aggressive compression.
        If WebP fails, falls back to JPEG.
        Optimized for instant loading and minimal bandwidth.

        Args:
            video_content: Video file content in bytes
            output_path: Path to save thumbnail (will use .webp or .jpg)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temp file for video
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                temp_video.write(video_content)
                temp_video_path = temp_video.name

            try:
                # Try WebP first (much better compression than JPEG)
                webp_path = output_path.replace('.jpg', '.webp')

                # Generate thumbnail using ffmpeg with WebP
                # -ss 1: seek to 1 second
                # -i: input file
                # -vframes 1: extract 1 frame
                # -vf scale=100:56: scale to 100x56 (16:9, ultra tiny for instant load)
                # -c:v libwebp: use WebP codec
                # -quality 60: WebP quality (0-100, 60 is good balance)
                # -compression_level 6: WebP compression (0-6, 6 is max compression)
                result = subprocess.run(
                    [
                        'ffmpeg',
                        '-y',  # Overwrite output
                        '-ss', '1',  # Seek to 1 second
                        '-i', temp_video_path,  # Input
                        '-vframes', '1',  # Extract 1 frame
                        '-vf', 'scale=100:56',  # Scale to 100x56 (ultra tiny)
                        '-c:v', 'libwebp',  # WebP codec
                        '-quality', '60',  # WebP quality
                        '-compression_level', '6',  # Max compression
                        webp_path
                    ],
                    capture_output=True,
                    timeout=10  # 10 second timeout
                )

                # If WebP succeeded, use it
                if result.returncode == 0 and os.path.exists(webp_path):
                    # Rename to original output path if needed
                    if webp_path != output_path:
                        if os.path.exists(output_path):
                            os.unlink(output_path)
                        os.rename(webp_path, output_path)
                    return True

                # Fallback to JPEG if WebP failed
                logger.warning("WebP thumbnail generation failed, falling back to JPEG")
                result = subprocess.run(
                    [
                        'ffmpeg',
                        '-y',  # Overwrite output
                        '-ss', '1',  # Seek to 1 second
                        '-i', temp_video_path,  # Input
                        '-vframes', '1',  # Extract 1 frame
                        '-vf', 'scale=100:56',  # Scale to 100x56
                        '-q:v', '10',  # JPEG quality (aggressive compression)
                        output_path
                    ],
                    capture_output=True,
                    timeout=10
                )

                return result.returncode == 0 and os.path.exists(output_path)

            finally:
                # Clean up temp video file
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)

        except Exception as e:
            logger.error(f"Error generating video thumbnail: {str(e)}", exc_info=True)
            return False

    async def _sync_folder_metadata(
        self,
        user_id: str,
        category: str,
        subfolder: str,
        file_size_delta: int,
        file_count_delta: int | None = None
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
            logger.warning(f"Failed to sync folder metadata: {str(e)}", extra={"user_id": user_id, "category": category, "subfolder": subfolder})

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

    async def upload_video(
        self,
        user_id: str,
        file: UploadFile,
        subfolder: Optional[str] = None
    ) -> FileUploadResponse:
        """Upload a video file to Supabase Storage"""
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "video"):
            allowed = ", ".join(self.settings.video_extensions)
            raise InvalidFileTypeError(
                f"Invalid video format. Allowed: {allowed}",
                details={"allowed_extensions": list(self.settings.video_extensions)},
            )

        # Get file size (file.file is the SpooledTemporaryFile)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # Validate size
        if not self.storage.validate_file_size(file_size, "video"):
            max_mb = self.settings.max_video_size / (1024 * 1024)
            raise FileSizeLimitError(
                f"File too large. Maximum size: {max_mb:.0f}MB",
                details={"max_size": self.settings.max_video_size},
            )

        # Generate unique filename
        unique_filename = self.storage.generate_unique_filename(file.filename)

        # Read video content for thumbnail generation
        await file.seek(0)
        video_content = await file.read()

        # Upload video to Supabase Storage
        await file.seek(0)  # Reset for upload
        storage_path, saved_size = await self.storage.upload_file(
            user_id=user_id,
            category="videos",
            upload_file=file,
            subfolder=subfolder,
            unique_filename=unique_filename
        )

        # Generate and upload thumbnail
        thumbnail_url = None
        try:
            # Generate thumbnail
            thumb_filename = f"{Path(unique_filename).stem}_thumb.jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as thumb_file:
                thumb_path = thumb_file.name

            if await self._generate_video_thumbnail(video_content, thumb_path):
                # Upload thumbnail to Supabase (same bucket, thumbnails folder)
                with open(thumb_path, 'rb') as thumb_f:
                    thumb_content = thumb_f.read()
                    thumb_storage_path = f"{user_id}/thumbnails/{thumb_filename}"

                    # Upload to videos bucket
                    self.supabase.storage.from_("videos").upload(
                        thumb_storage_path,
                        thumb_content,
                        {"content-type": "image/jpeg"}
                    )

                    # Get public URL
                    thumb_url_response = self.supabase.storage.from_("videos").create_signed_url(
                        path=thumb_storage_path,
                        expires_in=31536000  # 1 year
                    )
                    if thumb_url_response and "signedURL" in thumb_url_response:
                        thumbnail_url = thumb_url_response["signedURL"]

            # Clean up temp file
            if os.path.exists(thumb_path):
                os.unlink(thumb_path)

        except Exception as e:
            logger.warning(f"Failed to generate/upload thumbnail: {str(e)}", extra={"user_id": user_id, "filename": unique_filename})
            # Continue without thumbnail - not critical

        # Prepare additional metadata
        additional_meta = {}
        if thumbnail_url:
            additional_meta["thumbnail_url"] = thumbnail_url

        # Create metadata record with thumbnail URL
        await self._create_file_metadata(
            user_id=user_id,
            filename=unique_filename,
            filepath=storage_path,
            file_type="video",
            size_bytes=saved_size,
            mime_type=file.content_type,
            subfolder=subfolder,
            original_filename=file.filename,
            additional_metadata=additional_meta if additional_meta else None
        )

        # Sync folder metadata (increment count and size)
        if subfolder:
            await self._sync_folder_metadata(
                user_id=user_id,
                category="video",
                subfolder=subfolder,
                file_size_delta=saved_size
            )

        return FileUploadResponse(
            filename=unique_filename,
            filepath=storage_path,
            size=saved_size,
            message=f"Video uploaded successfully",
        )

    async def upload_audio(
        self,
        user_id: str,
        file: UploadFile,
        subfolder: Optional[str] = None
    ) -> FileUploadResponse:
        """Upload an audio file to Supabase Storage"""
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "audio"):
            allowed = ", ".join(self.settings.audio_extensions)
            raise InvalidFileTypeError(
                f"Invalid audio format. Allowed: {allowed}",
                details={"allowed_extensions": list(self.settings.audio_extensions)},
            )

        # Get file size (file.file is the SpooledTemporaryFile)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # Validate size
        if not self.storage.validate_file_size(file_size, "audio"):
            max_mb = self.settings.max_audio_size / (1024 * 1024)
            raise FileSizeLimitError(
                f"File too large. Maximum size: {max_mb:.0f}MB",
                details={"max_size": self.settings.max_audio_size},
            )

        # Generate unique filename
        unique_filename = self.storage.generate_unique_filename(file.filename)

        # Upload to Supabase Storage
        storage_path, saved_size = await self.storage.upload_file(
            user_id=user_id,
            category="audios",
            upload_file=file,
            subfolder=subfolder,
            unique_filename=unique_filename
        )

        # Create metadata record
        await self._create_file_metadata(
            user_id=user_id,
            filename=unique_filename,
            filepath=storage_path,
            file_type="audio",
            size_bytes=saved_size,
            mime_type=file.content_type,
            subfolder=subfolder,
            original_filename=file.filename
        )

        # Sync folder metadata (increment count and size)
        if subfolder:
            await self._sync_folder_metadata(
                user_id=user_id,
                category="audio",
                subfolder=subfolder,
                file_size_delta=saved_size
            )

        return FileUploadResponse(
            filename=unique_filename,
            filepath=storage_path,
            size=saved_size,
            message=f"Audio uploaded successfully",
        )

    async def upload_csv(
        self,
        user_id: str,
        file: UploadFile,
        save_file: bool = True
    ) -> TextCombinationsResponse:
        """Upload and parse a CSV file"""
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "csv"):
            raise InvalidFileTypeError(
                "Invalid file format. Only CSV files are allowed",
                details={"allowed_extensions": list(self.settings.csv_extensions)},
            )

        # Get file size (file.file is the SpooledTemporaryFile)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # Validate size
        if not self.storage.validate_file_size(file_size, "csv"):
            max_mb = self.settings.max_csv_size / (1024 * 1024)
            raise FileSizeLimitError(
                f"File too large. Maximum size: {max_mb:.0f}MB",
                details={"max_size": self.settings.max_csv_size},
            )

        # Read and parse CSV
        content = await file.read()
        text_content = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text_content))

        combinations = []
        for row in reader:
            if not row:
                continue
            segs = [c.strip() for c in row if c and c.strip()]
            if segs:
                combinations.append(segs)

        # Save file if requested
        saved_filepath = None
        filename = file.filename

        if save_file:
            # Generate unique filename
            unique_filename = self.storage.generate_unique_filename(file.filename)

            # Create new file-like object from content (file was already read)
            file.file = io.BytesIO(content)
            file.file.seek(0)

            # Upload to Supabase Storage
            storage_path, saved_size = await self.storage.upload_file(
                user_id=user_id,
                category="csv",
                upload_file=file,
                subfolder=None,
                unique_filename=unique_filename
            )
            
            # Create metadata record
            await self._create_file_metadata(
                user_id=user_id,
                filename=unique_filename,
                filepath=storage_path,
                file_type="csv",
                size_bytes=saved_size,
                mime_type=file.content_type,
                subfolder=None,
                original_filename=file.filename
            )
            
            saved_filepath = storage_path
            filename = unique_filename

        return TextCombinationsResponse(
            combinations=combinations,
            count=len(combinations),
            saved=save_file,
            filepath=saved_filepath,
            filename=filename,
        )

    async def list_videos(
        self,
        user_id: str,
        subfolder: Optional[str] = None
    ) -> FileListResponse:
        """List all video files for a user from database"""
        try:
            query = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("file_type", "video")
            
            if subfolder:
                query = query.eq("subfolder", subfolder)
            
            result = query.order("created_at", desc=True).execute()
            
            files = []
            for file_data in result.data:
                # Parse metadata if it's a JSON string
                metadata = file_data.get("metadata")
                if metadata and isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = None

                files.append(FileInfo(
                    filename=file_data["filename"],
                    filepath=file_data["filepath"],
                    size=file_data["size_bytes"],
                    modified=file_data["created_at"],
                    file_type="video",
                    metadata=metadata
                ))

            return FileListResponse(files=files, count=len(files))
        except Exception as e:
            raise StorageError(f"Failed to list videos: {str(e)}")

    async def list_audios(
        self,
        user_id: str,
        subfolder: Optional[str] = None
    ) -> FileListResponse:
        """List all audio files for a user from database"""
        try:
            query = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("file_type", "audio")
            
            if subfolder:
                query = query.eq("subfolder", subfolder)
            
            result = query.order("created_at", desc=True).execute()
            
            files = []
            for file_data in result.data:
                # Parse metadata if it's a JSON string
                metadata = file_data.get("metadata")
                if metadata and isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = None

                files.append(FileInfo(
                    filename=file_data["filename"],
                    filepath=file_data["filepath"],
                    size=file_data["size_bytes"],
                    modified=file_data["created_at"],
                    file_type="audio",
                    metadata=metadata
                ))

            return FileListResponse(files=files, count=len(files))
        except Exception as e:
            raise StorageError(f"Failed to list audios: {str(e)}")

    async def list_csvs(
        self,
        user_id: str
    ) -> FileListResponse:
        """List all CSV files for a user from database"""
        try:
            result = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("file_type", "csv") \
                .order("created_at", desc=True) \
                .execute()
            
            files = []
            for file_data in result.data:
                # Parse metadata if it's a JSON string
                metadata = file_data.get("metadata")
                if metadata and isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = None

                files.append(FileInfo(
                    filename=file_data["filename"],
                    filepath=file_data["filepath"],
                    size=file_data["size_bytes"],
                    modified=file_data["created_at"],
                    file_type="csv",
                    metadata=metadata
                ))

            return FileListResponse(files=files, count=len(files))
        except Exception as e:
            raise StorageError(f"Failed to list CSVs: {str(e)}")

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

            # Delete from storage
            await self.storage.delete_file(
                category=file_data["file_type"] + "s",  # video -> videos
                storage_path=file_data["filepath"]
            )

            # Delete metadata from database
            self.supabase.table("files").delete().eq("id", file_id).execute()

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
        from schemas.file_schemas import FileBulkDeleteResponse

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
                    logger.error(f"Error deleting file: {str(e)}", extra={"filepath": filepath}, exc_info=True)
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
                    logger.warning(f"Failed to sync folder metadata after bulk delete: {str(e)}", extra=folder_update)

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

    async def list_folders(
        self,
        user_id: str,
        category: str
    ) -> FolderListResponse:
        """
        List all folders for a user in a category.

        Queries the dedicated folders table with pre-calculated metadata.
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
            from schemas.file_schemas import FolderInfo
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

        Inserts into folders table. The actual Supabase Storage folder
        is created implicitly when first file is uploaded.
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
    ) -> tuple[str, int]:
        """
        Delete a folder and all its files.

        Args:
            user_id: User ID
            category: Category (videos, audios)
            folder_name: Folder name

        Returns:
            Tuple of (message, files_deleted_count)
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
                    # Delete from Supabase Storage
                    await self.storage.delete_file(
                        category=category,
                        storage_path=file_data["filepath"]
                    )

                    # Delete from database
                    self.supabase.table("files").delete().eq("id", file_data["id"]).execute()
                    files_deleted += 1

                except Exception as e:
                    logger.warning(f"Failed to delete file from folder: {str(e)}", extra={"filepath": file_data['filepath']})
                    continue

            # Delete folder from folders table
            self.supabase.table("folders").delete() \
                .eq("user_id", user_id) \
                .eq("category", category.rstrip("s")) \
                .eq("folder_name", folder_name) \
                .execute()

            from schemas.file_schemas import FolderDeleteResponse
            return FolderDeleteResponse(
                message=f"Folder '{folder_name}' deleted successfully",
                folder_name=folder_name,
                files_deleted=files_deleted
            )

        except Exception as e:
            raise StorageError(f"Failed to delete folder: {str(e)}")

    async def rename_file(
        self,
        user_id: str,
        filepath: str,
        new_display_name: str
    ):
        """
        Rename file (display name only - doesn't move physical file).

        Updates the original_filename in metadata for display purposes.

        Args:
            user_id: User ID
            filepath: File path
            new_display_name: New display name (can include extension)

        Returns:
            FileRenameResponse
        """
        from schemas.file_schemas import FileRenameResponse

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

            # Update metadata with new display name
            current_metadata = file_data.get("metadata") or {}
            if isinstance(current_metadata, str):
                import json
                current_metadata = json.loads(current_metadata)

            current_metadata["original_filename"] = new_display_name

            # Update in database
            self.supabase.table("files") \
                .update({"metadata": current_metadata}) \
                .eq("filepath", filepath) \
                .eq("user_id", user_id) \
                .execute()

            return FileRenameResponse(
                message="File renamed successfully",
                filepath=filepath,
                new_display_name=new_display_name
            )

        except Exception as e:
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
        from schemas.file_schemas import FileBulkMoveResponse

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
                    file_size = file_data["size"]

                    # Determine category from file_type
                    category = f"{file_type}s"  # video -> videos, audio -> audios

                    # Build new storage path
                    filename = filepath.split("/")[-1]
                    new_filepath = f"{user_id}/{destination_folder}/{filename}"

                    # Move file in Supabase Storage
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
                        source_key = f"{user_id}_{category}_{current_subfolder}"
                        if source_key not in folder_updates:
                            folder_updates[source_key] = {
                                "user_id": user_id,
                                "category": category,
                                "subfolder": current_subfolder,
                                "size_delta": 0,
                                "count_delta": 0
                            }
                        folder_updates[source_key]["size_delta"] -= file_size
                        folder_updates[source_key]["count_delta"] -= 1

                    # Destination folder (increase)
                    dest_key = f"{user_id}_{category}_{destination_folder}"
                    if dest_key not in folder_updates:
                        folder_updates[dest_key] = {
                            "user_id": user_id,
                            "category": category,
                            "subfolder": destination_folder,
                            "size_delta": 0,
                            "count_delta": 0
                        }
                    folder_updates[dest_key]["size_delta"] += file_size
                    folder_updates[dest_key]["count_delta"] += 1

                    moved_count += 1

                except Exception as e:
                    logger.error(f"Error moving file: {str(e)}", extra={"filepath": filepath}, exc_info=True)
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
                    logger.warning(f"Failed to sync folder metadata after bulk move: {str(e)}", extra=folder_update)

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
        List all processed/output video files.

        Note: Output files are stored locally (not in Supabase) for now.
        This is legacy behavior that should eventually migrate to Supabase Storage.

        Args:
            user_id: User ID (for future user-specific filtering)

        Returns:
            FileListResponse with output files
        """
        import os
        from datetime import datetime

        output_dir = self.settings.output_storage_path
        files_list = []

        if output_dir.exists():
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                        filepath = Path(root) / file
                        stat = filepath.stat()

                        # Get the folder name relative to output dir
                        relative_path = filepath.relative_to(output_dir)
                        folder_name = str(relative_path.parent) if relative_path.parent != Path('.') else ""

                        files_list.append({
                            "filename": file,
                            "filepath": str(filepath),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "file_type": "video",
                            "folder": folder_name
                        })

        # Sort by modified date, newest first
        files_list.sort(key=lambda x: x["modified"], reverse=True)

        return FileListResponse(files=files_list, count=len(files_list))
