from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fitz")
pytest.importorskip("docx")

from models.schemas import AgentState, CVMetadata


@patch("agents.cv_parser.fitz")
def test_extract_metadata_no_images_no_tables(mock_fitz):
    page = MagicMock()
    page.get_images.return_value = []
    page.find_tables.return_value.tables = []
    page.get_text = lambda *a, **kw: (
        {"blocks": [{"type": 0, "lines": [{"spans": [{"font": "Arial"}]}]}]}
        if kw or a == ("dict",)
        else "experience in python since 2020"
    )

    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_doc.__iter__.return_value = [page]
    mock_fitz.open.return_value = mock_doc

    from agents.cv_parser import extract_metadata

    result = extract_metadata("fake.pdf")
    assert isinstance(result, CVMetadata)
    assert result.has_tables is False
    assert result.has_images is False
    assert result.pages_count == 1
    assert "experience" in result.sections_found


@patch("agents.cv_parser.fitz")
def test_extract_metadata_with_tables_images(mock_fitz):
    def make_page():
        p = MagicMock()
        p.get_images.return_value = ["img"]
        p.find_tables.return_value.tables = ["t"]

        def get_text(*args, **kwargs):
            if args == ("dict",) or kwargs:
                return {
                    "blocks": [
                        {
                            "type": 0,
                            "lines": [
                                {
                                    "spans": [
                                        {"font": "Calibri"},
                                        {"font": "Arial"},
                                    ]
                                }
                            ],
                        }
                    ]
                }
            return "skills: python, java"

        p.get_text = get_text
        return p

    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2
    mock_doc.__iter__.return_value = [make_page(), make_page()]
    mock_fitz.open.return_value = mock_doc

    from agents.cv_parser import extract_metadata

    result = extract_metadata("fake.pdf")
    assert result.has_tables is True
    assert result.has_images is True
    assert result.pages_count == 2
    assert result.fonts_count == 2


@patch("agents.cv_parser.parse_cv_file")
@patch("agents.cv_parser.extract_metadata")
def test_cv_parser_agent_success(mock_extract, mock_parse):
    from agents.cv_parser import cv_parser_agent

    mock_cv = MagicMock()
    mock_cv.file_type = "pdf"
    mock_parse.return_value = mock_cv

    state = AgentState()
    result = cv_parser_agent(state, "/path/to/cv.pdf", "cv.pdf")
    assert result.error is None
    assert result.cv_data is not None
    mock_extract.assert_called_once_with("/path/to/cv.pdf")


@patch("agents.cv_parser.parse_cv_file")
def test_cv_parser_agent_docx_skips_metadata(mock_parse):
    from agents.cv_parser import cv_parser_agent

    mock_cv = MagicMock()
    mock_cv.file_type = "docx"
    mock_parse.return_value = mock_cv

    state = AgentState()
    with patch("agents.cv_parser.extract_metadata") as mock_extract:
        result = cv_parser_agent(state, "/path/to/cv.docx", "cv.docx")
        assert result.error is None
        assert result.cv_data is not None
        mock_extract.assert_not_called()


@patch("agents.cv_parser.parse_cv_file", side_effect=ValueError("corrupt file"))
def test_cv_parser_agent_error(mock_parse):
    from agents.cv_parser import cv_parser_agent

    state = AgentState()
    result = cv_parser_agent(state, "/path/to/bad.pdf", "bad.pdf")
    assert "Error parsing CV" in result.error
