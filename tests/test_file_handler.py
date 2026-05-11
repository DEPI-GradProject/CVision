import pytest
pytest.importorskip("fitz")
pytest.importorskip("docx")

from utils.file_handler import parse_cv_file


def test_parse_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("%PDF-1.4 fake pdf content")
    result = parse_cv_file(str(pdf_path), "test.pdf")
    assert result.file_name == "test.pdf"
    assert result.file_type == "pdf"
    assert result.raw_text is not None
