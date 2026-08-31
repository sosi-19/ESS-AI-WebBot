from fastapi import APIRouter, UploadFile, File
import os
import uuid

from app.services.upload_service import upload_service

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

UPLOAD_FOLDER = "uploads/temp"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Create filename
    filename = f"{file_id}_{file.filename}"

    # Full file path
    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    # Save uploaded file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Process upload
    result = upload_service.process_upload(
        file_id=file_id,
        file_name=file.filename,
        file_path=file_path
    )

    return {
        "message": "File uploaded successfully.",
        "file_id": result["file_id"],
        "filename": result["file_name"],
        "chunks": result["chunks"]
    }