"""
Migration script to move existing images from filesystem to GridFS.
Run this once to migrate existing uploads.
"""

import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from PIL import Image
import hashlib
import io
from datetime import datetime, timezone

# Configuration
UPLOAD_DIR = Path("/app/backend/uploads")
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'troa_db')

# Content type mapping
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp"
}


async def migrate_images():
    """Migrate all images from filesystem to GridFS"""
    
    if not UPLOAD_DIR.exists():
        print(f"Upload directory not found: {UPLOAD_DIR}")
        return
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name="images")
    
    # Get list of existing files in GridFS
    cursor = bucket.find({})
    existing_files = {f.filename async for f in cursor}
    
    # Get all image files in uploads directory
    image_files = list(UPLOAD_DIR.glob("*"))
    image_files = [f for f in image_files if f.suffix.lower() in CONTENT_TYPES]
    
    print(f"Found {len(image_files)} images in filesystem")
    print(f"Found {len(existing_files)} images already in GridFS")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for image_path in image_files:
        filename = image_path.name
        
        # Skip if already in GridFS
        if filename in existing_files:
            print(f"⏭️  Skipping (already exists): {filename}")
            skipped += 1
            continue
        
        try:
            # Read file content
            with open(image_path, "rb") as f:
                content = f.read()
            
            # Validate image
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()
            except Exception as e:
                print(f"❌ Invalid image file: {filename} - {e}")
                errors += 1
                continue
            
            # Calculate ETag
            etag = hashlib.md5(content).hexdigest()
            file_ext = image_path.suffix.lower()
            
            # Upload to GridFS
            await bucket.upload_from_stream(
                filename,
                io.BytesIO(content),
                metadata={
                    "content_type": CONTENT_TYPES.get(file_ext, "application/octet-stream"),
                    "original_filename": filename,
                    "etag": etag,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "size": len(content),
                    "migrated_from_filesystem": True
                }
            )
            
            print(f"✅ Migrated: {filename} ({len(content)} bytes)")
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating {filename}: {e}")
            errors += 1
    
    client.close()
    
    print("\n" + "=" * 50)
    print("Migration Summary:")
    print(f"  ✅ Migrated: {migrated}")
    print(f"  ⏭️  Skipped (already in GridFS): {skipped}")
    print(f"  ❌ Errors: {errors}")
    print("=" * 50)
    
    return {
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors
    }


if __name__ == "__main__":
    print("Starting image migration to GridFS...")
    print(f"Source: {UPLOAD_DIR}")
    print(f"Target: MongoDB GridFS ({MONGO_URL}/{DB_NAME})")
    print()
    
    asyncio.run(migrate_images())
