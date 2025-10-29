"""
CSV Service

Handles CSV file uploads and parsing:
- CSV validation and parsing
- Text combinations extraction
- File metadata creation
"""
import csv
import io
import logging
from typing import Optional

from fastapi import UploadFile

from core.config import Settings
from core.exceptions import (
    FileSizeLimitError,
    InvalidFileTypeError,
    StorageError,
)
from models.file import FileCreate
from schemas.file_schemas import (
    FileInfo,
    FileListResponse,
)
from schemas.processing_schemas import TextCombinationsResponse
from services.storage_service import StorageService
from supabase import Client


logger = logging.getLogger(__name__)


class CSVService:
    """Service for CSV file operations"""

    def __init__(
        self,
        settings: Settings,
        storage_service: StorageService,
        supabase: Client
    ):
        self.settings = settings
        self.storage = storage_service
        self.supabase = supabase

    async def _create_file_metadata(
        self,
        user_id: str,
        filename: str,
        filepath: str,
        file_type: str,
        size_bytes: int,
        mime_type: Optional[str] = None,
        subfolder: Optional[str] = None,
        original_filename: Optional[str] = None,
        additional_metadata: Optional[dict] = None
    ) -> dict:
        """Create file metadata record in database"""
        try:
            # Store original filename and any additional metadata
            metadata = {}
            if original_filename:
                metadata["original_filename"] = original_filename

            # Merge additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)

            # Only set metadata if we have any
            file_metadata = metadata if metadata else None

            file_data = FileCreate(
                user_id=user_id,
                filename=filename,
                filepath=filepath,
                file_type=file_type,
                size_bytes=size_bytes,
                mime_type=mime_type,
                subfolder=subfolder,
                metadata=file_metadata
            )

            result = self.supabase.table("files").insert(file_data.model_dump()).execute()

            if not result.data or len(result.data) == 0:
                raise StorageError("Failed to create file metadata in database")

            return result.data[0]
        except Exception as e:
            raise StorageError(f"Failed to save file metadata: {str(e)}")

    async def upload_csv(
        self,
        user_id: str,
        file: UploadFile,
        save_file: bool = True
    ) -> TextCombinationsResponse:
        """
        Upload and parse a CSV file.

        Validates CSV file, parses rows into text combinations,
        and optionally saves to S3 storage.

        Args:
            user_id: User ID
            file: CSV file to upload
            save_file: Whether to save file to storage (default: True)

        Returns:
            TextCombinationsResponse with parsed combinations and metadata
        """
        # Validate extension
        if not self.storage.validate_file_extension(file.filename, "csv"):
            raise InvalidFileTypeError(
                "Invalid file format. Only CSV files are allowed",
                details={"allowed_extensions": list(self.settings.csv_extensions)},
            )

        # Get file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # Validate size
        if not self.storage.validate_file_size(file_size, "csv"):
            max_mb = self.settings.max_csv_size / (1024 * 1024)
            raise FileSizeLimitError(
                f"File too large. Maximum size: {max_mb:.0f}MB",
                details={"max_size": self.settings.max_csv_size},
            )

        # Read and parse CSV
        content = await file.read()
        text_content = content.decode("utf-8-sig")
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
        filename = file.filename

        if save_file:
            # Create new file-like object from content (file was already read)
            file.file = io.BytesIO(content)
            file.file.seek(0)

            # Upload to AWS S3 (NO unique_filename param - uses (1), (2) for duplicates)
            storage_path, saved_size = await self.storage.upload_file(
                user_id=user_id,
                category="csv",
                upload_file=file,
                subfolder=None
            )

            # Extract filename from storage path
            uploaded_filename = storage_path.split("/")[-1]

            # Create metadata record
            await self._create_file_metadata(
                user_id=user_id,
                filename=uploaded_filename,
                filepath=storage_path,
                file_type="csv",
                size_bytes=saved_size,
                mime_type=file.content_type,
                subfolder=None,
                original_filename=file.filename
            )

            saved_filepath = storage_path
            filename = uploaded_filename

        return TextCombinationsResponse(
            combinations=combinations,
            count=len(combinations),
            saved=save_file,
            filepath=saved_filepath,
            filename=filename,
        )

    async def list_csvs(
        self,
        user_id: str
    ) -> FileListResponse:
        """
        List all CSV files for a user from database.

        Args:
            user_id: User ID

        Returns:
            FileListResponse with list of CSV files
        """
        try:
            result = self.supabase.table("files") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("file_type", "csv") \
                .order("created_at", desc=True) \
                .execute()

            files = []
            for file_data in result.data:
                # Parse metadata if it's a JSON string
                metadata = file_data.get("metadata")
                if metadata and isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = None

                files.append(FileInfo(
                    filename=file_data["filename"],
                    filepath=file_data["filepath"],
                    size=file_data["size_bytes"],
                    modified=file_data["created_at"],
                    file_type="csv",
                    metadata=metadata
                ))

            return FileListResponse(files=files, count=len(files))
        except Exception as e:
            raise StorageError(f"Failed to list CSVs: {str(e)}")
