import hashlib
import json
import logging
import os
import re
import shutil
import tempfile

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import settings

logger = logging.getLogger(__name__)

FAISS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data", "faiss_db")

_embeddings = None
_vectorstore = None
_SAFE_FAISS_DIR = None


def _get_safe_faiss_path() -> str:
    global _SAFE_FAISS_DIR
    if _SAFE_FAISS_DIR is not None:
        return _SAFE_FAISS_DIR

    try:
        FAISS_DIR.encode("ascii")
        _SAFE_FAISS_DIR = FAISS_DIR
        return _SAFE_FAISS_DIR
    except UnicodeEncodeError:
        pass

    safe_dir = os.path.join(tempfile.gettempdir(), "cv_faiss_cache")
    if os.path.exists(safe_dir):
        shutil.rmtree(safe_dir)

    logger.info("Copying FAISS index from Unicode path to ASCII-safe path: %s", safe_dir)
    shutil.copytree(FAISS_DIR, safe_dir)
    _SAFE_FAISS_DIR = safe_dir
    return _SAFE_FAISS_DIR


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _verify_faiss_integrity(faiss_dir: str | None = None) -> bool:
    if faiss_dir is None:
        faiss_dir = FAISS_DIR
    hash_path = os.path.join(faiss_dir, ".faiss_hash")
    if not os.path.exists(hash_path):
        logger.warning("No FAISS hash file found at %s", hash_path)
        return False

    try:
        with open(hash_path) as f:
            stored = json.load(f)
    except (json.JSONDecodeError, KeyError):
        return False

    hasher = hashlib.sha256()
    for root, _dirs, files in os.walk(faiss_dir):
        for fname in sorted(files):
            if fname == ".faiss_hash":
                continue
            path = os.path.join(root, fname)
            with open(path, "rb") as f:
                hasher.update(f.read())

    return hasher.hexdigest() == stored.get("sha256")


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        safe_path = _get_safe_faiss_path()

        logger.info(
            "Loading FAISS from: %s (exists: %s, files: %s)",
            safe_path,
            os.path.exists(os.path.join(safe_path, "index.faiss")),
            os.listdir(safe_path) if os.path.exists(safe_path) else "N/A",
        )

        if not os.path.exists(os.path.join(safe_path, "index.faiss")):
            raise FileNotFoundError(f"FAISS index not found at {safe_path}. Run ingest.py first.")

        integrity_ok = _verify_faiss_integrity(safe_path)

        if not integrity_ok and not settings.faiss_allow_dangerous:
            raise RuntimeError(
                "FAISS index integrity check failed and faiss_allow_dangerous=False. "
                "Set FAISS_ALLOW_DANGEROUS=true in .env to load anyway, "
                "or re-run ingest.py to regenerate the index."
            )

        if not integrity_ok:
            logger.warning(
                "FAISS index integrity check FAILED — loading with allow_dangerous=True "
                "because FAISS_ALLOW_DANGEROUS is enabled."
            )

        _vectorstore = FAISS.load_local(
            safe_path,
            get_embeddings(),
            allow_dangerous_deserialization=settings.faiss_allow_dangerous,
        )
    return _vectorstore


def search_jobs(query: str, k: int = 5):
    sanitized = re.sub(r"[^\w\s\-.,;:!?()/@]", "", query)[:200]
    if not sanitized.strip():
        return []

    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(sanitized, k=k)

    jobs = []
    for doc in results:
        jobs.append(
            {
                "title": doc.metadata["title"],
                "link": doc.metadata["link"],
                "price": doc.metadata["price"],
                "skills": doc.metadata["skills"],
            }
        )

    return jobs
