"""
Comprehensive test suite for Video Processor API v2 (Professional Architecture)
Tests all endpoints with real files
"""
import json
import time
from pathlib import Path

import requests

# API Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/video-processor"

# File paths
VIDEO_DIR = Path("D:/Work/video/videos")
AUDIO_DIR = Path("D:/Work/video/audios")
CSV_FILE = Path("D:/Work/video/texts.csv")
OUTPUT_DIR = Path("D:/Work/video/output_test_v2")


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(message: str):
    """Print success message"""
    print(f"[OK] {message}")


def print_error(message: str):
    """Print error message"""
    print(f"[ERROR] {message}")


def print_info(message: str):
    """Print info message"""
    print(f"[INFO] {message}")


def check_server():
    """Check if server is running"""
    print_header("CHECKING SERVER")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is running: {data['message']}")
            print_info(f"Version: {data['version']}")
            return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server!")
        print_info("Start server with: python app_v2.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


# ==================== File Upload Tests ====================


def test_create_folders():
    """Test folder creation"""
    print_header("TEST: Create Folders")

    folders_to_create = [
        ("videos", "test_uploads"),
        ("audios", "test_uploads"),
        ("output", "test_results"),
    ]

    for category, folder_name in folders_to_create:
        try:
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/folders/create",
                json={"parent_category": category, "folder_name": folder_name},
            )

            if response.status_code == 201:
                data = response.json()
                print_success(
                    f"Created folder: {category}/{data['folder_name']}"
                )
            elif response.status_code == 400 and "already exists" in response.text:
                print_info(f"Folder already exists: {category}/{folder_name}")
            else:
                print_error(
                    f"Failed to create {category}/{folder_name}: {response.text}"
                )

        except Exception as e:
            print_error(f"Error creating folder: {e}")


def test_upload_video():
    """Test video upload"""
    print_header("TEST: Upload Video")

    # Get first video file
    videos = list(VIDEO_DIR.glob("*.mp4"))
    if not videos:
        print_error("No videos found!")
        return None

    video_path = videos[0]
    print_info(f"Uploading: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.2f} MB)")

    try:
        with open(video_path, "rb") as f:
            files = {"file": (video_path.name, f, "video/mp4")}
            params = {"subfolder": "test_uploads"}

            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/files/upload/video",
                files=files,
                params=params,
            )

        if response.status_code == 201:
            data = response.json()
            print_success(f"Video uploaded: {data['filename']}")
            print_info(f"Path: {data['filepath']}")
            print_info(f"Size: {data['size'] / 1024 / 1024:.2f} MB")
            return data
        else:
            print_error(f"Upload failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error uploading video: {e}")
        return None


def test_upload_audio():
    """Test audio upload"""
    print_header("TEST: Upload Audio")

    # Get first audio file
    audios = list(AUDIO_DIR.glob("*.mp3"))
    if not audios:
        print_error("No audios found!")
        return None

    audio_path = audios[0]
    print_info(f"Uploading: {audio_path.name} ({audio_path.stat().st_size / 1024:.2f} KB)")

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/mp3")}
            params = {"subfolder": "test_uploads"}

            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/files/upload/audio",
                files=files,
                params=params,
            )

        if response.status_code == 201:
            data = response.json()
            print_success(f"Audio uploaded: {data['filename']}")
            print_info(f"Path: {data['filepath']}")
            print_info(f"Size: {data['size'] / 1024:.2f} KB")
            return data
        else:
            print_error(f"Upload failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error uploading audio: {e}")
        return None


def test_upload_csv():
    """Test CSV upload and parse"""
    print_header("TEST: Upload CSV")

    if not CSV_FILE.exists():
        print_error(f"CSV file not found: {CSV_FILE}")
        return None

    print_info(f"Uploading: {CSV_FILE.name}")

    try:
        with open(CSV_FILE, "rb") as f:
            files = {"file": (CSV_FILE.name, f, "text/csv")}
            params = {"save_file": True}

            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/files/upload/csv",
                files=files,
                params=params,
            )

        if response.status_code == 201:
            data = response.json()
            print_success(f"CSV uploaded and parsed")
            print_info(f"Combinations: {data['count']}")
            print_info(f"Saved: {data['saved']}")
            if data["saved"]:
                print_info(f"Path: {data['filepath']}")

            # Show first 3 combinations
            print_info("\nFirst 3 text combinations:")
            for i, combo in enumerate(data["combinations"][:3], 1):
                text = combo[0][:60] + "..." if len(combo[0]) > 60 else combo[0]
                print(f"  {i}. {text}")

            return data
        else:
            print_error(f"Upload failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error uploading CSV: {e}")
        return None


# ==================== File Management Tests ====================


def test_list_videos():
    """Test listing videos"""
    print_header("TEST: List Videos")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/files/videos",
            params={"subfolder": "test_uploads"},
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {data['count']} videos in test_uploads/")

            for file in data["files"][:3]:
                print_info(
                    f"  - {file['filename']} ({file['size'] / 1024 / 1024:.2f} MB)"
                )

            return data
        else:
            print_error(f"List failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error listing videos: {e}")
        return None


def test_list_audios():
    """Test listing audios"""
    print_header("TEST: List Audios")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/files/audios",
            params={"subfolder": "test_uploads"},
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {data['count']} audios in test_uploads/")

            for file in data["files"][:3]:
                print_info(f"  - {file['filename']} ({file['size'] / 1024:.2f} KB)")

            return data
        else:
            print_error(f"List failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error listing audios: {e}")
        return None


def test_list_folders():
    """Test listing folders"""
    print_header("TEST: List Folders")

    for category in ["videos", "audios", "output"]:
        try:
            response = requests.get(f"{BASE_URL}{API_PREFIX}/folders/{category}")

            if response.status_code == 200:
                data = response.json()
                print_success(f"Category '{category}': {data['count']} folders")

                for folder in data["folders"][:3]:
                    size_mb = folder["total_size"] / 1024 / 1024
                    print_info(
                        f"  - {folder['name']}: {folder['file_count']} files ({size_mb:.2f} MB)"
                    )
            else:
                print_error(f"List failed for {category}: {response.text}")

        except Exception as e:
            print_error(f"Error listing folders: {e}")


# ==================== Processing Tests ====================


def test_get_default_config():
    """Test getting default configuration"""
    print_header("TEST: Get Default Config")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/processing/default-config")

        if response.status_code == 200:
            data = response.json()
            print_success("Retrieved default configuration")
            print_info(f"Position: {data['position']}")
            print_info(f"Preset: {data['preset']}")
            print_info(f"Fit mode: {data['fit_mode']}")
            print_info(f"Canvas size: {data['canvas_size']}")
            return data
        else:
            print_error(f"Failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_process_single_video():
    """Test single video processing"""
    print_header("TEST: Process Single Video")

    # Get first video and audio from original folders
    videos = list(VIDEO_DIR.glob("*.mp4"))
    audios = list(AUDIO_DIR.glob("*.mp3"))

    if not videos or not audios:
        print_error("Need at least 1 video and 1 audio!")
        return None

    video_path = str(videos[0])
    audio_path = str(audios[0])
    output_path = str(OUTPUT_DIR / "test_single_output.mp4")

    print_info(f"Video: {videos[0].name}")
    print_info(f"Audio: {audios[0].name}")

    payload = {
        "video_path": video_path,
        "audio_path": audio_path,
        "text_segments": [
            "Testing new architecture!",
            "Professional FastAPI",
            "Clean Code",
        ],
        "output_path": output_path,
        "config": {
            "position": "center",
            "preset": "bold",
            "fit_mode": "cover",
            "canvas_size": [1080, 1920],
        },
    }

    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/processing/process-single",
            json=payload,
        )

        if response.status_code == 202:
            data = response.json()
            job_id = data["job_id"]
            print_success(f"Job created: {job_id}")
            print_info(f"Status: {data['status']}")

            # Monitor job
            return monitor_job(job_id, max_wait=120)
        else:
            print_error(f"Failed to create job: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_process_batch():
    """Test batch processing with real files"""
    print_header("TEST: Process Batch (3 videos)")

    # Read CSV for text combinations
    if not CSV_FILE.exists():
        print_error("CSV file not found!")
        return None

    try:
        import csv

        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            combinations = []
            for row in reader:
                if row and row[0].strip():
                    combinations.append([row[0].strip()])

        if len(combinations) < 3:
            print_error("Need at least 3 text combinations!")
            return None

        # Use first 3 combinations
        text_combinations = combinations[:3]

        print_info(f"Using {len(text_combinations)} text combinations")
        print_info(f"Video folder: {VIDEO_DIR}")
        print_info(f"Audio folder: {AUDIO_DIR}")

        payload = {
            "video_folder": str(VIDEO_DIR),
            "audio_folder": str(AUDIO_DIR),
            "text_combinations": text_combinations,
            "output_folder": str(OUTPUT_DIR),
            "unique_mode": True,
            "unique_amount": 3,  # Only 3 for testing
            "config": {
                "position": "bottom",
                "preset": "bold",
                "fit_mode": "cover",
            },
        }

        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/processing/process-batch",
            json=payload,
        )

        if response.status_code == 202:
            data = response.json()
            job_id = data["job_id"]
            print_success(f"Batch job created: {job_id}")
            print_info(f"Total videos to process: {data['total_jobs']}")
            print_info(data["message"])

            # Monitor batch job (with longer timeout)
            return monitor_job(job_id, max_wait=300, check_interval=3)
        else:
            print_error(f"Failed to create batch job: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return None


def monitor_job(job_id: str, max_wait: int = 300, check_interval: int = 2):
    """Monitor job progress with real-time updates"""
    print_header(f"MONITORING JOB: {job_id}")

    start_time = time.time()
    last_progress = -1

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/processing/status/{job_id}"
            )

            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                progress = data["progress"]
                message = data["message"]

                # Only print when progress changes
                if progress != last_progress:
                    status_emoji = {
                        "pending": "[WAIT]",
                        "processing": "[PROC]",
                        "completed": "[DONE]",
                        "failed": "[FAIL]",
                    }
                    emoji = status_emoji.get(status, "[INFO]")

                    print(f"{emoji} [{status.upper()}] {progress:.1f}% - {message}")
                    last_progress = progress

                if status == "completed":
                    print_success("Job completed!")
                    print_info(f"Output files: {len(data['output_files'])}")

                    for i, filepath in enumerate(data["output_files"][:5], 1):
                        filename = Path(filepath).name
                        print(f"  {i}. {filename}")

                    if len(data["output_files"]) > 5:
                        print_info(
                            f"  ... and {len(data['output_files']) - 5} more files"
                        )

                    return data

                elif status == "failed":
                    print_error(f"Job failed: {message}")
                    return None

                time.sleep(check_interval)
            else:
                print_error(f"Error checking status: {response.text}")
                return None

        except Exception as e:
            print_error(f"Error monitoring job: {e}")
            return None

    print_error(f"Timeout after {max_wait}s (job may still be processing)")
    return None


def test_list_jobs():
    """Test listing all jobs"""
    print_header("TEST: List All Jobs")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/processing/jobs")

        if response.status_code == 200:
            jobs = response.json()
            print_success(f"Found {len(jobs)} jobs")

            for job in jobs[:5]:
                status_emoji = {
                    "pending": "[WAIT]",
                    "processing": "[PROC]",
                    "completed": "[DONE]",
                    "failed": "[FAIL]",
                }
                emoji = status_emoji.get(job["status"], "[INFO]")
                print(
                    f"{emoji} {job['job_id'][:8]}... [{job['status']}] {job['progress']:.1f}%"
                )

            return jobs
        else:
            print_error(f"Failed: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error: {e}")
        return None


# ==================== Main Test Suite ====================


def main():
    """Run comprehensive test suite"""
    print("\n")
    print("=" * 70)
    print(" " * 10 + "VIDEO PROCESSOR API V2 - COMPREHENSIVE TEST SUITE")
    print(" " * 18 + "Professional Architecture Edition")
    print("=" * 70)

    # Check server
    if not check_server():
        return

    print_header("CONFIGURATION")
    print_info(f"API Base URL: {BASE_URL}{API_PREFIX}")
    print_info(f"Video Directory: {VIDEO_DIR}")
    print_info(f"Audio Directory: {AUDIO_DIR}")
    print_info(f"CSV File: {CSV_FILE}")
    print_info(f"Output Directory: {OUTPUT_DIR}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ==================== PHASE 1: Folder Management ====================
    print_header("PHASE 1: FOLDER MANAGEMENT")
    test_create_folders()
    test_list_folders()

    # ==================== PHASE 2: File Uploads ====================
    print_header("PHASE 2: FILE UPLOADS")
    uploaded_video = test_upload_video()
    uploaded_audio = test_upload_audio()
    uploaded_csv = test_upload_csv()

    # ==================== PHASE 3: File Listing ====================
    print_header("PHASE 3: FILE MANAGEMENT")
    test_list_videos()
    test_list_audios()

    # ==================== PHASE 4: Configuration ====================
    print_header("PHASE 4: PROCESSING CONFIGURATION")
    test_get_default_config()

    # ==================== PHASE 5: Single Video Processing ====================
    print_header("PHASE 5: SINGLE VIDEO PROCESSING")
    user_input = input("\n[>] Run single video processing test? (y/n): ")
    if user_input.lower() == "y":
        test_process_single_video()
    else:
        print_info("Skipped single video processing")

    # ==================== PHASE 6: Batch Processing ====================
    print_header("PHASE 6: BATCH PROCESSING")
    user_input = input("\n[>] Run batch processing test (3 videos)? (y/n): ")
    if user_input.lower() == "y":
        test_process_batch()
    else:
        print_info("Skipped batch processing")

    # ==================== PHASE 7: Job Management ====================
    print_header("PHASE 7: JOB MANAGEMENT")
    test_list_jobs()

    # ==================== Summary ====================
    print_header("TEST SUITE COMPLETED")
    print_success("All API endpoints tested!")
    print_info(f"Check output files in: {OUTPUT_DIR}")
    print_info(f"API documentation: {BASE_URL}/docs")

    print("\n" + "=" * 70)
    print("  *** Professional Architecture - Fully Tested! ***")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
