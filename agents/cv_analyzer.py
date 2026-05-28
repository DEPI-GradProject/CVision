# agents/cv_analyzer.py

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from models.schemas import AgentState, AnalysisResult, ATSResult, ATSBreakdown
from dotenv import load_dotenv
import json

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3
)

REQUIRED_SECTIONS = ["experience", "education", "skills"]
ACTION_VERBS = [
    "managed", "led", "developed", "created", "implemented",
    "designed", "built", "achieved", "improved", "increased",
    "decreased", "launched", "delivered", "coordinated", "analyzed",
    "spearheaded", "executed", "optimized", "streamlined", "drove"
]
PERSONAL_INFO_KEYWORDS = ["date of birth", "nationality", "marital status", "religion", "age", "gender"]

@tool
def ats_checker(metadata_json: str) -> str:
    """Calculate ATS score based on CV metadata."""
    data = json.loads(metadata_json)
    has_tables = data.get("has_tables", False)
    has_images = data.get("has_images", False)
    fonts_count = data.get("fonts_count", 1)
    pages_count = data.get("pages_count", 1)
    sections_found = [s.lower() for s in data.get("sections_found", [])]
    cv_text = data.get("cv_text", "").lower()
    issues = []

    format_score = 100
    if has_tables:
        format_score -= 30
        issues.append("Tables detected - ATS systems struggle to parse tables")
    if has_images:
        format_score -= 20
        issues.append("Images detected - ATS cannot read text inside images")
    if fonts_count > 3:
        format_score -= 20
        issues.append(f"Too many fonts ({fonts_count}) - use maximum 2 fonts")
    format_score = max(0, format_score)

    structure_score = 100
    for section in REQUIRED_SECTIONS:
        if section not in sections_found:
            structure_score -= 25
            issues.append(f"Missing required section: {section.capitalize()}")
    has_dates = any(str(year) in cv_text for year in range(2000, 2027))
    if not has_dates:
        structure_score -= 15
        issues.append("No clear dates found")
    if "summary" not in sections_found and "objective" not in sections_found:
        structure_score -= 10
        issues.append("Missing Summary or Objective section")
    structure_score = max(0, structure_score)

    content_score = 100
    action_verbs_found = sum(1 for verb in ACTION_VERBS if verb in cv_text)
    if action_verbs_found < 3:
        content_score -= 25
        issues.append("Too few action verbs")
    elif action_verbs_found < 6:
        content_score -= 10
        issues.append("Consider adding more action verbs")
    personal_info_found = [kw for kw in PERSONAL_INFO_KEYWORDS if kw in cv_text]
    if personal_info_found:
        content_score -= 20
        issues.append(f"Personal info found: {', '.join(personal_info_found)}")
    if not any(char.isdigit() for char in cv_text):
        content_score -= 15
        issues.append("No quantifiable achievements found")
    content_score = max(0, content_score)

    length_score = 100
    if pages_count < 1:
        length_score = 50
        issues.append("CV is too short")
    elif pages_count > 2:
        length_score -= 30
        issues.append(f"CV is {pages_count} pages - keep it to maximum 2 pages")
    length_score = max(0, length_score)

    ats_score = int((format_score * 0.25) + (structure_score * 0.25) + (content_score * 0.25) + (length_score * 0.25))

    return json.dumps({
        "ats_score": ats_score,
        "breakdown": {
            "format": format_score,
            "structure": structure_score,
            "content": content_score,
            "length": length_score
        },
        "issues": issues
    })

tools = [ats_checker]
agent = create_react_agent(llm, tools)

def cv_analyzer_agent(state: AgentState) -> AgentState:
    try:
        if state.cv_data is None:
            state.error = "No CV data found, run cv_parser first"
            return state

        cv_data = state.cv_data
        metadata = cv_data.metadata
        cv_text = cv_data.raw_text[:4000]

        metadata_json = json.dumps({
            "has_tables": metadata.has_tables if metadata else False,
            "has_images": metadata.has_images if metadata else False,
            "fonts_count": metadata.fonts_count if metadata else 1,
            "pages_count": metadata.pages_count if metadata else 1,
            "sections_found": metadata.sections_found if metadata else [],
            "cv_text": cv_text
        })

        result = agent.invoke({
            "messages": [HumanMessage(content=f"""
You are a professional CV analyst, ATS expert, and senior HR specialist.

You have two tasks:

1. Use the ats_checker tool with this metadata:
{metadata_json}

2. Analyze the CV text below as a senior HR specialist and provide:

- strengths: list of strong points in the CV
- weaknesses: list of weak points in the CV
- suggestions: list of actionable improvements
- skills_extracted: list of ALL technical and soft skills found
- years_of_experience: calculate total years of experience from the dates mentioned (return as float, e.g. 2.5)
- experience_level: based on years determine ONE of these exactly: "Internship", "Junior", "Mid-Level", "Senior", "Lead"
- target_job_title: suggest the BEST job title that fits this candidate's profile (e.g. "Backend Developer", "Data Scientist")

CV Text:
{cv_text}

Important rules:
- Calculate years_of_experience carefully from the dates in the CV
- If no experience found, set years_of_experience to 0 and experience_level to "Internship"
- target_job_title must be specific, not generic

Return your final answer as JSON only:
{{
  "strengths": [...],
  "weaknesses": [...],
  "suggestions": [...],
  "skills_extracted": [...],
  "years_of_experience": 2.5,
  "experience_level": "Junior",
  "target_job_title": "Backend Developer",
  "ats_result": {{
    "ats_score": 0,
    "breakdown": {{"format": 0, "structure": 0, "content": 0, "length": 0}},
    "issues": [...]
  }}
}}
""")]
        })

        last_message = result["messages"][-1].content
        clean = last_message
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        parsed = json.loads(clean)
        ats_data = parsed.get("ats_result", {})
        breakdown_data = ats_data.get("breakdown", {})

        state.analysis = AnalysisResult(
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            suggestions=parsed.get("suggestions", []),
            skills_extracted=parsed.get("skills_extracted", []),
            years_of_experience=parsed.get("years_of_experience", 0),
            experience_level=parsed.get("experience_level", "Junior"),
            target_job_title=parsed.get("target_job_title", ""),
            ats_result=ATSResult(
                ats_score=ats_data.get("ats_score", 0),
                breakdown=ATSBreakdown(
                    format=breakdown_data.get("format", 0),
                    structure=breakdown_data.get("structure", 0),
                    content=breakdown_data.get("content", 0),
                    length=breakdown_data.get("length", 0)
                ),
                issues=ats_data.get("issues", [])
            )
        )

    except Exception as e:
        state.error = f"Error analyzing CV: {str(e)}"

    return state