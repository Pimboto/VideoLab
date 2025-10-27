"""
Storage service for Supabase Storage operations

This service handles all file storage operations using Supabase Storage.
Files are organized by user_id and category (videos, audios, csv, output).
"""
import datetime
import hashlib
import re
from typing import List, Optional
from pathlib import Path

from fastapi import UploadFile
from supabase import Client

from core.config import Settings
from core.exceptions import (
    FileNotFoundError,
    FileSizeLimitError,
    InvalidCategoryError,
    InvalidFileTypeError,
    StorageError,
)
from utils.supabase_client import get_supabase_client


class StorageService:
    """Service for handling Supabase Storage operations"""

    BUCKET_MAP = {
        "videos": "videos",
        "audios": "audios",
        "csv": "csv",
        "output": "output",
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.supabase: Client = get_supabase_client()

    def validate_file_extension(self, filename: str, file_type: str) -> bool:
        """Validate if file extension is allowed for the given type"""
        ext = Path(filename).suffix.lower()

        if file_type == "video":
            return ext in self.settings.video_extensions
        elif file_type == "audio":
            return ext in self.settings.audio_extensions
        elif file_type == "csv":
            return ext in self.settings.csv_extensions

        return False

    def validate_file_size(self, file_size: int, file_type: str) -> bool:
        """Validate if file size is within limits"""
        limits = {
            "video": self.settings.max_video_size,
            "audio": self.settings.max_audio_size,
            "csv": self.settings.max_csv_size,
        }

        max_size = limits.get(file_type)
        if max_size is None:
            return False

        return file_size <= max_size

    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp and hash"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = Path(original_filename).stem
        ext = Path(original_filename).suffix
        random_hash = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"{name}_{timestamp}_{random_hash}{ext}"

    def sanitize_folder_name(self, folder_name: str) -> str:
        """Sanitize folder name to remove invalid characters"""
        return re.sub(r"[^\w\-_]", "_", folder_name)

    def get_bucket_name(self, category: str) -> str:
        """Get Supabase Storage bucket name for a category"""
        bucket = self.BUCKET_MAP.get(category)
        if not bucket:
            raise InvalidCategoryError(
                f"Invalid category: {category}. "
                f"Allowed: {', '.join(self.BUCKET_MAP.keys())}"
            )
        return bucket

    def build_storage_path(
        self,
        user_id: str,
        filename: str,
        subfolder: Optional[str] = None
    ) -> str:
        """
        Build storage path for a file.
        Format: {user_id}/{subfolder}/{filename} or {user_id}/{filename}
        """
        if subfolder:
            safe_subfolder = self.sanitize_folder_name(subfolder)
            return f"{user_id}/{safe_subfolder}/{filename}"
        return f"{user_id}/{filename}"

    async def upload_file(
        self,
        user_id: str,
        category: str,
        upload_file: UploadFile,
        subfolder: Optional[str] = None,
        unique_filename: Optional[str] = None
    ) -> tuple[str, int]:
        """
        Upload file to Supabase Storage.
        
        Args:
            user_id: User ID for organization
            category: Storage category (videos, audios, csv, output)
            upload_file: FastAPI UploadFile
            subfolder: Optional subfolder for organization
            unique_filename: Optional unique filename (generated if not provided)
        
        Returns:
            Tuple of (storage_path, file_size)
        
        Raises:
            StorageError: If upload fails
        """
        try:
            # Get bucket
            bucket = self.get_bucket_name(category)
            
            # Generate unique filename if not provided
            if not unique_filename:
                unique_filename = self.generate_unique_filename(upload_file.filename)
            
            # Build storage path
            storage_path = self.build_storage_path(user_id, unique_filename, subfolder)
            
            # Read file content
            await upload_file.seek(0)
            file_content = await upload_file.read()
            file_size = len(file_content)
            
            # Upload to Supabase Storage
            result = self.supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": upload_file.content_type or "application/octet-stream",
                    "cache-control": "3600",
                    "upsert": "false"  # Fail if file already exists
                }
            )
            
            if not result:
                raise StorageError(f"Failed to upload file to {bucket}/{storage_path}")
            
            return storage_path, file_size
            
        except Exception as e:
            raise StorageError(f"Failed to upload file: {str(e)}")

    async def download_file(
        self,
        category: str,
        storage_path: str
    ) -> bytes:
        """
        Download file from Supabase Storage.
        
        Args:
            category: Storage category
            storage_path: Path in storage bucket
        
        Returns:
            File content as bytes
        
        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If download fails
        """
        try:
            bucket = self.get_bucket_name(category)
            
            result = self.supabase.storage.from_(bucket).download(storage_path)
            
            if not result:
                raise FileNotFoundError(f"File not found: {bucket}/{storage_path}")
            
            return result
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to download file: {str(e)}")

    def get_public_url(
        self,
        category: str,
        storage_path: str
    ) -> str:
        """
        Get public URL for a file (or signed URL if bucket is private).
        
        Args:
            category: Storage category
            storage_path: Path in storage bucket
        
        Returns:
            Public or signed URL
        """
        try:
            bucket = self.get_bucket_name(category)
            
            # Get signed URL for private buckets (expires in 1 hour)
            result = self.supabase.storage.from_(bucket).create_signed_url(
                path=storage_path,
                expires_in=3600  # 1 hour
            )
            
            if result and "signedURL" in result:
                return result["signedURL"]
            
            # Fallback to public URL (might not work if bucket is private)
            return self.supabase.storage.from_(bucket).get_public_url(storage_path)
            
        except Exception as e:
            raise StorageError(f"Failed to get file URL: {str(e)}")

    async def delete_file(
        self,
        category: str,
        storage_path: str
    ) -> None:
        """
        Delete file from Supabase Storage.
        
        Args:
            category: Storage category
            storage_path: Path in storage bucket
        
        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If deletion fails
        """
        try:
            bucket = self.get_bucket_name(category)
            
            result = self.supabase.storage.from_(bucket).remove([storage_path])
            
            if not result:
                raise StorageError(f"Failed to delete file: {bucket}/{storage_path}")
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise FileNotFoundError(f"File not found: {bucket}/{storage_path}")
            raise StorageError(f"Failed to delete file: {str(e)}")

    async def list_files(
        self,
        category: str,
        user_id: str,
        subfolder: Optional[str] = None
    ) -> List[dict]:
        """
        List files in a user's folder.
        
        Args:
            category: Storage category
            user_id: User ID
            subfolder: Optional subfolder
        
        Returns:
            List of file metadata dicts
        """
        try:
            bucket = self.get_bucket_name(category)
            
            # Build path prefix
            if subfolder:
                safe_subfolder = self.sanitize_folder_name(subfolder)
                path = f"{user_id}/{safe_subfolder}"
            else:
                path = user_id
            
            result = self.supabase.storage.from_(bucket).list(path)
            
            if not result:
                return []
            
            return result
            
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
        Move file to new location (copy + delete).
        
        Args:
            category: Storage category
            source_path: Source path in bucket
            destination_path: Destination path in bucket
        
        Raises:
            FileNotFoundError: If source file doesn't exist
            StorageError: If move fails
        """
        try:
            bucket = self.get_bucket_name(category)
            
            # Supabase doesn't have a native move operation
            # We need to download, upload to new location, and delete old
            result = self.supabase.storage.from_(bucket).move(
                from_path=source_path,
                to_path=destination_path
            )
            
            if not result:
                raise StorageError(f"Failed to move file from {source_path} to {destination_path}")
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            raise StorageError(f"Failed to move file: {str(e)}")

    async def create_folder(
        self,
        category: str,
        user_id: str,
        folder_name: str
    ) -> str:
        """
        Create a folder (in Supabase Storage, folders are implicit).
        
        This creates a .gitkeep file to ensure the folder exists.
        
        Args:
            category: Storage category
            user_id: User ID
            folder_name: Folder name
        
        Returns:
            Folder path
        """
        try:
            bucket = self.get_bucket_name(category)
            safe_name = self.sanitize_folder_name(folder_name)
            folder_path = f"{user_id}/{safe_name}"
            
            # Create a .gitkeep file to make the folder exist
            placeholder_path = f"{folder_path}/.gitkeep"
            
            self.supabase.storage.from_(bucket).upload(
                path=placeholder_path,
                file=b"",
                file_options={"content-type": "text/plain"}
            )
            
            return folder_path
            
        except Exception as e:
            raise StorageError(f"Failed to create folder: {str(e)}")
