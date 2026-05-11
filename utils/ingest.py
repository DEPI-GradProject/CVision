import hashlib
import json
import logging
import os

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def _compute_faiss_hash(faiss_dir: str) -> str:
    hasher = hashlib.sha256()
    for root, _dirs, files in os.walk(faiss_dir):
        for fname in sorted(files):
            path = os.path.join(root, fname)
            with open(path, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()


def load_csv_to_faiss(csv_path: str = "Data/jobs.csv"):
    df = pd.read_csv(csv_path)

    documents = []
    for _, row in df.iterrows():
        content = f"Title: {row['Title']}\nSkills: {row['Skills']}"

        doc = Document(
            page_content=content,
            metadata={
                "title": str(row["Title"]),
                "link": str(row["Link"]),
                "price": str(row["Price"]),
                "skills": str(row["Skills"]),
            },
        )
        documents.append(doc)

    logger.info("Loading %s jobs into FAISS...", len(documents))

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local("Data/faiss_db")

    faiss_hash = _compute_faiss_hash("Data/faiss_db")
    hash_path = os.path.join("Data", "faiss_db", ".faiss_hash")
    with open(hash_path, "w") as f:
        f.write(json.dumps({"sha256": faiss_hash}))
    logger.info("FAISS index saved with hash: %s", faiss_hash)


if __name__ == "__main__":
    load_csv_to_faiss()
