import tempfile
import os
import boto3
from datetime import datetime
from dotenv import load_dotenv

from services.pdf_extractor import pdf_convertor_md
from services.resume_parser import map_md_to_json
from services.embedding_service import vector_store
from routers.ranking import register_parsed_resume
from database import sessionLocal
from routers.candidates import CANDIDATE

load_dotenv()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def process_resume_in_background(
    candidate_id: str,
    file_bytes: bytes,
    filename: str,
    file_url: str
):
    try:
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

        db = sessionLocal()
        try:
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
            print(f"Processed candidate '{candidate_id}' successfully.")
        finally:
            db.close()

    except Exception as e:
        print(f"Background task processing error for candidate '{candidate_id}': {e}")
