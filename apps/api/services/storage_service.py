"""
Storage service for AWS S3 operations

This service handles all file storage operations using AWS S3 + CloudFront.
Files are organized by user_id and category (videos, audios, csv, output, library).

Architecture:
- users/{user_id}/videos/{subfolder?}/filename.ext     # User private files
- users/{user_id}/audios/{subfolder?}/filename.ext
- users/{user_id}/csv/filename.ext
- users/{user_id}/output/filename.ext
- library/videos/{category}/filename.ext               # Global shared library
- library/audios/{category}/filename.ext
- library/images/{category}/filename.ext
"""
import datetime
import hashlib
import logging
import re
from typing import List, Optional
from pathlib import Path

from fastapi import UploadFile

from core.config import Settings
from core.exceptions import (
    FileNotFoundError,
    FileSizeLimitError,
    InvalidCategoryError,
    InvalidFileTypeError,
    StorageError,
)
from utils.aws_s3_client import S3Client, get_s3_client

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling AWS S3 Storage operations"""

    # Category to folder mapping
    CATEGORY_MAP = {
        "videos": "videos",
        "audios": "audios",
        "csv": "csv",
        "output": "output",
    }

    # Library categories (global shared content)
    LIBRARY_CATEGORIES = {
        "videos": "videos",
        "audios": "audios",
        "images": "images",
    }

    def __init__(self, settings: Settings, s3_client: Optional[S3Client] = None):
        self.settings = settings
        self.s3_client = s3_client or get_s3_client()

    def validate_file_extension(self, filename: str, file_type: str) -> bool:
        """Validate if file extension is allowed for the given type"""
        ext = Path(filename).suffix.lower()

        if file_type == "video":
            return ext in self.settings.video_extensions
        elif file_type == "audio":
            return ext in self.settings.audio_extensions
        elif file_type == "csv":
            return ext in self.settings.csv_extensions
        elif file_type == "image":
            return ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}

        return False

    def validate_file_size(self, file_size: int, file_type: str) -> bool:
        """Validate if file size is within limits"""
        limits = {
            "video": self.settings.max_video_size,
            "audio": self.settings.max_audio_size,
            "csv": self.settings.max_csv_size,
            "image": 10 * 1024 * 1024,  # 10 MB for images
        }

        max_size = limits.get(file_type)
        if max_size is None:
            return False

        return file_size <= max_size

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp and hash (DEPRECATED - for backwards compatibility)"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = Path(original_filename).stem
        ext = Path(original_filename).suffix
        random_hash = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"{name}_{timestamp}_{random_hash}{ext}"

    def get_unique_filename_no_timestamp(
        self,
        user_id: str,
        category: str,
        original_filename: str,
        subfolder: Optional[str] = None,
        is_library: bool = False
    ) -> str:
        """
        Get unique filename by adding (1), (2), etc if file already exists.

        Examples:
            video.mp4 -> video.mp4 (if doesn't exist)
            video.mp4 -> video (1).mp4 (if video.mp4 exists)
            video.mp4 -> video (2).mp4 (if video (1).mp4 exists)

        Args:
            user_id: User ID
            category: Storage category
            original_filename: Original filename
            subfolder: Optional subfolder
            is_library: Whether this is library content

        Returns:
            Unique filename

        Raises:
            StorageError: If too many duplicates (safety limit)
        """
        # Build path with original filename
        test_path = self.build_storage_path(
            user_id, category, original_filename, subfolder, is_library
        )

        # If doesn't exist, use original name
        if not self.s3_client.file_exists(test_path):
            return original_filename

        # Extract stem and extension
        stem = Path(original_filename).stem
        ext = Path(original_filename).suffix

        # Try with (1), (2), (3)...
        counter = 1
        while True:
            new_filename = f"{stem} ({counter}){ext}"
            test_path = self.build_storage_path(
                user_id, category, new_filename, subfolder, is_library
            )

            if not self.s3_client.file_exists(test_path):
                return new_filename

            counter += 1

            # Safety limit to prevent infinite loop
            if counter > 1000:
                raise StorageError(
                    f"Too many duplicate files for '{original_filename}'. "
                    f"Maximum 1000 duplicates allowed."
                )

    def sanitize_folder_name(self, folder_name: str) -> str:
        """Sanitize folder name to remove invalid characters"""
        return re.sub(r"[^\w\-_]", "_", folder_name)

    def get_category_folder(self, category: str) -> str:
        """Get folder name for a category"""
        folder = self.CATEGORY_MAP.get(category)
        if not folder:
            raise InvalidCategoryError(
                f"Invalid category: {category}. "
                f"Allowed: {', '.join(self.CATEGORY_MAP.keys())}"
            )
        return folder

    def build_storage_path(
        self,
        user_id: str,
        category: str,
        filename: str,
        subfolder: Optional[str] = None,
        is_library: bool = False
    ) -> str:
        """
        Build storage path (S3 key) for a file.

        User files: users/{user_id}/{category}/{subfolder?}/{filename}
        Library: library/{category}/{subfolder?}/{filename}
        """
        category_folder = self.get_category_folder(category)

        if is_library:
            # Library path: library/videos/category/filename.ext
            if subfolder:
                safe_subfolder = self.sanitize_folder_name(subfolder)
                return f"library/{category_folder}/{safe_subfolder}/{filename}"
            return f"library/{category_folder}/{filename}"
        else:
            # User path: users/user_id/videos/subfolder/filename.ext
            if subfolder:
                safe_subfolder = self.sanitize_folder_name(subfolder)
                return f"users/{user_id}/{category_folder}/{safe_subfolder}/{filename}"
            return f"users/{user_id}/{category_folder}/{filename}"

    async def upload_file(
        self,
        user_id: str,
        category: str,
        upload_file: UploadFile,
        subfolder: Optional[str] = None,
        unique_filename: Optional[str] = None,
        is_library: bool = False
    ) -> tuple[str, int]:
        """
        Upload file to AWS S3.

        NEW: Uses (1), (2) naming for duplicates instead of timestamps.

        Args:
            user_id: User ID for organization
            category: Storage category (videos, audios, csv, output)
            upload_file: FastAPI UploadFile
            subfolder: Optional subfolder for organization
            unique_filename: Optional unique filename (generated if not provided)
            is_library: Whether this is library (global) content

        Returns:
            Tuple of (storage_path, file_size)

        Raises:
            StorageError: If upload fails
        """
        try:
            # Generate unique filename if not provided
            # NEW: Uses (1), (2) for duplicates instead of timestamp
            if not unique_filename:
                unique_filename = self.get_unique_filename_no_timestamp(
                    user_id=user_id,
                    category=category,
                    original_filename=upload_file.filename,
                    subfolder=subfolder,
                    is_library=is_library
                )

            # Build storage path (S3 key)
            storage_path = self.build_storage_path(
                user_id, category, unique_filename, subfolder, is_library
            )

            # Read file content
            await upload_file.seek(0)
            file_content = await upload_file.read()
            file_size = len(file_content)

            # Upload to S3
            self.s3_client.upload_file(
                key=storage_path,
                file_content=file_content,
                content_type=upload_file.content_type or "application/octet-stream",
                metadata={"original_filename": upload_file.filename}
            )

            logger.info(
                f"File uploaded successfully: {storage_path}",
                extra={"user_id": user_id, "size": file_size, "file_name": unique_filename}
            )

            return storage_path, file_size

        except Exception as e:
            raise StorageError(f"Failed to upload file to S3: {str(e)}")

    async def upload_output_file(
        self,
        user_id: str,
        project_name: str,
        filename: str,
        file_content: bytes,
        content_type: str = "video/mp4"
    ) -> tuple[str, int]:
        """
        Upload output file to S3 with temporary tag for lifecycle deletion.

        Output files are automatically deleted after 24 hours by S3 lifecycle rule.

        Args:
            user_id: User ID
            project_name: Project name (used for folder organization)
            filename: Output filename
            file_content: File content as bytes
            content_type: MIME type

        Returns:
            Tuple of (storage_path, file_size)

        Raises:
            StorageError: If upload fails
        """
        try:
            # Sanitize project name for S3 (remove invalid characters)
            safe_project_name = self.sanitize_folder_name(project_name)
            
            # Build storage path: users/{user_id}/output/{project_name}/{filename}
            storage_path = f"users/{user_id}/output/{safe_project_name}/{filename}"
            file_size = len(file_content)

            # Upload to S3 with temporary tag
            # S3 lifecycle rule will delete after 24h based on this tag
            self.s3_client.upload_file_with_tags(
                key=storage_path,
                file_content=file_content,
                tags={"purpose": "temporary"},  # For lifecycle rule
                content_type=content_type,
                metadata={
                    "project_name": project_name,
                    "user_id": user_id,
                    "original_filename": filename
                }
            )

            logger.info(
                f"Output file uploaded with temporary tag: {storage_path}",
                extra={"user_id": user_id, "project_name": project_name, "size": file_size}
            )

            return storage_path, file_size

        except Exception as e:
            raise StorageError(f"Failed to upload output file to S3: {str(e)}")

    async def download_file(
        self,
        category: str,
        storage_path: str
    ) -> bytes:
        """
        Download file from AWS S3.

        Args:
            category: Storage category (for validation)
            storage_path: S3 key (path in bucket)

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If download fails
        """
        try:
            return self.s3_client.download_file(key=storage_path)

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to download file from S3: {str(e)}")

    def get_public_url(
        self,
        category: str,
        storage_path: str,
        expires_in: int = 3600,
        use_cloudfront: bool = True
    ) -> str:
        """
        Get public URL for a file (CloudFront or S3 presigned).

        Args:
            category: Storage category
            storage_path: S3 key
            expires_in: URL expiration in seconds (default: 1 hour)
            use_cloudfront: Use CloudFront URL (default: True)

        Returns:
            Public or presigned URL
        """
        try:
            return self.s3_client.generate_presigned_url(
                key=storage_path,
                expires_in=expires_in,
                use_cloudfront=use_cloudfront
            )

        except Exception as e:
            raise StorageError(f"Failed to generate file URL: {str(e)}")

    async def delete_file(
        self,
        category: str,
        storage_path: str
    ) -> None:
        """
        Delete file from AWS S3.

        Args:
            category: Storage category
            storage_path: S3 key

        Raises:
            StorageError: If deletion fails
        """
        try:
            self.s3_client.delete_file(key=storage_path)

        except Exception as e:
            raise StorageError(f"Failed to delete file from S3: {str(e)}")

    async def delete_files_batch(self, storage_paths: list[str]) -> tuple[int, int]:
        """
        Delete multiple files from S3 in batch.

        Args:
            storage_paths: List of S3 keys

        Returns:
            Tuple of (success_count, failure_count)
        """
        try:
            return self.s3_client.delete_files_batch(keys=storage_paths)
        except Exception as e:
            raise StorageError(f"Failed to batch delete files: {str(e)}")

    async def list_files(
        self,
        category: str,
        user_id: str,
        subfolder: Optional[str] = None,
        is_library: bool = False
    ) -> List[dict]:
        """
        List files in a user's folder or library.

        Args:
            category: Storage category
            user_id: User ID
            subfolder: Optional subfolder
            is_library: Whether to list library files

        Returns:
            List of file metadata dicts
        """
        try:
            # Build prefix
            category_folder = self.get_category_folder(category)

            if is_library:
                if subfolder:
                    safe_subfolder = self.sanitize_folder_name(subfolder)
                    prefix = f"library/{category_folder}/{safe_subfolder}/"
                else:
                    prefix = f"library/{category_folder}/"
            else:
                if subfolder:
                    safe_subfolder = self.sanitize_folder_name(subfolder)
                    prefix = f"users/{user_id}/{category_folder}/{safe_subfolder}/"
                else:
                    prefix = f"users/{user_id}/{category_folder}/"

            return self.s3_client.list_files(prefix=prefix)

        except Exception as e:
            # If path doesn't exist, return empty list instead of error
            return []

    async def move_file(
        self,
        category: str,
        source_path: str,
        destination_path: str
    ) -> None:
        """
        Move file to new location (copy + delete in S3).

        Args:
            category: Storage category
            source_path: Source S3 key
            destination_path: Destination S3 key

        Raises:
            FileNotFoundError: If source file doesn't exist
            StorageError: If move fails
        """
        try:
            self.s3_client.move_file(
                source_key=source_path,
                destination_key=destination_path
            )

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to move file in S3: {str(e)}")

    async def create_folder(
        self,
        category: str,
        user_id: str,
        folder_name: str,
        is_library: bool = False
    ) -> str:
        """
        Create a folder path.

        In S3, folders are implicit (created when files are uploaded).
        This method just validates the folder name and returns the path.

        Args:
            category: Storage category
            user_id: User ID
            folder_name: Folder name
            is_library: Whether this is library content

        Returns:
            Folder path (S3 prefix)
        """
        try:
            # Validate and sanitize
            category_folder = self.get_category_folder(category)
            safe_name = self.sanitize_folder_name(folder_name)

            if is_library:
                folder_path = f"library/{category_folder}/{safe_name}"
            else:
                folder_path = f"users/{user_id}/{category_folder}/{safe_name}"

            # Folders in S3 are implicit - they are created automatically
            # when files are uploaded to them
            return folder_path

        except Exception as e:
            raise StorageError(f"Failed to create folder path: {str(e)}")

    def file_exists(self, storage_path: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            storage_path: S3 key

        Returns:
            True if exists, False otherwise
        """
        return self.s3_client.file_exists(key=storage_path)

    async def rename_file_s3(
        self,
        user_id: str,
        category: str,
        old_filepath: str,
        new_filename: str,
        subfolder: Optional[str] = None,
        is_library: bool = False
    ) -> str:
        """
        Rename file in S3 (REAL rename with copy + delete).

        Handles duplicate names by adding (1), (2), etc.

        Args:
            user_id: User ID
            category: Storage category
            old_filepath: Current S3 path (full path)
            new_filename: New filename (just the filename, not full path)
            subfolder: Subfolder if applicable
            is_library: Whether this is library content

        Returns:
            New filepath (full S3 path)

        Raises:
            FileNotFoundError: If source file doesn't exist
            StorageError: If rename fails

        Examples:
            >>> rename_file_s3(
            ...     user_id="123",
            ...     category="videos",
            ...     old_filepath="users/123/videos/folder1/old_video.mp4",
            ...     new_filename="new_video.mp4",
            ...     subfolder="folder1"
            ... )
            "users/123/videos/folder1/new_video.mp4"

            If "new_video.mp4" already exists:
            "users/123/videos/folder1/new_video (1).mp4"
        """
        try:
            # Verify source exists
            if not self.s3_client.file_exists(old_filepath):
                raise FileNotFoundError(f"File not found: {old_filepath}")

            # Get unique filename (handles duplicates with (1), (2)...)
            unique_new_filename = self.get_unique_filename_no_timestamp(
                user_id=user_id,
                category=category,
                original_filename=new_filename,
                subfolder=subfolder,
                is_library=is_library
            )

            # Build new full path
            new_filepath = self.build_storage_path(
                user_id=user_id,
                category=category,
                filename=unique_new_filename,
                subfolder=subfolder,
                is_library=is_library
            )

            # Copy to new location
            self.s3_client.copy_object(
                source_key=old_filepath,
                destination_key=new_filepath
            )

            # Delete old file
            self.s3_client.delete_file(key=old_filepath)

            logger.info(
                f"File renamed in S3: {old_filepath} → {new_filepath}",
                extra={"user_id": user_id, "old_name": old_filepath.split('/')[-1], "new_name": unique_new_filename}
            )

            return new_filepath

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to rename file in S3: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to rename file: {str(e)}")
