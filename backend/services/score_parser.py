import os
import json

from groq import Groq
from dotenv import load_dotenv

from schema.resume import ResumeData
from schema.job_description import JobDescriptionData
from .embedding_text import build_json_to_text

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_candidate_score_with_llm(candidate_resume: ResumeData, jd: JobDescriptionData) -> dict:
    
    text_section = build_json_to_text(candidate_resume)
    project_summary = text_section["project_text"]
    experience_summary = text_section["experience_text"]
    education_summary = text_section["education_text"]
    
    prompt = f"""
    You are a lead Technical Recruter performing a numerical dossier evaluation for a candidate against a Job Description.
    
    TARGET JOB DESCRIPTION:
    - Role: {jd.role} ({jd.seniority})
    - Overview: {jd.company_overview}
    - Required Skills: {', '.join(jd.required_skills)}
    - Preferred Skills: {', '.join(jd.preferred_skills)}
    - Min Experience: {jd.minimum_years_experience} years 
    
    CANDIDATE DOSSIER TO EVALUATE
    1. Target Role: {candidate_resume.target_role or 'Not specified'}
    2. Total Experience: {candidate_resume.total_experience_years} years
    3. Education: {education_summary}
    4. Skills: {', '.join(candidate_resume.skills)}
    5. Work History: {experience_summary}
    6. Projects & Accomplishments: {project_summary}
    7. Certifications: {', '.join(candidate_resume.certifications)}
    8. Achievements: {', '.join(candidate_resume.achievements_or_rewards or [])}
    
    Evaluate EVERY single section of the dossier and return a JSON object with EXACTLY these fields:
    {{
        "domain_relevance_score": <float 0.0-100.0: how closely past work/projects match the target domain>,
        "project_quality_score": <float 0.0-100.0: technical complexity, depth, and impact vs simple CRUD/tutorials>,
        "work_experience_relevance_score": <float 0.0-100.0: alignment of past job roles and responsibilities with target role>,
        "education_pedigree_score": <float 0.0-100.0: college tier reputation and degree relevance>,
        "college_tier": "Tier 1" | "Tier 2" | "Tier 3" | "Unknown",
        "skills_match_score": <float 0.0-100.0: core domain skill coverage>,
        "certifications_achievements_score": <float 0.0-100.0: value of certifications, hackathons, awards, research papers>,
        "scoring_notes": {{
            "domain": "<1-line reason for domain score>",
            "projects": "<1-line reason for project score>",
            "work_exp": "<1-line reason for work experience score>",
            "education": "<1-line reason for education score>",
            "skills": "<1-line reason for skills score>",
            "achievements": "<1-line reason for achievements score>"
        }}
    }}
    Return ONLY valid JSON
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise RuntimeError(f"Unexpected LLM response type: {type(content).__name__}")
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"LLM Dossier Evaluation failed for candidate '{candidate_resume.candidate_id}': {str(e)}")
    