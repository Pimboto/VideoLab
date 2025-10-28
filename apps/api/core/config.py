"""
Application configuration using Pydantic Settings
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    app_name: str = Field(default="Video Processor API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    api_prefix: str = Field(default="/api/video-processor", alias="API_PREFIX")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # CORS Configuration
    allowed_origins: str | List[str] = Field(
        default="http://localhost:3000,http://localhost:3001",
        alias="ALLOWED_ORIGINS",
    )

    # Clerk Authentication
    clerk_publishable_key: str = Field(..., alias="CLERK_PUBLISHABLE_KEY")
    clerk_secret_key: str = Field(..., alias="CLERK_SECRET_KEY")
    clerk_jwks_url: str = Field(
        default="https://api.clerk.com/v1/jwks",
        alias="CLERK_JWKS_URL"
    )
    clerk_webhook_secret: str = Field(
        default="",  # Optional: only required if using webhooks
        alias="CLERK_WEBHOOK_SECRET"
    )

    # Supabase Configuration
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")

    # Storage Configuration
    # IMPORTANT: Set STORAGE_DIR environment variable to configure storage location
    # Example: STORAGE_DIR=/app/storage or STORAGE_DIR=D:/Work/video
    storage_base_dir: Path = Field(..., alias="STORAGE_DIR")

    # File Size Limits (in bytes)
    max_video_size: int = Field(default=500 * 1024 * 1024, alias="MAX_VIDEO_SIZE")  # 500 MB
    max_audio_size: int = Field(default=50 * 1024 * 1024, alias="MAX_AUDIO_SIZE")  # 50 MB
    max_csv_size: int = Field(default=5 * 1024 * 1024, alias="MAX_CSV_SIZE")  # 5 MB

    # Allowed Extensions
    video_extensions: set[str] = Field(
        default={".mp4", ".mov", ".m4v", ".avi", ".mkv"},
        alias="VIDEO_EXTENSIONS",
    )
    audio_extensions: set[str] = Field(
        default={".mp3", ".wav", ".m4a"},
        alias="AUDIO_EXTENSIONS",
    )
    csv_extensions: set[str] = Field(default={".csv"}, alias="CSV_EXTENSIONS")

    # Processing Configuration
    chunk_size: int = Field(default=8192, alias="CHUNK_SIZE")  # For file uploads
    job_poll_interval: int = Field(default=2000, alias="JOB_POLL_INTERVAL")  # milliseconds

    @field_validator("storage_base_dir", mode="before")
    @classmethod
    def ensure_path(cls, v) -> Path:
        """Convert string to Path"""
        return Path(v) if not isinstance(v, Path) else v

    @field_validator("allowed_origins")
    @classmethod
    def split_origins(cls, v) -> List[str]:
        """Split comma-separated origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def video_storage_path(self) -> Path:
        """Get video storage directory"""
        return self.storage_base_dir / "videos"

    @property
    def audio_storage_path(self) -> Path:
        """Get audio storage directory"""
        return self.storage_base_dir / "audios"

    @property
    def csv_storage_path(self) -> Path:
        """Get CSV storage directory"""
        return self.storage_base_dir / "csv"

    @property
    def output_storage_path(self) -> Path:
        """Get output storage directory"""
        return self.storage_base_dir / "output"

    @property
    def temp_storage_path(self) -> Path:
        """Get temp storage directory"""
        return self.storage_base_dir / "temp"

    def get_storage_path(self, category: str) -> Path:
        """Get storage path for a category"""
        paths = {
            "videos": self.video_storage_path,
            "audios": self.audio_storage_path,
            "csv": self.csv_storage_path,
            "output": self.output_storage_path,
            "temp": self.temp_storage_path,
        }
        if category not in paths:
            raise ValueError(f"Invalid storage category: {category}")
        return paths[category]

    def ensure_storage_directories(self) -> None:
        """Create all storage directories if they don't exist"""
        for category in ["videos", "audios", "csv", "output", "temp"]:
            path = self.get_storage_path(category)
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
