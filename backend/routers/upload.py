import re
import os
import io
import boto3
import uuid
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from typing import Optional

from services.pdf_extractor import pdf_convertor_md
from services.resume_parser import map_md_to_json
from services.embedding_service import FAISSS3VectorStore

load_dotenv()

router = APIRouter(prefix="/api/upload", tags=["Upload CV"])

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

vector_store = FAISSS3VectorStore()

def generate_unique_candidate_id(filename: Optional[str] = None) -> str:
    """Generate a clean, 100% unique candidate ID using filename + UUID."""
    clean_name = re.sub(r'[^A-Za-z0-9]', '', filename.replace('.pdf', '')).upper()[:10]
    unique_suffix = uuid.uuid4().hex[:8].upper()
    
    if clean_name:
        return f"CAND_{clean_name}_{unique_suffix}"
    return f"CAND_{unique_suffix}"


@router.post("/upload-file/")
def upload_single_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be in the pdf format."
        )
        
    candidate_id = generate_unique_candidate_id(file.filename)
    s3_dir_path = f"resumes/{candidate_id}/{file.filename}"
    
    try:
        file_bytes = file.file.read()
        
        s3_client.upload_fileobj(
            io.BytesIO(file_bytes),
            BUCKET_NAME,
            s3_dir_path,
        )
        file_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_dir_path}"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
            
        try: 
            md_content = pdf_convertor_md(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
        jsontext = map_md_to_json(md_content, candidate_id)
        
        vector_store.add_candidate(candidate_id, jsontext, sync_s3=True)
            
        return{
            "status": "success",
            "msg": "file uploaded, parsed, embeded and synced to s3 sucessfully!",
            "filename": file.filename,
            "candidate_id": candidate_id,
            "url": file_url,
            "embed": "vector embeded successfully!",
            "total_vector_in_faiss": vector_store.index.ntotal
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
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be zip"
        )
        
    folder_name = "Test_zip"
    s3_dir_path =  f"{folder_name}/{file.filename}"
    try:
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            s3_dir_path
        ) 
        zip_file_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_dir_path}"
        return{
            "msg":"zip file uploaded succesfully!",
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