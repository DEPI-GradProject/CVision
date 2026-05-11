import hashlib
import json
import logging
import os

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import settings

logger = logging.getLogger(__name__)

FAISS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data", "faiss_db")

_embeddings = None
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return _embeddings


def _verify_faiss_integrity() -> bool:
    hash_path = os.path.join(FAISS_DIR, ".faiss_hash")
    if not os.path.exists(hash_path):
        logger.warning("No FAISS hash file found at %s", hash_path)
        return False

    try:
        with open(hash_path) as f:
            stored = json.load(f)
    except (json.JSONDecodeError, KeyError):
        return False

    hasher = hashlib.sha256()
    for root, _dirs, files in os.walk(FAISS_DIR):
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
        if not os.path.exists(FAISS_DIR):
            raise FileNotFoundError(f"FAISS index not found at {FAISS_DIR}. Run ingest.py first.")

        integrity_ok = _verify_faiss_integrity()

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
            FAISS_DIR,
            get_embeddings(),
            allow_dangerous_deserialization=settings.faiss_allow_dangerous,
        )
    return _vectorstore


def search_jobs(query: str, k: int = 5):
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)

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
