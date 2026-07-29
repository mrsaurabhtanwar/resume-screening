import re
import os
import io
import boto3
import uuid
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from botocore.exceptions import NoCredentialsError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

from services.pdf_extractor import pdf_convertor_md
from services.resume_parser import map_md_to_json
from services.embedding_service import vector_store
from routers.ranking import register_parsed_resume
from routers.candidates import CANDIDATE, get_db

load_dotenv()

router = APIRouter(prefix="/api/upload", tags=["Upload CV"])

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def generate_unique_candidate_id(filename: Optional[str] = None) -> str:
    """Generate a clean, unique candidate ID using filename and short random hash."""
    if filename:
        clean_name = re.sub(r'[^A-Za-z0-9]', '', filename.replace('.pdf', '')).upper()[:12]
        short_hash = uuid.uuid4().hex[:6].upper()
        return f"CAND_{clean_name}_{short_hash}"
    return f"CAND_{uuid.uuid4().hex[:8].upper()}"


@router.post("/upload-file/")
def upload_single_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f"parsed_resumes/{candidate_id}.json",
            Body=jsontext.model_dump_json(),
            ContentType="application/json"
        )
        
        vector_store.add_candidate(candidate_id, jsontext, sync_s3=True)
        register_parsed_resume(candidate_id, jsontext)
        
        work_exp_list = [item.model_dump() for item in jsontext.work_experience] if jsontext.work_experience else []
        education_list = [item.model_dump() for item in jsontext.education] if jsontext.education else []
        project_list = [item.model_dump() for item in jsontext.projects] if jsontext.projects else []
        
        db_candidate = CANDIDATE(
            candidate_id=candidate_id,
            name=jsontext.name,
            email=jsontext.email,
            phone=jsontext.phone,
            location=jsontext.location,
            target_role=jsontext.target_role,
            total_experience_years=jsontext.total_experience_years,
            skills=jsontext.skills or [],
            work_experience=work_exp_list,
            education=education_list,
            projects=project_list,
            s3_url=file_url,
            created_at=datetime.now()
        )
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
        print(f"[DB Success] Candidate '{candidate_id}' saved to PostgreSQL!")
        
            
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