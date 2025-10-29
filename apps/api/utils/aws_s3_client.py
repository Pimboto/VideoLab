"""
AWS S3 Client for file storage operations

This client handles all interactions with AWS S3 and CloudFront.
Uses boto3 with singleton pattern for efficient connection pooling.
"""
import logging
from functools import lru_cache
from typing import Optional
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from core.config import Settings
from core.exceptions import StorageError, FileNotFoundError

logger = logging.getLogger(__name__)


class S3Client:
    """
    AWS S3 client for file operations with CloudFront integration.

    Features:
    - Upload/download/delete files from S3
    - Generate presigned URLs (S3 or CloudFront)
    - List files with pagination
    - Automatic retry and error handling
    """

    def __init__(self, settings: Settings):
        """Initialize S3 client with AWS credentials."""
        self.settings = settings

        # Configure boto3 with retry strategy
        config = Config(
            region_name=settings.aws_region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            }
        )

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config
        )

        self.bucket_name = settings.aws_s3_bucket
        self.cloudfront_domain = settings.aws_cloudfront_domain

        logger.info(f"S3 Client initialized - Bucket: {self.bucket_name}, Region: {settings.aws_region}")

    def upload_file(
        self,
        key: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to S3.

        Args:
            key: S3 object key (path in bucket)
            file_content: File content as bytes
            content_type: MIME type of the file
            metadata: Optional metadata dict

        Returns:
            S3 object key

        Raises:
            StorageError: If upload fails
        """
        try:
            # Prepare extra args
            extra_args = {
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000',  # 1 year cache
            }

            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                **extra_args
            )

            logger.info(f"File uploaded successfully to S3: {key}", extra={"size": len(file_content)})
            return key

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 upload failed: {error_code} - {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to upload file to S3: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to upload file: {str(e)}")

    def upload_file_with_tags(
        self,
        key: str,
        file_content: bytes,
        tags: dict[str, str],
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to S3 with object tags (for lifecycle rules).

        Args:
            key: S3 object key (path in bucket)
            file_content: File content as bytes
            tags: Tags dict for S3 object (e.g., {"purpose": "temporary"})
            content_type: MIME type of the file
            metadata: Optional metadata dict

        Returns:
            S3 object key

        Raises:
            StorageError: If upload fails

        Example:
            >>> client.upload_file_with_tags(
            ...     key="users/123/output/video.mp4",
            ...     file_content=b"...",
            ...     tags={"purpose": "temporary"}
            ... )
        """
        try:
            # Prepare extra args
            extra_args = {
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000',  # 1 year cache
            }

            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

            # Convert tags to URL query string format
            # Format: "key1=value1&key2=value2"
            tag_string = "&".join([f"{k}={v}" for k, v in tags.items()])
            if tag_string:
                extra_args['Tagging'] = tag_string

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                **extra_args
            )

            logger.info(
                f"File uploaded to S3 with tags: {key}",
                extra={"size": len(file_content), "tags": tags}
            )
            return key

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 upload with tags failed: {error_code} - {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to upload file to S3: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to upload file: {str(e)}")

    def download_file(self, key: str) -> bytes:
        """
        Download file from S3.

        Args:
            key: S3 object key

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            file_content = response['Body'].read()
            logger.info(f"File downloaded from S3: {key}", extra={"size": len(file_content)})
            return file_content

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')

            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: {key}")

            logger.error(f"S3 download failed: {error_code} - {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to download file from S3: {error_code}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to download file: {str(e)}")

    def delete_file(self, key: str) -> None:
        """
        Delete file from S3.

        Args:
            key: S3 object key

        Raises:
            StorageError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.info(f"File deleted from S3: {key}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 delete failed: {error_code} - {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to delete file from S3: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error deleting from S3: {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to delete file: {str(e)}")

    def delete_files_batch(self, keys: list[str]) -> tuple[int, int]:
        """
        Delete multiple files from S3 in batch.

        Args:
            keys: List of S3 object keys

        Returns:
            Tuple of (success_count, failure_count)
        """
        if not keys:
            return 0, 0

        try:
            # S3 batch delete (max 1000 per request)
            success_count = 0
            failure_count = 0

            # Process in chunks of 1000
            for i in range(0, len(keys), 1000):
                chunk = keys[i:i + 1000]

                response = self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={
                        'Objects': [{'Key': key} for key in chunk],
                        'Quiet': False
                    }
                )

                success_count += len(response.get('Deleted', []))
                failure_count += len(response.get('Errors', []))

            logger.info(f"Batch delete completed: {success_count} success, {failure_count} failures")
            return success_count, failure_count

        except Exception as e:
            logger.error(f"Batch delete failed: {str(e)}", exc_info=True, extra={"count": len(keys)})
            raise StorageError(f"Failed to batch delete files: {str(e)}")

    def copy_object(self, source_key: str, destination_key: str) -> None:
        """
        Copy object within S3 (without deleting source).

        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key

        Raises:
            FileNotFoundError: If source doesn't exist
            StorageError: If copy fails
        """
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': source_key},
                Key=destination_key
            )

            logger.info(f"File copied in S3: {source_key} → {destination_key}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')

            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"Source file not found: {source_key}")

            logger.error(f"S3 copy failed: {error_code} - {str(e)}", exc_info=True,
                        extra={"source": source_key, "destination": destination_key})
            raise StorageError(f"Failed to copy file in S3: {error_code}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error copying in S3: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to copy file: {str(e)}")

    def move_file(self, source_key: str, destination_key: str) -> None:
        """
        Move file within S3 (copy + delete).

        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key

        Raises:
            FileNotFoundError: If source doesn't exist
            StorageError: If move fails
        """
        try:
            # Copy object
            self.copy_object(source_key, destination_key)

            # Delete original
            self.delete_file(source_key)

            logger.info(f"File moved in S3: {source_key} → {destination_key}")

        except (FileNotFoundError, StorageError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error moving in S3: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to move file: {str(e)}")

    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list[dict]:
        """
        List files in S3 with prefix.

        Args:
            prefix: S3 key prefix to filter
            max_keys: Maximum number of keys to return

        Returns:
            List of file metadata dicts with keys: key, size, last_modified
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })

            logger.info(f"Listed {len(files)} files from S3", extra={"prefix": prefix})
            return files

        except Exception as e:
            logger.error(f"Failed to list S3 files: {str(e)}", exc_info=True, extra={"prefix": prefix})
            raise StorageError(f"Failed to list files: {str(e)}")

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        use_cloudfront: bool = True
    ) -> str:
        """
        Generate presigned URL for file access.

        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds (default: 1 hour)
            use_cloudfront: Use CloudFront URL instead of S3 (default: True)

        Returns:
            Presigned URL (CloudFront or S3)
        """
        try:
            if use_cloudfront and self.cloudfront_domain:
                # CloudFront URL (public, cached)
                url = f"https://{self.cloudfront_domain}/{key}"
                logger.info(f"Generated CloudFront URL: {key}")
                return url
            else:
                # S3 presigned URL (with expiration)
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': key
                    },
                    ExpiresIn=expires_in
                )
                logger.info(f"Generated S3 presigned URL: {key}", extra={"expires_in": expires_in})
                return url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}", exc_info=True, extra={"key": key})
            raise StorageError(f"Failed to generate URL: {str(e)}")

    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            key: S3 object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False
            raise
        except Exception:
            return False


@lru_cache
def get_s3_client() -> S3Client:
    """
    Get cached S3 client instance (singleton).

    Returns:
        S3Client instance
    """
    from core.config import get_settings
    settings = get_settings()
    return S3Client(settings)
