"""
Video Processing Router - Converts batch_core + ui functionality to HTTP endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict
from pathlib import Path
import uuid
import csv
import io
import re
import shutil
import datetime
import hashlib

import batch_core as core
from config import (
    get_storage_path, validate_file_size, validate_file_extension,
    ALLOWED_VIDEO_EXTENSIONS, ALLOWED_AUDIO_EXTENSIONS, MAX_FILE_SIZE
)

router = APIRouter(prefix="/api/video-processor", tags=["video-processor"])

# ==================== Models ====================

class FolderListRequest(BaseModel):
    folder_path: str = Field(..., description="Absolute path to folder")

class VideoListResponse(BaseModel):
    videos: List[str] = Field(..., description="List of video file paths")
    count: int

class AudioListResponse(BaseModel):
    audios: List[str] = Field(..., description="List of audio file paths")
    count: int

class TextSegment(BaseModel):
    segments: List[str] = Field(..., description="Text segments for one combination")

class TextCombinationsResponse(BaseModel):
    combinations: List[List[str]]
    count: int

class ProcessingConfig(BaseModel):
    position: str = Field(default="center", description="Text position: center, top, bottom")
    margin_pct: float = Field(default=0.16, ge=0, le=0.5)
    duration_policy: str = Field(default="shortest", description="shortest, audio, video, fixed")
    fixed_seconds: Optional[float] = Field(default=None, ge=0)
    canvas_size: Tuple[int, int] = Field(default=(1080, 1920))
    fit_mode: str = Field(default="cover", description="cover, contain, zoom")
    music_gain_db: int = Field(default=-8)
    mix_audio: bool = Field(default=False)
    preset: Optional[str] = Field(default=None, description="clean, bold, subtle, yellow, shadow")
    outline_px: int = Field(default=2, ge=0)
    fontsize_ratio: float = Field(default=0.036, ge=0.01, le=0.1)

class JobRequest(BaseModel):
    video_path: str
    audio_path: Optional[str] = None
    text_segments: List[str] = Field(default_factory=list)
    output_path: str
    config: Optional[ProcessingConfig] = None

class BatchJobRequest(BaseModel):
    video_folder: str
    audio_folder: Optional[str] = None
    text_combinations: List[List[str]] = Field(default_factory=list)
    output_folder: str
    config: Optional[ProcessingConfig] = None
    unique_mode: bool = Field(default=False, description="Use deterministic unique selection")
    unique_amount: Optional[int] = Field(default=None, ge=1)

class JobStatus(BaseModel):
    job_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    progress: float = Field(default=0.0, ge=0, le=100)
    message: str = ""
    output_files: List[str] = Field(default_factory=list)

class BatchJobResponse(BaseModel):
    job_id: str
    total_jobs: int
    message: str

class FileUploadResponse(BaseModel):
    filename: str
    filepath: str
    size: int
    message: str

class FileInfo(BaseModel):
    filename: str
    filepath: str
    size: int
    modified: str
    type: str

class FolderInfo(BaseModel):
    name: str
    path: str
    file_count: int
    total_size: int

class FolderListResponse(BaseModel):
    folders: List[FolderInfo]
    count: int

class FileListResponse(BaseModel):
    files: List[FileInfo]
    count: int

class DeleteFileRequest(BaseModel):
    filepath: str

class DeleteResponse(BaseModel):
    message: str
    filepath: str

class CreateFolderRequest(BaseModel):
    parent_category: str = Field(..., description="Category: videos, audios, csv, output")
    folder_name: str

class MoveFileRequest(BaseModel):
    source_path: str
    destination_folder: str

# ==================== State Management ====================

# Simple in-memory job tracking (for production, use Redis/DB)
job_statuses: dict[str, JobStatus] = {}

def update_job_status(job_id: str, status: str, progress: float = 0.0,
                      message: str = "", output_files: List[str] = None):
    if job_id in job_statuses:
        job_statuses[job_id].status = status
        job_statuses[job_id].progress = progress
        job_statuses[job_id].message = message
        if output_files:
            job_statuses[job_id].output_files = output_files

# ==================== Helper Functions ====================

def list_videos(folder: str) -> List[Path]:
    folder_path = Path(folder)
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder}")
    return core.list_files(folder_path, core.VIDEO_EXT)

def list_audios(folder: str) -> List[Path]:
    folder_path = Path(folder)
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder}")
    return core.list_files(folder_path, core.AUDIO_EXT)

def first_words(s: str, n: int = 20) -> str:
    return re.sub(r"[^\w\s]", "", s).strip()[:n] if s else "text"

def build_all_jobs(vids: List[Path], auds: List[Path], rows_used: List[List[str]]) -> List[tuple]:
    jobs = []
    for vpath in vids:
        for idx, segments in enumerate(rows_used):
            if auds:
                for apath in auds:
                    jobs.append((vpath, apath, segments, idx))
            else:
                jobs.append((vpath, None, segments, idx))
    return jobs

def build_deterministic_unique_jobs(vids: List[Path], auds: List[Path],
                                    rows_used: List[List[str]], want: int) -> List[tuple]:
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

def config_to_dict(config: Optional[ProcessingConfig]) -> dict:
    if config is None:
        return core.default_cfg()
    return config.model_dump()

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename with timestamp and hash"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = Path(original_filename).stem
    ext = Path(original_filename).suffix
    random_hash = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
    return f"{name}_{timestamp}_{random_hash}{ext}"

def get_file_info(filepath: Path, file_type: str) -> FileInfo:
    """Get file information"""
    stat = filepath.stat()
    return FileInfo(
        filename=filepath.name,
        filepath=str(filepath),
        size=stat.st_size,
        modified=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
        type=file_type
    )

def get_folder_info(folder_path: Path) -> FolderInfo:
    """Get folder information including file count and total size"""
    files = list(folder_path.iterdir()) if folder_path.exists() else []
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    file_count = sum(1 for f in files if f.is_file())

    return FolderInfo(
        name=folder_path.name,
        path=str(folder_path),
        file_count=file_count,
        total_size=total_size
    )

async def save_upload_file(upload_file: UploadFile, destination: Path) -> int:
    """Save uploaded file and return size"""
    destination.parent.mkdir(parents=True, exist_ok=True)

    total_size = 0
    with destination.open("wb") as buffer:
        while chunk := await upload_file.read(8192):  # 8KB chunks
            total_size += len(chunk)
            buffer.write(chunk)

    return total_size

# ==================== Background Processing ====================

async def process_single_job_bg(job_id: str, job_req: JobRequest):
    try:
        update_job_status(job_id, "processing", 50.0, "Processing video...")

        cfg = config_to_dict(job_req.config)
        video_path = Path(job_req.video_path)
        audio_path = Path(job_req.audio_path) if job_req.audio_path else None
        output_path = Path(job_req.output_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        success = core.run_one(
            video_path=video_path,
            audio_path=audio_path,
            text_segments=job_req.text_segments,
            output_path=output_path,
            cfg=cfg
        )

        if success:
            update_job_status(job_id, "completed", 100.0, "Done", [str(output_path)])
        else:
            update_job_status(job_id, "failed", 0.0, "Processing failed")

    except Exception as e:
        update_job_status(job_id, "failed", 0.0, f"Error: {str(e)}")

async def process_batch_jobs_bg(job_id: str, batch_req: BatchJobRequest):
    try:
        update_job_status(job_id, "processing", 0.0, "Building job list...")

        vids = list_videos(batch_req.video_folder)
        auds = list_audios(batch_req.audio_folder) if batch_req.audio_folder else []
        rows_used = batch_req.text_combinations if batch_req.text_combinations else [[]]

        if batch_req.unique_mode and batch_req.unique_amount:
            jobs = build_deterministic_unique_jobs(vids, auds, rows_used, batch_req.unique_amount)
        else:
            jobs = build_all_jobs(vids, auds, rows_used)

        if not jobs:
            update_job_status(job_id, "failed", 0.0, "No jobs to process")
            return

        cfg = config_to_dict(batch_req.config)
        outd = Path(batch_req.output_folder)
        outd.mkdir(parents=True, exist_ok=True)

        output_files = []
        total = len(jobs)

        for i, (vpath, apath, segments, idx) in enumerate(jobs, 1):
            progress = (i / total) * 100
            update_job_status(job_id, "processing", progress, f"Processing {i}/{total}")

            video_folder = outd / Path(vpath).stem
            video_folder.mkdir(parents=True, exist_ok=True)

            abase = apath.stem if apath else "noaudio"
            cap_key = first_words(segments[0] if segments else "text")
            safe_tbase = re.sub(r"[^\w\-_]", "_", f"combo{idx+1}_{cap_key}")[:50]
            out_path = video_folder / f"{abase}__{safe_tbase}.mp4"

            try:
                success = core.run_one(vpath, apath, segments, out_path, cfg)
                if success:
                    output_files.append(str(out_path))
            except Exception as e:
                print(f"Error processing job {i}: {e}")

        update_job_status(job_id, "completed", 100.0, f"Completed {len(output_files)}/{total} files", output_files)

    except Exception as e:
        update_job_status(job_id, "failed", 0.0, f"Batch processing error: {str(e)}")

# ==================== Endpoints ====================

@router.post("/list-videos", response_model=VideoListResponse)
async def api_list_videos(request: FolderListRequest):
    """List all video files in a folder"""
    videos = list_videos(request.folder_path)
    return VideoListResponse(
        videos=[str(v) for v in videos],
        count=len(videos)
    )

@router.post("/list-audios", response_model=AudioListResponse)
async def api_list_audios(request: FolderListRequest):
    """List all audio files in a folder"""
    audios = list_audios(request.folder_path)
    return AudioListResponse(
        audios=[str(a) for a in audios],
        count=len(audios)
    )

@router.post("/parse-csv", response_model=TextCombinationsResponse)
async def api_parse_csv(file: UploadFile = File(...)):
    """Upload and parse a CSV file with text combinations"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        content = await file.read()
        text_content = content.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text_content))

        combinations = []
        for row in reader:
            if not row:
                continue
            segs = [c.strip() for c in row if c and c.strip()]
            if segs:
                combinations.append(segs)

        return TextCombinationsResponse(
            combinations=combinations,
            count=len(combinations)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing CSV: {str(e)}")

@router.post("/process-single", response_model=JobStatus)
async def api_process_single(job_req: JobRequest, background_tasks: BackgroundTasks):
    """Process a single video job"""
    job_id = str(uuid.uuid4())

    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Job queued"
    )
    job_statuses[job_id] = job_status

    background_tasks.add_task(process_single_job_bg, job_id, job_req)

    return job_status

@router.post("/process-batch", response_model=BatchJobResponse)
async def api_process_batch(batch_req: BatchJobRequest, background_tasks: BackgroundTasks):
    """Process batch video jobs"""
    job_id = str(uuid.uuid4())

    # Quick validation
    vids = list_videos(batch_req.video_folder)
    if not vids:
        raise HTTPException(status_code=400, detail="No videos found in folder")

    auds = list_audios(batch_req.audio_folder) if batch_req.audio_folder else []
    rows = batch_req.text_combinations if batch_req.text_combinations else [[]]

    if batch_req.unique_mode and batch_req.unique_amount:
        total = min(batch_req.unique_amount, len(vids) * len(rows) * max(1, len(auds)))
    else:
        total = len(vids) * len(rows) * max(1, len(auds))

    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Batch job queued"
    )
    job_statuses[job_id] = job_status

    background_tasks.add_task(process_batch_jobs_bg, job_id, batch_req)

    return BatchJobResponse(
        job_id=job_id,
        total_jobs=total,
        message=f"Batch job started with {total} videos to process"
    )

@router.get("/status/{job_id}", response_model=JobStatus)
async def api_get_job_status(job_id: str):
    """Get status of a processing job"""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job_statuses[job_id]

@router.get("/jobs", response_model=List[JobStatus])
async def api_list_all_jobs():
    """List all jobs and their statuses"""
    return list(job_statuses.values())

@router.delete("/jobs/{job_id}")
async def api_delete_job(job_id: str):
    """Delete a job from tracking (doesn't stop processing)"""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    del job_statuses[job_id]
    return {"message": "Job deleted", "job_id": job_id}

@router.get("/default-config", response_model=ProcessingConfig)
async def api_get_default_config():
    """Get default processing configuration"""
    cfg = core.default_cfg()
    return ProcessingConfig(**cfg)

# ==================== File Upload Endpoints ====================

@router.post("/upload/video", response_model=FileUploadResponse)
async def api_upload_video(
    file: UploadFile = File(...),
    subfolder: Optional[str] = None
):
    """
    Upload a video file to the videos directory.
    Optionally specify a subfolder to organize videos.
    """
    # Validate file extension
    if not validate_file_extension(file.filename, "video"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video format. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Check file size (read first to get size)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if not validate_file_size(file_size, "video"):
        max_size_mb = MAX_FILE_SIZE["video"] / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )

    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)

    # Determine destination path
    base_path = get_storage_path("videos")
    if subfolder:
        # Sanitize subfolder name
        safe_subfolder = re.sub(r'[^\w\-_]', '_', subfolder)
        destination_dir = base_path / safe_subfolder
    else:
        destination_dir = base_path

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / unique_filename

    # Save file
    saved_size = await save_upload_file(file, destination)

    return FileUploadResponse(
        filename=unique_filename,
        filepath=str(destination),
        size=saved_size,
        message=f"Video uploaded successfully to {destination_dir.name}"
    )

@router.post("/upload/audio", response_model=FileUploadResponse)
async def api_upload_audio(
    file: UploadFile = File(...),
    subfolder: Optional[str] = None
):
    """
    Upload an audio file to the audios directory.
    Optionally specify a subfolder to organize audios.
    """
    # Validate file extension
    if not validate_file_extension(file.filename, "audio"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if not validate_file_size(file_size, "audio"):
        max_size_mb = MAX_FILE_SIZE["audio"] / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )

    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)

    # Determine destination path
    base_path = get_storage_path("audios")
    if subfolder:
        safe_subfolder = re.sub(r'[^\w\-_]', '_', subfolder)
        destination_dir = base_path / safe_subfolder
    else:
        destination_dir = base_path

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / unique_filename

    # Save file
    saved_size = await save_upload_file(file, destination)

    return FileUploadResponse(
        filename=unique_filename,
        filepath=str(destination),
        size=saved_size,
        message=f"Audio uploaded successfully to {destination_dir.name}"
    )

@router.post("/upload/csv", response_model=Dict)
async def api_upload_csv(
    file: UploadFile = File(...),
    save_file: bool = True
):
    """
    Upload and parse a CSV file.
    If save_file=True, saves the CSV to storage.
    Returns both the parsed combinations and file info.
    """
    # Validate file extension
    if not validate_file_extension(file.filename, "csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only CSV files are allowed"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if not validate_file_size(file_size, "csv"):
        max_size_mb = MAX_FILE_SIZE["csv"] / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )

    try:
        # Read and parse CSV
        content = await file.read()
        text_content = content.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text_content))

        combinations = []
        for row in reader:
            if not row:
                continue
            segs = [c.strip() for c in row if c and c.strip()]
            if segs:
                combinations.append(segs)

        # Save file if requested
        saved_filepath = None
        if save_file:
            unique_filename = generate_unique_filename(file.filename)
            destination = get_storage_path("csv") / unique_filename

            # Write the content we already read
            with destination.open("wb") as f:
                f.write(content)

            saved_filepath = str(destination)

        return {
            "combinations": combinations,
            "count": len(combinations),
            "saved": save_file,
            "filepath": saved_filepath,
            "filename": file.filename if not save_file else unique_filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing CSV: {str(e)}")

# ==================== File Management Endpoints ====================

@router.get("/files/videos", response_model=FileListResponse)
async def api_list_video_files(subfolder: Optional[str] = None):
    """
    List all video files with detailed information.
    Optionally filter by subfolder.
    """
    base_path = get_storage_path("videos")

    if subfolder:
        folder_path = base_path / subfolder
    else:
        folder_path = base_path

    if not folder_path.exists():
        return FileListResponse(files=[], count=0)

    files = []
    video_extensions = ALLOWED_VIDEO_EXTENSIONS

    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            files.append(get_file_info(file_path, "video"))

    # Sort by modified date, newest first
    files.sort(key=lambda x: x.modified, reverse=True)

    return FileListResponse(files=files, count=len(files))

@router.get("/files/audios", response_model=FileListResponse)
async def api_list_audio_files(subfolder: Optional[str] = None):
    """
    List all audio files with detailed information.
    Optionally filter by subfolder.
    """
    base_path = get_storage_path("audios")

    if subfolder:
        folder_path = base_path / subfolder
    else:
        folder_path = base_path

    if not folder_path.exists():
        return FileListResponse(files=[], count=0)

    files = []
    audio_extensions = ALLOWED_AUDIO_EXTENSIONS

    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
            files.append(get_file_info(file_path, "audio"))

    # Sort by modified date, newest first
    files.sort(key=lambda x: x.modified, reverse=True)

    return FileListResponse(files=files, count=len(files))

@router.get("/files/csv", response_model=FileListResponse)
async def api_list_csv_files():
    """List all saved CSV files with detailed information."""
    folder_path = get_storage_path("csv")

    if not folder_path.exists():
        return FileListResponse(files=[], count=0)

    files = []
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".csv":
            files.append(get_file_info(file_path, "csv"))

    # Sort by modified date, newest first
    files.sort(key=lambda x: x.modified, reverse=True)

    return FileListResponse(files=files, count=len(files))

@router.delete("/files/delete", response_model=DeleteResponse)
async def api_delete_file(request: DeleteFileRequest):
    """Delete a file by filepath"""
    file_path = Path(request.filepath)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.filepath}")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        file_path.unlink()
        return DeleteResponse(
            message="File deleted successfully",
            filepath=request.filepath
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# ==================== Folder Management Endpoints ====================

@router.get("/folders/{category}", response_model=FolderListResponse)
async def api_list_folders(category: str):
    """
    List all subfolders in a category (videos, audios, output).
    Returns folder information including file count and total size.
    """
    try:
        base_path = get_storage_path(category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: videos, audios, csv, output"
        )

    if not base_path.exists():
        return FolderListResponse(folders=[], count=0)

    folders = []
    for item in base_path.iterdir():
        if item.is_dir():
            folders.append(get_folder_info(item))

    # Sort by name
    folders.sort(key=lambda x: x.name)

    return FolderListResponse(folders=folders, count=len(folders))

@router.post("/folders/create")
async def api_create_folder(request: CreateFolderRequest):
    """Create a new subfolder in a category"""
    try:
        base_path = get_storage_path(request.parent_category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: videos, audios, csv, output"
        )

    # Sanitize folder name
    safe_name = re.sub(r'[^\w\-_]', '_', request.folder_name)

    new_folder = base_path / safe_name

    if new_folder.exists():
        raise HTTPException(status_code=400, detail=f"Folder already exists: {safe_name}")

    try:
        new_folder.mkdir(parents=True, exist_ok=False)
        return {
            "message": "Folder created successfully",
            "folder_name": safe_name,
            "folder_path": str(new_folder)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

@router.post("/files/move")
async def api_move_file(request: MoveFileRequest):
    """Move a file to a different folder"""
    source = Path(request.source_path)
    destination_dir = Path(request.destination_folder)

    if not source.exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {request.source_path}")

    if not source.is_file():
        raise HTTPException(status_code=400, detail="Source path is not a file")

    if not destination_dir.exists():
        destination_dir.mkdir(parents=True, exist_ok=True)

    if not destination_dir.is_dir():
        raise HTTPException(status_code=400, detail="Destination is not a folder")

    destination_file = destination_dir / source.name

    # Check if file already exists at destination
    if destination_file.exists():
        raise HTTPException(
            status_code=400,
            detail=f"File already exists at destination: {destination_file.name}"
        )

    try:
        shutil.move(str(source), str(destination_file))
        return {
            "message": "File moved successfully",
            "source": request.source_path,
            "destination": str(destination_file)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving file: {str(e)}")
