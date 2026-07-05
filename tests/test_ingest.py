import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

pytest.importorskip("langchain")
pytest.importorskip("faiss")


@patch("utils.ingest.HuggingFaceEmbeddings")
def test_load_csv_to_faiss_creates_index(mock_embeddings):
    mock_faiss = MagicMock()
    mock_embeddings.return_value = MagicMock()

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test.csv")
        df = pd.DataFrame(
            {
                "Title": ["Python Dev", "Data Scientist"],
                "Link": ["http://a.com", "http://b.com"],
                "Price": ["$100", "$120"],
                "Skills": ["python, django", "ml, pytorch"],
            }
        )
        df.to_csv(csv_path, index=False)

        os.makedirs(os.path.join(tmpdir, "Data", "faiss_db"), exist_ok=True)

        with (
            patch("utils.ingest.FAISS") as mock_faiss_cls,
            patch("os.getcwd", return_value=tmpdir),
        ):
            mock_faiss_cls.from_documents.return_value = mock_faiss
            mock_faiss.__class__.save_local = MagicMock()

            from utils.ingest import load_csv_to_faiss

            load_csv_to_faiss(csv_path)

            mock_faiss_cls.from_documents.assert_called_once()
            docs = mock_faiss_cls.from_documents.call_args[0][0]
            assert len(docs) == 2
            assert "python" in docs[0].page_content.lower()


@patch("utils.ingest.HuggingFaceEmbeddings")
def test_load_csv_to_faiss_empty_csv(mock_embeddings):
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "empty.csv")
        pd.DataFrame(columns=["Title", "Link", "Price", "Skills"]).to_csv(csv_path, index=False)

        os.makedirs(os.path.join(tmpdir, "Data", "faiss_db"), exist_ok=True)

        with (
            patch("utils.ingest.FAISS") as mock_faiss_cls,
            patch("os.getcwd", return_value=tmpdir),
        ):
            from utils.ingest import load_csv_to_faiss

            load_csv_to_faiss(csv_path)
            docs = mock_faiss_cls.from_documents.call_args[0][0]
            assert len(docs) == 0
