from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fitz")
pytest.importorskip("docx")

from utils.file_handler import extract_text_from_docx, extract_text_from_pdf, parse_cv_file


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


def test_parse_docx(tmp_path):
    docx_path = tmp_path / "test.docx"
    docx_path.touch()
    with patch("utils.file_handler.Document") as mock_doc_cls:
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_doc.tables = []
        mock_doc_cls.return_value = mock_doc
        result = parse_cv_file(str(docx_path), "test.docx")
        assert result.file_name == "test.docx"
        assert result.file_type == "docx"


def test_parse_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_cv_file("resume.txt", "resume.txt")


def test_parse_unsupported_extension_no_dot():
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_cv_file("resume", "resume")


@patch("utils.file_handler.fitz")
def test_extract_text_from_pdf(mock_fitz):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Hello World"
    mock_doc.__iter__.return_value = [mock_page]
    mock_doc.__enter__.return_value = mock_doc
    mock_fitz.open.return_value = mock_doc

    text = extract_text_from_pdf("fake.pdf")
    assert text == "Hello World"


def _make_docx_mock(paragraphs_texts, table_cells_texts=None):
    mock_doc = MagicMock()
    paras = []
    for text in paragraphs_texts:
        p = MagicMock()
        p.text = text
        paras.append(p)
    mock_doc.paragraphs = paras

    tables = []
    for cells_texts in table_cells_texts or []:
        cells = []
        for txt in cells_texts:
            c = MagicMock()
            c.text = txt
            cells.append(c)
        row = MagicMock()
        row.cells = cells
        t = MagicMock()
        t.rows = [row]
        tables.append(t)
    mock_doc.tables = tables
    return mock_doc


@patch("utils.file_handler.Document")
def test_extract_text_from_docx(mock_document_cls):
    mock_doc = _make_docx_mock(["Hello", "World"])
    mock_document_cls.return_value = mock_doc

    text = extract_text_from_docx("fake.docx")
    assert text == "Hello\nWorld"


@patch("utils.file_handler.Document")
def test_extract_text_from_docx_with_tables(mock_document_cls):
    mock_doc = _make_docx_mock([], [["Cell Data"]])
    mock_document_cls.return_value = mock_doc

    text = extract_text_from_docx("fake.docx")
    assert text == "Cell Data"
