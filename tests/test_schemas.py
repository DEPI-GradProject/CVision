from models.schemas import AgentState, AnalysisResult, ATSBreakdown, ATSResult, CVData, CVMetadata, Job, JobMatches


def test_cv_metadata_defaults():
    meta = CVMetadata(
        has_tables=False,
        has_images=True,
        sections_found=["experience", "education"],
        sections_missing=["summary"],
        fonts_count=2,
        pages_count=2,
        length_pages=2.0,
    )
    assert meta.has_tables is False
    assert meta.has_images is True
    assert len(meta.sections_found) == 2


def test_cv_data_with_metadata():
    meta = CVMetadata(
        has_tables=False,
        has_images=False,
        sections_found=[],
        sections_missing=[],
        fonts_count=1,
        pages_count=1,
        length_pages=1.0,
    )
    data = CVData(raw_text="test", file_name="resume.pdf", file_type="pdf", metadata=meta)
    assert data.file_type == "pdf"
    assert data.metadata is not None
    assert data.metadata.pages_count == 1


def test_cv_data_without_metadata():
    data = CVData(raw_text="test", file_name="resume.docx", file_type="docx")
    assert data.metadata is None


def test_ats_breakdown():
    breakdown = ATSBreakdown(format=80, structure=90, content=75, length=100)
    assert breakdown.format == 80
    assert breakdown.length == 100


def test_ats_result():
    breakdown = ATSBreakdown(format=80, structure=90, content=75, length=100)
    ats = ATSResult(
        ats_score=86,
        breakdown=breakdown,
        issues=["Missing summary section", "Too many fonts"],
    )
    assert ats.ats_score == 86
    assert len(ats.issues) == 2


def test_analysis_result():
    ats = ATSResult(
        ats_score=86,
        breakdown=ATSBreakdown(format=80, structure=90, content=75, length=100),
        issues=[],
    )
    analysis = AnalysisResult(
        strengths=["Good experience"],
        weaknesses=["Missing skills section"],
        suggestions=["Add skills"],
        skills_extracted=["Python", "FastAPI"],
        ats_result=ats,
    )
    assert len(analysis.strengths) == 1
    assert "Python" in analysis.skills_extracted
    assert analysis.ats_result.ats_score == 86


def test_agent_state_defaults():
    state = AgentState()
    assert state.file_path is None
    assert state.cv_data is None
    assert state.analysis is None
    assert state.job_matches is None
    assert state.final_report is None
    assert state.error is None


def test_agent_state_with_data():
    state = AgentState(
        file_path="/tmp/cv.pdf",
        file_name="cv.pdf",
        final_report="Great CV!",
        error=None,
    )
    assert state.file_name == "cv.pdf"
    assert state.final_report == "Great CV!"


def test_agent_state_error():
    state = AgentState(error="Parsing failed")
    assert state.error == "Parsing failed"


def test_job_matches():
    job = Job(
        title="Software Engineer",
        link="https://example.com/job",
        skills="Python, FastAPI",
        match_score=85,
        matched_skills=["Python"],
        missing_skills=["Docker"],
        reason="Good fit",
    )
    matches = JobMatches(matched_jobs=[job])
    assert len(matches.matched_jobs) == 1
    assert matches.matched_jobs[0].match_score == 85
    assert matches.matched_jobs[0].reason == "Good fit"


def test_job_minimal():
    job = Job(title="Engineer", link="https://example.com", skills="Python")
    assert job.match_score is None
    assert job.matched_skills is None
