"""
Project management routes
"""
from typing import List
from fastapi import APIRouter, Depends, Path, Query

from core.dependencies import get_project_service, get_current_user, get_storage_service
from core.exceptions import StorageError
from models.project import Project
from services.project_service import ProjectService
from services.storage_service import StorageService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[Project])
def list_projects(
    limit: int = Query(default=50, ge=1, le=100),
    include_deleted: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> List[Project]:
    """
    List all projects for the authenticated user.

    - **limit**: Maximum number of projects to return (default: 50)
    - **include_deleted**: Include soft-deleted projects
    """
    user_id = current_user["id"]
    return project_service.list_projects(
        user_id=user_id,
        limit=limit,
        include_deleted=include_deleted
    )


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Project:
    """
    Get details for a specific project.

    - **project_id**: UUID of the project
    """
    user_id = current_user["id"]
    return project_service.get_project(project_id, user_id)


@router.delete("/{project_id}")
def delete_project(
    project_id: str = Path(..., description="Project ID"),
    hard_delete: bool = Query(default=False, description="Permanently delete (vs soft delete)"),
    current_user: dict = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    """
    Delete a project (soft delete by default).

    - **project_id**: UUID of the project
    - **hard_delete**: If true, permanently removes from database
    """
    user_id = current_user["id"]
    success = project_service.delete_project(
        project_id=project_id,
        user_id=user_id,
        soft_delete=not hard_delete
    )

    if success:
        return {
            "success": True,
            "message": f"Project {'deleted' if hard_delete else 'archived'} successfully",
            "project_id": project_id
        }
    else:
        raise StorageError("Failed to delete project")


@router.get("/{project_id}/urls")
def get_project_urls(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get CloudFront signed URLs for project assets (preview, thumbnail, ZIP).

    Returns fresh signed URLs with 1-hour expiration for secure access.

    - **project_id**: UUID of the project
    """
    user_id = current_user["id"]
    project = project_service.get_project(project_id, user_id)

    # Generate fresh signed URLs from S3 paths
    urls = {
        "preview_video_url": None,
        "preview_thumbnail_url": None,
        "zip_url": None,
    }

    if project.preview_video_url:
        urls["preview_video_url"] = storage_service.get_public_url(
            category="output",
            storage_path=project.preview_video_url,
            expires_in=3600,
            use_cloudfront=True
        )

    if project.preview_thumbnail_url:
        urls["preview_thumbnail_url"] = storage_service.get_public_url(
            category="output",
            storage_path=project.preview_thumbnail_url,
            expires_in=3600,
            use_cloudfront=True
        )

    if project.zip_url:
        urls["zip_url"] = storage_service.get_public_url(
            category="output",
            storage_path=project.zip_url,
            expires_in=3600,
            use_cloudfront=True
        )

    return urls
