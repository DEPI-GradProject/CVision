from pydantic import BaseModel
from typing import Optional

class CVMetadata(BaseModel):
    has_tables: bool
    has_images: bool
    sections_found: list[str]
    sections_missing: list[str]
    fonts_count: int
    pages_count: int
    length_pages: float

class CVData(BaseModel):
    raw_text: str
    file_name: str
    file_type: str
    metadata: Optional[CVMetadata] = None

class ATSBreakdown(BaseModel):
    format: int
    structure: int
    content: int
    length: int

class ATSResult(BaseModel):
    ats_score: int
    breakdown: ATSBreakdown
    issues: list[str]

class AnalysisResult(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    skills_extracted: list[str]
    ats_result: Optional[ATSResult] = None
    years_of_experience: Optional[float] = None
    experience_level: Optional[str] = None
    target_job_title: Optional[str] = None

class Job(BaseModel):
    title: str
    link: str
    skills: str
    match_score: Optional[int] = None
    matched_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    reason: Optional[str] = None

class JobMatches(BaseModel):
    matched_jobs: list[Job]

class AgentState(BaseModel):
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    cv_data: Optional[CVData] = None
    analysis: Optional[AnalysisResult] = None
    job_matches: Optional[JobMatches] = None
    final_report: Optional[str] = None
    error: Optional[str] = None