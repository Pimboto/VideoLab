"""
Project service for managing projects with Supabase persistence
"""
from typing import List, Optional
from datetime import datetime, timedelta

from supabase import Client

from core.exceptions import StorageError
from models.project import Project, ProjectCreate, ProjectUpdate
from utils.supabase_client import get_supabase_client


class ProjectService:
    """Service for managing projects with Supabase persistence"""

    def __init__(self):
        self.supabase: Client = get_supabase_client()

    def create_project(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> Project:
        """
        Create a new project.

        Args:
            user_id: User ID from database
            name: Project name
            description: Optional project description
            expires_in_hours: Hours until project expires (default: 24)

        Returns:
            Created Project object

        Raises:
            StorageError: If creation fails
        """
        try:
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

            project_data = ProjectCreate(
                user_id=user_id,
                name=name,
                description=description
            )

            # Add expires_at to the data
            data_dict = project_data.model_dump()
            data_dict["expires_at"] = expires_at.isoformat()

            result = self.supabase.table("projects").insert(data_dict).execute()

            if not result.data or len(result.data) == 0:
                raise StorageError("Failed to create project in database")

            return Project(**result.data[0])
        except Exception as e:
            raise StorageError(f"Failed to create project: {str(e)}")

    def get_project(self, project_id: str, user_id: Optional[str] = None) -> Project:
        """
        Get project by ID.

        Args:
            project_id: Project ID
            user_id: Optional user ID for ownership verification

        Returns:
            Project object

        Raises:
            StorageError: If project doesn't exist or query fails
        """
        try:
            query = self.supabase.table("projects").select("*").eq("id", project_id)

            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data or len(result.data) == 0:
                raise StorageError(f"Project not found: {project_id}")

            return Project(**result.data[0])
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get project: {str(e)}")

    def update_project(
        self,
        project_id: str,
        update_data: ProjectUpdate,
        user_id: Optional[str] = None
    ) -> Project:
        """
        Update project information.

        Args:
            project_id: Project ID
            update_data: ProjectUpdate object with fields to update
            user_id: Optional user ID for ownership verification

        Returns:
            Updated Project object

        Raises:
            StorageError: If update fails
        """
        try:
            # Only include non-None values
            data_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

            if not data_dict:
                # Nothing to update, return current project
                return self.get_project(project_id, user_id)

            query = self.supabase.table("projects").update(data_dict).eq("id", project_id)

            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data or len(result.data) == 0:
                raise StorageError(f"Project not found: {project_id}")

            return Project(**result.data[0])
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to update project: {str(e)}")

    def update_project_output(
        self,
        project_id: str,
        preview_video_url: Optional[str] = None,
        preview_thumbnail_url: Optional[str] = None,
        zip_url: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Project:
        """
        Update project output URLs (preview, thumbnail, ZIP).

        Args:
            project_id: Project ID
            preview_video_url: URL to preview video
            preview_thumbnail_url: URL to preview thumbnail
            zip_url: URL to ZIP file
            user_id: Optional user ID for ownership verification

        Returns:
            Updated Project object
        """
        update_data = ProjectUpdate(
            preview_video_url=preview_video_url,
            preview_thumbnail_url=preview_thumbnail_url,
            zip_url=zip_url
        )
        return self.update_project(project_id, update_data, user_id)

    def update_project_stats(
        self,
        project_id: str,
        video_count: int,
        total_size_bytes: int,
        user_id: Optional[str] = None
    ) -> Project:
        """
        Update project statistics (video count, total size).

        Args:
            project_id: Project ID
            video_count: Total number of videos in project
            total_size_bytes: Total size in bytes
            user_id: Optional user ID for ownership verification

        Returns:
            Updated Project object
        """
        update_data = ProjectUpdate(
            video_count=video_count,
            total_size_bytes=total_size_bytes
        )
        return self.update_project(project_id, update_data, user_id)

    def list_projects(
        self,
        user_id: str,
        limit: int = 50,
        include_deleted: bool = False
    ) -> List[Project]:
        """
        List all projects for a user.

        Args:
            user_id: User ID
            limit: Maximum number of projects to return
            include_deleted: Include soft-deleted projects

        Returns:
            List of Project objects
        """
        try:
            query = self.supabase.table("projects") \
                .select("*") \
                .eq("user_id", user_id)

            if not include_deleted:
                query = query.is_("deleted_at", "null")

            query = query.order("created_at", desc=True).limit(limit)

            result = query.execute()

            return [Project(**project_data) for project_data in result.data]
        except Exception as e:
            raise StorageError(f"Failed to list projects: {str(e)}")

    def delete_project(
        self,
        project_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a project (soft or hard delete).

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification
            soft_delete: If True, marks as deleted; if False, removes from DB

        Returns:
            True if deleted successfully

        Raises:
            StorageError: If deletion fails
        """
        try:
            if soft_delete:
                # Soft delete: set deleted_at timestamp
                update_data = {"deleted_at": datetime.utcnow().isoformat()}
                result = self.supabase.table("projects") \
                    .update(update_data) \
                    .eq("id", project_id) \
                    .eq("user_id", user_id) \
                    .execute()
            else:
                # Hard delete: remove from database
                result = self.supabase.table("projects") \
                    .delete() \
                    .eq("id", project_id) \
                    .eq("user_id", user_id) \
                    .execute()

            if not result.data or len(result.data) == 0:
                raise StorageError(f"Project not found: {project_id}")

            return True
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete project: {str(e)}")

    def project_exists(self, project_id: str, user_id: Optional[str] = None) -> bool:
        """
        Check if project exists.

        Args:
            project_id: Project ID
            user_id: Optional user ID for ownership verification

        Returns:
            True if project exists, False otherwise
        """
        try:
            query = self.supabase.table("projects").select("id").eq("id", project_id)

            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            return result.data and len(result.data) > 0
        except Exception:
            return False
