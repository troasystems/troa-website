from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import shutil
import os
from PIL import Image
import logging

logger = logging.getLogger(__name__)

upload_router = APIRouter(prefix="/upload")

# Upload directory
UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS

@upload_router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    try:
        # Get backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        # Check file extension
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate it's a valid image
        try:
            img = Image.open(file_path)
            img.verify()
        except Exception as e:
            # Delete invalid file
            file_path.unlink()
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Get backend URL
        backend_url = os.getenv('REACT_APP_BACKEND_URL', str(request.base_url).rstrip('/'))
        image_url = f"{backend_url}/api/upload/image/{unique_filename}"
        
        logger.info(f"Image uploaded successfully: {unique_filename}")
        
        return {
            "filename": unique_filename,
            "url": image_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@upload_router.get("/image/{filename}")
async def get_image(filename: str):
    """Serve uploaded image"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path)
