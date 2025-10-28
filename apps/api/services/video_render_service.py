"""
Video rendering service - Core FFmpeg-based video processing
"""
import logging
import shutil
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

from core.config import Settings
from core.exceptions import ProcessingError
from schemas.processing_schemas import ProcessingConfig
from utils.ffmpeg_helper import probe_video, probe_audio_duration
from utils.text_renderer import EmojiTextRenderer, overlay_text_on_frame

logger = logging.getLogger(__name__)


def _ensure_even(value: int) -> int:
    """Ensure value is even (required for some codecs)."""
    return int(value) & ~1


def _resize_cover(frame: np.ndarray, out_width: int, out_height: int) -> np.ndarray:
    """
    Resize frame to cover output size (crop excess).

    Similar to CSS background-size: cover
    """
    height, width = frame.shape[:2]

    if width == 0 or height == 0:
        return np.zeros((out_height, out_width, 3), dtype=np.uint8)

    scale = max(out_width / float(width), out_height / float(height))
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))

    resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    # Center crop
    y0 = max(0, (new_height - out_height) // 2)
    x0 = max(0, (new_width - out_width) // 2)
    y1 = y0 + out_height
    x1 = x0 + out_width

    cropped = resized[y0:y1, x0:x1]

    # Final safety resize
    if cropped.shape[0] != out_height or cropped.shape[1] != out_width:
        cropped = cv2.resize(cropped, (out_width, out_height), interpolation=cv2.INTER_LINEAR)

    return cropped


def _resize_contain(frame: np.ndarray, out_width: int, out_height: int) -> np.ndarray:
    """
    Resize frame to fit within output size (letterbox/pillarbox).

    Similar to CSS background-size: contain
    """
    height, width = frame.shape[:2]

    if width == 0 or height == 0:
        return np.zeros((out_height, out_width, 3), dtype=np.uint8)

    scale = min(out_width / float(width), out_height / float(height))
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))

    resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    # Center on black canvas
    top = (out_height - new_height) // 2
    left = (out_width - new_width) // 2

    canvas = np.zeros((out_height, out_width, 3), dtype=resized.dtype)
    canvas[top:top + new_height, left:left + new_width] = resized

    return canvas


class VideoRenderService:
    """
    Service for rendering videos with text overlays and audio.

    Handles complete video processing pipeline using FFmpeg and OpenCV.
    """

    def __init__(self, settings: Settings):
        """Initialize video render service."""
        self.settings = settings

    def process_video(
        self,
        video_path: Path,
        output_path: Path,
        text_segments: list[str],
        audio_path: Optional[Path] = None,
        config: Optional[ProcessingConfig] = None,
    ) -> bool:
        """
        Process video with text overlays and audio.

        Args:
            video_path: Input video file path
            output_path: Output video file path
            text_segments: List of text segments to overlay
            audio_path: Optional audio file to add
            config: Processing configuration

        Returns:
            True if successful, False otherwise

        Raises:
            ProcessingError: If processing fails
        """
        # Use default config if not provided
        if config is None:
            config = ProcessingConfig()

        logger.info(
            f"Processing video: {output_path.name}",
            extra={
                "video": str(video_path),
                "output": str(output_path),
                "segments": len(text_segments),
                "has_audio": audio_path is not None
            }
        )

        try:
            # Probe video metadata
            src_width, src_height, video_duration, fps = probe_video(video_path)

            # Determine output dimensions
            out_width, out_height = config.canvas_size
            out_width = _ensure_even(out_width)
            out_height = _ensure_even(out_height)

            # Open video capture
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ProcessingError(f"Could not open video: {video_path}")

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Create video writer
            temp_video = output_path.with_suffix(".temp.mp4")
            temp_video.parent.mkdir(parents=True, exist_ok=True)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(temp_video), fourcc, fps, (out_width, out_height))

            # Try alternative codecs if mp4v fails
            if not writer.isOpened():
                for codec in ["XVID", "MJPG", "MP42"]:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    writer = cv2.VideoWriter(str(temp_video), fourcc, fps, (out_width, out_height))
                    if writer.isOpened():
                        logger.info(f"Using video codec: {codec}")
                        break

            if not writer.isOpened():
                raise ProcessingError("Could not initialize video writer with any codec")

            # Initialize text renderer
            font_size = max(18, int(out_height * config.fontsize_ratio))
            renderer = EmojiTextRenderer(
                font_size=font_size,
                outline_width=config.outline_px,
                preset=config.preset
            )

            # Pre-render all text segments
            max_text_width = int(out_width * (1 - 2 * config.margin_pct))
            rendered_texts = []

            for segment in text_segments:
                try:
                    rendered = renderer.render_text(segment, max_text_width)
                    rendered_texts.append(rendered)
                except Exception as e:
                    logger.error(
                        f"Error rendering text segment: {str(e)}",
                        extra={"segment": segment[:50]},
                        exc_info=True
                    )
                    # Use empty placeholder
                    rendered_texts.append(np.zeros((100, 100, 4), dtype=np.uint8))

            # Calculate target duration
            audio_duration = probe_audio_duration(audio_path) if audio_path else 0.0

            if config.duration_policy == "fixed" and config.fixed_seconds:
                target_duration = float(config.fixed_seconds)
            elif config.duration_policy == "audio" and audio_duration > 0:
                target_duration = audio_duration
            elif config.duration_policy == "video":
                target_duration = video_duration
            else:  # shortest
                target_duration = min(video_duration, audio_duration) if audio_duration > 0 else video_duration

            # Duration per text segment
            segment_duration = target_duration / len(text_segments) if text_segments else target_duration

            logger.info(
                f"Processing parameters: {out_width}x{out_height} @ {fps}fps, "
                f"duration={target_duration:.2f}s, segment_dur={segment_duration:.2f}s"
            )

            # Process frames
            max_frames = int(round(target_duration * fps))
            frame_idx = 0

            while frame_idx < max_frames:
                ok, frame = cap.read()
                if not ok:
                    break

                # Resize frame according to fit mode
                if config.fit_mode in ("cover", "zoom"):
                    frame = _resize_cover(frame, out_width, out_height)
                elif config.fit_mode == "contain":
                    frame = _resize_contain(frame, out_width, out_height)
                else:
                    frame = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_LINEAR)

                # Overlay text
                if rendered_texts:
                    time = frame_idx / fps
                    segment_idx = min(
                        int(time / segment_duration),
                        len(rendered_texts) - 1
                    ) if segment_duration > 0 else 0

                    frame = overlay_text_on_frame(
                        frame,
                        rendered_texts[segment_idx],
                        config.position,
                        config.margin_pct
                    )

                # Final size safety check
                frame_height, frame_width = frame.shape[:2]
                if frame_width != out_width or frame_height != out_height:
                    interp = cv2.INTER_AREA if (frame_width > out_width or frame_height > out_height) else cv2.INTER_LINEAR
                    frame = cv2.resize(frame, (out_width, out_height), interpolation=interp)

                writer.write(frame)
                frame_idx += 1

            cap.release()
            writer.release()

            # Add audio if provided
            if audio_path and audio_path.exists():
                logger.info(f"Adding audio: {audio_path.name}")
                self._add_audio_to_video(
                    temp_video,
                    output_path,
                    audio_path,
                    target_duration,
                    config
                )
            else:
                # No audio, just move temp file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_video), str(output_path))

            logger.info(f"Successfully processed: {output_path.name}")
            return True

        except Exception as e:
            logger.error(
                f"Error processing video: {str(e)}",
                extra={"video": str(video_path), "output": str(output_path)},
                exc_info=True
            )
            return False

    def _add_audio_to_video(
        self,
        temp_video: Path,
        output_path: Path,
        audio_path: Path,
        target_duration: float,
        config: ProcessingConfig
    ) -> None:
        """
        Add audio to video using moviepy.

        Args:
            temp_video: Temporary video file
            output_path: Final output path
            audio_path: Audio file to add
            target_duration: Target duration in seconds
            config: Processing configuration
        """
        try:
            video_clip = VideoFileClip(str(temp_video))
            audio_clip = AudioFileClip(str(audio_path))

            # Apply volume gain
            if config.music_gain_db != 0:
                volume_factor = 10 ** (config.music_gain_db / 20)
                audio_clip = audio_clip.with_volume_scaled(volume_factor)

            # Mix with original audio or replace
            if config.mix_audio and video_clip.audio:
                final_audio = CompositeAudioClip([video_clip.audio, audio_clip])
            else:
                final_audio = audio_clip

            # Trim to target duration
            if video_clip.duration and video_clip.duration > target_duration:
                video_clip = video_clip.subclipped(0, target_duration)

            if final_audio.duration and final_audio.duration > target_duration:
                final_audio = final_audio.subclipped(0, target_duration)

            # Combine video and audio
            final_clip = video_clip.with_audio(final_audio)

            # Write final output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(output_path.parent / "temp-audio.m4a"),
                remove_temp=True,
                logger=None  # Suppress moviepy logging
            )

            # Cleanup
            video_clip.close()
            audio_clip.close()
            if hasattr(final_clip, "close"):
                final_clip.close()

            # Remove temp video
            if temp_video.exists():
                try:
                    temp_video.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete temp video: {str(e)}")

        except Exception as e:
            logger.warning(
                f"Error adding audio, using video without audio: {str(e)}",
                extra={"audio": str(audio_path)}
            )
            # Fallback: move temp video without audio
            if temp_video.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_video), str(output_path))
