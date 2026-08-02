import json
import os
import uuid
from typing import Optional

from groq import Groq
from dotenv import load_dotenv

from schema.resume import ResumeData

load_dotenv()

client = Groq()

def sanitize_nulls(obj):
    """Recursively convert null values to empty strings or empty lists for Pydantic string fields."""
    if isinstance(obj, dict):
        return {k: sanitize_nulls(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nulls(i) for i in obj]
    elif obj is None:
        return ""
    return obj

def map_md_to_json(md_content: str, candidate_id: Optional[str] = None) -> ResumeData:
    prompt = f"""You are a Master Executive Technical Recruiter AI and ultra-precise resume parser.
Extract candidate data from the markdown resume text into strict JSON matching this exact structure:
{{
  "name": "Candidate Full Name or empty string",
  "email": "Email string or empty string",
  "phone": "Phone string or empty string",
  "location": "Location or city string or empty string",
  "social_links": {{
    "linkedin": "Full LinkedIn URL/handle or empty string",
    "github": "Full GitHub URL/handle or empty string",
    "leetcode": "Full LeetCode URL/handle or empty string",
    "portfolio": "Personal website/portfolio URL or empty string"
  }},
  "languages": ["Language 1", "Language 2"],
  "target_role": "Target Job Title inferred from header / education / experience or empty string",
  "summary": "Professional bio or career summary",
  "total_experience_years": 0.0,
  "skills": ["Skill1", "Skill2"],
  "work_experience": [
    {{
      "company": "Organization or Company Name",
      "title": "Role Title",
      "duration": "Duration string e.g. Jul 2025 - Present or empty string",
      "bullet_points": ["Achievement or responsibility 1"]
    }}
  ],
  "internship": [
    {{
      "company": "Company Name",
      "title": "Internship Title",
      "duration": "Duration string e.g. Oct 2025 - Dec 2025",
      "bullet_points": ["Achievement 1"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "duration": "Duration string or empty string",
      "tech_stack": ["Tech1", "Tech2"],
      "bullet_points": ["Highlight 1"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "university": "University or Institution Name",
      "year": "Graduation Year or dates e.g. 2020 - 2025"
    }}
  ],
  "certifications": [],
  "achievements_or_rewards": ["Award 1", "Scholarship 2"]
}}

CRITICAL DISAMBIGUATION & ACCURACY RULES:
1. SEPARATE PROJECTS FROM WORK EXPERIENCE:
   - Academic Projects, Personal Projects, Hackathon Projects, and University Coursework MUST be placed ONLY under `projects`. They are NOT work experience!
   - `work_experience` MUST contain ONLY formal employment or jobs at a company/organization.
   - If candidate is a student or graduate with NO formal employment jobs at companies, set `work_experience` to `[]` (empty list).
2. `total_experience_years`:
   - Calculate cumulative years ONLY from formal company employment and company internships.
   - Use the top-level overall role tenure for a company (e.g. "Acme Corp - Software Engineer: Jul 2025 - Present" = 1.0 year). Do NOT sum individual sub-project durations underneath a company role!
   - Do NOT count project durations towards `total_experience_years`.
   - If candidate has NO formal company employment or internships, `total_experience_years` MUST BE `0.0`!
3. Extract spoken languages into `languages` (default to ["English"]).
4. Extract all technical skills, tools, and frameworks into `skills`.
5. Extract degree and university name cleanly into `education`.

MARKDOWN RESUME TEXT:
{md_content}"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    content = completion.choices[0].message.content
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected LLM response type: {type(content).__name__}")

    raw_json = json.loads(content)
    json_response = sanitize_nulls(raw_json)

    if not candidate_id:
        candidate_id = f"CAND_{uuid.uuid4().hex[:8].upper()}"

    json_response["candidate_id"] = candidate_id
    json_response["raw_text"] = md_content

    return ResumeData(**json_response)
