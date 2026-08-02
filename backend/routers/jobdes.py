import os
from datetime import datetime
from dotenv import load_dotenv

from schema.job_description import JobDescriptionData
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import Session
from database import engine, sessionLocal, Base, get_db

load_dotenv()

router = APIRouter(prefix="/api/jobd", tags=["Job-Description"])

class JOBDES(Base):
    __tablename__ = "job-description"

    jd_id = Column(String, primary_key=True)
    role = Column(String, nullable=False)
    seniority = Column(String, nullable=False)
    company_overview = Column(String, nullable=False)
    required_skills = Column(JSON, nullable=False)
    preferred_skills = Column(JSON, nullable=False)
    responsibilities = Column(JSON, nullable=False)
    minimum_years_experience = Column(Integer, nullable=False)
    dt = Column(DateTime, nullable=False)

Base.metadata.create_all(bind=engine)

@router.post("/job-descriptions", status_code=status.HTTP_201_CREATED)
def add_job_descriptions(data: JobDescriptionData, db: Session = Depends(get_db)):
    existing_jd = db.query(JOBDES).filter(JOBDES.jd_id == data.jd_id).first()
    if existing_jd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job description with ID '{data.jd_id}' already exists."
        )

    db_job = JOBDES(
        jd_id=data.jd_id,
        role=data.role,
        seniority=data.seniority,
        company_overview=data.company_overview,
        required_skills=data.required_skills,
        preferred_skills=data.preferred_skills,
        responsibilities=data.responsibilities,
        minimum_years_experience=data.minimum_years_experience,
        dt=datetime.now()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return {
        "msg": f"Job description created with id: {db_job.jd_id}",
        "data": db_job
    }

@router.get("/job-descriptions")
def get_job_descriptions(db: Session = Depends(get_db)):
    job_des = db.query(JOBDES).all()
    return job_des

@router.get("/job-descriptions/{jd_id}")
def get_job_description(jd_id: str, db: Session = Depends(get_db)):
    job_des = db.query(JOBDES).filter(JOBDES.jd_id == jd_id).first()
    if not job_des:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with id '{jd_id}' not found."
        )
    return job_des

@router.put("/job-descriptions/{jd_id}")
def update_job_description(jd_id: str, data: JobDescriptionData, db: Session = Depends(get_db)):
    job_des = db.query(JOBDES).filter(JOBDES.jd_id == jd_id).first()
    if not job_des:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with id '{jd_id}' does not exist."
        )

    job_des.role = data.role
    job_des.seniority = data.seniority
    job_des.company_overview = data.company_overview
    job_des.required_skills = data.required_skills
    job_des.preferred_skills = data.preferred_skills
    job_des.responsibilities = data.responsibilities
    job_des.minimum_years_experience = data.minimum_years_experience

    db.commit()
    db.refresh(job_des)
    return {
        "msg": f"Job description with id '{data.jd_id}' has been updated successfully.",
        "data": job_des
    }

@router.delete("/job-descriptions/{jd_id}")
def delete_job_description(jd_id: str, db: Session = Depends(get_db)):
    job_des = db.query(JOBDES).filter(JOBDES.jd_id == jd_id).first()
    if not job_des:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with id '{jd_id}' does not exist."
        )

    db.delete(job_des)
    db.commit()
    return {
        "msg": f"Job description with id {jd_id} deleted successfully."
    }
