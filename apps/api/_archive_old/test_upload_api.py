"""
Test script for File Upload and Management API endpoints
Run with: python test_upload_api.py
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(title)
        print("=" * 60)

def print_response(response, show_full=False):
    print(f"Status: {response.status_code}")
    if response.status_code < 400:
        data = response.json()
        if show_full:
            print(json.dumps(data, indent=2))
        else:
            print(f"Response: {data}")
    else:
        print(f"Error: {response.text}")

def test_upload_video(video_path, subfolder=None):
    """Test video upload"""
    print_separator("Testing Video Upload")
    print(f"File: {video_path}")
    if subfolder:
        print(f"Subfolder: {subfolder}")

    if not Path(video_path).exists():
        print(f"⚠️  Video file not found: {video_path}")
        return None

    with open(video_path, 'rb') as f:
        files = {'file': (Path(video_path).name, f, 'video/mp4')}
        params = {}
        if subfolder:
            params['subfolder'] = subfolder

        response = requests.post(
            f"{BASE_URL}/api/video-processor/upload/video",
            files=files,
            params=params
        )

    print_response(response)
    return response.json() if response.status_code == 200 else None

def test_upload_audio(audio_path, subfolder=None):
    """Test audio upload"""
    print_separator("Testing Audio Upload")
    print(f"File: {audio_path}")
    if subfolder:
        print(f"Subfolder: {subfolder}")

    if not Path(audio_path).exists():
        print(f"⚠️  Audio file not found: {audio_path}")
        return None

    with open(audio_path, 'rb') as f:
        files = {'file': (Path(audio_path).name, f, 'audio/mp3')}
        params = {}
        if subfolder:
            params['subfolder'] = subfolder

        response = requests.post(
            f"{BASE_URL}/api/video-processor/upload/audio",
            files=files,
            params=params
        )

    print_response(response)
    return response.json() if response.status_code == 200 else None

def test_upload_csv(csv_path, save=True):
    """Test CSV upload and parse"""
    print_separator("Testing CSV Upload")
    print(f"File: {csv_path}")
    print(f"Save to storage: {save}")

    if not Path(csv_path).exists():
        print(f"⚠️  CSV file not found: {csv_path}")
        return None

    with open(csv_path, 'rb') as f:
        files = {'file': (Path(csv_path).name, f, 'text/csv')}
        params = {'save_file': save}

        response = requests.post(
            f"{BASE_URL}/api/video-processor/upload/csv",
            files=files,
            params=params
        )

    print_response(response)
    return response.json() if response.status_code == 200 else None

def test_list_video_files(subfolder=None):
    """Test listing video files"""
    print_separator("Testing List Video Files")
    params = {}
    if subfolder:
        params['subfolder'] = subfolder
        print(f"Subfolder: {subfolder}")

    response = requests.get(
        f"{BASE_URL}/api/video-processor/files/videos",
        params=params
    )

    print_response(response)
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['count']} videos")
        for file in data['files'][:3]:
            size_mb = file['size'] / (1024 * 1024)
            print(f"  - {file['filename']} ({size_mb:.2f} MB)")
        if data['count'] > 3:
            print(f"  ... and {data['count'] - 3} more")
    return response.json() if response.status_code == 200 else None

def test_list_audio_files(subfolder=None):
    """Test listing audio files"""
    print_separator("Testing List Audio Files")
    params = {}
    if subfolder:
        params['subfolder'] = subfolder
        print(f"Subfolder: {subfolder}")

    response = requests.get(
        f"{BASE_URL}/api/video-processor/files/audios",
        params=params
    )

    print_response(response)
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['count']} audios")
        for file in data['files'][:3]:
            size_mb = file['size'] / (1024 * 1024)
            print(f"  - {file['filename']} ({size_mb:.2f} MB)")
        if data['count'] > 3:
            print(f"  ... and {data['count'] - 3} more")
    return response.json() if response.status_code == 200 else None

def test_list_csv_files():
    """Test listing CSV files"""
    print_separator("Testing List CSV Files")

    response = requests.get(f"{BASE_URL}/api/video-processor/files/csv")

    print_response(response)
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['count']} CSV files")
        for file in data['files']:
            size_kb = file['size'] / 1024
            print(f"  - {file['filename']} ({size_kb:.2f} KB)")
    return response.json() if response.status_code == 200 else None

def test_list_folders(category):
    """Test listing folders"""
    print_separator(f"Testing List Folders - {category}")

    response = requests.get(f"{BASE_URL}/api/video-processor/folders/{category}")

    print_response(response)
    if response.status_code == 200:
        data = response.json()
        print(f"\nFound {data['count']} folders")
        for folder in data['folders']:
            size_mb = folder['total_size'] / (1024 * 1024)
            print(f"  - {folder['name']}: {folder['file_count']} files ({size_mb:.2f} MB)")
    return response.json() if response.status_code == 200 else None

def test_create_folder(category, folder_name):
    """Test creating a folder"""
    print_separator("Testing Create Folder")
    print(f"Category: {category}")
    print(f"Folder name: {folder_name}")

    payload = {
        "parent_category": category,
        "folder_name": folder_name
    }

    response = requests.post(
        f"{BASE_URL}/api/video-processor/folders/create",
        json=payload
    )

    print_response(response)
    return response.json() if response.status_code == 200 else None

def test_delete_file(filepath):
    """Test deleting a file"""
    print_separator("Testing Delete File")
    print(f"File: {filepath}")

    payload = {"filepath": filepath}

    response = requests.delete(
        f"{BASE_URL}/api/video-processor/files/delete",
        json=payload
    )

    print_response(response)
    return response.json() if response.status_code == 200 else None

def test_move_file(source_path, destination_folder):
    """Test moving a file"""
    print_separator("Testing Move File")
    print(f"Source: {source_path}")
    print(f"Destination: {destination_folder}")

    payload = {
        "source_path": source_path,
        "destination_folder": destination_folder
    }

    response = requests.post(
        f"{BASE_URL}/api/video-processor/files/move",
        json=payload
    )

    print_response(response)
    return response.json() if response.status_code == 200 else None

def main():
    """Run upload and file management tests"""
    print("=" * 60)
    print("FILE UPLOAD & MANAGEMENT API TEST SUITE")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n✓ API Server is running")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("Make sure the server is running on http://localhost:8000")
        print("Start with: python app.py")
        return

    # Example file paths - UPDATE THESE
    SAMPLE_VIDEO = "D:/Work/video/videos/video (1).mp4"
    SAMPLE_AUDIO = "D:/Work/video/audios/ReelAudio-2148.mp3"
    SAMPLE_CSV = "D:/Work/video/texts.csv"

    print("\n" + "=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    print(f"Sample video: {SAMPLE_VIDEO}")
    print(f"Sample audio: {SAMPLE_AUDIO}")
    print(f"Sample CSV: {SAMPLE_CSV}")
    print("\n⚠️  Update paths in test_upload_api.py if needed")

    # Test folder creation
    test_create_folder("videos", "test_uploads")
    test_create_folder("audios", "test_uploads")

    # Test uploads (uncomment to run actual uploads)
    """
    uploaded_video = test_upload_video(SAMPLE_VIDEO, subfolder="test_uploads")
    uploaded_audio = test_upload_audio(SAMPLE_AUDIO, subfolder="test_uploads")
    uploaded_csv = test_upload_csv(SAMPLE_CSV, save=True)
    """

    # Test file listing
    test_list_video_files()
    test_list_audio_files()
    test_list_csv_files()

    # Test folder listing
    test_list_folders("videos")
    test_list_folders("audios")
    test_list_folders("output")

    # Test file operations (uncomment to test with actual files)
    """
    # Move file test
    if uploaded_video:
        new_folder = "D:/Work/video/videos/moved_files"
        test_move_file(uploaded_video['filepath'], new_folder)

    # Delete file test
    if uploaded_audio:
        test_delete_file(uploaded_audio['filepath'])
    """

    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)
    print("\nTo test actual uploads, uncomment the upload sections in main()")
    print("Visit http://localhost:8000/docs for interactive API docs")

if __name__ == "__main__":
    main()
