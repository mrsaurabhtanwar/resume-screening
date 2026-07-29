from schema.resume import ResumeData
from schema.job_description import JobDescriptionData

def build_json_to_text(jsontext: ResumeData):
    
    role_text = f"Target Role: {jsontext.target_role}" if jsontext.target_role else ""
    summary_text = f"Summary: {jsontext.summary}" if jsontext.summary else ""
    
    skills_text = f"Skills: {', '.join(jsontext.skills)}" if jsontext.skills else ""
    
    exp_list = []
    for exp in jsontext.work_experience:
        bullents = " ".join(exp.bullet_points)
        exp_list.append(f"{exp.title} at {exp.company}: {bullents}")
    experience_text = f"Work Experience: {' '.join(exp_list)}" if exp_list else ""
    
    proj_list = []
    for proj in jsontext.projects:
        tech = f"(Tech: {', '.join(proj.tech_stack)})" if proj.tech_stack else ""
        bullents = " ".join(proj.bullet_points)
        proj_list.append(f"{proj.name}{tech}: {bullents}")
    projects_text = f"Projects: {' '.join(proj_list)}" if proj_list else ""
    
    edu_list = [f"{edu.degree} from {edu.university}" for edu in jsontext.education]
    education_text = f"Education: {', '.join(edu_list)}" if edu_list else ""
    
    certs_text = f"Cerifications: {', '.join(jsontext.certifications)}" if jsontext.certifications else ""
    awards_text = f"Achievements: {', '.join(jsontext.achievements_or_rewards)}" if jsontext.achievements_or_rewards else ""
    
    sections = [role_text, summary_text, skills_text, experience_text, projects_text, education_text, certs_text, awards_text]
    
    full_embedding_text = " | ".join([s for s in sections if s])
    
    return {
        "full_text": full_embedding_text, 
        "project_text":  projects_text, 
        "experience_text": experience_text, 
        "education_text": education_text
    }


def build_jobdes_json_to_text(Jobdes_text: JobDescriptionData) -> str:
    role_text = f"Job title: {Jobdes_text.role}" if Jobdes_text.role else ""
    seniority_text = f"Seniority Level: {Jobdes_text.seniority}" if Jobdes_text.seniority else ""
    overview_text = f"Company Overview: {Jobdes_text.company_overview}" if Jobdes_text.company_overview else ""
    
    req_skills_text = f"Required Skills: {', '.join(Jobdes_text.required_skills)}" if Jobdes_text.required_skills else ""
    pref_skills_text = f"Preferred Skills: {', '.join(Jobdes_text.preferred_skills)}" if Jobdes_text.preferred_skills else ""
    
    responsibilities_text = f"Responsibilities: {' '.join(Jobdes_text.responsibilities)}" if Jobdes_text.responsibilities else ""
    min_exp_text = f"Minimum Experience Required: {Jobdes_text.minimum_years_experience} years" if Jobdes_text.minimum_years_experience is not None else ""
    
    sections = [role_text, seniority_text, overview_text, req_skills_text, pref_skills_text, responsibilities_text, min_exp_text]
    
    full_jd_embedding_text = " | ".join([s for s in sections if s])
    return full_jd_embedding_text
    