"""
File service for file management operations
"""
import csv
import io
from pathlib import Path
from typing import List

from fastapi import UploadFile

from core.config import Settings
from core.exceptions import FileSizeLimitError, InvalidFileTypeError
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


class FileService:
    """Service for file management operations"""

    def __init__(self, settings: Settings, storage_service: StorageService):
        self.settings = settings
        self.storage = storage_service

    async def upload_video(
        self, file: UploadFile, subfolder: str | None = None
    ) -> FileUploadResponse:
        """Upload a video file"""
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

        # Generate unique filename
        unique_filename = self.storage.generate_unique_filename(file.filename)

        # Get destination path
        destination_dir = self.storage.get_storage_path("videos", subfolder)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / unique_filename

        # Save file
        saved_size = await self.storage.save_upload_file(file, destination)

        return FileUploadResponse(
            filename=unique_filename,
            filepath=str(destination),
            size=saved_size,
            message=f"Video uploaded successfully to {destination_dir.name}",
        )

    async def upload_audio(
        self, file: UploadFile, subfolder: str | None = None
    ) -> FileUploadResponse:
        """Upload an audio file"""
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

        # Generate unique filename
        unique_filename = self.storage.generate_unique_filename(file.filename)

        # Get destination path
        destination_dir = self.storage.get_storage_path("audios", subfolder)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / unique_filename

        # Save file
        saved_size = await self.storage.save_upload_file(file, destination)

        return FileUploadResponse(
            filename=unique_filename,
            filepath=str(destination),
            size=saved_size,
            message=f"Audio uploaded successfully to {destination_dir.name}",
        )

    async def upload_csv(
        self, file: UploadFile, save_file: bool = True
    ) -> TextCombinationsResponse:
        """Upload and parse a CSV file"""
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "csv"):
            raise InvalidFileTypeError(
                "Invalid file format. Only CSV files are allowed",
                details={"allowed_extensions": list(self.settings.csv_extensions)},
            )

        # Get file size
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
            unique_filename = self.storage.generate_unique_filename(file.filename)
            destination = self.settings.csv_storage_path / unique_filename

            with destination.open("wb") as f:
                f.write(content)

            saved_filepath = str(destination)
            filename = unique_filename

        return TextCombinationsResponse(
            combinations=combinations,
            count=len(combinations),
            saved=save_file,
            filepath=saved_filepath,
            filename=filename,
        )

    def list_videos(self, subfolder: str | None = None) -> FileListResponse:
        """List all video files"""
        folder_path = self.storage.get_storage_path("videos", subfolder)
        files = self.storage.list_files(
            folder_path, self.settings.video_extensions, "video"
        )
        return FileListResponse(files=files, count=len(files))

    def list_audios(self, subfolder: str | None = None) -> FileListResponse:
        """List all audio files"""
        folder_path = self.storage.get_storage_path("audios", subfolder)
        files = self.storage.list_files(
            folder_path, self.settings.audio_extensions, "audio"
        )
        return FileListResponse(files=files, count=len(files))

    def list_csvs(self) -> FileListResponse:
        """List all CSV files"""
        folder_path = self.settings.csv_storage_path
        files = self.storage.list_files(
            folder_path, self.settings.csv_extensions, "csv"
        )
        return FileListResponse(files=files, count=len(files))

    def delete_file(self, filepath: str) -> FileDeleteResponse:
        """Delete a file"""
        file_path = Path(filepath)
        self.storage.delete_file(file_path)

        return FileDeleteResponse(
            message="File deleted successfully", filepath=filepath
        )

    def move_file(self, source_path: str, destination_folder: str) -> FileMoveResponse:
        """Move a file to another folder"""
        source = Path(source_path)
        destination_dir = Path(destination_folder)

        new_path = self.storage.move_file(source, destination_dir)

        return FileMoveResponse(
            message="File moved successfully",
            source=source_path,
            destination=str(new_path),
        )

    def list_folders(self, category: str) -> FolderListResponse:
        """List all folders in a category"""
        folders = self.storage.list_folders(category)
        return FolderListResponse(folders=folders, count=len(folders))

    def create_folder(self, category: str, folder_name: str) -> FolderCreateResponse:
        """Create a new folder"""
        new_folder = self.storage.create_folder(category, folder_name)

        return FolderCreateResponse(
            message="Folder created successfully",
            folder_name=new_folder.name,
            folder_path=str(new_folder),
        )
