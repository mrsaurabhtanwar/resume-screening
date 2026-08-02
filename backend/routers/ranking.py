import json
import boto3
import os

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session

from schema.resume import ResumeData
from schema.job_description import JobDescriptionData
from services.embedding_service import vector_store
from services.ranking_engine import compute_composite_score
from database import get_db
from routers.jobdes import JOBDES

router = APIRouter(prefix="/api/ranking", tags=["Candidate Ranking"])

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

PARSED_RESUMES_REGISTRY: Dict[str, ResumeData] = {}

def register_parsed_resume(candidate_id: str, resume: ResumeData):
    PARSED_RESUMES_REGISTRY[candidate_id] = resume

def get_candidate_resume(candidate_id: str, db: Optional[Session] = None) -> Optional[ResumeData]:
    if candidate_id in PARSED_RESUMES_REGISTRY:
        return PARSED_RESUMES_REGISTRY[candidate_id]

    try:
        s3_key = f"parsed_resumes/{candidate_id}.json"
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        raw_json = json.loads(response["Body"].read().decode("utf-8"))
        resume_obj = ResumeData(**raw_json)

        PARSED_RESUMES_REGISTRY[candidate_id] = resume_obj
        return resume_obj
    except Exception as e:
        pass

    if db:
        try:
            from routers.candidates import CANDIDATE
            cand_db = db.query(CANDIDATE).filter(CANDIDATE.candidate_id == candidate_id).first()
            if cand_db:
                resume_obj = ResumeData(
                    candidate_id=cand_db.candidate_id,
                    name=cand_db.name or "Unknown",
                    email=cand_db.email or "",
                    phone=cand_db.phone or "",
                    location=cand_db.location or "",
                    target_role=cand_db.target_role or "",
                    total_experience_years=cand_db.total_experience_years or 0.0,
                    skills=cand_db.skills or [],
                    work_experience=cand_db.work_experience or [],
                    projects=cand_db.projects or [],
                    education=cand_db.education or []
                )
                PARSED_RESUMES_REGISTRY[candidate_id] = resume_obj
                return resume_obj
        except Exception:
            pass

    return None

@router.post("/rank", response_model=Dict[str, Any])
def rank_candidate(
    jd_id: str = Query(..., description="ID of the Job Description to rank candidate against"),
    top_k: int = Query(10, ge=1, le=50, description="Number of top candidates to return in the leaderboard"),
    db: Session = Depends(get_db)
):
    db_jd = db.query(JOBDES).filter(JOBDES.jd_id == jd_id).first()
    if not db_jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with ID '{jd_id}' not found."
        )

    jd_data = JobDescriptionData(
        jd_id=db_jd.jd_id,
        role=db_jd.role,
        seniority=db_jd.seniority,
        company_overview=db_jd.company_overview,
        required_skills=db_jd.required_skills or [],
        preferred_skills=db_jd.preferred_skills or [],
        responsibilities=db_jd.responsibilities or [],
        minimum_years_experience=db_jd.minimum_years_experience or 0
    )

    search_results = vector_store.search(jd_data, top_k=top_k)
    if not search_results:
        return{
            "status": "success",
            "msg": "No candidate vectors found in FAISS index",
            "jd_id": jd_id,
            "job_title": f"{jd_data.seniority} {jd_data.role}",
            "leaderboard": []
        }

    scored_candidates = []
    for candidate_id, vector_sim in search_results:
        resume_obj = get_candidate_resume(candidate_id, db=db)
        if resume_obj:
            score_data = compute_composite_score(resume_obj, jd_data, vector_sim)
            scored_candidates.append((score_data["composite_score"], candidate_id, resume_obj, score_data))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    leaderboard = []
    for rank_idx, (score, cand_id, resume, score_data) in enumerate(scored_candidates, start=1):
        leaderboard.append({
            "rank": rank_idx,
            "candidate_id": cand_id,
            "name": resume.name,
            "email": resume.email,
            "target_role": resume.target_role,
            "total_experience_years": resume.total_experience_years,
            "composite_score": score,
            "section_scores": score_data.get("section_scores", {}),
            "missing_required_skills": score_data.get("missing_required_skills")
        })

    return {
        "status": "success",
        "jd_id": jd_id,
        "job_title": f"{jd_data.seniority} {jd_data.role}",
        "total_candidate_found_in_faiss": len(search_results),
        "total_candidates_ranked": len(leaderboard),
        "leaderboard": leaderboard
    }
