"""
Folder management routes
"""
from fastapi import APIRouter, Body, Depends, Path

from core.dependencies import get_file_service, get_current_user
from schemas.file_schemas import (
    FolderCreateRequest,
    FolderCreateResponse,
    FolderDeleteRequest,
    FolderDeleteResponse,
    FolderListResponse,
)
from services.file_service import FileService

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("/{category}", response_model=FolderListResponse)
async def list_folders(
    category: str = Path(..., description="Category: videos, audios, csv, output"),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FolderListResponse:
    """
    List all subfolders in a category.

    Requires authentication.

    Returns folder information including file count and total size.

    - **category**: Category name (videos, audios, csv, output)
    """
    user_id = current_user["id"]
    return await file_service.list_folders(user_id, category)


@router.post("/create", response_model=FolderCreateResponse, status_code=201)
async def create_folder(
    request: FolderCreateRequest,
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FolderCreateResponse:
    """
    Create a new subfolder in a category.

    Requires authentication.

    - **parent_category**: Parent category (videos, audios, csv, output)
    - **folder_name**: Name of the folder to create
    """
    user_id = current_user["id"]
    return await file_service.create_folder(user_id, request.parent_category, request.folder_name)


@router.delete("/delete", response_model=FolderDeleteResponse)
async def delete_folder(
    request: FolderDeleteRequest = Body(...),
    current_user: dict = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
) -> FolderDeleteResponse:
    """
    Delete a folder and all its files.

    Requires authentication.

    WARNING: This will delete ALL files in the folder from storage and database.

    - **parent_category**: Parent category (videos, audios)
    - **folder_name**: Name of the folder to delete
    """
    user_id = current_user["id"]
    return await file_service.delete_folder(user_id, request.parent_category, request.folder_name)
