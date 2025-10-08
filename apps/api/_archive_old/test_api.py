"""
Test script for Video Processor API endpoints
Run with: python test_api.py
"""
import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test basic health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_list_videos(folder_path):
    """Test listing videos"""
    print(f"\n=== Testing List Videos ===")
    print(f"Folder: {folder_path}")
    response = requests.post(
        f"{BASE_URL}/api/video-processor/list-videos",
        json={"folder_path": folder_path}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} videos")
        for video in data['videos'][:3]:
            print(f"  - {Path(video).name}")
        if data['count'] > 3:
            print(f"  ... and {data['count'] - 3} more")
        return data
    else:
        print(f"Error: {response.text}")
        return None

def test_list_audios(folder_path):
    """Test listing audios"""
    print(f"\n=== Testing List Audios ===")
    print(f"Folder: {folder_path}")
    response = requests.post(
        f"{BASE_URL}/api/video-processor/list-audios",
        json={"folder_path": folder_path}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} audios")
        for audio in data['audios'][:3]:
            print(f"  - {Path(audio).name}")
        if data['count'] > 3:
            print(f"  ... and {data['count'] - 3} more")
        return data
    else:
        print(f"Error: {response.text}")
        return None

def test_parse_csv(csv_path):
    """Test CSV parsing"""
    print(f"\n=== Testing CSV Parsing ===")
    print(f"File: {csv_path}")

    if not Path(csv_path).exists():
        print(f"CSV file not found: {csv_path}")
        return None

    with open(csv_path, 'rb') as f:
        files = {'file': (Path(csv_path).name, f, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/video-processor/parse-csv",
            files=files
        )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} text combinations")
        for i, combo in enumerate(data['combinations'][:2], 1):
            print(f"  Combo {i}: {len(combo)} segments")
            for seg in combo[:2]:
                print(f"    - {seg[:50]}...")
        return data
    else:
        print(f"Error: {response.text}")
        return None

def test_default_config():
    """Test getting default config"""
    print(f"\n=== Testing Default Config ===")
    response = requests.get(f"{BASE_URL}/api/video-processor/default-config")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"Error: {response.text}")
        return None

def test_process_single(video_path, audio_path, output_path):
    """Test single video processing"""
    print(f"\n=== Testing Single Video Processing ===")
    print(f"Video: {Path(video_path).name}")
    print(f"Audio: {Path(audio_path).name if audio_path else 'None'}")

    payload = {
        "video_path": video_path,
        "audio_path": audio_path,
        "text_segments": [
            "Primer segmento de texto 🎬",
            "Segundo segmento 🎵",
            "Tercer segmento ✨"
        ],
        "output_path": output_path,
        "config": {
            "position": "bottom",
            "preset": "bold",
            "fit_mode": "cover"
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/video-processor/process-single",
        json=payload
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        job_id = data['job_id']
        print(f"Job created: {job_id}")
        print(f"Status: {data['status']}")

        # Monitor progress
        return monitor_job(job_id, max_wait=300)
    else:
        print(f"Error: {response.text}")
        return None

def test_process_batch(video_folder, audio_folder, output_folder, unique_mode=True, unique_amount=10):
    """Test batch video processing"""
    print(f"\n=== Testing Batch Video Processing ===")
    print(f"Videos: {video_folder}")
    print(f"Audios: {audio_folder}")
    print(f"Mode: {'Unique' if unique_mode else 'All combinations'}")
    if unique_mode:
        print(f"Amount: {unique_amount}")

    payload = {
        "video_folder": video_folder,
        "audio_folder": audio_folder,
        "text_combinations": [
            ["Primera combinación parte 1", "Primera combinación parte 2"],
            ["Segunda combinación parte 1", "Segunda combinación parte 2"],
            ["Tercera combinación 🎬", "Más texto 🎵"]
        ],
        "output_folder": output_folder,
        "unique_mode": unique_mode,
        "unique_amount": unique_amount if unique_mode else None,
        "config": {
            "position": "center",
            "preset": "bold"
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/video-processor/process-batch",
        json=payload
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        job_id = data['job_id']
        print(f"Batch job created: {job_id}")
        print(f"Total jobs: {data['total_jobs']}")
        print(f"Message: {data['message']}")

        # Monitor progress (don't wait for completion in test)
        return monitor_job(job_id, max_wait=60, check_interval=5)
    else:
        print(f"Error: {response.text}")
        return None

def monitor_job(job_id, max_wait=300, check_interval=2):
    """Monitor job progress"""
    print(f"\n=== Monitoring Job: {job_id} ===")

    start_time = time.time()
    last_progress = -1

    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/video-processor/status/{job_id}")

        if response.status_code == 200:
            data = response.json()
            status = data['status']
            progress = data['progress']
            message = data['message']

            # Only print if progress changed
            if progress != last_progress:
                print(f"[{status.upper()}] {progress:.1f}% - {message}")
                last_progress = progress

            if status == "completed":
                print(f"\n✓ Job completed!")
                print(f"Output files ({len(data['output_files'])}):")
                for f in data['output_files'][:5]:
                    print(f"  - {Path(f).name}")
                if len(data['output_files']) > 5:
                    print(f"  ... and {len(data['output_files']) - 5} more")
                return data

            elif status == "failed":
                print(f"\n✗ Job failed: {message}")
                return None

            time.sleep(check_interval)
        else:
            print(f"Error checking status: {response.text}")
            return None

    print(f"\n⚠ Timeout after {max_wait}s (job may still be processing)")
    return None

def test_list_jobs():
    """Test listing all jobs"""
    print(f"\n=== Testing List All Jobs ===")
    response = requests.get(f"{BASE_URL}/api/video-processor/jobs")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        jobs = response.json()
        print(f"Total jobs: {len(jobs)}")
        for job in jobs[:3]:
            print(f"  - {job['job_id'][:8]}... [{job['status']}] {job['progress']:.1f}%")
        return jobs
    else:
        print(f"Error: {response.text}")
        return None

def main():
    """Run tests"""
    print("=" * 60)
    print("VIDEO PROCESSOR API TEST SUITE")
    print("=" * 60)

    # Check if server is running
    try:
        test_health()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("Make sure the server is running on http://localhost:8000")
        print("Start with: python app.py")
        return

    # Get default config
    test_default_config()

    # Example paths - CHANGE THESE TO YOUR ACTUAL PATHS
    VIDEO_FOLDER = "D:/Work/video/videos"
    AUDIO_FOLDER = "D:/Work/video/audios"
    CSV_FILE = "D:/Work/video/texts.csv"
    OUTPUT_FOLDER = "D:/Work/video/output_test"

    print("\n" + "=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    print(f"Video folder: {VIDEO_FOLDER}")
    print(f"Audio folder: {AUDIO_FOLDER}")
    print(f"CSV file: {CSV_FILE}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print("\n⚠️  Update paths in test_api.py if needed")

    # Test listing
    videos = test_list_videos(VIDEO_FOLDER)
    audios = test_list_audios(AUDIO_FOLDER)

    if not videos or videos['count'] == 0:
        print(f"\n⚠️  No videos found in {VIDEO_FOLDER}")
        print("Update VIDEO_FOLDER in test_api.py")
        return

    # Test CSV parsing
    if Path(CSV_FILE).exists():
        test_parse_csv(CSV_FILE)
    else:
        print(f"\n⚠️  CSV file not found: {CSV_FILE}")

    # Test single processing (if you want to test)
    # Uncomment to run:
    """
    if videos and videos['count'] > 0:
        video_path = videos['videos'][0]
        audio_path = audios['audios'][0] if audios and audios['count'] > 0 else None
        output_path = f"{OUTPUT_FOLDER}/test_single_output.mp4"
        test_process_single(video_path, audio_path, output_path)
    """

    # Test batch processing (small batch for testing)
    # Uncomment to run:
    """
    if videos and videos['count'] > 0:
        test_process_batch(
            VIDEO_FOLDER,
            AUDIO_FOLDER if audios and audios['count'] > 0 else None,
            OUTPUT_FOLDER,
            unique_mode=True,
            unique_amount=5  # Small amount for testing
        )
    """

    # List all jobs
    test_list_jobs()

    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)
    print("\nTo run actual processing, uncomment the test functions in main()")
    print("Visit http://localhost:8000/docs for interactive API docs")

if __name__ == "__main__":
    main()
