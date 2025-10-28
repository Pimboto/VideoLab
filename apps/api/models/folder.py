"""
Folder model for database representation
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class FolderBase(BaseModel):
    """Base folder attributes"""
    user_id: str = Field(..., description="User ID who owns the folder")
    category: str = Field(..., description="Category: video or audio")
    folder_name: str = Field(..., description="Folder name (sanitized)")
    folder_path: str = Field(..., description="Full storage path: {user_id}/{folder_name}")


class FolderCreate(FolderBase):
    """Folder creation model"""
    pass


class FolderUpdate(BaseModel):
    """Folder update model (for metadata sync)"""
    file_count: Optional[int] = Field(None, ge=0, description="Number of files in folder")
    total_size: Optional[int] = Field(None, ge=0, description="Total size in bytes")


class Folder(FolderBase):
    """Complete folder model from database"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique folder ID")
    file_count: int = Field(0, ge=0, description="Number of files in folder")
    total_size: int = Field(0, ge=0, description="Total size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
