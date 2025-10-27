"""
File management routes
"""
from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
import os

from core.dependencies import get_file_service, get_current_user
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
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload a video file.

    Requires authentication.

    - **file**: Video file to upload
    - **subfolder**: Optional subfolder for organization (sent as form data)
    """
    user_id = current_user["id"]
    return await file_service.upload_video(user_id, file, subfolder)


@router.post("/upload/audio", response_model=FileUploadResponse, status_code=201)
async def upload_audio(
    file: UploadFile = File(...),
    subfolder: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    Upload an audio file.

    Requires authentication.

    - **file**: Audio file to upload
    - **subfolder**: Optional subfolder for organization (sent as form data)
    """
    user_id = current_user["id"]
    return await file_service.upload_audio(user_id, file, subfolder)


@router.post("/upload/csv", response_model=TextCombinationsResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    save_file: bool = Query(default=True),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> TextCombinationsResponse:
    """
    Upload and parse a CSV file.

    Requires authentication.

    - **file**: CSV file to upload and parse
    - **save_file**: Whether to save the file to storage
    """
    user_id = current_user["id"]
    return await file_service.upload_csv(user_id, file, save_file)


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
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all saved CSV files with detailed information.
    
    Requires authentication.
    """
    user_id = current_user["id"]
    return await file_service.list_csvs(user_id)


@router.get("/outputs", response_model=FileListResponse)
def list_outputs(
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    List all processed/output video files.
    
    Requires authentication.
    """
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


@router.get("/stream/video")
async def stream_video(
    filepath: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Stream a video file with range support for seeking.

    Requires authentication.

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
async def stream_audio(
    filepath: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Stream an audio file.

    Requires authentication.

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
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
