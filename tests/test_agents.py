import json
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("langchain_groq")
pytest.importorskip("langgraph")
pytest.importorskip("langchain_community")

# Patch ChatGroq at the source before any agent module imports it
_mock_llm = MagicMock()
_mock_llm.invoke.return_value.content = ""
_patcher = patch("langchain_groq.ChatGroq", return_value=_mock_llm)
_patcher.start()

# Patch HuggingFaceEmbeddings to prevent model download
patch("langchain_huggingface.HuggingFaceEmbeddings", MagicMock()).start()

from models.schemas import (  # noqa: E402
    AgentState,
    AnalysisResult,
    ATSBreakdown,
    ATSResult,
    CVData,
    CVMetadata,
    Job,
    JobMatches,
)


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        strengths=["Strong experience in Python"],
        weaknesses=["Missing education section"],
        suggestions=["Add education details"],
        skills_extracted=["Python", "FastAPI", "Docker"],
        ats_result=ATSResult(
            ats_score=75,
            breakdown=ATSBreakdown(format=80, structure=70, content=75, length=80),
            issues=["Missing required section: Education"],
        ),
    )


@pytest.fixture
def sample_job_matches():
    return JobMatches(
        matched_jobs=[
            Job(
                title="Backend Developer",
                link="https://example.com/job1",
                skills="Python, FastAPI, PostgreSQL",
                match_score=85,
                matched_skills=["Python", "FastAPI"],
                missing_skills=["PostgreSQL"],
                reason="Strong Python backend fit",
            )
        ]
    )


# --- ATS Checker Logic (pure function, no LLM) ---


def _compute_ats_score(metadata_dict: dict) -> dict:
    cv_text = metadata_dict.get("cv_text", "").lower()
    sections_found = [s.lower() for s in metadata_dict.get("sections_found", [])]
    issues = []

    format_score = 100
    if metadata_dict.get("has_tables"):
        format_score -= 30
        issues.append("Tables detected - ATS systems struggle to parse tables")
    if metadata_dict.get("has_images"):
        format_score -= 20
        issues.append("Images detected - ATS cannot read text inside images")
    fonts = metadata_dict.get("fonts_count", 1)
    if fonts > 3:
        format_score -= 20
        issues.append(f"Too many fonts ({fonts}) - use maximum 2 fonts")
    elif fonts > 2:
        format_score -= 10
        issues.append("Consider reducing fonts to 2")
    format_score = max(0, format_score)

    structure_score = 100
    for section in ["experience", "education", "skills"]:
        if section not in sections_found:
            structure_score -= 25
            issues.append(f"Missing required section: {section.capitalize()}")
    has_dates = any(str(year) in cv_text for year in range(2000, 2027))
    if not has_dates:
        structure_score -= 15
        issues.append("No clear dates found in experience or education")
    if "summary" not in sections_found and "objective" not in sections_found:
        structure_score -= 10
        issues.append("Missing Summary or Objective section")
    structure_score = max(0, structure_score)

    content_score = 100
    action_verbs = [
        "managed",
        "led",
        "developed",
        "created",
        "implemented",
        "designed",
        "built",
        "achieved",
        "improved",
        "increased",
        "decreased",
        "launched",
        "delivered",
        "coordinated",
        "analyzed",
        "spearheaded",
        "executed",
        "optimized",
        "streamlined",
        "drove",
    ]
    verbs_found = sum(1 for v in action_verbs if v in cv_text)
    if verbs_found < 3:
        content_score -= 25
        issues.append("Too few action verbs - add more dynamic language")
    elif verbs_found < 6:
        content_score -= 10
        issues.append("Consider adding more action verbs")
    personal_info_kw = [
        "date of birth",
        "nationality",
        "marital status",
        "religion",
        "age",
        "gender",
        "photo",
        "picture",
    ]
    personal_found = [kw for kw in personal_info_kw if kw in cv_text]
    if personal_found:
        content_score -= 20
        issues.append(f"Personal info found that may hurt ATS: {', '.join(personal_found)}")
    if not any(char.isdigit() for char in cv_text):
        content_score -= 15
        issues.append("No quantifiable achievements found - add numbers and percentages")
    content_score = max(0, content_score)

    length_score = 100
    pages = metadata_dict.get("pages_count", 1)
    if pages < 1:
        length_score = 50
        issues.append("CV is too short - minimum 1 page")
    elif pages > 2:
        length_score -= 30
        issues.append(f"CV is {pages} pages - keep it to maximum 2 pages")
    length_score = max(0, length_score)

    ats_score = int(sum(c * 0.25 for c in [format_score, structure_score, content_score, length_score]))

    return {
        "ats_score": ats_score,
        "breakdown": {
            "format": format_score,
            "structure": structure_score,
            "content": content_score,
            "length": length_score,
        },
        "issues": issues,
    }


class TestATSCheckerLogic:
    def test_perfect_cv(self):
        meta = {
            "has_tables": False,
            "has_images": False,
            "fonts_count": 1,
            "pages_count": 1,
            "sections_found": ["experience", "education", "skills"],
            "cv_text": "Managed team of 10 engineers. Python, FastAPI. 2020-2024.",
        }
        result = _compute_ats_score(meta)
        assert result["ats_score"] >= 70
        assert result["breakdown"]["format"] >= 80

    def test_poor_cv(self):
        meta = {
            "has_tables": True,
            "has_images": True,
            "fonts_count": 5,
            "pages_count": 3,
            "sections_found": [],
            "cv_text": "my cv",
        }
        result = _compute_ats_score(meta)
        assert result["ats_score"] <= 50
        assert len(result["issues"]) >= 3

    def test_personal_info_detected(self):
        meta = {
            "has_tables": False,
            "has_images": False,
            "fonts_count": 1,
            "pages_count": 1,
            "sections_found": ["experience", "education", "skills"],
            "cv_text": "Date of birth: 1990-01-01, Nationality: Egyptian",
        }
        result = _compute_ats_score(meta)
        issues_text = ", ".join(result["issues"])
        assert "Personal info" in issues_text

    def test_missing_sections_detected(self):
        meta = {
            "has_tables": False,
            "has_images": False,
            "fonts_count": 1,
            "pages_count": 1,
            "sections_found": ["summary"],
            "cv_text": "Some text.",
        }
        result = _compute_ats_score(meta)
        issues = " ".join(result["issues"]).lower()
        assert "experience" in issues or "education" in issues

    def test_long_cv_deducts_points(self):
        meta = {
            "has_tables": False,
            "has_images": False,
            "fonts_count": 1,
            "pages_count": 4,
            "sections_found": ["experience", "education", "skills"],
            "cv_text": "Managed team. Python. 2020-2024.",
        }
        result = _compute_ats_score(meta)
        assert result["breakdown"]["length"] <= 70


# --- Report Builder Tests (mock entire chain object) ---


class TestReportBuilder:
    def _make_mock_chain(self):
        mock = MagicMock()
        mock.invoke.return_value = "Mocked career report content."
        return mock

    @pytest.fixture(autouse=True)
    def _setup(self):
        mock_chain = self._make_mock_chain()
        patcher = patch("agents.report_builder.chain", mock_chain, create=True)
        patcher.start()
        yield
        patcher.stop()

    def test_report_builds_from_analysis(self, sample_analysis, sample_job_matches):
        from agents.report_builder import report_builder_agent

        state = AgentState(
            cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
            analysis=sample_analysis,
            job_matches=sample_job_matches,
        )
        result = report_builder_agent(state)
        assert result.error is None
        assert result.final_report == "Mocked career report content."

    def test_report_fails_without_analysis(self):
        from agents.report_builder import report_builder_agent

        state = AgentState(file_path="/tmp/test.pdf")
        result = report_builder_agent(state)
        assert result.error is not None

    def test_report_fails_without_job_matches(self, sample_analysis):
        from agents.report_builder import report_builder_agent

        state = AgentState(
            cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
            analysis=sample_analysis,
        )
        result = report_builder_agent(state)
        assert result.error is not None

    def test_report_with_zero_scores(self):
        from agents.report_builder import report_builder_agent

        state = AgentState(
            cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
            analysis=AnalysisResult(
                strengths=[],
                weaknesses=["Everything"],
                suggestions=["Improve everything"],
                skills_extracted=[],
                ats_result=ATSResult(
                    ats_score=0,
                    breakdown=ATSBreakdown(format=0, structure=0, content=0, length=0),
                    issues=["No content"],
                ),
            ),
            job_matches=JobMatches(matched_jobs=[]),
        )
        result = report_builder_agent(state)
        assert result.error is None

    def test_report_with_missing_ats_result(self):
        from agents.report_builder import report_builder_agent

        state = AgentState(
            cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
            analysis=AnalysisResult(
                strengths=["Good"],
                weaknesses=["Bad"],
                suggestions=["Fix"],
                skills_extracted=["Python"],
            ),
            job_matches=JobMatches(matched_jobs=[]),
        )
        result = report_builder_agent(state)
        assert result.error is None

    def test_report_with_no_jobs(self, sample_analysis):
        from agents.report_builder import report_builder_agent

        state = AgentState(
            cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
            analysis=sample_analysis,
            job_matches=JobMatches(matched_jobs=[]),
        )
        result = report_builder_agent(state)
        assert result.error is None


# --- Job Matcher Tests (mock entire chain objects + retriever) ---


class TestJobMatcher:
    @pytest.fixture(autouse=True)
    def _setup(self):
        import agents.job_matcher  # noqa: F811

        mock_match = MagicMock()
        mock_match.invoke.return_value = json.dumps(
            {
                "matched_jobs": [
                    {
                        "title": "Software Engineer",
                        "link": "https://example.com/job",
                        "skills": "Python, Go",
                        "match_score": 90,
                        "matched_skills": ["Python"],
                        "missing_skills": ["Go"],
                        "reason": "Great Python match",
                    }
                ]
            }
        )
        mock_query = MagicMock()
        mock_query.invoke.return_value = "Python developer enhanced query"
        mock_retriever = MagicMock()
        mock_retriever.return_value = []

        agents.job_matcher.match_chain = mock_match
        agents.job_matcher.query_chain = mock_query
        agents.job_matcher.search_jobs = mock_retriever
        yield

    def test_job_matcher_success(self, sample_analysis):
        from agents.job_matcher import job_matcher_agent

        state = AgentState(
            cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
            analysis=sample_analysis,
        )
        result = job_matcher_agent(state)
        assert result.error is None
        assert len(result.job_matches.matched_jobs) == 1

    def test_job_matcher_fails_without_analysis(self):
        from agents.job_matcher import job_matcher_agent

        state = AgentState(file_path="/tmp/test.pdf")
        result = job_matcher_agent(state)
        assert result.error is not None
        assert "analysis" in result.error.lower()

    def test_job_matcher_json_parse(self):
        mock_match = MagicMock()
        mock_match.invoke.return_value = '{"matched_jobs": []}'
        mock_query = MagicMock()
        mock_query.invoke.return_value = "query"
        mock_retriever = MagicMock()
        mock_retriever.return_value = []

        with (
            patch("agents.job_matcher.match_chain", mock_match, create=True),
            patch("agents.job_matcher.query_chain", mock_query, create=True),
            patch("agents.job_matcher.search_jobs", mock_retriever),
        ):
            from agents.job_matcher import job_matcher_agent

            state = AgentState(
                cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"),
                analysis=AnalysisResult(
                    strengths=[],
                    weaknesses=[],
                    suggestions=[],
                    skills_extracted=["Python"],
                    ats_result=ATSResult(
                        ats_score=50, breakdown=ATSBreakdown(format=50, structure=50, content=50, length=50), issues=[]
                    ),
                ),
            )
            result = job_matcher_agent(state)
            assert result.error is None
            assert len(result.job_matches.matched_jobs) == 0


# --- Workflow Edge Tests ---


class TestWorkflowEdges:
    @pytest.fixture(autouse=True)
    def _patch_deps(self):
        with (
            patch("agents.cv_parser.fitz"),
            patch("agents.cv_parser.parse_cv_file"),
        ):
            yield

    def test_should_continue_no_error(self):
        from graph.workflow import should_continue

        state = AgentState(cv_data=CVData(raw_text="test", file_name="test.pdf", file_type="pdf"))
        assert should_continue(state) == "continue"

    def test_should_continue_with_error(self):
        from graph.workflow import should_continue

        state = AgentState(error="Something went wrong")
        assert should_continue(state) == "end"


# --- Schema Roundtrip Tests ---


class TestSchemaConsistency:
    def test_ats_breakdown_roundtrip(self):
        data = {"format": 80, "structure": 90, "content": 75, "length": 100}
        bd = ATSBreakdown(**data)
        assert bd.model_dump() == data

    def test_job_roundtrip(self):
        data = {
            "title": "Engineer",
            "link": "https://example.com",
            "skills": "Python",
            "match_score": 90,
            "matched_skills": ["Python"],
            "missing_skills": ["Go"],
            "reason": "Good fit",
        }
        job = Job(**data)
        assert job.model_dump() == data

    def test_cv_metadata_roundtrip(self):
        data = {
            "has_tables": False,
            "has_images": False,
            "sections_found": ["exp"],
            "sections_missing": ["edu"],
            "fonts_count": 2,
            "pages_count": 1,
            "length_pages": 1.0,
        }
        meta = CVMetadata(**data)
        assert meta.model_dump() == data
