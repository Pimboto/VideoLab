"""
Storage service for file operations
"""
import datetime
import hashlib
import re
import shutil
from pathlib import Path
from typing import List

from fastapi import UploadFile

from core.config import Settings
from core.exceptions import (
    FileNotFoundError,
    FileSizeLimitError,
    FolderAlreadyExistsError,
    FolderNotFoundError,
    InvalidCategoryError,
    InvalidFileTypeError,
    StorageError,
)
from schemas.file_schemas import FileInfo, FolderInfo


class StorageService:
    """Service for handling file storage operations"""

    def __init__(self, settings: Settings):
        self.settings = settings

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

    def get_storage_path(self, category: str, subfolder: str | None = None) -> Path:
        """Get storage path for a category with optional subfolder"""
        try:
            base_path = self.settings.get_storage_path(category)
        except ValueError as e:
            raise InvalidCategoryError(str(e))

        if subfolder:
            safe_subfolder = self.sanitize_folder_name(subfolder)
            return base_path / safe_subfolder

        return base_path

    async def save_upload_file(
        self, upload_file: UploadFile, destination: Path
    ) -> int:
        """Save uploaded file and return size"""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)

            total_size = 0
            with destination.open("wb") as buffer:
                while chunk := await upload_file.read(self.settings.chunk_size):
                    total_size += len(chunk)
                    buffer.write(chunk)

            return total_size
        except Exception as e:
            if destination.exists():
                destination.unlink()
            raise StorageError(f"Failed to save file: {str(e)}")

    def get_file_info(self, filepath: Path, file_type: str) -> FileInfo:
        """Get detailed file information"""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not filepath.is_file():
            raise StorageError(f"Path is not a file: {filepath}")

        stat = filepath.stat()
        return FileInfo(
            filename=filepath.name,
            filepath=str(filepath),
            size=stat.st_size,
            modified=datetime.datetime.fromtimestamp(stat.st_mtime),
            file_type=file_type,
        )

    def list_files(
        self, folder_path: Path, extensions: set[str], file_type: str
    ) -> List[FileInfo]:
        """List all files in a folder with given extensions"""
        if not folder_path.exists():
            return []

        if not folder_path.is_dir():
            raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

        files = []
        for file_path in folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                files.append(self.get_file_info(file_path, file_type))

        # Sort by modified date, newest first
        files.sort(key=lambda x: x.modified, reverse=True)
        return files

    def delete_file(self, filepath: Path) -> None:
        """Delete a file"""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not filepath.is_file():
            raise StorageError(f"Path is not a file: {filepath}")

        try:
            filepath.unlink()
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}")

    def move_file(self, source: Path, destination_dir: Path) -> Path:
        """Move file to destination directory"""
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        if not source.is_file():
            raise StorageError(f"Source path is not a file: {source}")

        # Create destination directory if needed
        destination_dir.mkdir(parents=True, exist_ok=True)

        if not destination_dir.is_dir():
            raise StorageError(f"Destination is not a directory: {destination_dir}")

        destination_file = destination_dir / source.name

        if destination_file.exists():
            raise StorageError(
                f"File already exists at destination: {destination_file.name}"
            )

        try:
            shutil.move(str(source), str(destination_file))
            return destination_file
        except Exception as e:
            raise StorageError(f"Failed to move file: {str(e)}")

    def get_folder_info(self, folder_path: Path) -> FolderInfo:
        """Get folder information including file count and total size"""
        if not folder_path.exists():
            raise FolderNotFoundError(f"Folder not found: {folder_path}")

        if not folder_path.is_dir():
            raise StorageError(f"Path is not a directory: {folder_path}")

        files = [f for f in folder_path.iterdir() if f.is_file()]
        total_size = sum(f.stat().st_size for f in files)
        file_count = len(files)

        return FolderInfo(
            name=folder_path.name,
            path=str(folder_path),
            file_count=file_count,
            total_size=total_size,
        )

    def list_folders(self, category: str) -> List[FolderInfo]:
        """List all subfolders in a category"""
        try:
            base_path = self.settings.get_storage_path(category)
        except ValueError as e:
            raise InvalidCategoryError(str(e))

        if not base_path.exists():
            return []

        folders = []
        for item in base_path.iterdir():
            if item.is_dir():
                folders.append(self.get_folder_info(item))

        # Sort by name
        folders.sort(key=lambda x: x.name)
        return folders

    def create_folder(self, category: str, folder_name: str) -> Path:
        """Create a new folder in a category"""
        try:
            base_path = self.settings.get_storage_path(category)
        except ValueError as e:
            raise InvalidCategoryError(str(e))

        safe_name = self.sanitize_folder_name(folder_name)
        new_folder = base_path / safe_name

        if new_folder.exists():
            raise FolderAlreadyExistsError(f"Folder already exists: {safe_name}")

        try:
            new_folder.mkdir(parents=True, exist_ok=False)
            return new_folder
        except Exception as e:
            raise StorageError(f"Failed to create folder: {str(e)}")
