"""
Processing service for video processing operations

Works with AWS S3: downloads files from S3, processes them, and uploads results back.
"""
import logging
import re
import tempfile
from pathlib import Path
from typing import List, Optional

from core.config import Settings
from core.exceptions import (
    FileNotFoundError,
    FolderNotFoundError,
    ProcessingError,
    StorageError,
)
from schemas.processing_schemas import (
    AudioListResponse,
    ProcessingConfig,
    VideoListResponse,
)
from services.job_service import JobService
from services.storage_service import StorageService
from services.video_render_service import VideoRenderService
from utils.ffmpeg_helper import VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, run_ffmpeg_command

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for video processing operations with AWS S3 integration"""

    def __init__(
        self,
        settings: Settings,
        job_service: JobService,
        video_render_service: VideoRenderService,
        storage_service: Optional[StorageService] = None,
    ):
        self.settings = settings
        self.job_service = job_service
        self.video_render_service = video_render_service
        self.storage_service = storage_service

        if not storage_service:
            raise ValueError("StorageService is required for S3 operations")

    def _extract_subfolder_name(self, folder_path: str, user_id: str) -> str | None:
        """
        Extract subfolder name from folder_path.
        
        Handles both cases:
        - Simple folder name: "pimbo" -> "pimbo"
        - Full S3 path: "users/{user_id}/videos/pimbo" -> "pimbo"
        
        Args:
            folder_path: Folder path (can be simple name or full S3 path)
            user_id: User ID for validation
            
        Returns:
            Subfolder name or None if root folder
        """
        if not folder_path or not folder_path.strip():
            return None
            
        folder_path = folder_path.strip()
        
        # If it's a full S3 path, extract the subfolder name
        # Format: users/{user_id}/videos/{subfolder} or users/{user_id}/audios/{subfolder}
        if "/" in folder_path:
            # Split by "/" and get the last part (subfolder name)
            parts = folder_path.split("/")
            
            # Validate format: should end with subfolder name
            # Expected: users/{user_id}/videos/{subfolder} or users/{user_id}/audios/{subfolder}
            if len(parts) >= 4 and parts[0] == "users" and parts[1] == user_id:
                # Return the last part (subfolder name)
                subfolder = parts[-1]
                # Remove trailing slash if present
                return subfolder.rstrip("/") if subfolder else None
            else:
                # If format doesn't match, try to extract last meaningful part
                # Skip empty parts
                meaningful_parts = [p for p in parts if p and p.strip()]
                if meaningful_parts:
                    return meaningful_parts[-1]
        
        # Simple folder name case
        return folder_path if folder_path else None

    async def list_videos_in_folder(
        self, folder_path: str, user_id: str
    ) -> VideoListResponse:
        """
        List all videos in an S3 folder.

        Args:
            folder_path: Subfolder name (e.g., "My Videos") or full S3 path
            user_id: User ID for filtering

        Returns:
            VideoListResponse with S3 paths to videos
        """
        if not self.storage_service:
            raise StorageError("Storage service not available")

        try:
            # Extract subfolder name from path (handles both simple name and full path)
            subfolder = self._extract_subfolder_name(folder_path, user_id)
            
            # List files from S3 (await async method)
            s3_files = await self.storage_service.list_files(
                category="videos",
                user_id=user_id,
                subfolder=subfolder,
            )

            # Filter video files by extension
            videos = []
            for file_info in s3_files:
                key = file_info.get("key", "")
                if not key:
                    continue

                # Extract filename and check extension
                filename = key.split("/")[-1]
                ext = Path(filename).suffix.lower()
                if ext in VIDEO_EXTENSIONS:
                    videos.append(key)  # Return S3 key (full path)

            logger.info(
                f"Listed {len(videos)} videos from S3 folder: {folder_path}",
                extra={"user_id": user_id, "folder": folder_path},
            )

            return VideoListResponse(videos=videos, count=len(videos))

        except Exception as e:
            logger.error(
                f"Failed to list videos from S3: {str(e)}",
                exc_info=True,
                extra={"folder": folder_path, "user_id": user_id},
            )
            raise FolderNotFoundError(f"Failed to list videos: {str(e)}")

    async def list_audios_in_folder(
        self, folder_path: str, user_id: str
    ) -> AudioListResponse:
        """
        List all audios in an S3 folder.

        Args:
            folder_path: Subfolder name (e.g., "My Music") or full S3 path
            user_id: User ID for filtering

        Returns:
            AudioListResponse with S3 paths to audios
        """
        if not self.storage_service:
            raise StorageError("Storage service not available")

        try:
            # Extract subfolder name from path (handles both simple name and full path)
            subfolder = self._extract_subfolder_name(folder_path, user_id)
            
            # List files from S3 (await async method)
            s3_files = await self.storage_service.list_files(
                category="audios",
                user_id=user_id,
                subfolder=subfolder,
            )

            # Filter audio files by extension
            audios = []
            for file_info in s3_files:
                key = file_info.get("key", "")
                if not key:
                    continue

                # Extract filename and check extension
                filename = key.split("/")[-1]
                ext = Path(filename).suffix.lower()
                if ext in AUDIO_EXTENSIONS:
                    audios.append(key)  # Return S3 key (full path)

            logger.info(
                f"Listed {len(audios)} audios from S3 folder: {folder_path}",
                extra={"user_id": user_id, "folder": folder_path},
            )

            return AudioListResponse(audios=audios, count=len(audios))

        except Exception as e:
            logger.error(
                f"Failed to list audios from S3: {str(e)}",
                exc_info=True,
                extra={"folder": folder_path, "user_id": user_id},
            )
            raise FolderNotFoundError(f"Failed to list audios: {str(e)}")

    def get_default_config(self) -> dict:
        """Get default processing configuration"""
        return ProcessingConfig().model_dump()

    def _get_config(self, config: ProcessingConfig | None) -> ProcessingConfig:
        """Get ProcessingConfig, using defaults if not provided"""
        if config is None:
            return ProcessingConfig()
        return config

    async def _download_file_from_s3(self, s3_key: str, local_path: Path) -> None:
        """
        Download file from S3 to local temporary path.

        Args:
            s3_key: S3 object key (full path)
            local_path: Local path to save file

        Raises:
            FileNotFoundError: If file doesn't exist in S3
            StorageError: If download fails
        """
        if not self.storage_service:
            raise StorageError("Storage service not available")

        try:
            # Download file content from S3
            file_content = self.storage_service.s3_client.download_file(s3_key)

            # Write to local file
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(file_content)

            logger.debug(
                f"Downloaded file from S3: {s3_key} -> {local_path}",
                extra={"size": len(file_content)},
            )

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to download file from S3: {str(e)}",
                exc_info=True,
                extra={"s3_key": s3_key},
            )
            raise StorageError(f"Failed to download file from S3: {str(e)}")

    def _optimize_video(self, input_path: Path, output_path: Path) -> bool:
        """
        Optimize video using FFmpeg for smaller file size.

        Uses H.264 encoding with CRF 23 (good quality/size balance).
        Removes audio if present to reduce size.

        Args:
            input_path: Input video path
            output_path: Output video path

        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil

            ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
            if not ffmpeg:
                logger.warning("FFmpeg not found, skipping optimization")
                return False

            # FFmpeg command for optimization
            # -crf 23: High quality, reasonable file size
            # -preset slow: Better compression, slower encoding
            # -movflags +faststart: Better streaming (moov atom at start)
            # -c:a copy: Keep audio as-is (no re-encoding)
            cmd = [
                ffmpeg,
                "-i",
                str(input_path),
                "-c:v",
                "libx264",
                "-crf",
                "23",
                "-preset",
                "slow",
                "-movflags",
                "+faststart",
                "-c:a",
                "copy",  # Copy audio instead of removing
                "-y",  # Overwrite output
                str(output_path),
            ]

            # Run FFmpeg command with longer timeout for video processing
            run_ffmpeg_command(cmd, timeout=600)  # 10 minutes timeout

            # Check if output file was created and is smaller
            if output_path.exists():
                original_size = input_path.stat().st_size
                optimized_size = output_path.stat().st_size

                if optimized_size < original_size:
                    logger.info(
                        f"Video optimized: {original_size} -> {optimized_size} bytes "
                        f"({(1 - optimized_size/original_size)*100:.1f}% reduction)",
                        extra={
                            "original": original_size,
                            "optimized": optimized_size,
                            "reduction": f"{(1 - optimized_size/original_size)*100:.1f}%",
                        },
                    )
                    return True
                else:
                    # Optimized file is larger, use original
                    logger.warning(
                        f"Optimized file is larger, using original: {optimized_size} > {original_size}"
                    )
                    output_path.unlink()
                    return False

            return False

        except Exception as e:
            logger.warning(
                f"Video optimization failed, using original: {str(e)}",
                exc_info=True,
            )
            return False

    async def _upload_output_to_s3(
        self,
        local_output_path: Path,
        user_id: str,
        project_name: str,
        optimize: bool = True,
    ) -> str:
        """
        Upload processed video to S3 with temporary tag.
        Optionally optimizes video before uploading.

        Args:
            local_output_path: Path to local output file
            user_id: User ID for organizing in S3
            project_name: Project name for folder organization
            optimize: Whether to optimize video before uploading (default: True)

        Returns:
            S3 storage path

        Raises:
            StorageError: If upload fails
        """
        try:
            file_to_upload = local_output_path
            original_size = local_output_path.stat().st_size

            # Optimize video if requested
            if optimize:
                optimized_path = local_output_path.with_suffix(".optimized.mp4")
                if self._optimize_video(local_output_path, optimized_path):
                    file_to_upload = optimized_path
                    logger.info(
                        f"Using optimized video for upload: {optimized_path.name}",
                        extra={
                            "original_size": original_size,
                            "optimized_size": optimized_path.stat().st_size,
                        },
                    )

            # Read file content
            with open(file_to_upload, "rb") as f:
                file_content = f.read()

            # Upload to S3 with optimization
            s3_path, _ = await self.storage_service.upload_output_file(
                user_id=user_id,
                project_name=project_name,
                filename=local_output_path.name,  # Keep original filename
                file_content=file_content,
                content_type="video/mp4",
            )

            # Clean up temporary files
            try:
                local_output_path.unlink()
                logger.debug(f"Deleted local temporary file: {local_output_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {local_output_path}: {e}")

            if file_to_upload != local_output_path:
                try:
                    file_to_upload.unlink()
                    logger.debug(f"Deleted optimized temporary file: {file_to_upload}")
                except Exception as e:
                    logger.warning(
                        f"Failed to delete optimized temporary file {file_to_upload}: {e}"
                    )

            return s3_path

        except Exception as e:
            logger.error(f"Failed to upload output to S3: {str(e)}", exc_info=True)
            raise

    async def process_single_video(
        self,
        job_id: str,
        user_id: str,
        video_path: str,  # Now expects S3 key
        audio_path: str | None,  # Now expects S3 key or None
        text_segments: List[str],
        output_path: str,
        project_name: str,
        config: ProcessingConfig | None = None,
    ) -> None:
        """
        Process a single video (runs in background and uploads to S3).

        Args:
            job_id: Job ID
            user_id: User ID
            video_path: S3 key to video file
            audio_path: S3 key to audio file (optional)
            text_segments: List of text segments to overlay
            output_path: Output filename (not full path)
            project_name: Project name for folder organization
            config: Processing configuration
        """
        try:
            self.job_service.update_job(
                job_id, status="processing", progress=10.0, message="Downloading files from S3..."
            )

            cfg = self._get_config(config)

            # Use temporary directory for downloads and output
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_base = Path(temp_dir)

                # Download video from S3
                temp_video = temp_base / Path(video_path).name
                await self._download_file_from_s3(video_path, temp_video)

                # Download audio from S3 if provided
                temp_audio = None
                if audio_path:
                    temp_audio = temp_base / Path(audio_path).name
                    await self._download_file_from_s3(audio_path, temp_audio)

                self.job_service.update_job(
                    job_id, status="processing", progress=30.0, message="Processing video..."
                )

                # Process video
                temp_output = temp_base / Path(output_path).name
                success = self.video_render_service.process_video(
                    video_path=temp_video,
                    output_path=temp_output,
                    text_segments=text_segments,
                    audio_path=temp_audio,
                    config=cfg,
                )

                if success and self.storage_service:
                    # Upload to S3 with optimization
                    self.job_service.update_job(
                        job_id, status="processing", progress=80.0, message="Uploading to S3..."
                    )
                    s3_path = await self._upload_output_to_s3(temp_output, user_id, project_name)

                    self.job_service.update_job(
                        job_id,
                        status="completed",
                        progress=100.0,
                        message="Done",
                        output_files=[s3_path],
                    )
                else:
                    self.job_service.update_job(
                        job_id, status="failed", progress=0.0, message="Processing failed"
                    )

        except Exception as e:
            logger.error(
                f"Error processing single video: {str(e)}",
                exc_info=True,
                extra={"job_id": job_id, "video_path": video_path},
            )
            self.job_service.update_job(
                job_id, status="failed", progress=0.0, message=f"Error: {str(e)}"
            )

    def _first_words(self, text: str, n: int = 20) -> str:
        """Get first n characters of text, removing special chars"""
        return re.sub(r"[^\w\s]", "", text).strip()[:n] if text else "text"

    def _build_all_jobs(
        self, vids: List[str], auds: List[str], rows_used: List[List[str]]
    ) -> List[tuple]:
        """
        Build all cartesian product jobs.

        Args:
            vids: List of S3 keys to videos
            auds: List of S3 keys to audios
            rows_used: List of text segment combinations

        Returns:
            List of tuples: (video_s3_key, audio_s3_key or None, segments, idx)
        """
        jobs = []
        for vpath in vids:
            for idx, segments in enumerate(rows_used):
                if auds:
                    for apath in auds:
                        jobs.append((vpath, apath, segments, idx))
                else:
                    jobs.append((vpath, None, segments, idx))
        return jobs

    def _build_unique_jobs(
        self, vids: List[str], auds: List[str], rows_used: List[List[str]], want: int
    ) -> List[tuple]:
        """
        Build unique deterministic jobs.

        Args:
            vids: List of S3 keys to videos
            auds: List of S3 keys to audios
            rows_used: List of text segment combinations
            want: Number of unique jobs to generate

        Returns:
            List of tuples: (video_s3_key, audio_s3_key or None, segments, idx)
        """
        V = len(vids)
        C = max(1, len(rows_used))
        A = len(auds) if auds else 1

        if V == 0:
            return []

        total_possible = V * C * A
        N = min(want, total_possible)
        picks_per_video = [0] * V
        jobs = []

        for t in range(N):
            b = t % V
            k = picks_per_video[b]
            picks_per_video[b] += 1

            start_c = b % C
            cap_idx = (start_c + k) % C

            if auds:
                start_a = b % A
                aud_idx = (start_a + k) % A
                apath = auds[aud_idx]
            else:
                apath = None

            vpath = vids[b]
            segments = rows_used[cap_idx] if C > 0 else []
            jobs.append((vpath, apath, segments, cap_idx))

        return jobs

    async def process_batch_videos(
        self,
        job_id: str,
        user_id: str,
        video_folder: str,  # Subfolder name in S3
        audio_folder: str | None,  # Subfolder name in S3
        text_combinations: List[List[str]],
        output_folder: str,  # Not used anymore (always uploads to S3)
        project_name: str,
        unique_mode: bool = False,
        unique_amount: int | None = None,
        config: ProcessingConfig | None = None,
    ) -> None:
        """
        Process batch of videos from S3 (runs in background and uploads to S3).

        Args:
            job_id: Job ID
            user_id: User ID
            video_folder: Subfolder name in S3 (e.g., "My Videos")
            audio_folder: Subfolder name in S3 (e.g., "My Music") or None
            text_combinations: List of text segment combinations
            output_folder: Not used (kept for compatibility)
            project_name: Project name for folder organization
            unique_mode: Use deterministic unique selection
            unique_amount: Number of unique combinations
            config: Processing configuration
        """
        try:
            self.job_service.update_job(
                job_id, status="processing", progress=0.0, message="Listing files from S3..."
            )

            # List videos and audios from S3
            vids_response = await self.list_videos_in_folder(video_folder, user_id)
            vids = vids_response.videos  # List of S3 keys

            auds = []
            if audio_folder:
                auds_response = await self.list_audios_in_folder(audio_folder, user_id)
                auds = auds_response.audios  # List of S3 keys

            if not vids:
                self.job_service.update_job(
                    job_id, status="failed", progress=0.0, message="No videos found in folder"
                )
                return

            rows_used = text_combinations if text_combinations else [[]]

            # Build jobs
            if unique_mode and unique_amount:
                jobs = self._build_unique_jobs(vids, auds, rows_used, unique_amount)
            else:
                jobs = self._build_all_jobs(vids, auds, rows_used)

            if not jobs:
                self.job_service.update_job(
                    job_id, status="failed", progress=0.0, message="No jobs to process"
                )
                return

            cfg = self._get_config(config)
            total = len(jobs)

            self.job_service.update_job(
                job_id,
                status="processing",
                progress=5.0,
                message=f"Processing {total} videos...",
            )

            # Use temporary directory for downloads and outputs
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_base = Path(temp_dir)
                output_files = []

                for i, (vpath_s3, apath_s3, segments, idx) in enumerate(jobs, 1):
                    progress = 5 + (i / total) * 90  # 5% to 95%
                    self.job_service.update_job(
                        job_id,
                        status="processing",
                        progress=progress,
                        message=f"Processing {i}/{total}",
                    )

                    try:
                        # Download video from S3
                        video_filename = Path(vpath_s3).name
                        temp_video = temp_base / f"video_{i}_{video_filename}"
                        await self._download_file_from_s3(vpath_s3, temp_video)

                        # Download audio from S3 if provided
                        temp_audio = None
                        if apath_s3:
                            audio_filename = Path(apath_s3).name
                            temp_audio = temp_base / f"audio_{i}_{audio_filename}"
                            await self._download_file_from_s3(apath_s3, temp_audio)

                        # Build temporary output path
                        abase = Path(apath_s3).stem if apath_s3 else "noaudio"
                        cap_key = self._first_words(segments[0] if segments else "text")
                        safe_tbase = re.sub(r"[^\w\-_]", "_", f"combo{idx+1}_{cap_key}")[:50]
                        video_stem = Path(vpath_s3).stem
                        filename = f"{video_stem}_{abase}__{safe_tbase}.mp4"
                        temp_out_path = temp_base / filename

                        # Process video
                        success = self.video_render_service.process_video(
                            video_path=temp_video,
                            output_path=temp_out_path,
                            text_segments=segments,
                            audio_path=temp_audio,
                            config=cfg,
                        )

                        if success and self.storage_service:
                            # Upload to S3 with optimization
                            s3_path = await self._upload_output_to_s3(
                                temp_out_path, user_id, project_name
                            )
                            output_files.append(s3_path)
                        else:
                            logger.error(
                                f"Video processing failed for job {i}",
                                extra={"job_number": i, "total_jobs": total},
                            )

                        # Clean up downloaded files
                        try:
                            temp_video.unlink()
                            if temp_audio:
                                temp_audio.unlink()
                        except Exception as e:
                            logger.warning(f"Failed to cleanup temp files: {e}")

                    except Exception as e:
                        logger.error(
                            f"Error processing batch job {i}: {str(e)}",
                            exc_info=True,
                            extra={"job_number": i, "total_jobs": total},
                        )

                # All processing done, temporary files auto-deleted when exiting context
                self.job_service.update_job(
                    job_id,
                    status="completed",
                    progress=100.0,
                    message=f"Completed {len(output_files)}/{total} files",
                    output_files=output_files,
                )

        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}", exc_info=True)
            self.job_service.update_job(
                job_id,
                status="failed",
                progress=0.0,
                message=f"Batch processing error: {str(e)}",
            )
