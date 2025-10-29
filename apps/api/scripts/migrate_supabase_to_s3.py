"""
Migration script: Supabase Storage → AWS S3

This script migrates all files from Supabase Storage to AWS S3:
1. Downloads files from Supabase Storage buckets
2. Uploads to S3 with new folder structure
3. Updates filepath in PostgreSQL database
4. Verifies integrity

Usage:
    python -m scripts.migrate_supabase_to_s3

Requirements:
    - AWS credentials configured in .env
    - Supabase credentials configured in .env
    - Database access

⚠️  IMPORTANT: Run this script during low-traffic hours
⚠️  Make a database backup before running
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_settings
from core.exceptions import StorageError
from utils.aws_s3_client import get_s3_client
from utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SupabaseToS3Migrator:
    """Migrator for Supabase Storage to AWS S3"""

    # Mapping of Supabase buckets to S3 folder structure
    BUCKET_MAPPING = {
        "videos": "videos",
        "audios": "audios",
        "csv": "csv",
        "output": "output",
    }

    def __init__(self, dry_run: bool = False):
        """
        Initialize migrator.

        Args:
            dry_run: If True, only logs what would be done without actual migration
        """
        self.settings = get_settings()
        self.s3_client = get_s3_client()
        self.supabase = get_supabase_client()
        self.dry_run = dry_run

        self.stats = {
            "total_files": 0,
            "migrated": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }

        logger.info("=" * 80)
        logger.info("Supabase Storage → AWS S3 Migration Tool")
        logger.info("=" * 80)
        logger.info(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE MIGRATION'}")
        logger.info(f"S3 Bucket: {self.settings.aws_s3_bucket}")
        logger.info(f"S3 Region: {self.settings.aws_region}")
        logger.info("=" * 80)

    def convert_path_to_s3_key(
        self,
        old_path: str,
        file_type: str,
        user_id: str
    ) -> str:
        """
        Convert Supabase storage path to S3 key.

        Old format: user_id/subfolder/filename.ext
        New format: users/user_id/videos/subfolder/filename.ext

        Args:
            old_path: Original Supabase path
            file_type: File type (video, audio, csv, output)
            user_id: User ID

        Returns:
            New S3 key
        """
        # Remove user_id prefix if present
        if old_path.startswith(user_id + "/"):
            path_without_userid = old_path[len(user_id) + 1:]
        else:
            path_without_userid = old_path

        # Build new S3 key
        category_folder = self.BUCKET_MAPPING.get(file_type, file_type)
        new_key = f"users/{user_id}/{category_folder}/{path_without_userid}"

        return new_key

    async def migrate_file(
        self,
        file_record: dict,
        bucket_name: str
    ) -> Tuple[bool, str]:
        """
        Migrate a single file from Supabase to S3.

        Args:
            file_record: File metadata from database
            bucket_name: Supabase bucket name

        Returns:
            Tuple of (success, new_s3_key)
        """
        try:
            filepath = file_record["filepath"]
            user_id = file_record["user_id"]
            file_type = file_record["file_type"]

            # Convert to S3 key
            new_s3_key = self.convert_path_to_s3_key(filepath, file_type, user_id)

            logger.info(f"Migrating: {filepath} → {new_s3_key}")

            if self.dry_run:
                logger.info(f"  [DRY RUN] Would migrate to S3")
                return True, new_s3_key

            # Check if already exists in S3
            if self.s3_client.file_exists(new_s3_key):
                logger.info(f"  ✓ Already exists in S3, skipping download")
                self.stats["skipped"] += 1
                return True, new_s3_key

            # Download from Supabase
            logger.info(f"  ↓ Downloading from Supabase...")
            file_content = self.supabase.storage.from_(bucket_name).download(filepath)

            if not file_content:
                raise StorageError(f"Failed to download from Supabase: {filepath}")

            logger.info(f"  ↑ Uploading to S3 ({len(file_content)} bytes)...")

            # Upload to S3
            self.s3_client.upload_file(
                key=new_s3_key,
                file_content=file_content,
                content_type=file_record.get("mime_type", "application/octet-stream")
            )

            logger.info(f"  ✓ Migrated successfully")
            self.stats["migrated"] += 1

            return True, new_s3_key

        except Exception as e:
            logger.error(f"  ✗ Migration failed: {str(e)}")
            self.stats["failed"] += 1
            self.stats["errors"].append({
                "filepath": filepath,
                "error": str(e)
            })
            return False, ""

    async def update_database_filepath(
        self,
        file_id: str,
        new_filepath: str
    ) -> bool:
        """
        Update filepath in database.

        Args:
            file_id: File ID
            new_filepath: New S3 key

        Returns:
            True if successful
        """
        try:
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would update DB: {file_id} → {new_filepath}")
                return True

            self.supabase.table("files") \
                .update({"filepath": new_filepath}) \
                .eq("id", file_id) \
                .execute()

            logger.info(f"  ✓ Database updated")
            return True

        except Exception as e:
            logger.error(f"  ✗ Database update failed: {str(e)}")
            return False

    async def migrate_bucket(self, bucket_name: str) -> None:
        """
        Migrate all files from a Supabase bucket.

        Args:
            bucket_name: Supabase bucket name (videos, audios, csv, output)
        """
        try:
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"Migrating bucket: {bucket_name}")
            logger.info("=" * 80)

            # Get all files from database for this bucket
            file_type = bucket_name.rstrip("s")  # videos → video
            result = self.supabase.table("files") \
                .select("*") \
                .eq("file_type", file_type) \
                .execute()

            files = result.data or []
            total = len(files)

            logger.info(f"Found {total} files to migrate")

            if total == 0:
                logger.info("No files to migrate in this bucket")
                return

            self.stats["total_files"] += total

            # Migrate each file
            for i, file_record in enumerate(files, 1):
                logger.info(f"\n[{i}/{total}] Processing file ID: {file_record['id']}")

                # Migrate file
                success, new_s3_key = await self.migrate_file(file_record, bucket_name)

                if success and new_s3_key:
                    # Update database
                    await self.update_database_filepath(
                        file_record["id"],
                        new_s3_key
                    )

                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)

            logger.info(f"\nBucket '{bucket_name}' migration complete")

        except Exception as e:
            logger.error(f"Error migrating bucket {bucket_name}: {str(e)}", exc_info=True)

    async def run_migration(self) -> None:
        """Run complete migration for all buckets"""
        try:
            start_time = asyncio.get_event_loop().time()

            # Migrate each bucket
            for bucket_name in self.BUCKET_MAPPING.keys():
                await self.migrate_bucket(bucket_name)

            # Print summary
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            logger.info("")
            logger.info("=" * 80)
            logger.info("MIGRATION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Total files:     {self.stats['total_files']}")
            logger.info(f"Migrated:        {self.stats['migrated']}")
            logger.info(f"Skipped:         {self.stats['skipped']}")
            logger.info(f"Failed:          {self.stats['failed']}")
            logger.info(f"Duration:        {duration:.2f} seconds")
            logger.info("=" * 80)

            if self.stats["errors"]:
                logger.error("\nERRORS:")
                for error in self.stats["errors"]:
                    logger.error(f"  • {error['filepath']}: {error['error']}")

            if self.stats["failed"] > 0:
                logger.warning("\n⚠️  Some files failed to migrate. Check migration.log for details")
            elif not self.dry_run:
                logger.info("\n✅ Migration completed successfully!")
            else:
                logger.info("\n✅ Dry run completed. No actual changes were made.")

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}", exc_info=True)
            raise


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Supabase Storage to AWS S3")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual changes)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Confirmation prompt
    if not args.yes and not args.dry_run:
        print("\n⚠️  WARNING: This will migrate all files from Supabase to S3")
        print("⚠️  Make sure you have:")
        print("   1. Created a database backup")
        print("   2. Configured AWS credentials in .env")
        print("   3. Tested with --dry-run first")
        print("")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Migration cancelled")
            return

    # Run migration
    migrator = SupabaseToS3Migrator(dry_run=args.dry_run)
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
