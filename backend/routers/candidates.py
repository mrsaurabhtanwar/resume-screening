import os
import boto3

from dotenv import load_dotenv
from sqlalchemy import create_engine, String, Float, JSON, Column, DateTime
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from services.embedding_service import vector_store

load_dotenv()

router = APIRouter(prefix="/api/candidate", tags=["Candidates"])

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DB_URL, 
    connect_args={"sslmode":"require"},
    pool_pre_ping=True,
    pool_recycle=300
)


sessionLocal = sessionmaker(autoflush=True, bind=engine)
Base = declarative_base()

class CANDIDATE(Base):
    __tablename__ = "candidate-cv-data"
    
    candidate_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    location = Column(String)
    target_role = Column(String)
    total_experience_years = Column(Float)
    skills = Column(JSON)
    work_experience = Column(JSON)
    education = Column(JSON)
    projects = Column(JSON)
    s3_url = Column(String)
    created_at = Column(DateTime, nullable=False)
    
Base.metadata.create_all(engine)


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
       
        
@router.get("/candidates")
def get_candidates(
    min_exp: Optional[float] = Query(None, description="Minimum years of experience"),
    max_exp: Optional[float] = Query(None, description="Maximum years of experience"),
    skill: Optional[str] = Query(None, description="Filter candidates by specific skill (e.g Python, Docker)"),
    role: Optional[str] = Query(None, description="Filter by target job role"),
    search: Optional[str] = Query(None, description="keyword search in candidate name, email, or location"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    query = db.query(CANDIDATE)
    
    if min_exp is not None:
        query = query.filter(CANDIDATE.total_experience_years >= min_exp)
    if max_exp is not None:
        query = query.filter(CANDIDATE.total_experience_years <= max_exp)
    
    if role:
        query = query.filter(CANDIDATE.target_role.ilike(f"%{role}%"))
        
    if search:
        query = query.filter(
            (CANDIDATE.name.ilike(f"%{search}%")) |
            (CANDIDATE.email.ilike(f"%{search}%")) |
            (CANDIDATE.location.ilike(f"%{search}%"))
        )
    
    if skill:
        query = query.filter(CANDIDATE.skills.cast(String).ilike(f"%{skill}%"))
        
    total_count = query.count()
    candidates = query.order_by(CANDIDATE.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "status": "success",
        "total_matches": total_count,
        "limit": limit,
        "offset": offset,
        "candidates": candidates
    }

@router.get("/candidates/{candidate_id}")
def get_single_candidate(candidate_id: str, db: Session = Depends(get_db)):
    candidate_db = db.query(CANDIDATE).filter(CANDIDATE.candidate_id == candidate_id).first()
    if not candidate_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate details not found."
        )
    return candidate_db
        
@router.delete("/candidates/{candidate_id}")
def delete_candidate_db(candidate_id: str, db: Session = Depends(get_db)):
    candidate_db = db.query(CANDIDATE).filter(CANDIDATE.candidate_id == candidate_id).first()
    if not candidate_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found."
        )
    try:
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=f"parsed_resumes/{candidate_id}.json"
        )
        objects = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"resumes/{candidate_id}/"
        )
        if "Contents" in objects:
            for obj in objects["Contents"]:
                s3_client.delete_object(
                    Bucket=BUCKET_NAME,
                    Key=obj["Key"]
                )
    except Exception as e:
        print(f"[Warning] S3 deletion error: {e}")
        
    vector_store.remove_candidate(candidate_id)
    
    db.delete(candidate_db)
    db.commit()
    return {
        "status": "success",
        "msg": f"Candidate with {candidate_id} has been deleted from PostgreSQL, S3 and FAISS successfully!"
    }
        