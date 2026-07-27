from pydantic import BaseModel, Field
from typing import List

class JobDescriptionData(BaseModel):
    jd_id: str = Field(..., description="Unique JD ID")
    role: str = Field(..., description="Role title")
    seniority: str = Field(..., description="Junior, Mid, Senior, Lead")
    company_overview: str = Field(..., description="Company background")
    required_skills: List[str] = Field(default=[], description="Must-have technical skills")
    preferred_skills: List[str] = Field(default=[], description="Nice-to-have skills")
    responsibilities: List[str] = Field(default=[], description="Key duties")
    minimum_years_experience: int = Field(default=0, description="Minimum experience requirement")
