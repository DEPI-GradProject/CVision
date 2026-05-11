import pytest

pytest.importorskip("fitz")
pytest.importorskip("docx")

from utils.file_handler import parse_cv_file


def test_parse_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text(
        "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        "xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        "0000000058 00000 n \n0000000115 00000 n \n"
        "trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )
    result = parse_cv_file(str(pdf_path), "test.pdf")
    assert result.file_name == "test.pdf"
    assert result.file_type == "pdf"
    assert result.raw_text is not None
