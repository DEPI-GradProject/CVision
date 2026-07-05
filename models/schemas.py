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


class JobMatchRequest(BaseModel):
    job_description: str
    cv_text: str


class JobMatchResult(BaseModel):
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    improvement_tips: list[str]
    keyword_coverage: float = 0.0
    cv_text: str = ""


class TailorResumeResult(BaseModel):
    tailored_resume: str


class StandOutSuggestion(BaseModel):
    unique_selling_points: list[str]
    suggested_certifications: list[str]
    project_ideas: list[str]
    skill_enhancements: list[str]
    overall_strategy: str


class CoverLetterRequest(BaseModel):
    job_description: str
    cv_text: str


class CoverLetterResult(BaseModel):
    cover_letter: str


class RewriteSuggestion(BaseModel):
    original: str
    issue: str
    improved: str


class RewriteResult(BaseModel):
    overall_assessment: str
    rewrites: list[RewriteSuggestion]
    quick_wins: list[str]


class MarketSkill(BaseModel):
    skill: str
    job_count: int
    demand_level: str  # "high", "medium", "low"


# Agent State
class AgentState(BaseModel):
    file_path: str | None = None
    file_name: str | None = None
    cv_data: CVData | None = None
    analysis: AnalysisResult | None = None
    job_matches: JobMatches | None = None
    final_report: str | None = None
    error: str | None = None
