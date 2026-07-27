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
    prompt = f"""You are an expert executive technical recruiter AI and resume parser.
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
        "total_experience_years": 0,
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
            "duration": "Duration string or empty string",
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
            "year": "Graduation Year or dates"
            }}
        ],
        "certifications": [],
        "achievements_or_rewards": ["Award 1", "Scholarship 2"]
        }}

        CRITICAL EXTRACTION RULES (STRICT ACCURACY & NO BIAS):
        1. Extract ONLY facts explicitly stated in the provided text.
        2. If the candidate has NO formal employment experience listed in the text, return `[]` (empty list) for `work_experience`. NEVER invent companies or insert fake placeholder items!
        3. Extract all social media, portfolio, and code profile links (LinkedIn, GitHub, LeetCode, Kaggle, Portfolio) into `social_links`. If a link is just generic text like "LinkedIn" without a URL, set its value to empty string.
        4. Extract spoken and written languages into `languages` (default to ["English"] if no languages are explicitly mentioned).
        5. Extract items for `projects` ONLY if listed under Academic Projects, Personal Projects, or Projects sections.
        6. Extract ONLY individual technical skills, tools, frameworks, and programming languages for `skills`. Do NOT extract category headers!
        7. Extract honors, scholarships, awards, academic achievements, or leadership roles into `achievements_or_rewards`.
        8. If any string field is missing or unknown, return empty string `""` or `[]`. NEVER fill in generic placeholder words.
        
        MARKDOWN RESUME TEXT:
        {md_content}"""
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        response_format={"type": "json_object"}
    )

    raw_json = json.loads(completion.choices[0].message.content)
    
    # 1. Sanitize null values to empty strings for string fields
    json_response = sanitize_nulls(raw_json)
    
    # 2. Inject candidate_id and raw_text
    if not candidate_id:
        candidate_id = f"CAND_{uuid.uuid4().hex[:8].upper()}"
        
    json_response["candidate_id"] = candidate_id
    json_response["raw_text"] = md_content
    
    # 3. Build validated Pydantic model
    resume_obj = ResumeData(**json_response)
    return resume_obj
