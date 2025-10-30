"""
Media Upload Service

Handles video and audio uploads with optimizations:
- Video thumbnail generation
- Metadata creation
- Folder stats synchronization
"""
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from core.config import Settings
from core.exceptions import (
    FileSizeLimitError,
    InvalidFileTypeError,
    StorageError,
)
from schemas.file_schemas import FileUploadResponse
from services.storage_service import StorageService
from supabase import Client


logger = logging.getLogger(__name__)


class MediaUploadService:
    """Service for uploading video and audio files"""

    def __init__(
        self,
        settings: Settings,
        storage_service: StorageService,
        supabase: Client
    ):
        self.settings = settings
        self.storage = storage_service
        self.supabase = supabase

    async def _generate_video_thumbnail(
        self,
        video_content: bytes,
        output_path: str
    ) -> bool:
        """
        Generate optimized thumbnail from video using ffmpeg.

        Creates a 240x135 WebP thumbnail at 1 second mark with balanced quality.
        If WebP fails, falls back to JPEG.
        Optimized for good visual quality while maintaining reasonable file size.

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
                result = subprocess.run(
                    [
                        'ffmpeg',
                        '-y',  # Overwrite output
                        '-ss', '1',  # Seek to 1 second
                        '-i', temp_video_path,  # Input
                        '-vframes', '1',  # Extract 1 frame
                        '-vf', 'scale=135:240:force_original_aspect_ratio=decrease', 
                        '-c:v', 'libwebp',  # WebP codec
                        '-quality', '85',  # WebP quality (good balance)
                        '-compression_level', '4',  # Balanced compression
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
                        '-vf', 'scale=240:135:force_original_aspect_ratio=decrease',  # Scale to 240x135 (16:9 aspect ratio)
                        '-q:v', '5',  # JPEG quality (good balance - lower number = higher quality)
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

    async def _create_file_metadata(
        self,
        user_id: str,
        filename: str,
        filepath: str,
        file_type: str,
        size_bytes: int,
        mime_type: Optional[str],
        subfolder: Optional[str],
        original_filename: str,
        additional_metadata: Optional[dict] = None
    ) -> None:
        """Create file metadata record in database"""
        try:
            metadata = {
                "original_filename": original_filename,
                "storage_type": "s3"
            }

            if additional_metadata:
                metadata.update(additional_metadata)

            self.supabase.table("files").insert({
                "user_id": user_id,
                "filename": filename,
                "filepath": filepath,
                "file_type": file_type,
                "size_bytes": size_bytes,
                "mime_type": mime_type,
                "subfolder": subfolder,
                "metadata": metadata
            }).execute()

        except Exception as e:
            logger.error(f"Failed to create file metadata: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to create file metadata: {str(e)}")

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

    async def upload_video(
        self,
        user_id: str,
        file: UploadFile,
        subfolder: Optional[str] = None
    ) -> FileUploadResponse:
        """Upload a video file to AWS S3 with thumbnail generation"""
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "video"):
            allowed = ", ".join(self.settings.video_extensions)
            raise InvalidFileTypeError(
                f"Invalid video format. Allowed: {allowed}",
                details={"allowed_extensions": list(self.settings.video_extensions)},
            )

        # Get file size
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

        # Read video content for thumbnail generation
        await file.seek(0)
        video_content = await file.read()

        # Upload video to AWS S3 (NO unique_filename param - let it generate without timestamp)
        await file.seek(0)  # Reset for upload
        storage_path, saved_size = await self.storage.upload_file(
            user_id=user_id,
            category="videos",
            upload_file=file,
            subfolder=subfolder
        )

        # Extract filename from storage path
        uploaded_filename = storage_path.split("/")[-1]

        # Generate and upload thumbnail
        thumbnail_url = None
        try:
            # Generate thumbnail
            thumb_filename = f"{Path(uploaded_filename).stem}_thumb.jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as thumb_file:
                thumb_path = thumb_file.name

            if await self._generate_video_thumbnail(video_content, thumb_path):
                # Upload thumbnail to S3
                with open(thumb_path, 'rb') as thumb_f:
                    thumb_content = thumb_f.read()

                    # Build S3 key for thumbnail
                    thumb_storage_path = f"users/{user_id}/videos/thumbnails/{thumb_filename}"

                    # Upload to S3
                    self.storage.s3_client.upload_file(
                        key=thumb_storage_path,
                        file_content=thumb_content,
                        content_type="image/jpeg"
                    )

                    # Get CloudFront URL
                    thumbnail_url = self.storage.get_public_url(
                        category="videos",
                        storage_path=thumb_storage_path,
                        expires_in=31536000,  # 1 year
                        use_cloudfront=True
                    )

            # Clean up temp file
            if os.path.exists(thumb_path):
                os.unlink(thumb_path)

        except Exception as e:
            logger.warning(f"Failed to generate/upload thumbnail: {str(e)}", extra={"user_id": user_id, "file_name": uploaded_filename})
            # Continue without thumbnail - not critical

        # Prepare additional metadata
        additional_meta = {}
        if thumbnail_url:
            additional_meta["thumbnail_url"] = thumbnail_url

        # Create metadata record with thumbnail URL
        await self._create_file_metadata(
            user_id=user_id,
            filename=uploaded_filename,
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
            filename=uploaded_filename,
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
        """Upload an audio file to AWS S3"""
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "audio"):
            allowed = ", ".join(self.settings.audio_extensions)
            raise InvalidFileTypeError(
                f"Invalid audio format. Allowed: {allowed}",
                details={"allowed_extensions": list(self.settings.audio_extensions)},
            )

        # Get file size
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

        # Upload to AWS S3 (NO unique_filename param - let it generate without timestamp)
        storage_path, saved_size = await self.storage.upload_file(
            user_id=user_id,
            category="audios",
            upload_file=file,
            subfolder=subfolder
        )

        # Extract filename from storage path
        uploaded_filename = storage_path.split("/")[-1]

        # Create metadata record
        await self._create_file_metadata(
            user_id=user_id,
            filename=uploaded_filename,
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
            filename=uploaded_filename,
            filepath=storage_path,
            size=saved_size,
            message=f"Audio uploaded successfully",
        )
