"""
Configuration for storage paths and file management
"""
from pathlib import Path
import os
from typing import Dict

# Base storage directory (configurable via env)
BASE_STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "D:/Work/video"))

# Storage subdirectories
STORAGE_PATHS = {
    "videos": BASE_STORAGE_DIR / "videos",
    "audios": BASE_STORAGE_DIR / "audios",
    "csv": BASE_STORAGE_DIR / "csv",
    "output": BASE_STORAGE_DIR / "output",
    "temp": BASE_STORAGE_DIR / "temp",
}

# File size limits (in bytes)
MAX_FILE_SIZE = {
    "video": 500 * 1024 * 1024,  # 500 MB
    "audio": 50 * 1024 * 1024,   # 50 MB
    "csv": 5 * 1024 * 1024,      # 5 MB
}

# Allowed extensions
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}
ALLOWED_CSV_EXTENSIONS = {".csv"}

def ensure_storage_dirs():
    """Create storage directories if they don't exist"""
    for path in STORAGE_PATHS.values():
        path.mkdir(parents=True, exist_ok=True)

def get_storage_path(category: str) -> Path:
    """Get storage path for a category"""
    if category not in STORAGE_PATHS:
        raise ValueError(f"Invalid storage category: {category}")
    path = STORAGE_PATHS[category]
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_file_size(file_size: int, file_type: str) -> bool:
    """Validate file size against limits"""
    if file_type not in MAX_FILE_SIZE:
        return False
    return file_size <= MAX_FILE_SIZE[file_type]

def validate_file_extension(filename: str, file_type: str) -> bool:
    """Validate file extension"""
    ext = Path(filename).suffix.lower()
    if file_type == "video":
        return ext in ALLOWED_VIDEO_EXTENSIONS
    elif file_type == "audio":
        return ext in ALLOWED_AUDIO_EXTENSIONS
    elif file_type == "csv":
        return ext in ALLOWED_CSV_EXTENSIONS
    return False

# Initialize storage directories on import
ensure_storage_dirs()
