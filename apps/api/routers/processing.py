"""
Video processing routes
"""
from typing import List

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Path

from core.dependencies import get_job_service, get_processing_service, get_current_user
from schemas.job_schemas import BatchJobResponse, JobDeleteResponse, JobStatus
from schemas.processing_schemas import (
    AudioListRequest,
    AudioListResponse,
    BatchProcessRequest,
    ProcessingConfig,
    SingleProcessRequest,
    VideoListRequest,
    VideoListResponse,
)
from services.job_service import JobService
from services.processing_service import ProcessingService

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/list-videos", response_model=VideoListResponse)
def list_videos(
    request: VideoListRequest,
    current_user: dict = Depends(get_current_user),
    processing_service: ProcessingService = Depends(get_processing_service),
) -> VideoListResponse:
    """
    List all video files in a folder.

    Requires authentication.

    - **folder_path**: Absolute path to video folder
    """
    return processing_service.list_videos_in_folder(request.folder_path)


@router.post("/list-audios", response_model=AudioListResponse)
def list_audios(
    request: AudioListRequest,
    current_user: dict = Depends(get_current_user),
    processing_service: ProcessingService = Depends(get_processing_service),
) -> AudioListResponse:
    """
    List all audio files in a folder.

    Requires authentication.

    - **folder_path**: Absolute path to audio folder
    """
    return processing_service.list_audios_in_folder(request.folder_path)


@router.get("/default-config", response_model=ProcessingConfig)
def get_default_config(
    current_user: dict = Depends(get_current_user),
    processing_service: ProcessingService = Depends(get_processing_service),
) -> ProcessingConfig:
    """
    Get default processing configuration.
    
    Requires authentication.
    """
    cfg = processing_service.get_default_config()
    return ProcessingConfig(**cfg)


@router.post("/process-single", response_model=JobStatus, status_code=202)
async def process_single_video(
    request: SingleProcessRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
    processing_service: ProcessingService = Depends(get_processing_service),
) -> JobStatus:
    """
    Process a single video with text and audio.

    Requires authentication.

    Creates a background job and returns immediately.
    Use the job_id to poll for status.

    - **video_path**: Path to input video
    - **audio_path**: Path to audio file (optional)
    - **text_segments**: List of text segments to overlay
    - **output_path**: Path for output video
    - **config**: Processing configuration (optional)
    """
    job_id = job_service.create_job("pending", "Job queued")

    background_tasks.add_task(
        processing_service.process_single_video,
        job_id,
        request.video_path,
        request.audio_path,
        request.text_segments,
        request.output_path,
        request.config,
    )

    return job_service.get_job(job_id)


@router.post("/process-batch", response_model=BatchJobResponse, status_code=202)
async def process_batch_videos(
    request: BatchProcessRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
    processing_service: ProcessingService = Depends(get_processing_service),
) -> BatchJobResponse:
    """
    Process multiple videos in batch.

    Requires authentication.

    Creates a background job and returns immediately.
    Use the job_id to poll for status.

    - **video_folder**: Folder containing videos
    - **audio_folder**: Folder containing audios (optional)
    - **text_combinations**: List of text combinations
    - **output_folder**: Output folder for processed videos
    - **unique_mode**: Use deterministic unique selection
    - **unique_amount**: Number of unique combinations (if unique_mode=True)
    - **config**: Processing configuration (optional)
    """
    # Quick validation
    vids_response = processing_service.list_videos_in_folder(request.video_folder)
    if vids_response.count == 0:
        from core.exceptions import ValidationError

        raise ValidationError("No videos found in folder")

    auds_count = 0
    if request.audio_folder:
        auds_response = processing_service.list_audios_in_folder(request.audio_folder)
        auds_count = auds_response.count

    rows_count = len(request.text_combinations) if request.text_combinations else 1

    if request.unique_mode and request.unique_amount:
        total = min(
            request.unique_amount,
            vids_response.count * rows_count * max(1, auds_count),
        )
    else:
        total = vids_response.count * rows_count * max(1, auds_count)

    job_id = job_service.create_job("pending", "Batch job queued")

    background_tasks.add_task(
        processing_service.process_batch_videos,
        job_id,
        request.video_folder,
        request.audio_folder,
        request.text_combinations,
        request.output_folder,
        request.unique_mode,
        request.unique_amount,
        request.config,
    )

    return BatchJobResponse(
        job_id=job_id,
        total_jobs=total,
        message=f"Batch job started with {total} videos to process",
    )


@router.get("/status/{job_id}", response_model=JobStatus)
def get_job_status(
    job_id: str = Path(..., description="Job ID to query"),
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> JobStatus:
    """
    Get the status of a processing job.

    Requires authentication.

    - **job_id**: Unique job identifier
    """
    return job_service.get_job(job_id)


@router.get("/jobs", response_model=List[JobStatus])
def list_all_jobs(
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> List[JobStatus]:
    """
    List all processing jobs and their statuses.
    
    Requires authentication.
    """
    return job_service.list_jobs()


@router.delete("/jobs/{job_id}", response_model=JobDeleteResponse)
def delete_job(
    job_id: str = Path(..., description="Job ID to delete"),
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> JobDeleteResponse:
    """
    Delete a job from tracking.

    Requires authentication.

    Note: This doesn't stop processing if job is already running.

    - **job_id**: Unique job identifier
    """
    return job_service.delete_job(job_id)
