"""
File models

These models represent file metadata in the database.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FileBase(BaseModel):
    """Base file model"""
    
    filename: str
    filepath: str  # Path in Supabase Storage
    file_type: str  # 'video', 'audio', 'csv'
    size_bytes: int
    mime_type: Optional[str] = None
    subfolder: Optional[str] = None
    metadata: Optional[dict] = None


class FileCreate(FileBase):
    """Model for creating a new file record"""
    
    user_id: str = Field(..., description="User ID from database")


class FileUpdate(BaseModel):
    """Model for updating file metadata"""
    
    filename: Optional[str] = None
    subfolder: Optional[str] = None
    metadata: Optional[dict] = None


class File(FileBase):
    """Complete file model as stored in database"""
    
    id: str = Field(..., description="UUID from database")
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

