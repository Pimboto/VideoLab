"""
Job service for managing processing jobs with Supabase persistence
"""
from typing import List, Optional
from datetime import datetime

from supabase import Client

from core.exceptions import JobNotFoundError, StorageError
from models.job import JobCreate, JobUpdate
from schemas.job_schemas import JobDeleteResponse, JobStatus
from utils.supabase_client import get_supabase_client


class JobService:
    """Service for managing job state with Supabase persistence"""

    def __init__(self):
        self.supabase: Client = get_supabase_client()

    def create_job(
        self,
        user_id: str,
        job_type: str = "batch",
        initial_status: str = "pending",
        message: str = "",
        config: Optional[dict] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Create a new job and return its ID.
        
        Args:
            user_id: User ID from database
            job_type: Type of job ('single', 'batch', 'ai-generation')
            initial_status: Initial job status
            message: Initial message
            config: Job configuration dict
            project_id: Optional project ID
        
        Returns:
            Job ID (UUID)
        """
        try:
            job_data = JobCreate(
                user_id=user_id,
                job_type=job_type,
                status=initial_status,
                progress=0.0,
                message=message,
                config=config,
                project_id=project_id
            )
            
            result = self.supabase.table("jobs").insert(job_data.model_dump()).execute()
            
            if not result.data or len(result.data) == 0:
                raise StorageError("Failed to create job in database")
            
            return result.data[0]["id"]
        except Exception as e:
            raise StorageError(f"Failed to create job: {str(e)}")

    def get_job(self, job_id: str, user_id: Optional[str] = None) -> JobStatus:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            user_id: Optional user ID for ownership verification
        
        Returns:
            JobStatus object
        
        Raises:
            JobNotFoundError: If job doesn't exist or user doesn't own it
        """
        try:
            query = self.supabase.table("jobs").select("*").eq("id", job_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if not result.data or len(result.data) == 0:
                raise JobNotFoundError(f"Job not found: {job_id}")
            
            job_data = result.data[0]
            
            return JobStatus(
                job_id=job_data["id"],
                status=job_data["status"],
                progress=job_data.get("progress", 0.0),
                message=job_data.get("message", ""),
                output_files=job_data.get("output_files", []),
            )
        except JobNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get job: {str(e)}")

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        output_files: Optional[List[str]] = None,
        error: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            progress: New progress (0.0-100.0)
            message: New message
            output_files: List of output file paths
            error: Error message if failed
            user_id: Optional user ID for ownership verification
        """
        try:
            update_data = {}
            
            if status is not None:
                update_data["status"] = status
                
                # Set timestamps based on status
                if status == "processing" and "started_at" not in update_data:
                    update_data["started_at"] = datetime.utcnow().isoformat()
                elif status in ["completed", "failed"]:
                    update_data["completed_at"] = datetime.utcnow().isoformat()
            
            if progress is not None:
                update_data["progress"] = progress
            
            if message is not None:
                update_data["message"] = message
            
            if output_files is not None:
                update_data["output_files"] = output_files
            
            if error is not None:
                update_data["error"] = error
            
            if not update_data:
                return  # Nothing to update
            
            query = self.supabase.table("jobs").update(update_data).eq("id", job_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if not result.data or len(result.data) == 0:
                raise JobNotFoundError(f"Job not found: {job_id}")
            
        except JobNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to update job: {str(e)}")

    def list_jobs(self, user_id: str, limit: int = 50) -> List[JobStatus]:
        """
        List all jobs for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of jobs to return
        
        Returns:
            List of JobStatus objects
        """
        try:
            result = self.supabase.table("jobs") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            jobs = []
            for job_data in result.data:
                jobs.append(JobStatus(
                    job_id=job_data["id"],
                    status=job_data["status"],
                    progress=job_data.get("progress", 0.0),
                    message=job_data.get("message", ""),
                    output_files=job_data.get("output_files", []),
                ))
            
            return jobs
        except Exception as e:
            raise StorageError(f"Failed to list jobs: {str(e)}")

    def delete_job(self, job_id: str, user_id: str) -> JobDeleteResponse:
        """
        Delete a job from tracking.
        
        Args:
            job_id: Job ID
            user_id: User ID for ownership verification
        
        Returns:
            JobDeleteResponse
        
        Raises:
            JobNotFoundError: If job doesn't exist or user doesn't own it
        """
        try:
            result = self.supabase.table("jobs") \
                .delete() \
                .eq("id", job_id) \
                .eq("user_id", user_id) \
                .execute()
            
            if not result.data or len(result.data) == 0:
                raise JobNotFoundError(f"Job not found: {job_id}")
            
            return JobDeleteResponse(message="Job deleted", job_id=job_id)
        except JobNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete job: {str(e)}")

    def job_exists(self, job_id: str, user_id: Optional[str] = None) -> bool:
        """
        Check if job exists.
        
        Args:
            job_id: Job ID
            user_id: Optional user ID for ownership verification
        
        Returns:
            True if job exists, False otherwise
        """
        try:
            query = self.supabase.table("jobs").select("id").eq("id", job_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            return result.data and len(result.data) > 0
        except Exception:
            return False
