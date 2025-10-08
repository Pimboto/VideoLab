"""
Folder management routes
"""
from fastapi import APIRouter, Depends, Path

from core.dependencies import get_file_service
from schemas.file_schemas import (
    FolderCreateRequest,
    FolderCreateResponse,
    FolderListResponse,
)
from services.file_service import FileService

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("/{category}", response_model=FolderListResponse)
def list_folders(
    category: str = Path(..., description="Category: videos, audios, csv, output"),
    file_service: FileService = Depends(get_file_service),
) -> FolderListResponse:
    """
    List all subfolders in a category.

    Returns folder information including file count and total size.

    - **category**: Category name (videos, audios, csv, output)
    """
    return file_service.list_folders(category)


@router.post("/create", response_model=FolderCreateResponse, status_code=201)
def create_folder(
    request: FolderCreateRequest,
    file_service: FileService = Depends(get_file_service),
) -> FolderCreateResponse:
    """
    Create a new subfolder in a category.

    - **parent_category**: Parent category (videos, audios, csv, output)
    - **folder_name**: Name of the folder to create
    """
    return file_service.create_folder(request.parent_category, request.folder_name)
