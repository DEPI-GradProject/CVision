# agents/cv_analyzer.py

import json
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from config import settings
from models.schemas import AgentState, AnalysisResult, ATSBreakdown, ATSResult

llm = ChatGroq(model=settings.groq_model_large, temperature=0.3)

STANDARD_FONTS = ["arial", "calibri", "times new roman", "helvetica", "georgia", "verdana", "tahoma", "trebuchet"]

REQUIRED_SECTIONS = ["experience", "education", "skills"]
RECOMMENDED_SECTIONS = ["summary", "objective", "certifications", "projects"]

ACTION_VERBS = [
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

PERSONAL_INFO_KEYWORDS = [
    "date of birth",
    "nationality",
    "marital status",
    "religion",
    "age",
    "gender",
    "photo",
    "picture",
]


def compute_ats(data: dict) -> dict:
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
    elif fonts_count > 2:
        format_score -= 10
        issues.append("Consider reducing fonts to 2")
    format_score = max(0, format_score)

    structure_score = 100
    for section in REQUIRED_SECTIONS:
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
    action_verbs_found = sum(1 for verb in ACTION_VERBS if verb in cv_text)
    if action_verbs_found < 3:
        content_score -= 25
        issues.append("Too few action verbs - add more dynamic language")
    elif action_verbs_found < 6:
        content_score -= 10
        issues.append("Consider adding more action verbs")

    personal_info_found = [kw for kw in PERSONAL_INFO_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", cv_text)]
    if personal_info_found:
        content_score -= 20
        issues.append(f"Personal info found that may hurt ATS: {', '.join(personal_info_found)}")

    has_numbers = any(char.isdigit() for char in cv_text)
    if not has_numbers:
        content_score -= 15
        issues.append("No quantifiable achievements found - add numbers and percentages")
    content_score = max(0, content_score)

    length_score = 100
    if pages_count < 1:
        length_score = 50
        issues.append("CV is too short - minimum 1 page")
    elif pages_count > 2:
        length_score -= 30
        issues.append(f"CV is {pages_count} pages - keep it to maximum 2 pages")
    length_score = max(0, length_score)

    ats_score = int((format_score * 0.25) + (structure_score * 0.25) + (content_score * 0.25) + (length_score * 0.25))

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


analysis_prompt = PromptTemplate.from_template("""
You are a professional CV analyst. Analyze the following CV text and return JSON only.

CV Text:
{cv_text}

Return JSON with this exact format (no extra text, no markdown):
{{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."],
  "skills_extracted": ["..."]
}}
""")

analysis_chain = analysis_prompt | llm | StrOutputParser()


def cv_analyzer_agent(state: AgentState) -> AgentState:
    try:
        if state.cv_data is None:
            state.error = "No CV data found, run cv_parser first"
            return state

        metadata = state.cv_data.metadata

        ats_data = compute_ats(
            {
                "has_tables": metadata.has_tables if metadata else False,
                "has_images": metadata.has_images if metadata else False,
                "fonts_count": metadata.fonts_count if metadata else 1,
                "pages_count": metadata.pages_count if metadata else 1,
                "sections_found": metadata.sections_found if metadata else [],
                "cv_text": state.cv_data.raw_text,
            }
        )

        result = analysis_chain.invoke({"cv_text": state.cv_data.raw_text})

        clean = result
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        parsed = json.loads(clean)

        breakdown_data = ats_data["breakdown"]

        state.analysis = AnalysisResult(
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            suggestions=parsed.get("suggestions", []),
            skills_extracted=parsed.get("skills_extracted", []),
            ats_result=ATSResult(
                ats_score=ats_data["ats_score"],
                breakdown=ATSBreakdown(
                    format=breakdown_data["format"],
                    structure=breakdown_data["structure"],
                    content=breakdown_data["content"],
                    length=breakdown_data["length"],
                ),
                issues=ats_data["issues"],
            ),
        )

    except Exception as e:
        state.error = f"Error analyzing CV: {str(e)}"

    return state
