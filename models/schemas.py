# models/schemas.py


from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _coerce_skills(v):
    if isinstance(v, list):
        return ", ".join(str(s) for s in v)
    return v


SkillsField = Annotated[str, BeforeValidator(_coerce_skills)]


# CV Parser Output
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
    metadata: CVMetadata | None = None


# CV Analyzer Output
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
    ats_result: ATSResult | None = None


# Job Matcher Output
class Job(BaseModel):
    title: str
    link: str
    skills: SkillsField
    match_score: int | None = None
    matched_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    reason: str | None = None


class JobMatches(BaseModel):
    matched_jobs: list[Job]


# Agent State
class AgentState(BaseModel):
    file_path: str | None = None
    file_name: str | None = None
    cv_data: CVData | None = None
    analysis: AnalysisResult | None = None
    job_matches: JobMatches | None = None
    final_report: str | None = None
    error: str | None = None
