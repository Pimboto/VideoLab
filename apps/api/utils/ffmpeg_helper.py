"""
FFmpeg helper utilities for video processing
"""
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

from core.exceptions import ProcessingError

logger = logging.getLogger(__name__)

# Video and audio file extensions
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}


def check_ffmpeg_installed() -> str:
    """
    Check if FFmpeg is installed and available.

    Returns:
        Path to ffprobe executable

    Raises:
        ProcessingError: If FFmpeg is not installed
    """
    ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    if not ffprobe:
        raise ProcessingError(
            "FFmpeg not found. Please install FFmpeg and ensure it's on your PATH."
        )
    return ffprobe


def run_ffmpeg_command(cmd: list[str], timeout: int = 30) -> str:
    """
    Run FFmpeg command and return output.

    Args:
        cmd: Command and arguments as list
        timeout: Command timeout in seconds

    Returns:
        Command stdout output

    Raises:
        ProcessingError: If command fails
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            logger.error(
                f"FFmpeg command failed: {' '.join(cmd)}",
                extra={"stderr": result.stderr[:400]}
            )
            raise ProcessingError(f"FFmpeg command failed: {result.stderr[:200]}")

        return result.stdout

    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg command timeout: {' '.join(cmd)}")
        raise ProcessingError(f"FFmpeg command timed out after {timeout}s")
    except Exception as e:
        logger.error(f"FFmpeg command error: {str(e)}", exc_info=True)
        raise ProcessingError(f"FFmpeg command error: {str(e)}")


def probe_video(video_path: Path) -> Tuple[int, int, float, float]:
    """
    Probe video file to get metadata.

    Args:
        video_path: Path to video file

    Returns:
        Tuple of (width, height, duration, fps)

    Raises:
        ProcessingError: If probing fails
    """
    ffprobe = check_ffmpeg_installed()

    try:
        # Get video stream metadata
        meta = run_ffmpeg_command([
            ffprobe, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate",
            "-of", "json",
            str(video_path)
        ])

        data = json.loads(meta)
        if not data.get("streams"):
            raise ProcessingError(f"Cannot read video metadata: {video_path}")

        stream = data["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])

        # Parse frame rate
        fps_str = stream.get("r_frame_rate", "30/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / max(float(den), 1.0)
        else:
            fps = float(fps_str)
        fps = min(fps, 60.0)  # Cap at 60fps

        # Get duration
        dur_str = run_ffmpeg_command([
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nokey=1:noprint_wrappers=1",
            str(video_path)
        ]).strip()

        duration = float(dur_str) if dur_str and dur_str != "N/A" else 0.0

        logger.info(
            f"Video probed: {width}x{height}, {fps}fps, {duration:.2f}s",
            extra={"path": str(video_path)}
        )

        return width, height, duration, fps

    except Exception as e:
        logger.error(f"Error probing video: {str(e)}", exc_info=True)
        raise ProcessingError(f"Failed to probe video: {str(e)}")


def probe_audio_duration(audio_path: Path | None) -> float:
    """
    Probe audio file to get duration.

    Args:
        audio_path: Path to audio file (can be None)

    Returns:
        Duration in seconds (0.0 if no audio or error)
    """
    if not audio_path or not audio_path.exists():
        return 0.0

    ffprobe = check_ffmpeg_installed()

    try:
        dur_str = run_ffmpeg_command([
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nokey=1:noprint_wrappers=1",
            str(audio_path)
        ]).strip()

        duration = float(dur_str) if dur_str and dur_str != "N/A" else 0.0

        logger.info(f"Audio duration: {duration:.2f}s", extra={"path": str(audio_path)})
        return duration

    except Exception as e:
        logger.warning(f"Error probing audio duration: {str(e)}")
        return 0.0


def list_media_files(folder: Path, extensions: set[str]) -> list[Path]:
    """
    List media files in folder with given extensions.

    Args:
        folder: Folder path
        extensions: Set of file extensions (e.g., {".mp4", ".mov"})

    Returns:
        Sorted list of file paths
    """
    if not folder.exists():
        logger.warning(f"Folder does not exist: {folder}")
        return []

    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    ]

    return sorted(files)
