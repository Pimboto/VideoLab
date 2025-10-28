"""
File-related Pydantic schemas
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, ConfigDict


# Request Schemas
class FileUploadRequest(BaseModel):
    """Base request for file uploads"""

    subfolder: str | None = Field(default=None, description="Optional subfolder for organization")


class FileDeleteRequest(BaseModel):
    """Request to delete a file"""

    filepath: str = Field(..., description="Absolute path to file to delete")


class FileBulkDeleteRequest(BaseModel):
    """Request to delete multiple files"""

    filepaths: List[str] = Field(..., description="List of file paths to delete", min_length=1)


class FileRenameRequest(BaseModel):
    """Request to rename a file (display name only)"""

    filepath: str = Field(..., description="File path")
    new_name: str = Field(..., description="New display name (without extension)")


class FileMoveRequest(BaseModel):
    """Request to move a file"""

    source_path: str = Field(..., description="Source file path")
    destination_folder: str = Field(..., description="Destination folder path")


class FileBulkMoveRequest(BaseModel):
    """Request to move multiple files"""

    filepaths: List[str] = Field(..., description="List of file paths to move", min_length=1)
    destination_folder: str = Field(..., description="Destination folder name")


class FolderCreateRequest(BaseModel):
    """Request to create a folder"""

    parent_category: str = Field(
        ..., description="Parent category (videos, audios, csv, output)"
    )
    folder_name: str = Field(..., description="Name of the folder to create")


class FolderDeleteRequest(BaseModel):
    """Request to delete a folder"""

    parent_category: str = Field(
        ..., description="Parent category (videos, audios)"
    )
    folder_name: str = Field(..., description="Name of the folder to delete")


class FolderListRequest(BaseModel):
    """Request to list files in a folder"""

    folder_path: str = Field(..., description="Absolute path to folder")


# Response Schemas
class FileInfo(BaseModel):
    """Detailed file information"""

    model_config = ConfigDict(from_attributes=True)

    filename: str = Field(..., description="Name of the file")
    filepath: str = Field(..., description="Absolute path to file")
    size: int = Field(..., description="File size in bytes", ge=0)
    modified: datetime = Field(..., description="Last modified timestamp")
    file_type: str = Field(..., description="Type of file (video, audio, csv)")
    metadata: dict | None = Field(default=None, description="Additional file metadata")


class FileUploadResponse(BaseModel):
    """Response after successful file upload"""

    filename: str = Field(..., description="Generated unique filename")
    filepath: str = Field(..., description="Full path to uploaded file")
    size: int = Field(..., description="File size in bytes", ge=0)
    message: str = Field(..., description="Success message")


class FileListResponse(BaseModel):
    """Response with list of files"""

    files: List[FileInfo] = Field(default_factory=list, description="List of files")
    count: int = Field(..., description="Total count of files", ge=0)


class FileDeleteResponse(BaseModel):
    """Response after file deletion"""

    message: str = Field(..., description="Success message")
    filepath: str = Field(..., description="Path of deleted file")


class FileBulkDeleteResponse(BaseModel):
    """Response after bulk file deletion"""

    message: str = Field(..., description="Success message")
    deleted_count: int = Field(..., description="Number of files successfully deleted", ge=0)
    failed_count: int = Field(0, description="Number of files that failed to delete", ge=0)
    failed_files: List[str] = Field(default_factory=list, description="List of file paths that failed to delete")


class FileRenameResponse(BaseModel):
    """Response after renaming file"""

    message: str = Field(..., description="Success message")
    filepath: str = Field(..., description="File path")
    new_display_name: str = Field(..., description="New display name")


class FileMoveResponse(BaseModel):
    """Response after moving file"""

    message: str = Field(..., description="Success message")
    source: str = Field(..., description="Original file path")
    destination: str = Field(..., description="New file path")


class FileBulkMoveResponse(BaseModel):
    """Response after bulk file move"""

    message: str = Field(..., description="Success message")
    moved_count: int = Field(..., description="Number of files successfully moved", ge=0)
    failed_count: int = Field(0, description="Number of files that failed to move", ge=0)
    failed_files: List[str] = Field(default_factory=list, description="List of file paths that failed to move")
    destination_folder: str = Field(..., description="Destination folder name")


class FolderInfo(BaseModel):
    """Folder information with stats"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Folder name")
    path: str = Field(..., description="Absolute path to folder")
    file_count: int = Field(..., description="Number of files in folder", ge=0)
    total_size: int = Field(..., description="Total size of all files in bytes", ge=0)


class FolderListResponse(BaseModel):
    """Response with list of folders"""

    folders: List[FolderInfo] = Field(default_factory=list, description="List of folders")
    count: int = Field(..., description="Total count of folders", ge=0)


class FolderCreateResponse(BaseModel):
    """Response after folder creation"""

    message: str = Field(..., description="Success message")
    folder_name: str = Field(..., description="Name of created folder")
    folder_path: str = Field(..., description="Full path to created folder")


class FolderDeleteResponse(BaseModel):
    """Response after folder deletion"""

    message: str = Field(..., description="Success message")
    folder_name: str = Field(..., description="Name of deleted folder")
    files_deleted: int = Field(0, description="Number of files deleted from folder")
