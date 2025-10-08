"""
Job service for managing processing jobs
"""
import uuid
from typing import Dict, List

from core.exceptions import JobNotFoundError
from schemas.job_schemas import JobDeleteResponse, JobStatus


class JobService:
    """Service for managing job state"""

    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}

    def create_job(self, initial_status: str = "pending", message: str = "") -> str:
        """Create a new job and return its ID"""
        job_id = str(uuid.uuid4())

        job = JobStatus(
            job_id=job_id,
            status=initial_status,
            progress=0.0,
            message=message,
            output_files=[],
        )

        self._jobs[job_id] = job
        return job_id

    def get_job(self, job_id: str) -> JobStatus:
        """Get job by ID"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job not found: {job_id}")
        return self._jobs[job_id]

    def update_job(
        self,
        job_id: str,
        status: str | None = None,
        progress: float | None = None,
        message: str | None = None,
        output_files: List[str] | None = None,
    ) -> None:
        """Update job status"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job not found: {job_id}")

        job = self._jobs[job_id]

        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message is not None:
            job.message = message
        if output_files is not None:
            job.output_files = output_files

    def list_jobs(self) -> List[JobStatus]:
        """List all jobs"""
        return list(self._jobs.values())

    def delete_job(self, job_id: str) -> JobDeleteResponse:
        """Delete a job from tracking"""
        if job_id not in self._jobs:
            raise JobNotFoundError(f"Job not found: {job_id}")

        del self._jobs[job_id]

        return JobDeleteResponse(message="Job deleted", job_id=job_id)

    def job_exists(self, job_id: str) -> bool:
        """Check if job exists"""
        return job_id in self._jobs
