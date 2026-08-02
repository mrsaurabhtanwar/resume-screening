from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ExperienceItem(BaseModel):
    company: str = Field(default="", description="Company or organization name")
    title: str = Field(default="", description="Job title or role")
    duration: str = Field(default="", description="Duration string e.g. Jan 2021 - Present")
    bullet_points: List[str] = Field(default=[], description="Achievements and duties")

class InternshipItems(BaseModel):
    company: str = Field(default="", description="Company name in which internship did")
    title: str = Field(default="", description="Intern's job title")
    duration: str = Field(default="", description="Duration of the internship")
    bullet_points: List[str]= Field(default=[], description="Points that are related to the internship")

class EducationItem(BaseModel):
    degree: str = Field(default="", description="Degree or qualification earned")
    university: str = Field(default="", description="University, college, or institution name")
    year: str = Field(default="", description="Graduation year or dates")

class ProjectItem(BaseModel):
    name: str = Field(default="", description="Project name")
    duration: str = Field(default="", description="Project duration")
    tech_stack: List[str] = Field(default=[], description="Technologies used in project")
    bullet_points: List[str] = Field(default=[], description="Key project highlights")

class ResumeData(BaseModel):
    candidate_id: str = Field(..., description="Unique identifier for candidate")
    target_role: Optional[str] = Field(default=None, description="Target job role")
    name: str = Field(..., description="Full candidate name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Location or city")
    social_links: Optional[Dict[str, Any]] = Field(default_factory=dict)
    languages: Optional[List[str]] = Field(default_factory=list, description="Languages")
    summary: str = Field(default="", description="Professional bio or summary")
    total_experience_years: float = Field(default=0, description="Total experience in years")
    skills: List[str] = Field(default=[], description="List of technical and domain skills")
    work_experience: List[ExperienceItem] = Field(default=[], description="Career experience history")
    internship: List[InternshipItems] = Field(default_factory=list, description="Details of the internships")
    projects: List[ProjectItem] = Field(default=[], description="Key engineering projects")
    education: List[EducationItem] = Field(default=[], description="Educational history")
    certifications: List[str] = Field(default=[], description="Professional certifications")
    achievements_or_rewards: Optional[List[str]] = Field(default_factory=list, description="Any achievements, awards, or honors")
    raw_text: Optional[str] = Field(default=None, description="Raw extracted text from PDF")
