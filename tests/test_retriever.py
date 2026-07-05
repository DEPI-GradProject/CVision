import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("langchain")
pytest.importorskip("faiss")
pytest.importorskip("sentence_transformers")


@patch("utils.retriever.HuggingFaceEmbeddings")
def test_get_embeddings_lazy_init(mock_embeddings):
    from utils.retriever import get_embeddings

    emb1 = get_embeddings()
    emb2 = get_embeddings()
    assert emb1 is emb2
    mock_embeddings.assert_called_once()


def test_get_vectorstore_missing_index():
    with (
        patch("utils.retriever._get_safe_faiss_path", return_value="/nonexistent/path"),
        patch("utils.retriever.os.path.exists", return_value=False),
    ):
        from utils.retriever import get_vectorstore

        with pytest.raises(FileNotFoundError, match="FAISS index not found"):
            get_vectorstore()


@patch("utils.retriever.HuggingFaceEmbeddings")
def test_get_vectorstore_integrity_fail(mock_embeddings):
    with tempfile.TemporaryDirectory() as tmpdir:
        faiss_path = os.path.join(tmpdir, "index.faiss")
        with open(faiss_path, "w") as f:
            f.write("fake")
        hash_path = os.path.join(tmpdir, ".faiss_hash")
        with open(hash_path, "w") as f:
            json.dump({"sha256": "deadbeef"}, f)

        with (
            patch("utils.retriever._get_safe_faiss_path", return_value=tmpdir),
            patch("utils.retriever.settings") as mock_settings,
        ):
            mock_settings.faiss_allow_dangerous = False

            from utils.retriever import get_vectorstore

            with pytest.raises(RuntimeError, match="integrity check failed"):
                get_vectorstore()


@patch("utils.retriever.HuggingFaceEmbeddings")
def test_search_jobs_sanitizes_query(mock_embeddings):
    with (
        patch("utils.retriever.get_vectorstore") as mock_get_vs,
    ):
        mock_vs = MagicMock()
        mock_get_vs.return_value = mock_vs
        mock_vs.similarity_search.return_value = []

        from utils.retriever import search_jobs

        result = search_jobs("hello world", k=3)
        assert result == []
        mock_vs.similarity_search.assert_called_once_with("hello world", k=3)


@patch("utils.retriever.HuggingFaceEmbeddings")
def test_search_jobs_empty_query(mock_embeddings):
    from utils.retriever import search_jobs

    result = search_jobs("")
    assert result == []


@patch("utils.retriever.HuggingFaceEmbeddings")
def test_verify_faiss_integrity_no_hash(mock_embeddings):
    with tempfile.TemporaryDirectory() as tmpdir:
        from utils.retriever import _verify_faiss_integrity

        assert _verify_faiss_integrity(tmpdir) is False


@patch("utils.retriever.HuggingFaceEmbeddings")
def test_verify_faiss_integrity_valid_hash(mock_embeddings):
    import hashlib

    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "index.faiss")
        with open(index_path, "wb") as f:
            f.write(b"some binary data")

        hasher = hashlib.sha256()
        hasher.update(b"some binary data")
        actual_hash = hasher.hexdigest()

        hash_path = os.path.join(tmpdir, ".faiss_hash")
        with open(hash_path, "w") as f:
            json.dump({"sha256": actual_hash}, f)

        from utils.retriever import _verify_faiss_integrity

        assert _verify_faiss_integrity(tmpdir) is True
