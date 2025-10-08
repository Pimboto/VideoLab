"""
File management routes
"""
from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
import os

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
    subfolder: str | None = Form(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload a video file.

    - **file**: Video file to upload
    - **subfolder**: Optional subfolder for organization (sent as form data)
    """
    return await file_service.upload_video(file, subfolder)


@router.post("/upload/audio", response_model=FileUploadResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload an audio file.

    - **file**: Audio file to upload
    - **subfolder**: Optional subfolder for organization (sent as form data)
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


@router.get("/outputs", response_model=FileListResponse)
def list_outputs(
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """List all processed/output video files."""
    import os
    from datetime import datetime

    output_dir = Path("D:/Work/video/output")
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


@router.get("/stream/video")
async def stream_video(filepath: str = Query(...)):
    """
    Stream a video file with range support for seeking.

    - **filepath**: Absolute path to the video file
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Determine media type from extension
    ext = file_path.suffix.lower()
    media_types = {
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
        '.m4v': 'video/x-m4v',
    }
    media_type = media_types.get(ext, 'video/mp4')

    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=file_path.name
    )


@router.get("/stream/audio")
async def stream_audio(filepath: str = Query(...)):
    """
    Stream an audio file.

    - **filepath**: Absolute path to the audio file
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Determine media type from extension
    ext = file_path.suffix.lower()
    media_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.aac': 'audio/aac',
    }
    media_type = media_types.get(ext, 'audio/mpeg')

    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=file_path.name
    )


@router.get("/preview/csv", response_model=TextCombinationsResponse)
async def preview_csv(
    filepath: str = Query(...),
    file_service: FileService = Depends(get_file_service),
) -> TextCombinationsResponse:
    """
    Preview a CSV file without uploading.

    - **filepath**: Absolute path to the CSV file
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CSV file not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Read and parse the CSV file
    import csv
    combinations = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # Skip empty rows
                    combinations.append(row)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    return TextCombinationsResponse(
        filename=file_path.name,
        combinations=combinations,
        count=len(combinations)
    )
