"""
File management routes
"""
import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
import os

from core.dependencies import (
    get_file_service,
    get_current_user,
    get_media_upload_service,
    get_csv_service,
)
from core.exceptions import StorageError
from schemas.file_schemas import (
    FileDeleteRequest,
    FileDeleteResponse,
    FileBulkDeleteRequest,
    FileBulkDeleteResponse,
    FileListResponse,
    FileRenameRequest,
    FileRenameResponse,
    FileMoveRequest,
    FileMoveResponse,
    FileBulkMoveRequest,
    FileBulkMoveResponse,
    FileUploadResponse,
)
from schemas.processing_schemas import TextCombinationsResponse
from services.file_service import FileService
from services.media_upload_service import MediaUploadService
from services.csv_service import CSVService

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)


@router.post("/upload/video", response_model=FileUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),
    media_service: MediaUploadService = Depends(get_media_upload_service),
) -> FileUploadResponse:
    """
    Upload a video file.

    Requires authentication.

    - **file**: Video file to upload
    - **subfolder**: Optional subfolder for organization (sent as form data)
    """
    user_id = current_user["id"]
    return await media_service.upload_video(user_id, file, subfolder)


@router.post("/upload/audio", response_model=FileUploadResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),
    media_service: MediaUploadService = Depends(get_media_upload_service),
) -> FileUploadResponse:
    """
    Upload an audio file.

    Requires authentication.

    - **file**: Audio file to upload
    - **subfolder**: Optional subfolder for organization (sent as form data)
    """
    user_id = current_user["id"]
    return await media_service.upload_audio(user_id, file, subfolder)


@router.post("/upload/csv", response_model=TextCombinationsResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    save_file: bool = Query(default=True),
    current_user: dict = Depends(get_current_user),
    csv_service: CSVService = Depends(get_csv_service),
) -> TextCombinationsResponse:
    """
    Upload and parse a CSV file.

    Requires authentication.

    - **file**: CSV file to upload and parse
    - **save_file**: Whether to save the file to storage
    """
    user_id = current_user["id"]
    return await csv_service.upload_csv(user_id, file, save_file)


@router.get("/videos", response_model=FileListResponse)
async def list_videos(
    subfolder: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all video files with detailed information.

    Requires authentication.

    - **subfolder**: Optional subfolder filter
    """
    user_id = current_user["id"]
    return await file_service.list_videos(user_id, subfolder)


@router.get("/audios", response_model=FileListResponse)
async def list_audios(
    subfolder: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all audio files with detailed information.

    Requires authentication.

    - **subfolder**: Optional subfolder filter
    """
    user_id = current_user["id"]
    return await file_service.list_audios(user_id, subfolder)


@router.get("/csv", response_model=FileListResponse)
async def list_csvs(
    current_user: dict = Depends(get_current_user),
    csv_service: CSVService = Depends(get_csv_service),
) -> FileListResponse:
    """
    List all saved CSV files with detailed information.

    Requires authentication.
    """
    user_id = current_user["id"]
    return await csv_service.list_csvs(user_id)


@router.get("/outputs", response_model=FileListResponse)
def list_outputs(
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all processed/output video files.

    Requires authentication.
    """
    user_id = current_user["id"]
    return file_service.list_output_files(user_id)


@router.delete("/delete", response_model=FileDeleteResponse)
async def delete_file(
    request: FileDeleteRequest,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileDeleteResponse:
    """
    Delete a file.

    Requires authentication.

    - **filepath**: Absolute path to file to delete
    """
    user_id = current_user["id"]
    return await file_service.delete_file_by_path(user_id, request.filepath)


@router.post("/bulk-delete", response_model=FileBulkDeleteResponse)
async def bulk_delete_files(
    request: FileBulkDeleteRequest,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileBulkDeleteResponse:
    """
    Delete multiple files in a single request.

    Best practice for deleting many files:
    - Reduces number of HTTP requests
    - Updates folder metadata once per folder (not per file)
    - Returns detailed success/failure information

    Requires authentication.

    - **filepaths**: List of file paths to delete
    """
    user_id = current_user["id"]
    return await file_service.bulk_delete_files(user_id, request.filepaths)


@router.patch("/rename", response_model=FileRenameResponse)
async def rename_file(
    request: FileRenameRequest,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileRenameResponse:
    """
    Rename file (display name only - doesn't move physical file).

    Updates the original_filename in metadata for display purposes.

    Requires authentication.

    - **filepath**: File path
    - **new_name**: New display name (without extension)
    """
    user_id = current_user["id"]
    return await file_service.rename_file(user_id, request.filepath, request.new_name)


@router.post("/move", response_model=FileMoveResponse)
def move_file(
    request: FileMoveRequest,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileMoveResponse:
    """
    Move a file to another folder.

    Requires authentication.

    - **source_path**: Source file path
    - **destination_folder**: Destination folder path
    """
    return file_service.move_file(request.source_path, request.destination_folder)


@router.post("/bulk-move", response_model=FileBulkMoveResponse)
async def bulk_move_files(
    request: FileBulkMoveRequest,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileBulkMoveResponse:
    """
    Move multiple files to a destination folder in a single operation.

    Best practice for moving many files:
    - Reduces number of HTTP requests
    - Updates folder metadata once per folder (not per file)
    - Returns detailed success/failure information

    Requires authentication.

    - **filepaths**: List of file paths to move
    - **destination_folder**: Destination folder name
    """
    user_id = current_user["id"]
    return await file_service.bulk_move_files(user_id, request.filepaths, request.destination_folder)


@router.get("/stream-url/video")
async def get_video_stream_url(
    filepath: str = Query(...),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
):
    """
    Get CloudFront URL for streaming a video file from S3.

    Requires authentication. Returns JSON with CloudFront URL.

    - **filepath**: Storage path to the video file
    """
    user_id = current_user["id"]

    # Verify file belongs to user
    result = file_service.supabase.table("files") \
        .select("*") \
        .eq("filepath", filepath) \
        .eq("user_id", user_id) \
        .eq("file_type", "video") \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Video file not found")

    # Generate CloudFront URL (valid for 1 hour)
    try:
        url = file_service.storage.get_public_url(
            category="videos",
            storage_path=filepath,
            expires_in=3600,  # 1 hour
            use_cloudfront=True
        )

        return {"url": url}

    except Exception as e:
        logger.error(f"Error getting video stream URL: {str(e)}", exc_info=True, extra={"filepath": filepath, "user_id": user_id})
        raise StorageError("Failed to get video stream URL")


@router.get("/stream-url/audio")
async def get_audio_stream_url(
    filepath: str = Query(...),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
):
    """
    Get CloudFront URL for streaming an audio file from S3.

    Requires authentication. Returns JSON with CloudFront URL.

    - **filepath**: Storage path to the audio file
    """
    user_id = current_user["id"]

    # Verify file belongs to user
    result = file_service.supabase.table("files") \
        .select("*") \
        .eq("filepath", filepath) \
        .eq("user_id", user_id) \
        .eq("file_type", "audio") \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Generate CloudFront URL (valid for 1 hour)
    try:
        url = file_service.storage.get_public_url(
            category="audios",
            storage_path=filepath,
            expires_in=3600,  # 1 hour
            use_cloudfront=True
        )

        return {"url": url}

    except Exception as e:
        logger.error(f"Error getting audio stream URL: {str(e)}", exc_info=True, extra={"filepath": filepath, "user_id": user_id})
        raise StorageError("Failed to get audio stream URL")


@router.get("/preview/csv", response_model=TextCombinationsResponse)
async def preview_csv(
    filepath: str = Query(...),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> TextCombinationsResponse:
    """
    Preview a CSV file from Supabase Storage.

    Requires authentication.

    - **filepath**: Storage path to the CSV file (e.g., user_id/filename.csv)
    """
    import csv
    import io

    user_id = current_user["id"]

    # Get file from database
    supabase = file_service.supabase
    result = supabase.table("files") \
        .select("*") \
        .eq("filepath", filepath) \
        .eq("user_id", user_id) \
        .eq("file_type", "csv") \
        .execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="CSV file not found")

    file_data = result.data[0]

    # Download file from Supabase Storage
    try:
        storage_service = file_service.storage
        file_content = await storage_service.download_file(
            category="csv",
            storage_path=filepath
        )

        # Parse CSV
        text_content = file_content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text_content))

        combinations = []
        for row in reader:
            if row:  # Skip empty rows
                segs = [c.strip() for c in row if c and c.strip()]
                if segs:
                    combinations.append(segs)

        # Get display name from metadata
        display_name = file_data["filename"]
        if file_data.get("metadata"):
            import json
            try:
                metadata = json.loads(file_data["metadata"]) if isinstance(file_data["metadata"], str) else file_data["metadata"]
                display_name = metadata.get("original_filename", file_data["filename"])
            except:
                pass

        return TextCombinationsResponse(
            filename=display_name,
            combinations=combinations,
            count=len(combinations),
            saved=True,
            filepath=filepath
        )
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}", exc_info=True, extra={"filepath": filepath, "user_id": user_id})
        raise StorageError("Failed to read CSV file")
