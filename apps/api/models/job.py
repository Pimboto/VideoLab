"""
Job models

These models represent processing jobs in the database.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class JobBase(BaseModel):
    """Base job model"""
    
    job_type: str  # 'single', 'batch', 'ai-generation'
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: float = 0.0
    message: Optional[str] = None
    config: Optional[dict] = None
    input_files: Optional[List[str]] = None  # Array of file IDs or paths
    output_files: Optional[List[str]] = None  # Array of output paths
    error: Optional[str] = None


class JobCreate(JobBase):
    """Model for creating a new job"""
    
    user_id: str = Field(..., description="User ID from database")
    project_id: Optional[str] = None


class JobUpdate(BaseModel):
    """Model for updating job status"""
    
    status: Optional[str] = None
    progress: Optional[float] = None
    message: Optional[str] = None
    output_files: Optional[List[str]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Job(JobBase):
    """Complete job model as stored in database"""
    
    id: str = Field(..., description="UUID from database")
    user_id: str
    project_id: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

