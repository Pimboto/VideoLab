"""
User models

These models represent the user data structure in the database.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user model with common fields"""

    email: str  # Email is required (always provided by Clerk webhook)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if not v or '@' not in v:
            raise ValueError('Valid email is required')
        return v.strip()


class UserCreate(UserBase):
    """Model for creating a new user"""

    clerk_id: str = Field(..., description="Clerk user ID")


class UserUpdate(BaseModel):
    """Model for updating user information"""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class User(UserBase):
    """Complete user model as stored in database"""

    id: str = Field(..., description="UUID from database")
    clerk_id: str = Field(..., description="Clerk user ID")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
