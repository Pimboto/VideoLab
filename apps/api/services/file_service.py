"""
File service for file management operations with Supabase Storage and DB
"""
import csv
import io
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


class FileService:
    """Service for file management operations with Supabase"""

    def __init__(self, settings: Settings, storage_service: StorageService):
        self.settings = settings
        self.storage = storage_service
        self.supabase: Client = get_supabase_client()

    async def _create_file_metadata(
        self,
        user_id: str,
        filename: str,
        filepath: str,
        file_type: str,
        size_bytes: int,
        mime_type: Optional[str] = None,
        subfolder: Optional[str] = None,
        original_filename: Optional[str] = None
    ) -> dict:
        """Create file metadata record in database"""
        try:
            # Store original filename in metadata
            metadata = None
            if original_filename:
                metadata = {"original_filename": original_filename}

            file_data = FileCreate(
                user_id=user_id,
                filename=filename,
                filepath=filepath,
                file_type=file_type,
                size_bytes=size_bytes,
                mime_type=mime_type,
                subfolder=subfolder,
                metadata=metadata
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

        # Upload to Supabase Storage
        storage_path, saved_size = await self.storage.upload_file(
            user_id=user_id,
            category="videos",
            upload_file=file,
            subfolder=subfolder,
            unique_filename=unique_filename
        )

        # Create metadata record
        await self._create_file_metadata(
            user_id=user_id,
            filename=unique_filename,
            filepath=storage_path,
            file_type="video",
            size_bytes=saved_size,
            mime_type=file.content_type,
            subfolder=subfolder,
            original_filename=file.filename
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

            return FileDeleteResponse(
                message="File deleted successfully",
                filepath=file_data["filepath"]
            )
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}")

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
        """List all subfolders for a user in a category"""
        try:
            # Get unique subfolders from database
            result = self.supabase.table("files") \
                .select("subfolder") \
                .eq("user_id", user_id) \
                .eq("file_type", category.rstrip("s")) \
                .not_.is_("subfolder", "null") \
                .execute()
            
            # Get unique subfolders and count files
            subfolder_stats = {}
            for row in result.data:
                subfolder = row["subfolder"]
                if subfolder:
                    if subfolder not in subfolder_stats:
                        subfolder_stats[subfolder] = 0
                    subfolder_stats[subfolder] += 1
            
            folders = []
            for subfolder, count in subfolder_stats.items():
                from schemas.file_schemas import FolderInfo
                folders.append(FolderInfo(
                    name=subfolder,
                    path=f"{user_id}/{subfolder}",
                    file_count=count,
                    total_size=0  # We'd need to query file sizes separately
                ))
            
            return FolderListResponse(folders=folders, count=len(folders))
        except Exception as e:
            raise StorageError(f"Failed to list folders: {str(e)}")

    async def create_folder(
        self,
        user_id: str,
        category: str,
        folder_name: str
    ) -> FolderCreateResponse:
        """Create a new folder in Supabase Storage"""
        try:
            folder_path = await self.storage.create_folder(
                category=category,
                user_id=user_id,
                folder_name=folder_name
            )
            
            return FolderCreateResponse(
                message="Folder created successfully",
                folder_name=folder_name,
                folder_path=folder_path,
            )
        except Exception as e:
            raise StorageError(f"Failed to create folder: {str(e)}")
