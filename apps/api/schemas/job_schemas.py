"""
Job-related Pydantic schemas
"""
from typing import List

from pydantic import BaseModel, Field, field_validator


class JobStatus(BaseModel):
    """Job status information"""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    message: str = Field(default="", description="Status message")
    output_files: List[str] = Field(
        default_factory=list, description="List of output file paths"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value"""
        allowed = {"pending", "processing", "completed", "failed"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


class JobCreateResponse(BaseModel):
    """Response after creating a job"""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Creation message")


class BatchJobResponse(BaseModel):
    """Response after creating a batch job"""

    job_id: str = Field(..., description="Unique job identifier")
    total_jobs: int = Field(..., description="Total number of videos to process", ge=0)
    message: str = Field(..., description="Creation message")


class JobListResponse(BaseModel):
    """Response with list of jobs"""

    jobs: List[JobStatus] = Field(default_factory=list, description="List of jobs")
    count: int = Field(..., description="Total count of jobs", ge=0)


class JobDeleteResponse(BaseModel):
    """Response after deleting a job"""

    message: str = Field(..., description="Deletion message")
    job_id: str = Field(..., description="ID of deleted job")
