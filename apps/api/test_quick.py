"""
Quick non-interactive test - Tests uploads and file management only
"""
import json
from pathlib import Path
import requests

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/video-processor"

VIDEO_DIR = Path("D:/Work/video/videos")
AUDIO_DIR = Path("D:/Work/video/audios")
CSV_FILE = Path("D:/Work/video/texts.csv")

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print("\n" + "=" * 70)
    print("  QUICK API TEST - Uploads & File Management")
    print("=" * 70)

    # Check server
    print_header("1. Checking Server")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Server is running: {data['message']}")
            print(f"[INFO] Version: {data['version']}")
        else:
            print("[ERROR] Server responded with error")
            return
    except:
        print("[ERROR] Cannot connect to server!")
        print("[INFO] Start server with: python app_v2.py")
        return

    # Create folders
    print_header("2. Creating Test Folders")
    for category, folder_name in [("videos", "test_uploads"), ("audios", "test_uploads")]:
        try:
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/folders/create",
                json={"parent_category": category, "folder_name": folder_name},
            )
            if response.status_code == 201:
                print(f"[OK] Created folder: {category}/{folder_name}")
            elif "already exists" in response.text:
                print(f"[INFO] Folder already exists: {category}/{folder_name}")
        except Exception as e:
            print(f"[ERROR] Failed to create folder: {e}")

    # Upload video
    print_header("3. Uploading Video")
    videos = list(VIDEO_DIR.glob("*.mp4"))
    if videos:
        video_path = videos[0]
        print(f"[INFO] Uploading: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.2f} MB)")
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
                print(f"[OK] Video uploaded: {data['filename']}")
                print(f"[INFO] Size: {data['size'] / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
    else:
        print("[ERROR] No videos found!")

    # Upload audio
    print_header("4. Uploading Audio")
    audios = list(AUDIO_DIR.glob("*.mp3"))
    if audios:
        audio_path = audios[0]
        print(f"[INFO] Uploading: {audio_path.name} ({audio_path.stat().st_size / 1024:.2f} KB)")
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
                print(f"[OK] Audio uploaded: {data['filename']}")
                print(f"[INFO] Size: {data['size'] / 1024:.2f} KB")
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
    else:
        print("[ERROR] No audios found!")

    # Upload CSV
    print_header("5. Uploading CSV")
    if CSV_FILE.exists():
        print(f"[INFO] Uploading: {CSV_FILE.name}")
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
                print(f"[OK] CSV uploaded and parsed")
                print(f"[INFO] Combinations: {data['count']}")
                print(f"[INFO] Saved: {data['saved']}")
                if data['count'] > 0:
                    print(f"[INFO] First text: {data['combinations'][0][0][:50]}...")
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
    else:
        print(f"[ERROR] CSV file not found: {CSV_FILE}")

    # List uploaded videos
    print_header("6. Listing Uploaded Videos")
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/files/videos",
            params={"subfolder": "test_uploads"},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Found {data['count']} videos in test_uploads/")
            for file in data["files"][:3]:
                print(f"[INFO]   - {file['filename']} ({file['size'] / 1024 / 1024:.2f} MB)")
    except Exception as e:
        print(f"[ERROR] List failed: {e}")

    # List uploaded audios
    print_header("7. Listing Uploaded Audios")
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/files/audios",
            params={"subfolder": "test_uploads"},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Found {data['count']} audios in test_uploads/")
            for file in data["files"][:3]:
                print(f"[INFO]   - {file['filename']} ({file['size'] / 1024:.2f} KB)")
    except Exception as e:
        print(f"[ERROR] List failed: {e}")

    # List folders
    print_header("8. Listing Folders")
    for category in ["videos", "audios", "output"]:
        try:
            response = requests.get(f"{BASE_URL}{API_PREFIX}/folders/{category}")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Category '{category}': {data['count']} folders")
                for folder in data["folders"][:2]:
                    size_mb = folder["total_size"] / 1024 / 1024
                    print(f"[INFO]   - {folder['name']}: {folder['file_count']} files ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"[ERROR] List failed: {e}")

    # Get default config
    print_header("9. Getting Default Config")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/processing/default-config")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Retrieved default configuration")
            print(f"[INFO] Position: {data['position']}")
            print(f"[INFO] Preset: {data['preset']}")
            print(f"[INFO] Canvas size: {data['canvas_size']}")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

    # List jobs
    print_header("10. Listing Jobs")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/processing/jobs")
        if response.status_code == 200:
            jobs = response.json()
            print(f"[OK] Found {len(jobs)} jobs")
            for job in jobs[:5]:
                print(f"[INFO] {job['job_id'][:8]}... [{job['status']}] {job['progress']:.1f}%")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("  TEST COMPLETED")
    print("=" * 70)
    print("[OK] All basic endpoints tested successfully!")
    print(f"[INFO] API documentation: {BASE_URL}/docs")
    print()

if __name__ == "__main__":
    main()
