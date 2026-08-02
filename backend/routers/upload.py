import re
import os
import io
import boto3
import uuid
import zipfile

from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from typing import Optional

from services.backgroundtask import process_resume_in_background

load_dotenv()

router = APIRouter(prefix="/api/upload", tags=["Upload CV"])

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
MAX_ZIP_SIZE_BYTES = 50 * 1024 * 1024


def get_safe_filename(filename: Optional[str]) -> str:
    """Discard path components supplied by the client before creating an S3 key."""
    return (filename or "upload").replace("\\", "/").rsplit("/", 1)[-1]

def generate_unique_candidate_id(filename: Optional[str] = None) -> str:
    """Generate a clean, unique candidate ID using filename and short random hash."""
    if filename:
        clean_name = re.sub(r'[^A-Za-z0-9]', '', filename.replace('.pdf', '')).upper()[:12]
        short_hash = uuid.uuid4().hex[:6].upper()
        return f"CAND_{clean_name}_{short_hash}"
    return f"CAND_{uuid.uuid4().hex[:8].upper()}"

@router.post("/upload-file/")
def upload_single_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    filename = get_safe_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be in the pdf format."
        )

    file_bytes = file.file.read(MAX_PDF_SIZE_BYTES + 1)
    if len(file_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF files must be 10 MiB or smaller."
        )
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid PDF."
        )

    candidate_id = generate_unique_candidate_id(filename)
    s3_dir_path = f"resumes/{candidate_id}/{filename}"

    try:
        s3_client.upload_fileobj(
            io.BytesIO(file_bytes),
            BUCKET_NAME,
            s3_dir_path,
        )
        file_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_dir_path}"

        background_tasks.add_task(
            process_resume_in_background,
            candidate_id,
            file_bytes,
            filename,
            file_url
        )

        return {
            "status": "success",
            "msg": "Resume uploaded successfully! Parsing & FAISS indexing are running in the background.",
            "filename": file.filename,
            "candidate_id": candidate_id,
            "url": file_url
        }
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS credentials not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 upload failed: {str(e)}"
        )

@router.post("/upload-zip-file/")
def upload_zip_file(file: UploadFile = File(...)):
    filename = get_safe_filename(file.filename)
    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be zip"
        )

    file_bytes = file.file.read(MAX_ZIP_SIZE_BYTES + 1)
    if len(file_bytes) > MAX_ZIP_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="ZIP archives must be 50 MiB or smaller."
        )
    if not zipfile.is_zipfile(io.BytesIO(file_bytes)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid ZIP archive."
        )

    archive_id = uuid.uuid4().hex[:12]
    s3_dir_path = f"archives/{archive_id}/{filename}"
    try:
        s3_client.upload_fileobj(
            io.BytesIO(file_bytes),
            BUCKET_NAME,
            s3_dir_path
        )
        zip_file_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_dir_path}"
        return {
            "msg": "ZIP archive uploaded successfully. Archive processing is not implemented.",
            "url": zip_file_url
        }
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS credentials not found."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 upload failed."
        )
