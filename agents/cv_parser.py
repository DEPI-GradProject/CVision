# agents/cv_parser.py

import fitz  # pymupdf
from models.schemas import AgentState, CVMetadata
from utils.file_handler import parse_cv_file

SECTIONS_KEYWORDS = [
    "experience", "education", "skills", "summary", "objective",
    "projects", "certifications", "languages", "references",
    "achievements", "awards", "volunteer", "publications"
]

def extract_metadata(file_path: str) -> CVMetadata:
    doc = fitz.open(file_path)
    
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

    doc.close()

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
        length_pages=float(pages_count)
    )

def cv_parser_agent(state: AgentState, file_path: str, file_name: str) -> AgentState:
    try:
        cv_data = parse_cv_file(file_path, file_name)
        
        if cv_data.file_type == "pdf":
            metadata = extract_metadata(file_path)
            cv_data.metadata = metadata

        state.cv_data = cv_data

    except Exception as e:
        state.error = f"Error parsing CV: {str(e)}"

    return state