import math

from typing import Dict, Any

from schema.resume import ResumeData
from schema.job_description import JobDescriptionData
from services.score_parser import evaluate_candidate_score_with_llm

def _calculate_elastic_experience_score(cand_exp: float, req_exp: int) -> float:
    if req_exp <= 0:
        return 100
    if cand_exp == 0:
        return 20.0
    
    ratio = cand_exp/float(req_exp)
    if ratio >= 1.0:
        bonus = min(10.0, (cand_exp - req_exp)*1.5)
        return min(100.0, 90.0+bonus)
    else:
        return round(math.pow(ratio, 0.75)*90.0, 2)
    
def compute_composite_score(
    candidate: ResumeData,
    jd: JobDescriptionData,
    vector_similarity: float
) -> Dict[str, Any]:
    
    llm_eval_score = evaluate_candidate_score_with_llm(candidate, jd)
    vector_sim_score = round(max(0.0, float(vector_similarity))*100, 2)
    
    cand_skiils = set(s.lower().strip() for s in candidate.skills)
    matched_req_skills = [s for s in jd.required_skills if s.lower().strip() in cand_skiils]
    missing_req_skill = [s for s in jd.required_skills if s.lower().strip() not in cand_skiils]
    direct_skill_coverage = round((len(matched_req_skills)/ max(1, len(jd.required_skills)))* 100.0, 2)
    
    combined_skills_score = round(
        (0.4 * vector_sim_score) +
        (0.3 * direct_skill_coverage) +
        (0.3 * float(llm_eval_score.get("skills_match_score", 70.0))),
        2
    )
    
    elsatic_exp_score = _calculate_elastic_experience_score(candidate.total_experience_years, jd.minimum_years_experience)
    
    domain_score = float(llm_eval_score.get("domain_relevance_score", 70.0))
    
    project_score = float(llm_eval_score.get("project_quality_score", 65.0))
    
    work_exp_score = float(llm_eval_score.get("work_experience_relevance_score", 70.0))
    
    edu_score = float(llm_eval_score.get("education_pedigree_score", 60.0))
    
    cert_achieve_score = float(llm_eval_score.get("certifications_achievements_score", 50.0))
    
    effective_domain_work_score = round((0.6 * domain_score) + (0.4 * work_exp_score), 2)
    
    effective_edu_achieve_score = round((0.6 * edu_score) + (0.4 * cert_achieve_score), 2)
    
    composite_score = round(
        (0.30 * effective_domain_work_score) + 
        (0.25 * project_score) +
        (0.20 * combined_skills_score) +
        (0.15 * elsatic_exp_score) +
        (0.10 * effective_edu_achieve_score),
        2
    )
    return {
        "composite_score" : composite_score,
        "section_scores": {
            "domain_relevance": domain_score,
            "project_quality": project_score,
            "work_experience_relevance": work_exp_score,
            "combined_skills": combined_skills_score,
            "vector_similarity": vector_sim_score,
            "elastic_experience": elsatic_exp_score,
            "education_pedigree": edu_score,
            "certifications_achievements": cert_achieve_score,
        },
        "missing_required_skills": missing_req_skill
    }