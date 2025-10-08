"""
Video processing-related Pydantic schemas
"""
from typing import List, Tuple

from pydantic import BaseModel, Field, field_validator


class ProcessingConfig(BaseModel):
    """Configuration for video processing"""

    position: str = Field(
        default="center", description="Text position: center, top, bottom"
    )
    margin_pct: float = Field(default=0.16, ge=0.0, le=0.5, description="Margin percentage")
    duration_policy: str = Field(
        default="shortest", description="Duration policy: shortest, audio, video, fixed"
    )
    fixed_seconds: float | None = Field(
        default=None, ge=0, description="Fixed duration in seconds (if policy=fixed)"
    )
    canvas_size: Tuple[int, int] = Field(
        default=(1080, 1920), description="Canvas size (width, height)"
    )
    fit_mode: str = Field(default="cover", description="Fit mode: cover, contain, zoom")
    music_gain_db: int = Field(default=-8, description="Music gain in dB")
    mix_audio: bool = Field(default=False, description="Mix original audio with music")
    preset: str | None = Field(
        default=None, description="Text preset: clean, bold, subtle, yellow, shadow"
    )
    outline_px: int = Field(default=2, ge=0, description="Text outline width in pixels")
    fontsize_ratio: float = Field(
        default=0.036, ge=0.01, le=0.1, description="Font size ratio"
    )

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str) -> str:
        """Validate position value"""
        allowed = {"center", "top", "bottom"}
        if v not in allowed:
            raise ValueError(f"Position must be one of: {', '.join(allowed)}")
        return v

    @field_validator("duration_policy")
    @classmethod
    def validate_duration_policy(cls, v: str) -> str:
        """Validate duration policy"""
        allowed = {"shortest", "audio", "video", "fixed"}
        if v not in allowed:
            raise ValueError(f"Duration policy must be one of: {', '.join(allowed)}")
        return v

    @field_validator("fit_mode")
    @classmethod
    def validate_fit_mode(cls, v: str) -> str:
        """Validate fit mode"""
        allowed = {"cover", "contain", "zoom"}
        if v not in allowed:
            raise ValueError(f"Fit mode must be one of: {', '.join(allowed)}")
        return v


class VideoListRequest(BaseModel):
    """Request to list videos in a folder"""

    folder_path: str = Field(..., description="Absolute path to video folder")


class AudioListRequest(BaseModel):
    """Request to list audios in a folder"""

    folder_path: str = Field(..., description="Absolute path to audio folder")


class VideoListResponse(BaseModel):
    """Response with list of video paths"""

    videos: List[str] = Field(default_factory=list, description="List of video file paths")
    count: int = Field(..., description="Total count of videos", ge=0)


class AudioListResponse(BaseModel):
    """Response with list of audio paths"""

    audios: List[str] = Field(default_factory=list, description="List of audio file paths")
    count: int = Field(..., description="Total count of audios", ge=0)


class TextCombinationsResponse(BaseModel):
    """Response with parsed text combinations"""

    combinations: List[List[str]] = Field(
        default_factory=list, description="List of text segment combinations"
    )
    count: int = Field(..., description="Total count of combinations", ge=0)
    saved: bool = Field(default=False, description="Whether file was saved")
    filepath: str | None = Field(default=None, description="Path to saved CSV file")
    filename: str = Field(..., description="Original or generated filename")


class SingleProcessRequest(BaseModel):
    """Request to process a single video"""

    video_path: str = Field(..., description="Path to input video")
    audio_path: str | None = Field(default=None, description="Path to audio file")
    text_segments: List[str] = Field(
        default_factory=list, description="List of text segments"
    )
    output_path: str = Field(..., description="Path for output video")
    config: ProcessingConfig | None = Field(default=None, description="Processing configuration")


class BatchProcessRequest(BaseModel):
    """Request to process batch of videos"""

    video_folder: str = Field(..., description="Folder containing videos")
    audio_folder: str | None = Field(default=None, description="Folder containing audios")
    text_combinations: List[List[str]] = Field(
        default_factory=list, description="List of text combinations"
    )
    output_folder: str = Field(..., description="Output folder for processed videos")
    unique_mode: bool = Field(
        default=False, description="Use deterministic unique selection"
    )
    unique_amount: int | None = Field(
        default=None, ge=1, description="Number of unique combinations (if unique_mode=True)"
    )
    config: ProcessingConfig | None = Field(default=None, description="Processing configuration")
