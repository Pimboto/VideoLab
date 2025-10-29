"""
Processing service for video processing operations
"""
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import List, Optional

from core.config import Settings
from core.exceptions import (
    FileNotFoundError,
    FolderNotFoundError,
    ProcessingError,
)
from schemas.processing_schemas import (
    AudioListResponse,
    ProcessingConfig,
    VideoListResponse,
)
from services.job_service import JobService
from services.storage_service import StorageService
from services.video_render_service import VideoRenderService
from utils.ffmpeg_helper import list_media_files, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for video processing operations"""

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

    def list_videos_in_folder(self, folder_path: str) -> VideoListResponse:
        """List all videos in a folder"""
        folder = Path(folder_path)

        if not folder.exists():
            raise FolderNotFoundError(f"Folder not found: {folder_path}")

        if not folder.is_dir():
            raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

        videos = list_media_files(folder, VIDEO_EXTENSIONS)
        return VideoListResponse(videos=[str(v) for v in videos], count=len(videos))

    def list_audios_in_folder(self, folder_path: str) -> AudioListResponse:
        """List all audios in a folder"""
        folder = Path(folder_path)

        if not folder.exists():
            raise FolderNotFoundError(f"Folder not found: {folder_path}")

        if not folder.is_dir():
            raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

        audios = list_media_files(folder, AUDIO_EXTENSIONS)
        return AudioListResponse(audios=[str(a) for a in audios], count=len(audios))

    def get_default_config(self) -> dict:
        """Get default processing configuration"""
        return ProcessingConfig().model_dump()

    def _get_config(self, config: ProcessingConfig | None) -> ProcessingConfig:
        """Get ProcessingConfig, using defaults if not provided"""
        if config is None:
            return ProcessingConfig()
        return config

    async def _upload_output_to_s3(
        self,
        local_output_path: Path,
        user_id: str,
        job_id: str
    ) -> str:
        """
        Upload processed video to S3 with temporary tag.

        Args:
            local_output_path: Path to local output file
            user_id: User ID for organizing in S3
            job_id: Job ID for grouping outputs

        Returns:
            S3 storage path

        Raises:
            StorageError: If upload fails
        """
        try:
            # Read file content
            with open(local_output_path, 'rb') as f:
                file_content = f.read()

            # Upload to S3 with temporary tag
            s3_path, _ = await self.storage_service.upload_output_file(
                user_id=user_id,
                job_id=job_id,
                filename=local_output_path.name,
                file_content=file_content,
                content_type="video/mp4"
            )

            # Delete local temporary file
            try:
                local_output_path.unlink()
                logger.debug(f"Deleted local temporary file: {local_output_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {local_output_path}: {e}")

            return s3_path

        except Exception as e:
            logger.error(f"Failed to upload output to S3: {str(e)}", exc_info=True)
            raise

    async def process_single_video(
        self,
        job_id: str,
        user_id: str,
        video_path: str,
        audio_path: str | None,
        text_segments: List[str],
        output_path: str,
        config: ProcessingConfig | None = None,
    ) -> None:
        """Process a single video (runs in background and uploads to S3)"""
        try:
            self.job_service.update_job(
                job_id, status="processing", progress=50.0, message="Processing video..."
            )

            cfg = self._get_config(config)
            video_path_obj = Path(video_path)
            audio_path_obj = Path(audio_path) if audio_path else None

            if not video_path_obj.exists():
                raise FileNotFoundError(f"Video not found: {video_path}")

            # Use temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_output = Path(temp_dir) / Path(output_path).name

                success = self.video_render_service.process_video(
                    video_path=video_path_obj,
                    output_path=temp_output,
                    text_segments=text_segments,
                    audio_path=audio_path_obj,
                    config=cfg,
                )

                if success and self.storage_service:
                    # Upload to S3 with temporary tag
                    s3_path = await self._upload_output_to_s3(temp_output, user_id, job_id)

                    self.job_service.update_job(
                        job_id,
                        status="completed",
                        progress=100.0,
                        message="Done",
                        output_files=[s3_path],
                    )
                elif success:
                    # Fallback: save locally if storage_service not available
                    logger.warning("Storage service not available, saving output locally")
                    output_path_obj = Path(output_path)
                    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    temp_output.rename(output_path_obj)

                    self.job_service.update_job(
                        job_id,
                        status="completed",
                        progress=100.0,
                        message="Done",
                        output_files=[str(output_path_obj)],
                    )
                else:
                    self.job_service.update_job(
                        job_id, status="failed", progress=0.0, message="Processing failed"
                    )

        except Exception as e:
            logger.error(
                f"Error processing single video: {str(e)}",
                exc_info=True,
                extra={"job_id": job_id, "video_path": video_path}
            )
            self.job_service.update_job(
                job_id, status="failed", progress=0.0, message=f"Error: {str(e)}"
            )

    def _first_words(self, text: str, n: int = 20) -> str:
        """Get first n characters of text, removing special chars"""
        return re.sub(r"[^\w\s]", "", text).strip()[:n] if text else "text"

    def _build_all_jobs(
        self, vids: List[Path], auds: List[Path], rows_used: List[List[str]]
    ) -> List[tuple]:
        """Build all cartesian product jobs"""
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
        self, vids: List[Path], auds: List[Path], rows_used: List[List[str]], want: int
    ) -> List[tuple]:
        """Build unique deterministic jobs"""
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
        video_folder: str,
        audio_folder: str | None,
        text_combinations: List[List[str]],
        output_folder: str,
        unique_mode: bool = False,
        unique_amount: int | None = None,
        config: ProcessingConfig | None = None,
    ) -> None:
        """Process batch of videos (runs in background and uploads to S3)"""
        try:
            self.job_service.update_job(
                job_id, status="processing", progress=0.0, message="Building job list..."
            )

            # List videos and audios
            vids_response = self.list_videos_in_folder(video_folder)
            vids = [Path(v) for v in vids_response.videos]

            auds = []
            if audio_folder:
                auds_response = self.list_audios_in_folder(audio_folder)
                auds = [Path(a) for a in auds_response.audios]

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

            # Use temporary directory for all outputs
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_outd = Path(temp_dir)
                output_files = []
                total = len(jobs)

                for i, (vpath, apath, segments, idx) in enumerate(jobs, 1):
                    progress = (i / total) * 100
                    self.job_service.update_job(
                        job_id,
                        status="processing",
                        progress=progress,
                        message=f"Processing {i}/{total}",
                    )

                    # Build temporary output path
                    abase = apath.stem if apath else "noaudio"
                    cap_key = self._first_words(segments[0] if segments else "text")
                    safe_tbase = re.sub(r"[^\w\-_]", "_", f"combo{idx+1}_{cap_key}")[:50]
                    filename = f"{vpath.stem}_{abase}__{safe_tbase}.mp4"
                    temp_out_path = temp_outd / filename

                    try:
                        success = self.video_render_service.process_video(
                            video_path=vpath,
                            output_path=temp_out_path,
                            text_segments=segments,
                            audio_path=apath,
                            config=cfg,
                        )

                        if success and self.storage_service:
                            # Upload to S3 with temporary tag
                            s3_path = await self._upload_output_to_s3(
                                temp_out_path, user_id, job_id
                            )
                            output_files.append(s3_path)
                        elif success:
                            # Fallback: save locally
                            logger.warning("Storage service not available, saving output locally")
                            local_outd = Path(output_folder)
                            local_outd.mkdir(parents=True, exist_ok=True)
                            final_path = local_outd / filename
                            temp_out_path.rename(final_path)
                            output_files.append(str(final_path))
                    except Exception as e:
                        logger.error(
                            f"Error processing batch job {i}: {str(e)}",
                            exc_info=True,
                            extra={"job_number": i, "total_jobs": total}
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
