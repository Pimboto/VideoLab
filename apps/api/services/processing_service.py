"""
Processing service for video processing operations
"""
import re
from pathlib import Path
from typing import List

import batch_core as core

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


class ProcessingService:
    """Service for video processing operations"""

    def __init__(self, settings: Settings, job_service: JobService):
        self.settings = settings
        self.job_service = job_service

    def list_videos_in_folder(self, folder_path: str) -> VideoListResponse:
        """List all videos in a folder"""
        folder = Path(folder_path)

        if not folder.exists():
            raise FolderNotFoundError(f"Folder not found: {folder_path}")

        if not folder.is_dir():
            raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

        videos = core.list_files(folder, core.VIDEO_EXT)
        return VideoListResponse(videos=[str(v) for v in videos], count=len(videos))

    def list_audios_in_folder(self, folder_path: str) -> AudioListResponse:
        """List all audios in a folder"""
        folder = Path(folder_path)

        if not folder.exists():
            raise FolderNotFoundError(f"Folder not found: {folder_path}")

        if not folder.is_dir():
            raise FolderNotFoundError(f"Path is not a directory: {folder_path}")

        audios = core.list_files(folder, core.AUDIO_EXT)
        return AudioListResponse(audios=[str(a) for a in audios], count=len(audios))

    def get_default_config(self) -> dict:
        """Get default processing configuration"""
        return core.default_cfg()

    def config_to_dict(self, config: ProcessingConfig | None) -> dict:
        """Convert ProcessingConfig to dict for batch_core"""
        if config is None:
            return core.default_cfg()

        return {
            "position": config.position,
            "margin_pct": config.margin_pct,
            "duration_policy": config.duration_policy,
            "fixed_seconds": config.fixed_seconds,
            "canvas_size": config.canvas_size,
            "fit_mode": config.fit_mode,
            "music_gain_db": config.music_gain_db,
            "mix_audio": config.mix_audio,
            "preset": config.preset,
            "outline_px": config.outline_px,
            "fontsize_ratio": config.fontsize_ratio,
        }

    async def process_single_video(
        self,
        job_id: str,
        video_path: str,
        audio_path: str | None,
        text_segments: List[str],
        output_path: str,
        config: ProcessingConfig | None = None,
    ) -> None:
        """Process a single video (runs in background)"""
        try:
            self.job_service.update_job(
                job_id, status="processing", progress=50.0, message="Processing video..."
            )

            cfg = self.config_to_dict(config)
            video_path_obj = Path(video_path)
            audio_path_obj = Path(audio_path) if audio_path else None
            output_path_obj = Path(output_path)

            if not video_path_obj.exists():
                raise FileNotFoundError(f"Video not found: {video_path}")

            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            success = core.run_one(
                video_path=video_path_obj,
                audio_path=audio_path_obj,
                text_segments=text_segments,
                output_path=output_path_obj,
                cfg=cfg,
            )

            if success:
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
        video_folder: str,
        audio_folder: str | None,
        text_combinations: List[List[str]],
        output_folder: str,
        unique_mode: bool = False,
        unique_amount: int | None = None,
        config: ProcessingConfig | None = None,
    ) -> None:
        """Process batch of videos (runs in background)"""
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

            cfg = self.config_to_dict(config)
            outd = Path(output_folder)
            outd.mkdir(parents=True, exist_ok=True)

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

                video_folder = outd / vpath.stem
                video_folder.mkdir(parents=True, exist_ok=True)

                abase = apath.stem if apath else "noaudio"
                cap_key = self._first_words(segments[0] if segments else "text")
                safe_tbase = re.sub(r"[^\w\-_]", "_", f"combo{idx+1}_{cap_key}")[:50]
                out_path = video_folder / f"{abase}__{safe_tbase}.mp4"

                try:
                    success = core.run_one(vpath, apath, segments, out_path, cfg)
                    if success:
                        output_files.append(str(out_path))
                except Exception as e:
                    print(f"Error processing job {i}: {e}")

            self.job_service.update_job(
                job_id,
                status="completed",
                progress=100.0,
                message=f"Completed {len(output_files)}/{total} files",
                output_files=output_files,
            )

        except Exception as e:
            self.job_service.update_job(
                job_id,
                status="failed",
                progress=0.0,
                message=f"Batch processing error: {str(e)}",
            )
