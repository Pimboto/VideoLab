"""
Project models

These models represent output projects in the database.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project model"""

    name: str
    description: Optional[str] = None
    output_folder: Optional[str] = None  # Supabase Storage folder path
    video_count: int = 0
    total_size_bytes: int = 0
    preview_video_url: Optional[str] = None  # URL to preview video
    preview_thumbnail_url: Optional[str] = None  # URL to preview thumbnail
    zip_url: Optional[str] = None  # URL to ZIP file with all videos


class ProjectCreate(ProjectBase):
    """Model for creating a new project"""
    
    user_id: str = Field(..., description="User ID from database")


class ProjectUpdate(BaseModel):
    """Model for updating project information"""

    name: Optional[str] = None
    description: Optional[str] = None
    video_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    preview_video_url: Optional[str] = None
    preview_thumbnail_url: Optional[str] = None
    zip_url: Optional[str] = None
    deleted_at: Optional[datetime] = None


class Project(ProjectBase):
    """Complete project model as stored in database"""
    
    id: str = Field(..., description="UUID from database")
    user_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None  # Auto-cleanup after 24h
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

