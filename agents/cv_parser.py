# agents/cv_parser.py

import logging
import re

import fitz  # pymupdf

from models.schemas import AgentState, CVMetadata
from utils.file_handler import parse_cv_file

logger = logging.getLogger(__name__)

SECTIONS_KEYWORDS = [
    "experience",
    "education",
    "skills",
    "summary",
    "objective",
    "projects",
    "certifications",
    "languages",
    "references",
    "achievements",
    "awards",
    "volunteer",
    "publications",
]

CV_SECTION_PATTERNS = [
    r"\bexperience\b",
    r"\beducation\b",
    r"\bskills\b",
    r"\bsummary\b",
    r"\bobjective\b",
    r"\bprojects?\b",
    r"\bcertifications?\b",
    r"\blanguages?\b",
    r"\breferences?\b",
    r"\b(?:work\s+)?(?:history|experience)\b",
    r"\bemployment\b",
    r"\bacademic\s+(?:background|qualifications?)\b",
    r"\bprofessional\s+(?:experience|summary|background)\b",
    r"\btechnical\s+skills?\b",
    r"\bcore\s+competencies?\b",
]

TICKET_KEYWORDS = [
    "ticket",
    "boarding",
    "passenger",
    "flight",
    "seat",
    "gate",
    "departure",
    "arrival",
    "train",
    "railway",
    "receipt",
    "invoice",
    "order",
    "payment",
    "transaction",
    "purchase",
    "refund",
    "tax",
    "bill",
    "subscription",
    "warranty",
]


def validate_cv_text(text: str) -> tuple[bool, str]:
    if not text or len(text.strip()) < 50:
        return False, "The uploaded file contains no readable text. Please upload a valid CV (PDF or DOCX)."

    lower = text.lower()

    email_count = len(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    phone_count = len(re.findall(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", text))
    year_matches = re.findall(r"\b(?:19|20)\d{2}\b", text)
    year_count = len(year_matches)
    date_range = len(
        re.findall(
            r"(?:19|20)\d{2}\s*[-–to]+\s*(?:19|20)\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(?:19|20)\d{2}",
            text,
            re.IGNORECASE,
        )
    )

    section_score = 0
    for pat in CV_SECTION_PATTERNS:
        if re.search(pat, lower):
            section_score += 1

    ticket_score = 0
    for kw in TICKET_KEYWORDS:
        if kw in lower:
            ticket_score += 1

    has_email = email_count > 0
    has_phone = phone_count >= 1
    has_years = year_count >= 2
    has_date_ranges = date_range >= 1 or year_count >= 3
    has_sections = section_score >= 2
    has_name_pattern = bool(re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", text.strip()[:100]))
    has_length = len(text) > 300

    confidence = 0
    if has_email:
        confidence += 20
    if has_phone:
        confidence += 15
    if has_years:
        confidence += 10
    if has_date_ranges:
        confidence += 15
    if has_sections:
        confidence += 20
    if has_name_pattern:
        confidence += 10
    if has_length:
        confidence += 10

    if ticket_score >= 3:
        return False, (
            "This file appears to be a ticket, receipt, or invoice — not a CV/resume. "
            "Please upload a document that contains your work experience, education, and skills."
        )

    if confidence < 25:
        return False, (
            "This doesn't look like a CV/resume. A typical CV includes sections like "
            "Experience, Education, and Skills, along with your contact info. "
            "Please upload a valid CV in PDF or DOCX format."
        )

    if confidence < 40:
        return False, (
            "We couldn't confirm this is a CV/resume. It's missing common sections like "
            "work experience, education history, or contact details. "
            "Please upload a properly formatted CV."
        )

    return True, ""


def extract_metadata(file_path: str) -> CVMetadata:
    with fitz.open(file_path) as doc:
        pages_count = len(doc)
        has_tables = False
        has_images = False
        fonts_set = set()
        sections_found = []
        full_text = ""

        for page in doc:
            # Check images
            if page.get_images():
                has_images = True

            # Check tables
            if page.find_tables().tables:
                has_tables = True

            # Extract fonts
            for block in page.get_text("dict")["blocks"]:
                if block["type"] == 0:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            fonts_set.add(span["font"])

            full_text += page.get_text().lower()

    # Detect sections
    for section in SECTIONS_KEYWORDS:
        if section in full_text:
            sections_found.append(section)

    sections_missing = [s for s in SECTIONS_KEYWORDS if s not in sections_found]

    return CVMetadata(
        has_tables=has_tables,
        has_images=has_images,
        sections_found=sections_found,
        sections_missing=sections_missing,
        fonts_count=len(fonts_set),
        pages_count=pages_count,
        length_pages=float(pages_count),
    )


def cv_parser_agent(state: AgentState, file_path: str, file_name: str) -> AgentState:
    try:
        cv_data = parse_cv_file(file_path, file_name)

        if cv_data.file_type == "pdf":
            metadata = extract_metadata(file_path)
            cv_data.metadata = metadata

        is_valid, msg = validate_cv_text(cv_data.raw_text)
        if not is_valid:
            state.error = msg
            return state

        state.cv_data = cv_data

    except Exception as e:
        logger.error("CV parser agent error: %s", e, exc_info=True)
        state.error = f"Error parsing CV: {str(e)}"

    return state
