"""
File management routes
"""
from fastapi import APIRouter, Depends, File, Query, UploadFile

from core.dependencies import get_file_service
from schemas.file_schemas import (
    FileDeleteRequest,
    FileDeleteResponse,
    FileListResponse,
    FileMoveRequest,
    FileMoveResponse,
    FileUploadResponse,
)
from schemas.processing_schemas import TextCombinationsResponse
from services.file_service import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload/video", response_model=FileUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    subfolder: str | None = Query(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload a video file.

    - **file**: Video file to upload
    - **subfolder**: Optional subfolder for organization
    """
    return await file_service.upload_video(file, subfolder)


@router.post("/upload/audio", response_model=FileUploadResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    subfolder: str | None = Query(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload an audio file.

    - **file**: Audio file to upload
    - **subfolder**: Optional subfolder for organization
    """
    return await file_service.upload_audio(file, subfolder)


@router.post("/upload/csv", response_model=TextCombinationsResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    save_file: bool = Query(default=True),
    file_service: FileService = Depends(get_file_service),
) -> TextCombinationsResponse:
    """
    Upload and parse a CSV file.

    - **file**: CSV file to upload and parse
    - **save_file**: Whether to save the file to storage
    """
    return await file_service.upload_csv(file, save_file)


@router.get("/videos", response_model=FileListResponse)
def list_videos(
    subfolder: str | None = Query(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all video files with detailed information.

    - **subfolder**: Optional subfolder filter
    """
    return file_service.list_videos(subfolder)


@router.get("/audios", response_model=FileListResponse)
def list_audios(
    subfolder: str | None = Query(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all audio files with detailed information.

    - **subfolder**: Optional subfolder filter
    """
    return file_service.list_audios(subfolder)


@router.get("/csv", response_model=FileListResponse)
def list_csvs(
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """List all saved CSV files with detailed information."""
    return file_service.list_csvs()


@router.delete("/delete", response_model=FileDeleteResponse)
def delete_file(
    request: FileDeleteRequest,
    file_service: FileService = Depends(get_file_service),
) -> FileDeleteResponse:
    """
    Delete a file.

    - **filepath**: Absolute path to file to delete
    """
    return file_service.delete_file(request.filepath)


@router.post("/move", response_model=FileMoveResponse)
def move_file(
    request: FileMoveRequest,
    file_service: FileService = Depends(get_file_service),
) -> FileMoveResponse:
    """
    Move a file to another folder.

    - **source_path**: Source file path
    - **destination_folder**: Destination folder path
    """
    return file_service.move_file(request.source_path, request.destination_folder)
