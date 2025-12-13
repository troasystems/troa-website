"""
GridFS-based image storage for production environments.
Images are stored in MongoDB GridFS for persistence across pod restarts.
Browser caching is enabled via Cache-Control and ETag headers.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from PIL import Image
import hashlib
import uuid
import io
import os
import logging
from datetime import datetime, timezone
from auth import require_admin

logger = logging.getLogger(__name__)

gridfs_router = APIRouter(prefix="/upload")

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Content type mapping
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp"
}

# Cache duration: 30 days in seconds
CACHE_MAX_AGE = 30 * 24 * 60 * 60


async def get_gridfs_bucket():
    """Get GridFS bucket from MongoDB"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'troa_db')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    bucket = AsyncIOMotorGridFSBucket(db, bucket_name="images")
    return bucket, client, db


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension"""
    return os.path.splitext(filename)[1].lower()


@gridfs_router.post("/image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Upload an image file to GridFS - admin only"""
    try:
        # Require admin authentication
        await require_admin(request)
        
        # Get backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        
        # Check file extension
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate it's a valid image
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Generate unique filename and ETag
        file_ext = get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        etag = hashlib.md5(content).hexdigest()
        
        # Get GridFS bucket
        bucket, client, db = await get_gridfs_bucket()
        
        # Store file in GridFS with metadata
        file_id = await bucket.upload_from_stream(
            unique_filename,
            io.BytesIO(content),
            metadata={
                "content_type": CONTENT_TYPES.get(file_ext, "application/octet-stream"),
                "original_filename": file.filename,
                "etag": etag,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "size": len(content)
            }
        )
        
        client.close()
        
        image_url = f"{backend_url}/api/upload/image/{unique_filename}"
        
        logger.info(f"Image uploaded to GridFS: {unique_filename} (ID: {file_id})")
        
        return {
            "filename": unique_filename,
            "url": image_url,
            "file_id": str(file_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image to GridFS: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")


@gridfs_router.get("/image/{filename}")
async def get_image(filename: str, request: Request):
    """
    Serve image from GridFS with browser caching support.
    
    Caching Strategy:
    - Cache-Control: max-age=2592000 (30 days)
    - ETag: MD5 hash of file content
    - Returns 304 Not Modified if client has cached version
    """
    try:
        bucket, client, db = await get_gridfs_bucket()
        
        # Find the file by filename in the files collection
        file_doc = await db["images.files"].find_one({"filename": filename})
        
        if not file_doc:
            client.close()
            raise HTTPException(status_code=404, detail="Image not found")
        
        file_id = file_doc["_id"]
        metadata = file_doc.get("metadata", {})
        
        # Get ETag from metadata
        etag = metadata.get("etag", str(file_id))
        content_type = metadata.get("content_type", "application/octet-stream")
        
        # Check if client has cached version (If-None-Match header)
        client_etag = request.headers.get("if-none-match")
        if client_etag and client_etag.strip('"') == etag:
            client.close()
            return Response(
                status_code=304,
                headers={
                    "ETag": f'"{etag}"',
                    "Cache-Control": f"public, max-age={CACHE_MAX_AGE}"
                }
            )
        
        # Download file content
        download_stream = await bucket.open_download_stream(file_id)
        content = await download_stream.read()
        
        client.close()
        
        # Return image with caching headers
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Cache-Control": f"public, max-age={CACHE_MAX_AGE}",
                "ETag": f'"{etag}"',
                "Content-Length": str(len(content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image from GridFS: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve image")


@gridfs_router.delete("/image/{filename}")
async def delete_image(filename: str, request: Request):
    """Delete an image from GridFS - admin only"""
    try:
        await require_admin(request)
        
        bucket, client, db = await get_gridfs_bucket()
        
        # Find the file by filename
        file_doc = await db["images.files"].find_one({"filename": filename})
        
        if not file_doc:
            client.close()
            raise HTTPException(status_code=404, detail="Image not found")
        
        file_id = file_doc["_id"]
        
        # Delete the file
        await bucket.delete(file_id)
        
        client.close()
        
        logger.info(f"Image deleted from GridFS: {filename}")
        
        return {"message": "Image deleted successfully", "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image from GridFS: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete image")


@gridfs_router.get("/stats")
async def get_storage_stats(request: Request):
    """Get storage statistics - admin only"""
    try:
        await require_admin(request)
        
        bucket, client, db = await get_gridfs_bucket()
        
        # Count files and total size
        cursor = bucket.find({})
        files = await cursor.to_list(length=1000)
        
        total_files = len(files)
        total_size = sum(f.length for f in files)
        
        client.close()
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get storage stats")
